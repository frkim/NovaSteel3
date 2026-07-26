import { AnalyticsDashboard } from './components/AnalyticsDashboard'
import type { ShellContext } from './types'

const standaloneContext: ShellContext = {
  themeMode: 'light',
  locale: 'en-LU',
  activePersona: 'PlantManager',
  site: 'lu',
  demoMode: true,
  tokenRef: 'standalone-demo-reference',
  bridgeVersion: '1.0',
  navigation: {
    section: 'command-center',
    subView: null,
    site: 'lu',
  },
}

function App() {
  return <AnalyticsDashboard context={standaloneContext} emit={() => undefined} />
}

export default App
