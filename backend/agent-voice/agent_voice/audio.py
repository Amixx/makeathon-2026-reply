from __future__ import annotations

import io
import shutil
import subprocess
import sys
import tempfile
import wave


def play_pcm_bytes(pcm: bytes, sample_rate: int = 22050) -> None:
    """Play raw int16 mono PCM bytes via sounddevice. Blocks until done."""
    import numpy as np
    import sounddevice as sd

    audio = np.frombuffer(pcm, dtype="<i2")
    sd.play(audio, samplerate=sample_rate)
    sd.wait()


class MicrophoneRecorder:
    def __init__(self, sample_rate: int = 16000) -> None:
        self.sample_rate = sample_rate

    def record_with_vad(
        self,
        rms_threshold: int = 500,
        silence_duration: float = 1.2,
        max_duration: float = 30.0,
        start_timeout: float = 15.0,
    ) -> bytes:
        try:
            import numpy as np
            import sounddevice as sd
        except ImportError as exc:
            raise RuntimeError("sounddevice/numpy not installed; use --text-only.") from exc

        CHUNK = 512
        silence_limit = int(silence_duration * self.sample_rate / CHUNK)
        max_chunks = int(max_duration * self.sample_rate / CHUNK)
        timeout_chunks = int(start_timeout * self.sample_rate / CHUNK)

        chunks: list[bytes] = []
        state = "waiting"
        silence_count = 0
        speech_count = 0
        waiting_count = 0

        print("Listening...", flush=True)

        with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype="int16", blocksize=CHUNK) as stream:
            while len(chunks) < max_chunks:
                data, _ = stream.read(CHUNK)
                rms = int(np.sqrt(np.mean(data.astype(np.float32) ** 2)))
                is_speech = rms > rms_threshold

                if state == "waiting":
                    waiting_count += 1
                    if is_speech:
                        state = "speaking"
                        chunks.append(data.copy().tobytes())
                        speech_count = 1
                    elif waiting_count >= timeout_chunks:
                        raise RuntimeError("No speech detected within timeout.")
                else:  # speaking
                    chunks.append(data.copy().tobytes())
                    if is_speech:
                        silence_count = 0
                        speech_count += 1
                    else:
                        silence_count += 1
                        if silence_count >= silence_limit:
                            break

        if not chunks:
            raise RuntimeError("No speech captured.")

        audio_bytes = b"".join(chunks)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_bytes)
        return buf.getvalue()

    def record_wav_bytes(self) -> bytes:
        """Legacy Enter-to-start/stop recording. Kept for fallback."""
        try:
            import sounddevice as sd
        except ImportError as exc:
            raise RuntimeError("sounddevice is not installed; use --text-only instead.") from exc

        chunks: list[bytes] = []

        def callback(indata, _frames, _time_info, status) -> None:
            if status:
                print(f"[audio] recorder status: {status}", file=sys.stderr)
            chunks.append(indata.copy().tobytes())

        input("\nPress Enter to start recording.")
        with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype="int16", callback=callback):
            input("Recording... press Enter to stop. ")

        audio_bytes = b"".join(chunks)
        if not audio_bytes:
            raise RuntimeError("No microphone audio was captured.")

        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_bytes)
        return buffer.getvalue()


class LocalAudioPlayer:
    def play_mp3(self, audio_bytes: bytes) -> None:
        player_cmd = self._player_command()
        if player_cmd is None:
            raise RuntimeError("No local audio player found; use --no-tts or --text-only.")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp:
            temp.write(audio_bytes)
            temp_path = temp.name

        try:
            subprocess.run(
                [*player_cmd, temp_path],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        finally:
            try:
                from pathlib import Path

                Path(temp_path).unlink(missing_ok=True)
            except OSError:
                pass

    @staticmethod
    def _player_command() -> list[str] | None:
        if sys.platform == "darwin" and shutil.which("afplay"):
            return ["afplay"]
        if shutil.which("ffplay"):
            return ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"]
        if shutil.which("mpg123"):
            return ["mpg123", "-q"]
        return None
