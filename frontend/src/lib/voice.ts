import { config } from './config';

export type TranscribeResult = {
  text: string;
  fields: {
    vision?: string;
    interests?: string[];
    interest?: string;
    blockers?: string;
    program?: string;
    semester?: string;
  };
  summary?: string;
};

export type TranscribeBlockersResult = {
  text: string;
  fields: {
    blockers?: string;
    tags?: string[];
  };
  summary?: string;
};

function filenameForBlob(blob: Blob): string {
  const type = (blob.type || '').toLowerCase();
  if (type.includes('mp4')) return 'voice-memo.mp4';
  if (type.includes('ogg')) return 'voice-memo.ogg';
  if (type.includes('mpeg') || type.includes('mp3')) return 'voice-memo.mp3';
  if (type.includes('wav')) return 'voice-memo.wav';
  if (type.includes('m4a')) return 'voice-memo.m4a';
  return 'voice-memo.webm';
}

async function postAudio<T>(path: string, blob: Blob): Promise<T> {
  const form = new FormData();
  form.append('audio', blob, filenameForBlob(blob));
  const res = await fetch(`${config.agentUrl}${path}`, {
    method: 'POST',
    body: form,
  });
  if (!res.ok) {
    const data = (await res.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(data?.detail || `transcribe failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export function transcribeAudio(blob: Blob): Promise<TranscribeResult> {
  return postAudio<TranscribeResult>('/agent/voice/transcribe', blob);
}

export function transcribeBlockers(blob: Blob): Promise<TranscribeBlockersResult> {
  return postAudio<TranscribeBlockersResult>('/agent/voice/transcribe-blockers', blob);
}
