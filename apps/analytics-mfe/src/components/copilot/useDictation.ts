import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

/**
 * Minimal typings for the Web Speech API. It is still a draft specification and
 * is not in `lib.dom.d.ts`, so the surface actually used here is declared
 * locally rather than pulling in an ambient dependency.
 */
interface SpeechRecognitionAlternativeLike {
  transcript: string
}

interface SpeechRecognitionResultLike {
  readonly length: number
  isFinal: boolean
  [index: number]: SpeechRecognitionAlternativeLike
}

interface SpeechRecognitionEventLike {
  resultIndex: number
  results: {
    readonly length: number
    [index: number]: SpeechRecognitionResultLike
  }
}

interface SpeechRecognitionLike {
  lang: string
  continuous: boolean
  interimResults: boolean
  start(): void
  stop(): void
  abort(): void
  onresult: ((event: SpeechRecognitionEventLike) => void) | null
  onerror: (() => void) | null
  onend: (() => void) | null
}

type SpeechRecognitionCtor = new () => SpeechRecognitionLike

function recognitionCtor(): SpeechRecognitionCtor | null {
  if (typeof window === 'undefined') {
    return null
  }
  const scope = window as unknown as {
    SpeechRecognition?: SpeechRecognitionCtor
    webkitSpeechRecognition?: SpeechRecognitionCtor
  }
  return scope.SpeechRecognition ?? scope.webkitSpeechRecognition ?? null
}

/** BCP-47 tags the recogniser understands, keyed by our two-letter language. */
const RECOGNITION_LOCALES: Record<string, string> = {
  en: 'en-US',
  fr: 'fr-FR',
  de: 'de-DE',
  nl: 'nl-NL',
  es: 'es-ES',
}

export interface Dictation {
  /** False when the browser has no Web Speech API; the button stays disabled. */
  supported: boolean
  listening: boolean
  start(): void
  stop(): void
}

/**
 * Dictation is browser-side on purpose: it keeps audio off the NovaSteel
 * backend entirely, so no consent or retention obligation is created by the
 * chat composer. Browsers without the API simply get a disabled microphone.
 */
export function useDictation(
  language: string,
  onTranscript: (text: string) => void,
): Dictation {
  const [listening, setListening] = useState(false)
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null)
  const callbackRef = useRef(onTranscript)
  callbackRef.current = onTranscript

  const supported = useMemo(() => recognitionCtor() !== null, [])

  const stop = useCallback(() => {
    recognitionRef.current?.stop()
    recognitionRef.current = null
    setListening(false)
  }, [])

  const start = useCallback(() => {
    const Ctor = recognitionCtor()
    if (!Ctor || recognitionRef.current) {
      return
    }
    const recognition = new Ctor()
    recognition.lang = RECOGNITION_LOCALES[language] ?? RECOGNITION_LOCALES.en
    recognition.continuous = false
    recognition.interimResults = false
    recognition.onresult = (event) => {
      let transcript = ''
      for (let index = event.resultIndex; index < event.results.length; index += 1) {
        const result = event.results[index]
        if (result.isFinal && result.length > 0) {
          transcript += result[0].transcript
        }
      }
      if (transcript.trim()) {
        callbackRef.current(transcript.trim())
      }
    }
    recognition.onerror = () => {
      recognitionRef.current = null
      setListening(false)
    }
    recognition.onend = () => {
      recognitionRef.current = null
      setListening(false)
    }
    recognitionRef.current = recognition
    recognition.start()
    setListening(true)
  }, [language])

  useEffect(() => () => recognitionRef.current?.abort(), [])

  return { supported, listening, start, stop }
}
