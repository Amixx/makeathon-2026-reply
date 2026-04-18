import { config, isVoiceConfigured } from "./config";

const ELEVENLABS_BASE = "https://api.elevenlabs.io/v1";

function pickMimeType(): string {
  const candidates = [
    "audio/webm;codecs=opus",
    "audio/webm",
    "audio/mp4",
    "audio/ogg;codecs=opus",
  ];
  for (const c of candidates) {
    if (
      typeof MediaRecorder !== "undefined" &&
      MediaRecorder.isTypeSupported?.(c)
    ) {
      return c;
    }
  }
  return "";
}

export type Recording = {
  stop: () => Promise<Blob>;
};

export async function startRecording(): Promise<Recording> {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const mimeType = pickMimeType();
  const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : {});
  const chunks: Blob[] = [];
  recorder.addEventListener("dataavailable", (e) => {
    if (e.data && e.data.size > 0) chunks.push(e.data);
  });
  recorder.start();

  return {
    stop: () =>
      new Promise<Blob>((resolve) => {
        recorder.addEventListener(
          "stop",
          () => {
            for (const track of stream.getTracks()) track.stop();
            resolve(
              new Blob(chunks, { type: recorder.mimeType || "audio/webm" }),
            );
          },
          { once: true },
        );
        recorder.stop();
      }),
  };
}

export async function transcribe(blob: Blob): Promise<string> {
  if (!isVoiceConfigured()) {
    throw new Error("ElevenLabs API key is not configured.");
  }
  const form = new FormData();
  const ext = blob.type.includes("mp4") ? "m4a" : "webm";
  form.append("file", blob, `recording.${ext}`);
  form.append("model_id", config.elevenLabsSttModel);

  const res = await fetch(`${ELEVENLABS_BASE}/speech-to-text`, {
    method: "POST",
    headers: { "xi-api-key": config.elevenLabsApiKey },
    body: form,
  });
  if (!res.ok) {
    throw new Error(`ElevenLabs STT failed: ${res.status} ${await res.text()}`);
  }
  const data = (await res.json()) as { text?: string };
  return (data.text ?? "").trim();
}

export async function speak(text: string): Promise<HTMLAudioElement> {
  if (!isVoiceConfigured()) {
    throw new Error("ElevenLabs API key is not configured.");
  }
  if (!text.trim()) throw new Error("No text to speak.");

  const url = `${ELEVENLABS_BASE}/text-to-speech/${encodeURIComponent(
    config.elevenLabsVoiceId,
  )}/stream?output_format=mp3_44100_128`;

  const res = await fetch(url, {
    method: "POST",
    headers: {
      "xi-api-key": config.elevenLabsApiKey,
      "content-type": "application/json",
    },
    body: JSON.stringify({
      text,
      model_id: config.elevenLabsModelId,
    }),
  });
  if (!res.ok) {
    throw new Error(`ElevenLabs TTS failed: ${res.status} ${await res.text()}`);
  }
  const blob = await res.blob();
  const audio = new Audio(URL.createObjectURL(blob));
  await audio.play();
  return audio;
}
