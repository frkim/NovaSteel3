import { useCallback, useEffect, useId, useMemo, useRef, useState, type ReactNode } from 'react'
import {
  Box,
  Button,
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
import AddIcon from '@mui/icons-material/Add'
import RemoveIcon from '@mui/icons-material/Remove'
import { useAnalytics } from '../../context/analytics'
import { useDocked } from '../dock/dockContext'
import { prefersReducedMotion } from '../../designTokens'
import { ChartZoomContext, type ChartDataZoomRegistration } from './ChartZoomContext'

export interface ChartTableColumn {
  key: string
  label: string
}

const ZOOM_STEPS = [50, 75, 100, 125, 150, 200, 300]

export interface ChartContainerProps {
  title: string
  summary: string
  children: ReactNode
  /** Underlying data exposed via the accessible "View as table" fallback (§14.2). */
  tableColumns?: ChartTableColumn[]
  tableRows?: Array<Record<string, string | number>>
  actions?: ReactNode
  height?: number
  /**
   * Help Assistant topic, e.g. `chart.heatmap`. Defaults to the generic chart
   * explanation so an unlabelled chart still explains itself.
   */
  helpTopic?: string
  /** Dock panel id; read by the panel collector, not by this component. */
  id?: string
  /** Makes the dock tab dismissible and clears the state that produced it. */
  onDockClose?: () => void
  dockWidth?: number
  dockHeight?: number
  /** Whether zoom controls are shown. Defaults to true. */
  zoomable?: boolean
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
  helpTopic = 'generic.chart',
  id,
  onDockClose,
  dockWidth,
  dockHeight,
  zoomable = true,
}: ChartContainerProps) {
  const { t } = useAnalytics()
  const [asTable, setAsTable] = useState(false)
  const [zoom, setZoom] = useState(100)
  const dataZoomRegistrations = useRef(new Map<symbol, ChartDataZoomRegistration>())
  const [dataZoomActive, setDataZoomActive] = useState(false)
  const summaryId = useId()
  const canToggle = Boolean(tableColumns && tableRows)
  const docked = useDocked()
  void onDockClose
  void dockWidth
  void dockHeight

  const zoomIn = useCallback(() => {
    setZoom((current) => {
      const idx = ZOOM_STEPS.indexOf(current)
      return idx < ZOOM_STEPS.length - 1 ? ZOOM_STEPS[idx + 1] : current
    })
  }, [])

  const zoomOut = useCallback(() => {
    setZoom((current) => {
      const idx = ZOOM_STEPS.indexOf(current)
      return idx > 0 ? ZOOM_STEPS[idx - 1] : current
    })
  }, [])

  const updateDataZoomActive = useCallback(() => {
    const nextActive = [...dataZoomRegistrations.current.values()].some((registration) => registration.isZoomed)
    setDataZoomActive((current) => (current === nextActive ? current : nextActive))
  }, [])

  const registerDataZoom = useCallback(
    (registration: ChartDataZoomRegistration) => {
      const key = Symbol('chart-data-zoom')
      dataZoomRegistrations.current.set(key, registration)
      updateDataZoomActive()
      return () => {
        dataZoomRegistrations.current.delete(key)
        updateDataZoomActive()
      }
    },
    [updateDataZoomActive],
  )

  const zoomReset = useCallback(() => {
    setZoom(100)
    for (const registration of dataZoomRegistrations.current.values()) {
      registration.reset()
    }
  }, [])

  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent) => {
      if (!zoomable || asTable) return
      const mod = event.ctrlKey || event.metaKey
      if (!mod) return
      if (event.key === '+' || event.key === '=') {
        event.preventDefault()
        zoomIn()
      } else if (event.key === '-') {
        event.preventDefault()
        zoomOut()
      } else if (event.key === '0') {
        event.preventDefault()
        zoomReset()
      }
    },
    [zoomable, asTable, zoomIn, zoomOut, zoomReset],
  )

  useEffect(() => {
    setZoom(100)
  }, [asTable])

  const showZoom = zoomable && !asTable
  const isZoomed = zoom !== 100 || dataZoomActive
  const reducedMotion = useMemo(() => prefersReducedMotion(), [])
  const chartZoomContext = useMemo(
    () => ({ brushZoomEnabled: showZoom, registerDataZoom }),
    [registerDataZoom, showZoom],
  )

  const zoomControls = showZoom ? (
    <Stack direction="row" spacing={0.25} sx={{ alignItems: 'center' }}>
      <IconButton
        aria-label={t('chart.zoomOut')}
        size="small"
        onClick={zoomOut}
        disabled={zoom === ZOOM_STEPS[0]}
      >
        <RemoveIcon fontSize="small" />
      </IconButton>
      <Tooltip title={t('chart.zoomReset')}>
        <Typography
          component="button"
          variant="caption"
          onClick={zoomReset}
          aria-label={t('chart.zoomLevel', { level: zoom })}
          sx={{
            border: 'none',
            background: 'none',
            cursor: 'pointer',
            fontWeight: 600,
            px: 0.5,
            minWidth: 36,
            textAlign: 'center',
            color: 'text.secondary',
            '&:hover': { color: 'text.primary' },
          }}
        >
          {zoom}%
        </Typography>
      </Tooltip>
      <IconButton
        aria-label={t('chart.zoomIn')}
        size="small"
        onClick={zoomIn}
        disabled={zoom === ZOOM_STEPS[ZOOM_STEPS.length - 1]}
      >
        <AddIcon fontSize="small" />
      </IconButton>
      {dataZoomActive && (
        <Button size="small" variant="text" onClick={zoomReset} sx={{ ml: 0.5, minWidth: 0 }}>
          {t('chart.selectZoomReset')}
        </Button>
      )}
    </Stack>
  ) : null

  const chartContent = (
    <Box
      role="img"
      aria-label={`${title}. ${summary}`}
      aria-describedby={summaryId}
      sx={{
        ...(isZoomed
          ? { overflow: 'auto', maxHeight: height + 60, position: 'relative' }
          : {}),
      }}
    >
      <Box
        sx={{
          width: zoom !== 100 ? `${zoom}%` : '100%',
          height: zoom !== 100 ? height * (zoom / 100) : undefined,
          transition: reducedMotion ? 'none' : 'width 0.15s ease, height 0.15s ease',
        }}
      >
        {children}
      </Box>
    </Box>
  )

  const body = (
    <>
      <Stack direction="row" sx={{ alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
        <Typography component="figcaption" variant="h3">
          {title}
        </Typography>
        <Stack direction="row" spacing={0.5} sx={{ alignItems: 'center' }}>
          {zoomControls}
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
        chartContent
      )}

      <Typography id={summaryId} color="text.secondary" variant="caption" sx={{ display: 'block', mt: 1 }}>
        {summary}
      </Typography>
    </>
  )

  const containerProps = {
    onKeyDown: handleKeyDown,
    tabIndex: zoomable ? 0 : undefined,
  }

  if (docked) {
    return (
      <Box
        id={id}
        component="figure"
        data-help={helpTopic}
        data-help-detail={summary}
        sx={{ m: 0, minWidth: 0 }}
        {...containerProps}
      >
        <ChartZoomContext.Provider value={chartZoomContext}>{body}</ChartZoomContext.Provider>
      </Box>
    )
  }

  return (
    <Card
      id={id}
      component="figure"
      data-help={helpTopic}
      data-help-detail={summary}
      sx={{ m: 0 }}
      {...containerProps}
    >
      <CardContent>
        <ChartZoomContext.Provider value={chartZoomContext}>{body}</ChartZoomContext.Provider>
      </CardContent>
    </Card>
  )
}
ChartContainer.dockRole = 'panel' as const
