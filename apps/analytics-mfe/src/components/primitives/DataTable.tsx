import { useMemo, useRef, useState, type ReactNode } from 'react'
import {
  Box,
  Button,
  Checkbox,
  Chip,
  Divider,
  IconButton,
  InputAdornment,
  ListItemText,
  Menu,
  MenuItem,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
  TableSortLabel,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material'
import SearchIcon from '@mui/icons-material/Search'
import ViewColumnIcon from '@mui/icons-material/ViewColumn'
import DownloadIcon from '@mui/icons-material/Download'
import RefreshIcon from '@mui/icons-material/Refresh'
import DensitySmallIcon from '@mui/icons-material/DensitySmall'
import DensityMediumIcon from '@mui/icons-material/DensityMedium'
import { useAnalytics } from '../../context/analytics'
import { useDebouncedValue } from '../../hooks/useDebouncedValue'
import { downloadCsv, type CsvColumn } from '../../utils/csv'
import {
  columnValue,
  processRows,
  type ColumnType,
  type ProcessColumn,
  type SortRule,
} from '../../utils/tableProcessing'

export interface DataTableColumn<T> {
  key: string
  label: string
  type?: ColumnType
  sortable?: boolean
  searchable?: boolean
  align?: 'left' | 'right' | 'center'
  width?: number | string
  render?: (row: T) => ReactNode
  value?: (row: T) => string | number | null | undefined
  hideable?: boolean
  defaultHidden?: boolean
}

export interface DataTableProps<T> {
  rows: T[]
  columns: DataTableColumn<T>[]
  getRowId: (row: T) => string
  caption: string
  defaultSort?: SortRule[]
  exportable?: boolean
  exportFileName?: string
  onRowClick?: (row: T) => void
  onRefresh?: () => void
  toolbarExtras?: ReactNode
  pageSizeOptions?: number[]
  virtualizeThreshold?: number
  emptyMessage?: string
  initialPageSize?: number
}

const ROW_HEIGHT = { comfortable: 45, compact: 34 }

export function DataTable<T>({
  rows,
  columns,
  getRowId,
  caption,
  defaultSort = [],
  exportable = true,
  exportFileName = 'novasteel-export',
  onRowClick,
  onRefresh,
  toolbarExtras,
  pageSizeOptions = [25, 50, 100],
  virtualizeThreshold = 200,
  emptyMessage,
  initialPageSize = 25,
}: DataTableProps<T>) {
  const { t } = useAnalytics()
  const [sort, setSort] = useState<SortRule[]>(defaultSort)
  const [rawColumnSearch, setRawColumnSearch] = useState<Record<string, string>>({})
  const [rawGlobalSearch, setRawGlobalSearch] = useState('')
  const [hidden, setHidden] = useState<Set<string>>(
    () => new Set(columns.filter((column) => column.defaultHidden).map((column) => column.key)),
  )
  const [compact, setCompact] = useState(false)
  const [page, setPage] = useState(0)
  const [pageSize, setPageSize] = useState(initialPageSize)
  const [columnsAnchor, setColumnsAnchor] = useState<HTMLElement | null>(null)
  const [scrollTop, setScrollTop] = useState(0)
  const scrollRef = useRef<HTMLDivElement>(null)

  const columnSearch = useDebouncedValue(rawColumnSearch, 250)
  const globalSearch = useDebouncedValue(rawGlobalSearch, 250)

  const processColumns = useMemo<ProcessColumn<T>[]>(
    () =>
      columns.map((column) => ({
        key: column.key,
        type: column.type,
        searchable: column.searchable,
        value: column.value,
      })),
    [columns],
  )

  const processed = useMemo(
    () => processRows(rows, processColumns, { sort, columnSearch, globalSearch }),
    [rows, processColumns, sort, columnSearch, globalSearch],
  )

  const visibleColumns = columns.filter((column) => !hidden.has(column.key))
  const activeColumnFilters = Object.entries(columnSearch).filter(([, value]) => value.trim())
  const hasActiveFilters = activeColumnFilters.length > 0 || globalSearch.trim().length > 0
  const virtualize = processed.length > virtualizeThreshold

  const toggleSort = (key: string, additive: boolean) => {
    setSort((current) => {
      const existing = current.find((rule) => rule.key === key)
      const others = additive ? current.filter((rule) => rule.key !== key) : []
      if (!existing) {
        return [...others, { key, direction: 'asc' }]
      }
      if (existing.direction === 'asc') {
        return [...others, { key, direction: 'desc' }]
      }
      return others
    })
    setPage(0)
  }

  const sortDirection = (key: string): 'asc' | 'desc' | false => {
    const rule = sort.find((entry) => entry.key === key)
    return rule ? rule.direction : false
  }

  const resetFilters = () => {
    setRawColumnSearch({})
    setRawGlobalSearch('')
    setPage(0)
  }

  const handleExport = () => {
    const csvColumns: CsvColumn<T>[] = visibleColumns.map((column) => ({
      key: column.key,
      label: column.label,
      value: (row) => columnValue(row, column) ?? '',
    }))
    downloadCsv(exportFileName, processed, csvColumns)
  }

  const cellContent = (row: T, column: DataTableColumn<T>): ReactNode => {
    if (column.render) {
      return column.render(row)
    }
    const value = columnValue(row, column)
    return value === null || value === undefined ? '—' : String(value)
  }

  const rowHeight = compact ? ROW_HEIGHT.compact : ROW_HEIGHT.comfortable
  const paged = virtualize ? processed : processed.slice(page * pageSize, page * pageSize + pageSize)

  // Windowed virtualization for large sets keeps <table> semantics with spacer rows.
  const viewportHeight = 460
  const overscan = 6
  const startIndex = virtualize ? Math.max(0, Math.floor(scrollTop / rowHeight) - overscan) : 0
  const visibleCount = virtualize ? Math.ceil(viewportHeight / rowHeight) + overscan * 2 : paged.length
  const windowRows = virtualize ? processed.slice(startIndex, startIndex + visibleCount) : paged
  const topSpacer = virtualize ? startIndex * rowHeight : 0
  const bottomSpacer = virtualize ? Math.max(0, (processed.length - startIndex - windowRows.length) * rowHeight) : 0

  const headerCells = (
    <>
      <TableRow>
        {visibleColumns.map((column) => (
          <TableCell
            key={column.key}
            align={column.align}
            sortDirection={sortDirection(column.key)}
            aria-sort={
              sortDirection(column.key) === 'asc'
                ? 'ascending'
                : sortDirection(column.key) === 'desc'
                  ? 'descending'
                  : 'none'
            }
            sx={{ width: column.width, whiteSpace: 'nowrap' }}
          >
            {column.sortable === false ? (
              column.label
            ) : (
              <TableSortLabel
                active={sortDirection(column.key) !== false}
                direction={sortDirection(column.key) === 'desc' ? 'desc' : 'asc'}
                onClick={(event) => toggleSort(column.key, event.shiftKey)}
              >
                {column.label}
              </TableSortLabel>
            )}
          </TableCell>
        ))}
      </TableRow>
      <TableRow>
        {visibleColumns.map((column) => (
          <TableCell key={column.key} sx={{ py: 0.5 }}>
            {column.searchable === false ? null : (
              <TextField
                variant="standard"
                size="small"
                fullWidth
                value={rawColumnSearch[column.key] ?? ''}
                onChange={(event) => {
                  setRawColumnSearch((current) => ({ ...current, [column.key]: event.target.value }))
                  setPage(0)
                }}
                placeholder={t('table.columnSearch', { column: column.label })}
                slotProps={{
                  input: {
                    startAdornment: (
                      <InputAdornment position="start">
                        <SearchIcon fontSize="inherit" />
                      </InputAdornment>
                    ),
                  },
                  htmlInput: { 'aria-label': t('table.columnSearch', { column: column.label }) },
                }}
              />
            )}
          </TableCell>
        ))}
      </TableRow>
    </>
  )

  return (
    <Box>
      <Stack
        direction={{ xs: 'column', md: 'row' }}
        spacing={1}
        sx={{ alignItems: { md: 'center' }, mb: 1 }}
      >
        <TextField
          size="small"
          value={rawGlobalSearch}
          onChange={(event) => {
            setRawGlobalSearch(event.target.value)
            setPage(0)
          }}
          placeholder={t('table.search')}
          sx={{ minWidth: 220 }}
          slotProps={{
            input: {
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon fontSize="small" />
                </InputAdornment>
              ),
            },
            htmlInput: { 'aria-label': t('table.search') },
          }}
        />
        <Stack direction="row" spacing={0.5} sx={{ flexWrap: 'wrap', alignItems: 'center' }}>
          {activeColumnFilters.map(([key, value]) => {
            const column = columns.find((entry) => entry.key === key)
            return (
              <Chip
                key={key}
                size="small"
                label={`${column?.label ?? key}: ${value}`}
                onDelete={() => setRawColumnSearch((current) => ({ ...current, [key]: '' }))}
              />
            )
          })}
        </Stack>
        <Box sx={{ flex: 1 }} />
        {toolbarExtras}
        <Tooltip title={t('table.columns')}>
          <IconButton aria-label={t('table.columns')} onClick={(event) => setColumnsAnchor(event.currentTarget)}>
            <ViewColumnIcon />
          </IconButton>
        </Tooltip>
        <Tooltip title={t('table.density')}>
          <IconButton aria-label={t('table.density')} aria-pressed={compact} onClick={() => setCompact((value) => !value)}>
            {compact ? <DensityMediumIcon /> : <DensitySmallIcon />}
          </IconButton>
        </Tooltip>
        {exportable && (
          <Tooltip title={t('table.export')}>
            <IconButton aria-label={t('table.export')} onClick={handleExport}>
              <DownloadIcon />
            </IconButton>
          </Tooltip>
        )}
        {onRefresh && (
          <Tooltip title={t('table.refresh')}>
            <IconButton aria-label={t('table.refresh')} onClick={onRefresh}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        )}
      </Stack>

      <Menu anchorEl={columnsAnchor} open={Boolean(columnsAnchor)} onClose={() => setColumnsAnchor(null)}>
        {columns
          .filter((column) => column.hideable !== false)
          .map((column) => (
            <MenuItem
              key={column.key}
              onClick={() =>
                setHidden((current) => {
                  const next = new Set(current)
                  if (next.has(column.key)) {
                    next.delete(column.key)
                  } else {
                    next.add(column.key)
                  }
                  return next
                })
              }
            >
              <Checkbox size="small" checked={!hidden.has(column.key)} />
              <ListItemText primary={column.label} />
            </MenuItem>
          ))}
      </Menu>

      <TableContainer
        ref={scrollRef}
        onScroll={virtualize ? (event) => setScrollTop((event.target as HTMLDivElement).scrollTop) : undefined}
        sx={{ maxHeight: virtualize ? viewportHeight : undefined, border: 1, borderColor: 'divider', borderRadius: 1 }}
      >
        <Table
          size={compact ? 'small' : 'medium'}
          stickyHeader
          aria-label={caption}
          aria-rowcount={processed.length}
        >
          <caption className="ns-visually-hidden">{caption}</caption>
          <TableHead>{headerCells}</TableHead>
          <TableBody>
            {topSpacer > 0 && (
              <TableRow style={{ height: topSpacer }} aria-hidden>
                <TableCell colSpan={visibleColumns.length} sx={{ p: 0, border: 0 }} />
              </TableRow>
            )}
            {windowRows.map((row) => (
              <TableRow
                key={getRowId(row)}
                hover
                tabIndex={onRowClick ? 0 : undefined}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
                onKeyDown={
                  onRowClick
                    ? (event) => {
                        if (event.key === 'Enter') {
                          onRowClick(row)
                        }
                      }
                    : undefined
                }
                sx={{ cursor: onRowClick ? 'pointer' : 'default', height: rowHeight }}
              >
                {visibleColumns.map((column) => (
                  <TableCell key={column.key} align={column.align}>
                    {cellContent(row, column)}
                  </TableCell>
                ))}
              </TableRow>
            ))}
            {bottomSpacer > 0 && (
              <TableRow style={{ height: bottomSpacer }} aria-hidden>
                <TableCell colSpan={visibleColumns.length} sx={{ p: 0, border: 0 }} />
              </TableRow>
            )}
            {processed.length === 0 && (
              <TableRow>
                <TableCell colSpan={visibleColumns.length}>
                  <Stack spacing={1} sx={{ alignItems: 'center', py: 3 }}>
                    <Typography variant="body2" color="text.secondary">
                      {emptyMessage ?? t('state.empty.filters')}
                    </Typography>
                    {hasActiveFilters && (
                      <Button size="small" variant="outlined" onClick={resetFilters}>
                        {t('table.clearFilters')}
                      </Button>
                    )}
                  </Stack>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Divider />
      {virtualize ? (
        <Typography variant="caption" color="text.secondary" sx={{ p: 1, display: 'block' }} aria-live="polite">
          {t('table.rows', { from: 1, to: processed.length, total: processed.length })} · virtualized
        </Typography>
      ) : (
        <TablePagination
          component="div"
          count={processed.length}
          page={page}
          onPageChange={(_, nextPage) => setPage(nextPage)}
          rowsPerPage={pageSize}
          onRowsPerPageChange={(event) => {
            setPageSize(Number(event.target.value))
            setPage(0)
          }}
          rowsPerPageOptions={pageSizeOptions}
        />
      )}
    </Box>
  )
}
