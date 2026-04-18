from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

import yaml

from .audio import MicrophoneRecorder, play_pcm_bytes
from .config import load_settings
from .elevenlabs_client import ElevenLabsClient
from .models import SessionState, TranscriptResult
from .question_agent import QuestionAgent
from .response_cache import ResponseCache
from .storage import SessionStore

_FINISH_COMMANDS = {"done", "exit", "quit", "stop", "finish"}


class VoiceInterviewApp:
    def __init__(
        self,
        *,
        text_only: bool,
        no_tts: bool,
        pre_warm: bool,
        session_id: str | None,
        initial_context_path: Path | None,
    ) -> None:
        self.settings = load_settings()
        self.store = SessionStore(self.settings.logs_dir)
        initial_context = self._load_initial_context(initial_context_path)
        self.state = SessionState.create(initial_context=initial_context, session_id=session_id)
        self.question_agent = QuestionAgent(self.settings)
        self.voice_client = ElevenLabsClient(self.settings)
        self.response_cache = ResponseCache(self.settings.cache_dir, self.voice_client)
        self.recorder = MicrophoneRecorder(sample_rate=self.settings.recording_sample_rate)
        self.text_only = text_only
        self.no_tts = no_tts
        self.pre_warm = pre_warm

    async def run(self) -> None:
        log_path = self.store.save(self.state)
        print(f"Session: {self.state.session_id}  |  Log: {log_path}")
        print("Press Ctrl-C at any time to finish and save.\n")

        if self.pre_warm and not self.no_tts:
            await self.response_cache.pre_warm()

        try:
            await self._opening_turn()
            turns_taken = 0
            while not self.state.completed and turns_taken < self.settings.max_turns:
                transcript = await self._collect_user_turn()
                if transcript is None:
                    break
                text = transcript.text.strip()
                if not text:
                    print("(Nothing captured — try again.)")
                    continue
                self.state.add_user_turn(transcript)
                self.store.save(self.state)
                await self._assistant_turn(latest_user_text=text)
                turns_taken += 1
        except KeyboardInterrupt:
            print("\nStopping.")

        self._print_summary()

    async def _opening_turn(self) -> None:
        opening = (
            "Hi, I'm your career copilot. I'll ask a few short questions so I can understand "
            "what kind of future you want to build. To start, what kind of work or direction "
            "feels most exciting to you right now?"
        )
        self.state.add_assistant_event(opening, stage="intro", meta={"goal": "start the interview"})
        self.store.save(self.state)
        print(f"Coach: {opening}\n")
        if not self.no_tts:
            try:
                await self.voice_client.play_streaming(opening)
            except Exception as exc:  # noqa: BLE001
                print(f"[voice] TTS failed: {exc}")

    async def _assistant_turn(self, latest_user_text: str | None) -> None:
        if not self.no_tts:
            sr = self.settings.elevenlabs_tts_sample_rate

            # Pick regex-matched response (or generic filler) and get its cached audio
            filler_text = self.response_cache.match_text(latest_user_text or "")
            filler_audio = await self.response_cache.get_audio(filler_text)

            # Kick off LLM in background, then immediately play filler from cache
            decision_task = asyncio.create_task(
                self.question_agent.decide(self.state, latest_user_text)
            )
            await asyncio.to_thread(play_pcm_bytes, filler_audio, sr)

            # LLM is usually done by now; wait if not
            decision = await decision_task

            self.state.apply_decision(decision)
            reply = decision.spoken_reply or self._fallback_reply(decision)
            self.state.add_assistant_turn(reply, decision)
            self.store.save(self.state)
            print(f"Coach: {reply}\n")
            try:
                await self.voice_client.play_streaming(reply)
            except Exception as exc:  # noqa: BLE001
                print(f"[voice] TTS failed: {exc}")
        else:
            decision = await self.question_agent.decide(self.state, latest_user_text)
            self.state.apply_decision(decision)
            reply = decision.spoken_reply or self._fallback_reply(decision)
            self.state.add_assistant_turn(reply, decision)
            self.store.save(self.state)
            print(f"Coach: {reply}\n")

    def _fallback_reply(self, decision) -> str:
        if decision.completion_signal:
            return decision.closing_summary or "Thanks, that gives me a solid picture. Let's stop here."
        return f"Thanks, that helps. {decision.question}" if decision.question else "Tell me a bit more."

    async def _collect_user_turn(self) -> TranscriptResult | None:
        if self.text_only:
            try:
                text = input("You (or 'done' to finish): ").strip()
            except (EOFError, KeyboardInterrupt):
                return None
            if text.casefold() in _FINISH_COMMANDS:
                return None
            return TranscriptResult(text=text)

        try:
            wav_bytes = await asyncio.to_thread(
                self.recorder.record_with_vad,
                self.settings.vad_rms_threshold,
                self.settings.vad_silence_duration,
            )
            transcript = await self.voice_client.transcribe(wav_bytes)
            print(f"You: {transcript.text}")
            return transcript
        except KeyboardInterrupt:
            return None
        except Exception as exc:  # noqa: BLE001
            print(f"[voice] capture/transcription failed ({exc}), falling back to text.")
            try:
                text = input("You (or 'done' to finish): ").strip()
            except (EOFError, KeyboardInterrupt):
                return None
            if text.casefold() in _FINISH_COMMANDS:
                return None
            return TranscriptResult(text=text)

    def _print_summary(self) -> None:
        self.store.save(self.state)
        log_path = self.store.path_for(self.state.session_id)
        print("\n--- Session saved ---")
        print(f"Log: {log_path}")
        profile = self.state.profile
        if profile:
            print("\nCaptured profile:")
            for key, value in profile.items():
                if value:
                    print(f"  {key.replace('_', ' ').capitalize()}: {value}")
        print()

    def _load_initial_context(self, initial_context_path: Path | None) -> dict:
        if initial_context_path is None:
            return {}
        if not initial_context_path.exists():
            raise FileNotFoundError(f"Initial context file not found: {initial_context_path}")
        return yaml.safe_load(initial_context_path.read_text(encoding="utf-8")) or {}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the local voice interview agent.")
    parser.add_argument("--initial-context", type=Path, default=None)
    parser.add_argument("--session-id", default=None)
    parser.add_argument("--text-only", action="store_true", help="Keyboard input, no mic/speaker.")
    parser.add_argument("--no-tts", action="store_true", help="Use mic but skip speaker output.")
    parser.add_argument(
        "--pre-warm",
        action="store_true",
        help="Pre-generate all cached filler audio before starting (recommended for demos).",
    )
    return parser.parse_args()


async def _main() -> None:
    args = parse_args()
    app = VoiceInterviewApp(
        text_only=args.text_only,
        no_tts=args.no_tts,
        pre_warm=args.pre_warm,
        session_id=args.session_id,
        initial_context_path=args.initial_context,
    )
    await app.run()


def cli() -> None:
    asyncio.run(_main())


if __name__ == "__main__":
    cli()
