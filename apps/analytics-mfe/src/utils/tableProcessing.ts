export type ColumnType = 'text' | 'number' | 'enum' | 'date'

export interface ProcessColumn<T> {
  key: string
  type?: ColumnType
  searchable?: boolean
  value?: (row: T) => string | number | null | undefined
}

export interface SortRule {
  key: string
  direction: 'asc' | 'desc'
}

export interface ProcessOptions {
  sort: SortRule[]
  columnSearch: Record<string, string>
  globalSearch: string
}

export function columnValue<T>(row: T, column: ProcessColumn<T>): string | number | null | undefined {
  if (column.value) {
    return column.value(row)
  }
  return (row as Record<string, unknown>)[column.key] as string | number | null | undefined
}

function asText(value: string | number | null | undefined): string {
  return value === null || value === undefined ? '' : String(value)
}

/**
 * Applies TBL-STD semantics client-side: per-column search (AND across columns),
 * global search (OR within a row's searchable columns, AND-combined with column
 * search), and stable multi-column sort. Extracted for direct unit testing.
 */
export function processRows<T>(
  rows: T[],
  columns: ProcessColumn<T>[],
  options: ProcessOptions,
): T[] {
  const columnByKey = new Map(columns.map((column) => [column.key, column]))
  const searchableColumns = columns.filter((column) => column.searchable !== false)

  let result = rows.filter((row) => {
    for (const [key, term] of Object.entries(options.columnSearch)) {
      const trimmed = term.trim().toLowerCase()
      if (!trimmed) {
        continue
      }
      const column = columnByKey.get(key)
      if (!column) {
        continue
      }
      if (!asText(columnValue(row, column)).toLowerCase().includes(trimmed)) {
        return false
      }
    }
    const global = options.globalSearch.trim().toLowerCase()
    if (global) {
      const matches = searchableColumns.some((column) =>
        asText(columnValue(row, column)).toLowerCase().includes(global),
      )
      if (!matches) {
        return false
      }
    }
    return true
  })

  if (options.sort.length > 0) {
    const decorated = result.map((row, index) => ({ row, index }))
    decorated.sort((a, b) => {
      for (const rule of options.sort) {
        const column = columnByKey.get(rule.key)
        if (!column) {
          continue
        }
        const left = columnValue(a.row, column)
        const right = columnValue(b.row, column)
        let comparison: number
        if (column.type === 'number') {
          comparison = (Number(left) || 0) - (Number(right) || 0)
        } else {
          comparison = asText(left).localeCompare(asText(right), undefined, { numeric: true })
        }
        if (comparison !== 0) {
          return rule.direction === 'asc' ? comparison : -comparison
        }
      }
      return a.index - b.index
    })
    result = decorated.map((entry) => entry.row)
  }

  return result
}
