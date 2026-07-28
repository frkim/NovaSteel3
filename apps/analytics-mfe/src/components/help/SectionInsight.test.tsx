import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SectionInsight } from './SectionInsight'
import { createTranslator } from '../../i18n/messages'

const t = createTranslator('en-GB')

describe('SectionInsight', () => {
  it('renders nothing for a section with no narrative topic', () => {
    const { container } = render(<SectionInsight section="platform-ops" locale="en-GB" t={t} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('opens the explanation from the title affordance and closes on Escape', async () => {
    const user = userEvent.setup()
    render(<SectionInsight section="energy-optimization" locale="en-GB" t={t} />)

    await user.click(screen.getByTestId('section-insight-toggle'))
    const popup = await screen.findByTestId('section-insight-popup')
    expect(popup).toHaveTextContent('How energy is optimised')
    expect(popup).toHaveTextContent('Why it matters in a steel plant')

    await user.keyboard('{Escape}')
    expect(screen.queryByTestId('section-insight-popup')).not.toBeInTheDocument()
  })

  it('shows both languages when the shell asks for bilingual help', async () => {
    const user = userEvent.setup()
    render(<SectionInsight section="knowledge-hub" locale="en-GB" bilingual t={t} />)

    await user.click(screen.getByTestId('section-insight-toggle'))
    const popup = await screen.findByTestId('section-insight-popup')
    expect(popup.querySelectorAll('[data-bilingual-segment="fr"]').length).toBeGreaterThan(0)
    expect(popup.querySelectorAll('[data-bilingual-segment="en"]').length).toBeGreaterThan(0)
  })
})
