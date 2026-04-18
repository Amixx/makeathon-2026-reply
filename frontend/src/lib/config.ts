const env = import.meta.env;

export const config = {
  agentUrl: env.VITE_AGENT_URL ?? "http://localhost:8000",
  elevenLabsApiKey: env.VITE_ELEVENLABS_API_KEY ?? "",
  elevenLabsVoiceId: env.VITE_ELEVENLABS_VOICE_ID ?? "JBFqnCBsd6RMkjVDRZzb",
  elevenLabsModelId: env.VITE_ELEVENLABS_MODEL_ID ?? "eleven_multilingual_v2",
  elevenLabsSttModel: env.VITE_ELEVENLABS_STT_MODEL ?? "scribe_v2",
} as const;

export function isVoiceConfigured(): boolean {
  return config.elevenLabsApiKey.length > 0;
}
