import { createContext, useContext, useEffect, useRef, type ReactNode } from 'react'
import { Box } from '@mui/material'
import {
  DockviewReact,
  themeLight,
  themeDark,
  type DockviewApi,
  type DockviewReadyEvent,
  type IDockviewPanelProps,
} from 'dockview-react'
import 'dockview-react/dist/styles/dockview.css'

const WORKSPACE_PANEL = 'workspace'
const COPILOT_PANEL = 'copilot'
const LAYOUT_KEY = 'novasteel.copilot.dock.v1'

interface DockSlots {
  workspace: ReactNode
  copilot: ReactNode
}

/**
 * Dockview mounts panels through `createPortal`, so React context — including
 * the MUI theme and the analytics context — still flows into panel content.
 * Passing the rendered nodes through a context (rather than through panel
 * `params`) keeps them live: a panel is constructed once, but its content must
 * re-render whenever the dashboard state changes.
 */
const DockSlotContext = createContext<DockSlots>({ workspace: null, copilot: null })

function WorkspacePanel(_props: IDockviewPanelProps) {
  const slots = useContext(DockSlotContext)
  return (
    <Box data-testid="copilot-workspace-slot" sx={{ height: '100%', overflow: 'auto', p: 0.5 }}>
      {slots.workspace}
    </Box>
  )
}

function CopilotPanelHost(_props: IDockviewPanelProps) {
  const slots = useContext(DockSlotContext)
  return <Box sx={{ height: '100%', minHeight: 0 }}>{slots.copilot}</Box>
}

const COMPONENTS = {
  [WORKSPACE_PANEL]: WorkspacePanel,
  [COPILOT_PANEL]: CopilotPanelHost,
}

function readLayout(): object | null {
  try {
    const raw = window.localStorage.getItem(LAYOUT_KEY)
    return raw ? (JSON.parse(raw) as object) : null
  } catch {
    return null
  }
}

function writeLayout(api: DockviewApi): void {
  try {
    window.localStorage.setItem(LAYOUT_KEY, JSON.stringify(api.toJSON()))
  } catch {
    // A full or disabled storage quota must never break the dashboard.
  }
}

export interface CopilotDockProps {
  open: boolean
  workspace: ReactNode
  copilot: ReactNode
  themeMode: 'light' | 'dark'
  /** Height of the dock surface; the grid needs a bounded container. */
  height?: number | string
}

/**
 * Hosts the dashboard and the Copilot chat in a Dockview grid.
 *
 * While the chat is closed the workspace renders exactly as it did before the
 * feature existed — no grid, no portal, no layout cost. Opening the chat swaps
 * in the dock with the chat docked to the right, from where it can be dragged
 * to any edge. Floating groups are disabled on purpose: the requirement is a
 * docked panel, never a free-floating window.
 */
export function CopilotDock({ open, workspace, copilot, themeMode, height }: CopilotDockProps) {
  const apiRef = useRef<DockviewApi | null>(null)
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const disposableRef = useRef<{ dispose(): void } | null>(null)

  useEffect(
    () => () => {
      if (saveTimer.current) {
        clearTimeout(saveTimer.current)
      }
      disposableRef.current?.dispose()
    },
    [],
  )

  if (!open) {
    return <>{workspace}</>
  }

  const onReady = (event: DockviewReadyEvent) => {
    apiRef.current = event.api
    disposableRef.current?.dispose()
    disposableRef.current = event.api.onDidLayoutChange(() => {
      // The event fires repeatedly while a sash or a tab is dragged.
      if (saveTimer.current) {
        clearTimeout(saveTimer.current)
      }
      saveTimer.current = setTimeout(() => {
        if (apiRef.current) {
          writeLayout(apiRef.current)
        }
      }, 400)
    })

    const saved = readLayout()
    if (saved) {
      try {
        event.api.fromJSON(saved as Parameters<DockviewApi['fromJSON']>[0])
        if (event.api.panels.length === 2) {
          return
        }
      } catch {
        // Fall through to the default layout below.
      }
      event.api.clear()
    }
    event.api.addPanel({
      id: WORKSPACE_PANEL,
      component: WORKSPACE_PANEL,
      title: 'Dashboard',
    })
    event.api.addPanel({
      id: COPILOT_PANEL,
      component: COPILOT_PANEL,
      title: 'Copilot',
      position: { referencePanel: WORKSPACE_PANEL, direction: 'right' },
      initialWidth: 420,
    })
  }

  return (
    <Box
      data-testid="copilot-dock"
      sx={{
        height: height ?? 'clamp(520px, calc(100vh - 260px), 1200px)',
        minHeight: 0,
        borderRadius: 1,
        overflow: 'hidden',
        border: 1,
        borderColor: 'divider',
      }}
    >
      <DockSlotContext.Provider value={{ workspace, copilot }}>
        <DockviewReact
          components={COMPONENTS}
          onReady={onReady}
          disableFloatingGroups
          theme={themeMode === 'dark' ? themeDark : themeLight}
        />
      </DockSlotContext.Provider>
    </Box>
  )
}
