import { describe, expect, it } from 'vitest'
import { processRows, type ProcessColumn } from './tableProcessing'

interface Row {
  name: string
  risk: number
  owner: string
}

const columns: ProcessColumn<Row>[] = [
  { key: 'name', type: 'text' },
  { key: 'risk', type: 'number' },
  { key: 'owner', type: 'text' },
]

const rows: Row[] = [
  { name: 'BF2', risk: 82, owner: 'A. Weber' },
  { name: 'BF1', risk: 12, owner: 'M. Dupont' },
  { name: 'RHF', risk: 34, owner: 'A. Weber' },
]

describe('processRows (TBL-STD semantics)', () => {
  it('sorts numerically descending', () => {
    const result = processRows(rows, columns, {
      sort: [{ key: 'risk', direction: 'desc' }],
      columnSearch: {},
      globalSearch: '',
    })
    expect(result.map((row) => row.name)).toEqual(['BF2', 'RHF', 'BF1'])
  })

  it('sorts numerically ascending', () => {
    const result = processRows(rows, columns, {
      sort: [{ key: 'risk', direction: 'asc' }],
      columnSearch: {},
      globalSearch: '',
    })
    expect(result.map((row) => row.name)).toEqual(['BF1', 'RHF', 'BF2'])
  })

  it('filters by a single column (contains)', () => {
    const result = processRows(rows, columns, {
      sort: [],
      columnSearch: { name: 'BF' },
      globalSearch: '',
    })
    expect(result.map((row) => row.name)).toEqual(['BF2', 'BF1'])
  })

  it('combines per-column searches with AND', () => {
    const result = processRows(rows, columns, {
      sort: [],
      columnSearch: { name: 'BF', owner: 'Weber' },
      globalSearch: '',
    })
    expect(result.map((row) => row.name)).toEqual(['BF2'])
  })

  it('applies global search across searchable columns (OR)', () => {
    const result = processRows(rows, columns, {
      sort: [],
      columnSearch: {},
      globalSearch: 'dupont',
    })
    expect(result.map((row) => row.name)).toEqual(['BF1'])
  })

  it('AND-combines global search with per-column search', () => {
    const result = processRows(rows, columns, {
      sort: [],
      columnSearch: { owner: 'Weber' },
      globalSearch: 'RHF',
    })
    expect(result.map((row) => row.name)).toEqual(['RHF'])
  })

  it('performs a stable multi-column sort', () => {
    const result = processRows(rows, columns, {
      sort: [
        { key: 'owner', direction: 'asc' },
        { key: 'risk', direction: 'desc' },
      ],
      columnSearch: {},
      globalSearch: '',
    })
    expect(result.map((row) => row.name)).toEqual(['BF2', 'RHF', 'BF1'])
  })
})
