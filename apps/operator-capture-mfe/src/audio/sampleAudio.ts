/**
 * The sample interview shipped with the app, so anyone can exercise the whole
 * capture flow without a microphone or a quiet room.
 *
 * The audio narrates `services/knowledge-orchestrator/fixtures/interview_transcript.json`
 * verbatim (see `scripts/generate-sample-audio.ps1`), which is the same fixture the
 * backend returns when it transcribes in demo mode. Importing the sample therefore
 * produces a transcript that matches what you just heard.
 *
 * The interview is synthetic: a fictional persona, no real personal data.
 */

export const SAMPLE_AUDIO = {
  fileName: 'blast-furnace-hearth-cooling-en.wav',
  mimeType: 'audio/wav',
  /** Matching entry in `DOMAINS`, so the drafted procedure classifies correctly. */
  domain: 'Blast Furnace',
  language: 'en',
} as const

export function sampleAudioUrl(): string {
  const base = typeof import.meta.env?.BASE_URL === 'string' ? import.meta.env.BASE_URL : '/'
  return `${base.endsWith('/') ? base : `${base}/`}samples/${SAMPLE_AUDIO.fileName}`
}

/**
 * Fetch the bundled sample as a File so it goes through exactly the same import
 * path as a file the operator picked themselves.
 */
export async function loadSampleAudioFile(signal?: AbortSignal): Promise<File> {
  const response = await fetch(sampleAudioUrl(), { signal })
  if (!response.ok) {
    throw new Error(`Sample audio unavailable (HTTP ${response.status}).`)
  }
  const blob = await response.blob()
  return new File([blob], SAMPLE_AUDIO.fileName, { type: SAMPLE_AUDIO.mimeType })
}
