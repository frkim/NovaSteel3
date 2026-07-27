import { useId, useState, type ReactNode } from 'react'
import {
  Box,
  Card,
  CardContent,
  IconButton,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
  Typography,
} from '@mui/material'
import TableRowsIcon from '@mui/icons-material/TableRows'
import ShowChartIcon from '@mui/icons-material/ShowChart'
import { useAnalytics } from '../../context/analytics'
import { useDocked } from '../dock/dockContext'

export interface ChartTableColumn {
  key: string
  label: string
}

export interface ChartContainerProps {
  title: string
  summary: string
  children: ReactNode
  /** Underlying data exposed via the accessible "View as table" fallback (§14.2). */
  tableColumns?: ChartTableColumn[]
  tableRows?: Array<Record<string, string | number>>
  actions?: ReactNode
  height?: number
  /** Dock panel id; read by the panel collector, not by this component. */
  id?: string
  /** Makes the dock tab dismissible and clears the state that produced it. */
  onDockClose?: () => void
  dockWidth?: number
  dockHeight?: number
}

/**
 * Wraps every D3 visual with an accessible name, a text summary, and a
 * "View as table" fallback so charts satisfy WCAG 2.2 AA (UX §14.2, §17).
 */
export function ChartContainer({
  title,
  summary,
  children,
  tableColumns,
  tableRows,
  actions,
  height = 260,
  id,
  onDockClose,
  dockWidth,
  dockHeight,
}: ChartContainerProps) {
  const { t } = useAnalytics()
  const [asTable, setAsTable] = useState(false)
  const summaryId = useId()
  const canToggle = Boolean(tableColumns && tableRows)
  const docked = useDocked()
  void onDockClose
  void dockWidth
  void dockHeight

  const body = (
    <>
      <Stack direction="row" sx={{ alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
        <Typography component="figcaption" variant="h3">
          {title}
        </Typography>
        <Stack direction="row" spacing={0.5} sx={{ alignItems: 'center' }}>
          {actions}
          {canToggle && (
            <Tooltip title={asTable ? t('table.viewAsChart') : t('table.viewAsTable')}>
              <IconButton
                aria-label={asTable ? t('table.viewAsChart') : t('table.viewAsTable')}
                aria-pressed={asTable}
                onClick={() => setAsTable((value) => !value)}
                size="small"
              >
                {asTable ? <ShowChartIcon fontSize="small" /> : <TableRowsIcon fontSize="small" />}
              </IconButton>
            </Tooltip>
          )}
        </Stack>
      </Stack>

      {asTable && canToggle ? (
        <TableContainer sx={{ maxHeight: height + 40 }}>
          <Table aria-label={`${title} data`} size="small" stickyHeader>
            <TableHead>
              <TableRow>
                {tableColumns!.map((column) => (
                  <TableCell key={column.key}>{column.label}</TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {tableRows!.map((row, index) => (
                <TableRow key={index}>
                  {tableColumns!.map((column) => (
                    <TableCell key={column.key}>{row[column.key]}</TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      ) : (
        <Box role="img" aria-label={`${title}. ${summary}`} aria-describedby={summaryId}>
          {children}
        </Box>
      )}

      <Typography id={summaryId} color="text.secondary" variant="caption" sx={{ display: 'block', mt: 1 }}>
        {summary}
      </Typography>
    </>
  )

  // Docked, the tab supplies the frame; the caption stays because a chart is
  // only accessible with its own name and text summary next to it.
  if (docked) {
    return (
      <Box id={id} component="figure" sx={{ m: 0, minWidth: 0 }}>
        {body}
      </Box>
    )
  }

  return (
    <Card id={id} component="figure" sx={{ m: 0 }}>
      <CardContent>{body}</CardContent>
    </Card>
  )
}
ChartContainer.dockRole = 'panel' as const
