import { describe, expect, it } from 'vitest'
import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders } from '../../test/renderWithProviders'
import { DataTable, type DataTableColumn } from './DataTable'

interface Row {
  id: string
  unit: string
  risk: number
}

const rows: Row[] = [
  { id: '1', unit: 'BF2', risk: 82 },
  { id: '2', unit: 'BF1', risk: 12 },
  { id: '3', unit: 'RHF', risk: 34 },
]

const columns: DataTableColumn<Row>[] = [
  { key: 'unit', label: 'Unit', type: 'text' },
  { key: 'risk', label: 'Risk', type: 'number', align: 'right' },
]

function bodyUnits(): string[] {
  const table = screen.getByRole('table')
  const bodyRows = within(table).getAllByRole('row').slice(2) // skip label + search header rows
  return bodyRows
    .map((row) => within(row).queryAllByRole('cell')[0]?.textContent ?? '')
    .filter((text) => text === 'BF1' || text === 'BF2' || text === 'RHF')
}

describe('DataTable (TBL-STD)', () => {
  it('renders every row and honors the default descending sort', () => {
    renderWithProviders(
      <DataTable
        caption="Furnace units"
        rows={rows}
        columns={columns}
        getRowId={(row) => row.id}
        defaultSort={[{ key: 'risk', direction: 'desc' }]}
      />,
    )
    expect(bodyUnits()).toEqual(['BF2', 'RHF', 'BF1'])
  })

  it('re-sorts when a column header is clicked', async () => {
    const user = userEvent.setup({ delay: null })
    renderWithProviders(
      <DataTable
        caption="Furnace units"
        rows={rows}
        columns={columns}
        getRowId={(row) => row.id}
        defaultSort={[{ key: 'risk', direction: 'desc' }]}
      />,
    )
    await user.click(screen.getByText('Unit'))
    await waitFor(() => expect(bodyUnits()).toEqual(['BF1', 'BF2', 'RHF']))
  })

  it('filters rows through the global search box', async () => {
    renderWithProviders(
      <DataTable caption="Furnace units" rows={rows} columns={columns} getRowId={(row) => row.id} />,
    )
    fireEvent.change(screen.getByLabelText('Search all columns'), { target: { value: 'RHF' } })
    await waitFor(() => expect(bodyUnits()).toEqual(['RHF']), { timeout: 2000 })
  })

  it('filters rows through a per-column header search', async () => {
    renderWithProviders(
      <DataTable caption="Furnace units" rows={rows} columns={columns} getRowId={(row) => row.id} />,
    )
    fireEvent.change(screen.getByLabelText('Search Unit'), { target: { value: 'BF' } })
    await waitFor(() => expect(bodyUnits().sort()).toEqual(['BF1', 'BF2']), { timeout: 2000 })
  })
})
