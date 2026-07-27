import { useEffect, useMemo, useState, useSyncExternalStore } from 'react'
import {
  Alert,
  Box,
  Breadcrumbs,
  Button,
  Chip,
  CssBaseline,
  Paper,
  Stack,
  Tab,
  Tabs,
  ThemeProvider,
  Typography,
} from '@mui/material'
import PlayCircleOutlineIcon from '@mui/icons-material/PlayArrow'
import StopCircleIcon from '@mui/icons-material/Stop'
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome'
import GridViewIcon from '@mui/icons-material/GridView'
import { createNovaSteelTheme, resolveThemeMode } from '../designTokens'
import { DataClient } from '../api/dataClient'
import { CopilotClient } from '../api/copilotClient'
import { DeviceClient } from '../api/deviceClient'
import { AnalyticsContext, type AnalyticsContextValue } from '../context/analytics'
import { createTranslator } from '../i18n/messages'
import { resolveSection } from '../personaRoutes'
import type { MicrofrontendEmitter, ShellContext } from '../types'
import { resolveScreen } from './screens/screenRegistry'
import { ErrorBoundary } from './ErrorBoundary'
import { DemoTour } from './DemoTour'
import { CopilotDock } from './copilot/CopilotDock'
import { CopilotPanel } from './copilot/CopilotPanel'
import { hasDockLayouts, resetDockLayouts, subscribeDockPresence } from './dock/dockCommands'

interface AnalyticsDashboardProps {
  context: ShellContext
  emit: MicrofrontendEmitter
}

export function AnalyticsDashboard({ context, emit }: AnalyticsDashboardProps) {
  const theme = useMemo(() => createNovaSteelTheme(context.themeMode), [context.themeMode])
  const [tourOpen, setTourOpen] = useState(false)
  const [copilotOpen, setCopilotOpen] = useState(false)
  const dockPresent = useSyncExternalStore(subscribeDockPresence, hasDockLayouts, () => false)

  const client = useMemo(
    () => new DataClient(context),
    // Recreate only when request-shaping fields change to avoid refetch storms.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [context.bffBaseUrl, context.locale, context.demoMode],
  )
  const copilotClient = useMemo(
    () => new CopilotClient(context),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [context.bffBaseUrl, context.locale],
  )
  const deviceClient = useMemo(
    () => new DeviceClient(context),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [context.bffBaseUrl, context.locale],
  )
  const translator = useMemo(() => createTranslator(context.locale), [context.locale])

  const contextValue = useMemo<AnalyticsContextValue>(() => {
    const permitted = context.permittedActions
    return {
      context,
      emit,
      client,
      deviceClient,
      locale: context.locale,
      site: context.site,
      unitSystem: 'metric',
      t: translator,
      demoMode: context.demoMode,
      can: (action: string) => !permitted || permitted.length === 0 || permitted.includes(action),
    }
  }, [context, emit, client, deviceClient, translator])

  const { section, tab } = resolveSection(context.navigation.section, context.navigation.subView)
  const Screen = resolveScreen(section.section, tab.slug) ?? resolveScreen(section.section, section.defaultSubView)

  useEffect(() => {
    // Keep the standalone/dev token CSS variables aligned with the resolved theme.
    document.documentElement.dataset.theme = resolveThemeMode(context.themeMode)
  }, [context.themeMode])

  const navigateToTab = (slug: string) => {
    emit('nav.intent', { route: `/${context.site}/${section.section}/${slug}` })
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box className="analytics-dashboard" component="div">
        {context.demoMode && (
          <Alert
            severity="warning"
            role="status"
            icon={false}
            sx={{ mb: 2, fontWeight: 600 }}
            data-testid="demo-banner"
          >
            {translator('app.synthetic')}
          </Alert>
        )}

        <Stack
          direction={{ xs: 'column', md: 'row' }}
          spacing={2}
          sx={{ justifyContent: 'space-between', alignItems: { md: 'flex-start' }, mb: 2 }}
        >
          <Box>
            <Breadcrumbs aria-label="breadcrumb" sx={{ mb: 0.5 }}>
              <Typography variant="caption" color="text.secondary">
                {context.site.toUpperCase()}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {section.title}
              </Typography>
              {section.tabs.length > 1 && (
                <Typography variant="caption" color="text.primary">
                  {tab.label}
                </Typography>
              )}
            </Breadcrumbs>
            <Typography component="h1" variant="h1">
              {section.title}
            </Typography>
            <Typography color="text.secondary" variant="body2">
              {section.description}
            </Typography>
          </Box>
          <Stack direction="row" spacing={1} sx={{ alignItems: 'center', flexWrap: 'wrap' }}>
            <Chip variant="outlined" size="small" label={section.persona} />
            {dockPresent && (
              <Button
                size="small"
                variant="outlined"
                startIcon={<GridViewIcon />}
                data-testid="dock-reset"
                title={translator('dock.reset.hint')}
                onClick={() => resetDockLayouts()}
              >
                {translator('dock.reset')}
              </Button>
            )}
            <Button
              size="small"
              variant={copilotOpen ? 'contained' : 'outlined'}
              startIcon={<AutoAwesomeIcon />}
              aria-pressed={copilotOpen}
              data-testid="copilot-toggle"
              onClick={() => setCopilotOpen((open) => !open)}
            >
              {copilotOpen ? translator('copilot.close') : translator('copilot.title')}
            </Button>
            {context.demoMode && (
              <Button
                size="small"
                variant={tourOpen ? 'contained' : 'outlined'}
                startIcon={tourOpen ? <StopCircleIcon /> : <PlayCircleOutlineIcon />}
                onClick={() => setTourOpen((open) => !open)}
              >
                {tourOpen ? translator('demo.tour.stop') : translator('demo.tour.start')}
              </Button>
            )}
          </Stack>
        </Stack>

        {section.tabs.length > 1 && (
          <Paper elevation={0} sx={{ mb: 2, borderBottom: 1, borderColor: 'divider' }}>
            <Tabs
              aria-label={`${section.title} sub-views`}
              value={tab.slug}
              onChange={(_, slug: string) => navigateToTab(slug)}
              variant="scrollable"
              scrollButtons="auto"
            >
              {section.tabs.map((entry) => (
                <Tab key={entry.slug} label={entry.label} value={entry.slug} />
              ))}
            </Tabs>
          </Paper>
        )}

        <AnalyticsContext.Provider value={contextValue}>
          <CopilotDock
            open={copilotOpen}
            themeMode={resolveThemeMode(context.themeMode)}
            onCloseCopilot={() => setCopilotOpen(false)}
            workspace={
              <ErrorBoundary key={`${section.section}/${tab.slug}`}>
                <Box component="main">
                  {Screen ? <Screen /> : <MissingScreen title={section.title} />}
                </Box>
              </ErrorBoundary>
            }
            copilot={
              <CopilotPanel
                client={copilotClient}
                section={section.section}
                subView={tab.slug}
                site={context.site}
                screenTitle={section.title}
                persona={section.persona}
                locale={context.locale}
                onClose={() => setCopilotOpen(false)}
              />
            }
          />
          {context.demoMode && (
            <DemoTour open={tourOpen} onClose={() => setTourOpen(false)} emit={emit} site={context.site} />
          )}
        </AnalyticsContext.Provider>
      </Box>
    </ThemeProvider>
  )
}

function MissingScreen({ title }: { title: string }) {
  return (
    <Alert severity="info" role="status">
      {title} is available from the navigation. Select a sub-view to continue.
    </Alert>
  )
}
