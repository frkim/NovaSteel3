import { describe, expect, it } from 'vitest'
import { fireEvent, screen } from '@testing-library/react'
import { renderWithProviders } from '../../test/renderWithProviders'
import { createTranslator } from '../../i18n/messages'
import { ChartContainer } from './ChartContainer'

const t = createTranslator('en-LU')

const baseProps = {
  title: 'Test Chart',
  summary: 'A test chart summary',
  tableColumns: [{ key: 'x', label: 'X' }],
  tableRows: [{ x: 1 }],
}

describe('ChartContainer zoom', () => {
  it('renders zoom controls with catalog labels', () => {
    renderWithProviders(
      <ChartContainer {...baseProps}>
        <div>chart</div>
      </ChartContainer>,
    )
    expect(screen.getByLabelText(t('chart.zoomIn'))).toBeInTheDocument()
    expect(screen.getByLabelText(t('chart.zoomOut'))).toBeInTheDocument()
    expect(screen.getByLabelText(t('chart.zoomLevel', { level: 100 }))).toHaveTextContent('100%')
  })

  it('increases zoom level on plus click', () => {
    renderWithProviders(
      <ChartContainer {...baseProps}>
        <div>chart</div>
      </ChartContainer>,
    )
    fireEvent.click(screen.getByLabelText(t('chart.zoomIn')))
    expect(screen.getByLabelText(t('chart.zoomLevel', { level: 125 }))).toHaveTextContent('125%')
  })

  it('decreases zoom level on minus click', () => {
    renderWithProviders(
      <ChartContainer {...baseProps}>
        <div>chart</div>
      </ChartContainer>,
    )
    fireEvent.click(screen.getByLabelText(t('chart.zoomOut')))
    expect(screen.getByLabelText(t('chart.zoomLevel', { level: 75 }))).toHaveTextContent('75%')
  })

  it('clamps zoom at maximum (300%)', () => {
    renderWithProviders(
      <ChartContainer {...baseProps}>
        <div>chart</div>
      </ChartContainer>,
    )
    const zoomIn = screen.getByLabelText(t('chart.zoomIn'))
    for (let i = 0; i < 10; i++) fireEvent.click(zoomIn)
    expect(screen.getByLabelText(t('chart.zoomLevel', { level: 300 }))).toHaveTextContent('300%')
    expect(zoomIn).toBeDisabled()
  })

  it('clamps zoom at minimum (50%)', () => {
    renderWithProviders(
      <ChartContainer {...baseProps}>
        <div>chart</div>
      </ChartContainer>,
    )
    const zoomOut = screen.getByLabelText(t('chart.zoomOut'))
    for (let i = 0; i < 10; i++) fireEvent.click(zoomOut)
    expect(screen.getByLabelText(t('chart.zoomLevel', { level: 50 }))).toHaveTextContent('50%')
    expect(zoomOut).toBeDisabled()
  })

  it('resets to 100% when percentage is clicked', () => {
    renderWithProviders(
      <ChartContainer {...baseProps}>
        <div>chart</div>
      </ChartContainer>,
    )
    fireEvent.click(screen.getByLabelText(t('chart.zoomIn')))
    fireEvent.click(screen.getByLabelText(t('chart.zoomIn')))
    expect(screen.getByLabelText(t('chart.zoomLevel', { level: 150 }))).toHaveTextContent('150%')
    fireEvent.click(screen.getByLabelText(t('chart.zoomLevel', { level: 150 })))
    expect(screen.getByLabelText(t('chart.zoomLevel', { level: 100 }))).toHaveTextContent('100%')
  })

  it('hides zoom controls when in table mode', () => {
    renderWithProviders(
      <ChartContainer {...baseProps}>
        <div>chart</div>
      </ChartContainer>,
    )
    fireEvent.click(screen.getByLabelText(t('table.viewAsTable')))
    expect(screen.queryByLabelText(t('chart.zoomIn'))).not.toBeInTheDocument()
    expect(screen.queryByLabelText(t('chart.zoomOut'))).not.toBeInTheDocument()
  })

  it('hides zoom controls when zoomable is false', () => {
    renderWithProviders(
      <ChartContainer {...baseProps} zoomable={false}>
        <div>chart</div>
      </ChartContainer>,
    )
    expect(screen.queryByLabelText(t('chart.zoomIn'))).not.toBeInTheDocument()
    expect(screen.queryByLabelText(t('chart.zoomOut'))).not.toBeInTheDocument()
  })

  it('preserves data-help attributes', () => {
    const { container } = renderWithProviders(
      <ChartContainer {...baseProps} helpTopic="chart.line">
        <div>chart</div>
      </ChartContainer>,
    )
    const figure = container.querySelector('[data-help="chart.line"]')
    expect(figure).toBeInTheDocument()
    expect(figure).toHaveAttribute('data-help-detail', baseProps.summary)
  })
})
