import { useEffect, useState } from 'react'
import { AnalyticsDashboard } from './components/AnalyticsDashboard'
import type { ShellContext } from './types'

/**
 * Standalone development harness.
 *
 * The shell normally supplies the navigation context. Reading it from the hash
 * (`#/company-website/home`) lets the whole route surface be exercised — and
 * screenshotted — without booting the Blazor shell.
 */
function navigationFromHash(): { section: string; subView: string | null } {
  const raw = typeof window === 'undefined' ? '' : window.location.hash.replace(/^#\/?/, '')
  const [section, subView] = raw.split('/')
  return {
    section: section && section.length > 0 ? section : 'command-center',
    subView: subView && subView.length > 0 ? subView : null,
  }
}

function App() {
  const [route, setRoute] = useState(navigationFromHash)

  useEffect(() => {
    const onHashChange = () => setRoute(navigationFromHash())
    window.addEventListener('hashchange', onHashChange)
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [])

  const standaloneContext: ShellContext = {
    themeMode: 'light',
    locale: 'en-LU',
    activePersona: 'PlantManager',
    primaryPersona: 'PlantManager',
    site: 'lu',
    tokenRef: 'standalone-demo-reference',
    bridgeVersion: '1.0',
    navigation: {
      section: route.section,
      subView: route.subView,
      site: 'lu',
    },
  }

  return <AnalyticsDashboard context={standaloneContext} emit={() => undefined} />
}

export default App
