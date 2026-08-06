/**
 * Audio-file helpers shared by the recorder (import path) and the API client
 * (multipart filename). The accepted type list mirrors `_AUDIO_ALLOWED_CONTENT_TYPES`
 * in the BFF's `routes.py`: rejecting an unusable file in the browser is far kinder
 * than letting an operator wait through an upload that ends in a 415.
 */

export const MAX_AUDIO_FILE_BYTES = 25 * 1024 * 1024

/** Content types the BFF accepts on POST /v1/knowledge/interviews/{id}/audio. */
export const ACCEPTED_AUDIO_TYPES = ['audio/webm', 'audio/ogg', 'audio/wav', 'audio/mpeg', 'audio/mp4'] as const

export type AcceptedAudioType = (typeof ACCEPTED_AUDIO_TYPES)[number]

/**
 * Browsers and operating systems disagree about audio MIME types: the same .wav
 * arrives as `audio/wav`, `audio/x-wav` or `audio/wave` depending on the platform.
 * Fold the common spellings onto the canonical type the backend expects.
 */
const TYPE_ALIASES: Record<string, AcceptedAudioType> = {
  'audio/wav': 'audio/wav',
  'audio/wave': 'audio/wav',
  'audio/x-wav': 'audio/wav',
  'audio/x-pn-wav': 'audio/wav',
  'audio/vnd.wave': 'audio/wav',
  'audio/mpeg': 'audio/mpeg',
  'audio/mp3': 'audio/mpeg',
  'audio/x-mp3': 'audio/mpeg',
  'audio/x-mpeg': 'audio/mpeg',
  'audio/mp4': 'audio/mp4',
  'audio/m4a': 'audio/mp4',
  'audio/x-m4a': 'audio/mp4',
  'audio/webm': 'audio/webm',
  'video/webm': 'audio/webm',
  'audio/ogg': 'audio/ogg',
  'audio/x-ogg': 'audio/ogg',
  'audio/opus': 'audio/ogg',
  'audio/vorbis': 'audio/ogg',
}

/** Last-resort mapping for files the browser reports as octet-stream or blank. */
const EXTENSION_TYPES: Record<string, AcceptedAudioType> = {
  wav: 'audio/wav',
  wave: 'audio/wav',
  mp3: 'audio/mpeg',
  m4a: 'audio/mp4',
  mp4: 'audio/mp4',
  webm: 'audio/webm',
  ogg: 'audio/ogg',
  oga: 'audio/ogg',
  opus: 'audio/ogg',
}

const TYPE_EXTENSIONS: Record<AcceptedAudioType, string> = {
  'audio/wav': 'wav',
  'audio/mpeg': 'mp3',
  'audio/mp4': 'm4a',
  'audio/webm': 'webm',
  'audio/ogg': 'ogg',
}

/** `accept` value for the file picker; extensions included because iOS ignores MIME-only lists. */
export const AUDIO_FILE_ACCEPT = 'audio/*,.wav,.mp3,.m4a,.mp4,.webm,.ogg,.oga,.opus'

function fileExtension(fileName: string): string {
  const dot = fileName.lastIndexOf('.')
  return dot >= 0 ? fileName.slice(dot + 1).toLowerCase() : ''
}

/**
 * Resolve a file to a content type the backend accepts, or `null` when it is not
 * usable audio. Falls back to the filename extension because Safari and some
 * Android file providers hand over `application/octet-stream` for perfectly good audio.
 */
export function normalizeAudioType(rawType: string | undefined, fileName = ''): AcceptedAudioType | null {
  const bare = (rawType ?? '').split(';')[0].trim().toLowerCase()
  const byType = TYPE_ALIASES[bare]
  if (byType) {
    return byType
  }
  return EXTENSION_TYPES[fileExtension(fileName)] ?? null
}

/** Filename extension to use when posting a blob of this type. */
export function audioExtensionFor(mimeType: string | undefined): string {
  const normalized = normalizeAudioType(mimeType)
  return normalized ? TYPE_EXTENSIONS[normalized] : 'bin'
}

/**
 * Read the duration of an audio URL via a detached media element. Resolves to 0
 * rather than rejecting: duration is metadata for the review screen, so a codec
 * the browser cannot introspect must not block an otherwise valid import.
 */
export function probeAudioDuration(url: string, timeoutMs = 5000): Promise<number> {
  return new Promise((resolve) => {
    if (typeof document === 'undefined') {
      resolve(0)
      return
    }
    const audio = document.createElement('audio')
    let settled = false
    let timer: ReturnType<typeof setTimeout> | undefined

    const finish = (value: number) => {
      if (settled) {
        return
      }
      settled = true
      if (timer !== undefined) {
        clearTimeout(timer)
      }
      audio.onloadedmetadata = null
      audio.onerror = null
      audio.removeAttribute('src')
      resolve(Number.isFinite(value) && value > 0 ? value : 0)
    }

    timer = setTimeout(() => finish(0), timeoutMs)
    audio.preload = 'metadata'
    audio.onloadedmetadata = () => finish(audio.duration)
    audio.onerror = () => finish(0)
    audio.src = url
  })
}
