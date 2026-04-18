import { useCallback, useRef, useState } from 'react';

export type VoiceRecorderState = {
  listening: boolean;
  blob: Blob | null;
  error: string | null;
  start: () => Promise<void>;
  stop: () => Promise<Blob | null>;
};

function pickMimeType(): string {
  const candidates = [
    'audio/webm;codecs=opus',
    'audio/webm',
    'audio/mp4',
    'audio/ogg;codecs=opus',
  ];
  for (const c of candidates) {
    if (typeof MediaRecorder !== 'undefined' && MediaRecorder.isTypeSupported?.(c)) {
      return c;
    }
  }
  return '';
}

export function useVoiceRecorder(): VoiceRecorderState {
  const [listening, setListening] = useState(false);
  const [blob, setBlob] = useState<Blob | null>(null);
  const [error, setError] = useState<string | null>(null);

  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const resolveRef = useRef<((b: Blob) => void) | null>(null);

  const start = useCallback(async () => {
    try {
      setError(null);
      setBlob(null);
      chunksRef.current = [];

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const mimeType = pickMimeType();
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : {});
      recorderRef.current = recorder;

      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = () => {
        const finalBlob = new Blob(chunksRef.current, {
          type: recorder.mimeType || 'audio/webm',
        });
        setBlob(finalBlob);
        setListening(false);
        for (const track of stream.getTracks()) track.stop();
        resolveRef.current?.(finalBlob);
        resolveRef.current = null;
      };

      recorder.start(250); // collect chunks every 250ms
      setListening(true);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
      setListening(false);
    }
  }, []);

  const stop = useCallback((): Promise<Blob | null> => {
    const recorder = recorderRef.current;
    if (!recorder || recorder.state === 'inactive') {
      setListening(false);
      return Promise.resolve(null);
    }
    return new Promise<Blob | null>((resolve) => {
      resolveRef.current = resolve;
      recorder.stop();
    });
  }, []);

  return { listening, blob, error, start, stop };
}
