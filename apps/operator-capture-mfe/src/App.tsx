import { useEffect, useMemo, useState } from 'react'
import {
  AppBar,
  Box,
  Chip,
  Container,
  CssBaseline,
  MenuItem,
  Select,
  Stack,
  Toolbar,
  Typography,
} from '@mui/material'
import CloudOffIcon from '@mui/icons-material/CloudOff'
import ScienceIcon from '@mui/icons-material/ScienceOutlined'
import { ThemeProvider } from '@mui/material/styles'
import { AppContext } from './components/appContext'
import { CaptureWizard } from './components/CaptureWizard'
import { createCaptureTheme } from './designTokens'
import { CAPTURE_LANGUAGES, type CaptureLanguage } from './types'
import { createTranslator, LANGUAGE_LABELS, languageOf } from './i18n/messages'
import { demoMode } from './config'

function initialLanguage(): CaptureLanguage {
  const nav = typeof navigator !== 'undefined' ? navigator.language : 'en'
  return languageOf(nav) as CaptureLanguage
}

export default function App() {
  const [language, setLanguage] = useState<CaptureLanguage>(initialLanguage)
  const [online, setOnline] = useState(typeof navigator === 'undefined' ? true : navigator.onLine)

  const theme = useMemo(() => createCaptureTheme('dark'), [])
  const t = useMemo(() => createTranslator(language), [language])
  const isDemo = useMemo(() => demoMode(), [])

  useEffect(() => {
    document.documentElement.lang = language
  }, [language])

  useEffect(() => {
    const goOnline = () => setOnline(true)
    const goOffline = () => setOnline(false)
    window.addEventListener('online', goOnline)
    window.addEventListener('offline', goOffline)
    return () => {
      window.removeEventListener('online', goOnline)
      window.removeEventListener('offline', goOffline)
    }
  }, [])

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AppContext.Provider value={{ t, language, setLanguage, online }}>
        <AppBar position="sticky" elevation={0} sx={{ borderBottom: 1, borderColor: 'divider' }} color="default">
          <Toolbar sx={{ gap: 1 }}>
            <Box sx={{ flexGrow: 1, minWidth: 0 }}>
              <Typography variant="h3" component="h1" noWrap>
                {t('app.title')}
              </Typography>
            </Box>
            <Select
              size="small"
              value={language}
              onChange={(e) => setLanguage(e.target.value as CaptureLanguage)}
              aria-label={t('common.language')}
              sx={{ minWidth: 120 }}
            >
              {CAPTURE_LANGUAGES.map((code) => (
                <MenuItem key={code} value={code}>
                  {LANGUAGE_LABELS[code]}
                </MenuItem>
              ))}
            </Select>
          </Toolbar>
        </AppBar>

        <Container maxWidth="sm" sx={{ py: 2, px: { xs: 1.5, sm: 3 } }}>
          <Stack spacing={2}>
            <Stack direction="row" spacing={1} sx={{ flexWrap: 'wrap' }}>
              {isDemo && (
                <Chip size="small" color="secondary" variant="outlined" icon={<ScienceIcon />} label={t('app.synthetic')} />
              )}
              {!online && (
                <Chip size="small" color="warning" variant="outlined" icon={<CloudOffIcon />} label={t('app.offline')} />
              )}
            </Stack>
            <Typography variant="body2" color="text.secondary">
              {t('app.subtitle')}
            </Typography>
            <CaptureWizard />
          </Stack>
        </Container>
      </AppContext.Provider>
    </ThemeProvider>
  )
}
