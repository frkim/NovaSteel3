import { createRoot } from 'react-dom/client'
import './index.css'
import { AnalyticsDashboard } from './components/AnalyticsDashboard'
import type { MicrofrontendEmitter, MicrofrontendInstance, ShellContext } from './types'

export function mountAnalyticsMicrofrontend(
  host: HTMLElement,
  initialContext: ShellContext,
  emit: MicrofrontendEmitter,
): MicrofrontendInstance {
  const root = createRoot(host)
  let context = initialContext

  const render = () => {
    root.render(<AnalyticsDashboard context={context} emit={emit} />)
  }

  render()

  return {
    update(nextContext: ShellContext) {
      context = nextContext
      render()
    },
    unmount() {
      root.unmount()
    },
  }
}
