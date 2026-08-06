import { describe, expect, it, vi } from 'vitest'
import { screen, fireEvent } from '@testing-library/react'
import { ConsentGate, type ConsentValues } from './ConsentGate'
import { renderWithApp, testAppValue } from '../test/renderWithApp'

const initial: ConsentValues = {
  operatorRef: '',
  title: '',
  domain: 'Blast Furnace',
  language: 'en',
  retentionDays: 365,
}

function startButton(): HTMLButtonElement {
  return screen.getByRole('button', { name: /start recording|record/i }) as HTMLButtonElement
}

describe('ConsentGate', () => {
  it('keeps the start action disabled until consent and required fields are set', () => {
    renderWithApp(<ConsentGate initial={initial} onSubmit={vi.fn()} />, testAppValue())

    expect(startButton()).toBeDisabled()

    fireEvent.change(screen.getByLabelText(/procedure title/i), { target: { value: 'Tap the furnace' } })
    fireEvent.change(screen.getByLabelText(/operator/i), { target: { value: 'op-7' } })
    // Still disabled: consent not granted yet.
    expect(startButton()).toBeDisabled()

    fireEvent.click(screen.getByRole('checkbox'))
    expect(startButton()).toBeEnabled()
  })

  it('submits the captured consent values', () => {
    const onSubmit = vi.fn()
    renderWithApp(<ConsentGate initial={initial} onSubmit={onSubmit} />, testAppValue())

    fireEvent.change(screen.getByLabelText(/procedure title/i), { target: { value: 'Ladle prep' } })
    fireEvent.change(screen.getByLabelText(/operator/i), { target: { value: 'op-3' } })
    fireEvent.click(screen.getByRole('checkbox'))
    fireEvent.click(startButton())

    expect(onSubmit).toHaveBeenCalledTimes(1)
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({ operatorRef: 'op-3', title: 'Ladle prep', retentionDays: 365 }),
    )
  })

  it('does not submit when consent is withheld even if fields are filled', () => {
    const onSubmit = vi.fn()
    renderWithApp(<ConsentGate initial={initial} onSubmit={onSubmit} />, testAppValue())

    fireEvent.change(screen.getByLabelText(/procedure title/i), { target: { value: 'X' } })
    fireEvent.change(screen.getByLabelText(/operator/i), { target: { value: 'op-1' } })
    fireEvent.click(startButton())

    expect(onSubmit).not.toHaveBeenCalled()
  })
})
