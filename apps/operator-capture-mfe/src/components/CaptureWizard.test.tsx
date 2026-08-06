import { describe, expect, it, afterEach, vi } from 'vitest'
import { screen, fireEvent, waitFor, act } from '@testing-library/react'
import { CaptureWizard } from './CaptureWizard'
import { CaptureClient } from '../api/captureClient'
import { renderWithApp } from '../test/renderWithApp'
import { installMediaMocks } from '../test/mediaMocks'

// jsdom never loads media, so the real probe would sit on its timeout.
vi.mock('../audio/audioFile', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../audio/audioFile')>()),
  probeAudioDuration: vi.fn(async () => 67.9),
}))

function fillConsent(): void {
  fireEvent.change(screen.getByLabelText(/procedure title/i), { target: { value: 'Tap the furnace' } })
  fireEvent.change(screen.getByLabelText(/operator/i), { target: { value: 'op-9' } })
  fireEvent.click(screen.getByRole('checkbox'))
}

async function reachRecordStep(client: CaptureClient): Promise<void> {
  renderWithApp(<CaptureWizard client={client} />)
  fillConsent()
  fireEvent.click(screen.getByRole('button', { name: /continue to recording/i }))
  await screen.findByRole('button', { name: /^start recording$/i })
}

function fileInput(): HTMLInputElement {
  const input = document.querySelector('input[type="file"]')
  if (!input) {
    throw new Error('file input not rendered')
  }
  return input as HTMLInputElement
}

describe('CaptureWizard integration', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('hard-gates recording behind consent', () => {
    const client = new CaptureClient({ http: null })
    renderWithApp(<CaptureWizard client={client} />)

    // The recorder control is not reachable while the consent gate is showing.
    expect(screen.queryByRole('button', { name: /^start recording$/i })).toBeNull()
    expect(screen.getByRole('button', { name: /continue to recording/i })).toBeDisabled()
  })

  it('drives the full happy path and calls draft + submit', async () => {
    const mocks = installMediaMocks()
    const client = new CaptureClient({ http: null })
    const createInterview = vi.spyOn(client, 'createInterview')
    const uploadAudio = vi.spyOn(client, 'uploadAudio')
    const createDraft = vi.spyOn(client, 'createDraft')
    const submitForReview = vi.spyOn(client, 'submitForReview')

    renderWithApp(<CaptureWizard client={client} />)

    // 1) Consent -> record
    fillConsent()
    fireEvent.click(screen.getByRole('button', { name: /continue to recording/i }))
    await waitFor(() => expect(createInterview).toHaveBeenCalled())
    const startBtn = await screen.findByRole('button', { name: /^start recording$/i })

    // 2) Record -> stop
    await act(async () => {
      fireEvent.click(startBtn)
    })
    const stopBtn = await screen.findByRole('button', { name: /^stop$/i })
    await act(async () => {
      fireEvent.click(stopBtn)
    })

    // 3) Review -> upload
    const uploadBtn = await screen.findByRole('button', { name: /upload recording/i })
    fireEvent.click(uploadBtn)
    await waitFor(() => expect(uploadAudio).toHaveBeenCalled())

    // 4) Transcript ready -> store
    const saveBtn = await screen.findByRole('button', { name: /save to knowledge hub/i })
    fireEvent.click(saveBtn)

    // 5) Store: create draft then submit for review
    const createBtn = await screen.findByRole('button', { name: /create draft procedure/i })
    fireEvent.click(createBtn)
    await waitFor(() => expect(createDraft).toHaveBeenCalled())

    const submitBtn = await screen.findByRole('button', { name: /submit for review/i })
    fireEvent.click(submitBtn)
    await waitFor(() => expect(submitForReview).toHaveBeenCalled())

    // Human-in-the-loop confirmation is surfaced.
    expect(await screen.findByRole('button', { name: /capture another procedure/i })).toBeInTheDocument()

    mocks.restore()
  })

  it('accepts an imported audio file, plays it back and uploads it', async () => {
    const mocks = installMediaMocks()
    const client = new CaptureClient({ http: null })
    const uploadAudio = vi.spyOn(client, 'uploadAudio')

    await reachRecordStep(client)

    const file = new File(['audio-bytes'], 'hearth-cooling.wav', { type: 'audio/wav' })
    await act(async () => {
      fireEvent.change(fileInput(), { target: { files: [file] } })
    })

    // Review step: the operator can hear the file before anything is sent.
    expect(await screen.findByText(/review the imported audio/i)).toBeInTheDocument()
    expect(screen.getByText('hearth-cooling.wav')).toBeInTheDocument()
    expect(document.querySelector('audio')).toBeTruthy()

    fireEvent.click(screen.getByRole('button', { name: /upload audio/i }))

    await waitFor(() => expect(uploadAudio).toHaveBeenCalled())
    const [, request] = uploadAudio.mock.calls[0]
    expect(request.blob.type).toBe('audio/wav')
    expect(request.durationSeconds).toBeCloseTo(67.9)

    mocks.restore()
  })

  it('loads the bundled sample interview through the same import path', async () => {
    const mocks = installMediaMocks()
    const client = new CaptureClient({ http: null })
    const fetchMock = vi.fn(async () => ({
      ok: true,
      status: 200,
      blob: async () => new Blob(['sample-bytes'], { type: 'audio/wav' }),
    }))
    vi.stubGlobal('fetch', fetchMock)

    await reachRecordStep(client)

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /load the sample interview/i }))
    })

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/samples/blast-furnace-hearth-cooling-en.wav'),
      expect.anything(),
    )
    expect(await screen.findByText(/review the imported audio/i)).toBeInTheDocument()
    expect(screen.getByText('blast-furnace-hearth-cooling-en.wav')).toBeInTheDocument()

    vi.unstubAllGlobals()
    mocks.restore()
  })

  it('rejects a file that is not audio without leaving the record step', async () => {
    const mocks = installMediaMocks()
    const client = new CaptureClient({ http: null })

    await reachRecordStep(client)

    const file = new File(['%PDF-'], 'procedure.pdf', { type: 'application/pdf' })
    await act(async () => {
      fireEvent.change(fileInput(), { target: { files: [file] } })
    })

    expect(await screen.findByRole('alert')).toHaveTextContent(/not an audio format/i)
    // The import affordance stays available so the operator can pick again.
    expect(screen.getByRole('button', { name: /import an audio file/i })).toBeInTheDocument()

    mocks.restore()
  })
})
