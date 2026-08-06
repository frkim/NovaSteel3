import { describe, expect, it, afterEach, vi } from 'vitest'
import { screen, fireEvent, waitFor, act } from '@testing-library/react'
import { CaptureWizard } from './CaptureWizard'
import { CaptureClient } from '../api/captureClient'
import { renderWithApp } from '../test/renderWithApp'
import { installMediaMocks } from '../test/mediaMocks'

function fillConsent(): void {
  fireEvent.change(screen.getByLabelText(/procedure title/i), { target: { value: 'Tap the furnace' } })
  fireEvent.change(screen.getByLabelText(/operator/i), { target: { value: 'op-9' } })
  fireEvent.click(screen.getByRole('checkbox'))
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
})
