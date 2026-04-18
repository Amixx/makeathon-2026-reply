import { config } from './config';

export type TranscribeResult = {
  text: string;
  fields: {
    vision?: string;
    interests?: string[];
    blockers?: string;
  };
};

export async function transcribeAudio(blob: Blob): Promise<TranscribeResult> {
  const form = new FormData();
  form.append('audio', blob, 'vision.webm');
  const res = await fetch(`${config.agentUrl}/agent/voice/transcribe`, {
    method: 'POST',
    body: form,
  });
  if (!res.ok) throw new Error(`transcribe failed: ${res.status}`);
  return res.json() as Promise<TranscribeResult>;
}
