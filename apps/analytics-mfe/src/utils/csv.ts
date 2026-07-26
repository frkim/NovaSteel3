/** Client-side CSV export honoring the caller's current columns and rows. */

function escapeCsvValue(value: unknown): string {
  if (value === null || value === undefined) {
    return ''
  }
  const text = typeof value === 'object' ? JSON.stringify(value) : String(value)
  if (/[",\n\r]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`
  }
  return text
}

export interface CsvColumn<T> {
  key: keyof T | string
  label: string
  value?: (row: T) => unknown
}

export function toCsv<T>(rows: T[], columns: CsvColumn<T>[]): string {
  const header = columns.map((column) => escapeCsvValue(column.label)).join(',')
  const body = rows
    .map((row) =>
      columns
        .map((column) =>
          escapeCsvValue(
            column.value ? column.value(row) : (row as Record<string, unknown>)[column.key as string],
          ),
        )
        .join(','),
    )
    .join('\r\n')
  return `${header}\r\n${body}`
}

export function downloadCsv<T>(filename: string, rows: T[], columns: CsvColumn<T>[]): void {
  if (typeof document === 'undefined') {
    return
  }
  const csv = toCsv(rows, columns)
  const blob = new Blob([`\ufeff${csv}`], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename.endsWith('.csv') ? filename : `${filename}.csv`
  document.body.appendChild(anchor)
  anchor.click()
  document.body.removeChild(anchor)
  URL.revokeObjectURL(url)
}
