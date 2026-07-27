import { createContext, useContext, useEffect, useMemo, useRef, useState } from 'react'
import { Box, IconButton, Tooltip } from '@mui/material'
import CloseFullscreenIcon from '@mui/icons-material/CloseFullscreen'
import OpenInFullIcon from '@mui/icons-material/OpenInFull'
import {
  DockviewDefaultTab,
  DockviewReact,
  themeDark,
  themeLight,
  type DockviewApi,
  type DockviewReadyEvent,
  type IDockviewHeaderActionsProps,
  type IDockviewPanelHeaderProps,
  type IDockviewPanelProps,
} from 'dockview-react'
import 'dockview-react/dist/styles/dockview.css'
import type { DockPanelSpec } from './dockTypes'
import { registerDockReset, registerDockReveal } from './dockCommands'

const PANEL_COMPONENT = 'novasteel-panel'
const TAB_COMPONENT = 'novasteel-tab'
const LAYOUT_PREFIX = 'novasteel.dock.v1.'

const DockSpecsContext = createContext<DockPanelSpec[]>([])

type SerializedLayout = Parameters<DockviewApi['fromJSON']>[0]

function useSpec(panelId: string): DockPanelSpec | undefined {
  const specs = useContext(DockSpecsContext)
  return specs.find((spec) => spec.id === panelId)
}

function DockPanelHost(props: IDockviewPanelProps) {
  const spec = useSpec(props.api.id)
  return (
    <Box
      data-dock-panel={props.api.id}
      sx={{ height: '100%', width: '100%', overflow: 'auto', p: spec?.bleed ? 0 : 1, minWidth: 0 }}
    >
      {spec?.content}
    </Box>
  )
}

/**
 * Tabs are the only place a panel can be dismissed, so the close affordance has
 * to mean something: it appears exactly when the owning screen supplied an
 * `onDockClose`, and it delegates to that callback rather than removing the
 * panel behind React's back.
 */
function DockTab(props: IDockviewPanelHeaderProps) {
  const spec = useSpec(props.api.id)
  const closable = Boolean(spec?.closable && spec.onClose)
  return (
    <DockviewDefaultTab
      {...props}
      hideClose={!closable}
      closeActionOverride={closable ? spec?.onClose : undefined}
      data-testid={`dock-tab-${props.api.id}`}
    />
  )
}

/**
 * Per-group maximize toggle. Maximizing is the fastest way for a presenter to
 * take one panel full-screen and come straight back, which is why it sits in
 * the tab bar rather than behind a context menu.
 */
function MaximizeAction(props: IDockviewHeaderActionsProps) {
  const [isMaximized, setIsMaximized] = useState(() => props.api.isMaximized())

  useEffect(() => {
    setIsMaximized(props.api.isMaximized())
    const disposable = props.containerApi.onDidMaximizedGroupChange(() => {
      setIsMaximized(props.api.isMaximized())
    })
    return () => disposable.dispose()
  }, [props.api, props.containerApi])

  const toggle = () => {
    if (props.api.isMaximized()) {
      props.api.exitMaximized()
    } else {
      props.api.maximize()
    }
  }

  const label = isMaximized ? 'Restore panel' : 'Maximize panel'
  return (
    <Tooltip title={label}>
      <IconButton size="small" onClick={toggle} aria-label={label}>
        {isMaximized ? <CloseFullscreenIcon fontSize="inherit" /> : <OpenInFullIcon fontSize="inherit" />}
      </IconButton>
    </Tooltip>
  )
}

const COMPONENTS = { [PANEL_COMPONENT]: DockPanelHost }
const TAB_COMPONENTS = { [TAB_COMPONENT]: DockTab }

function storageKey(layoutKey: string): string {
  return `${LAYOUT_PREFIX}${layoutKey}`
}

function readLayout(layoutKey: string): SerializedLayout | null {
  try {
    const raw = window.localStorage.getItem(storageKey(layoutKey))
    return raw ? (JSON.parse(raw) as SerializedLayout) : null
  } catch {
    return null
  }
}

function writeLayout(layoutKey: string, api: DockviewApi): void {
  try {
    window.localStorage.setItem(storageKey(layoutKey), JSON.stringify(api.toJSON()))
  } catch {
    // A full or disabled storage quota must never break the dashboard.
  }
}

function clearLayout(layoutKey: string): void {
  try {
    window.localStorage.removeItem(storageKey(layoutKey))
  } catch {
    // Ignored for the same reason as above.
  }
}

function addSpecPanel(
  api: DockviewApi,
  spec: DockPanelSpec,
  previousId: string | undefined,
  successorId?: string,
): void {
  const referenceId = spec.reference ?? previousId
  // With no predecessor on the grid yet — a KPI band that only appears once its
  // data loads, for instance — anchor above the following panel so the panel
  // order still matches the order the screen declares.
  const position = referenceId
    ? { referencePanel: referenceId, direction: spec.placement === 'right' ? 'right' : 'below' }
    : successorId
      ? { referencePanel: successorId, direction: 'above' }
      : undefined
  api.addPanel({
    id: spec.id,
    component: PANEL_COMPONENT,
    tabComponent: TAB_COMPONENT,
    title: spec.title,
    // Panels stay mounted on background tabs so that in-flight fetches, chart
    // state and `document.getElementById` drill-downs keep working.
    renderer: 'always',
    ...(position ? { position: position as Parameters<DockviewApi['addPanel']>[0]['position'] } : {}),
    ...(spec.initialWidth ? { initialWidth: spec.initialWidth } : {}),
    ...(spec.initialHeight ? { initialHeight: spec.initialHeight } : {}),
  })
}

/**
 * `initialWidth` / `initialHeight` only apply to a panel that opens into a new
 * group, and never to the very first one, so the requested sizes are applied
 * again once the whole grid exists. Without this the KPI band claims half the
 * viewport and the table underneath it shows two rows.
 */
function applyPreferredSizes(api: DockviewApi, specs: DockPanelSpec[]): void {
  for (const spec of specs) {
    if (!spec.initialHeight && !spec.initialWidth) {
      continue
    }
    const panel = api.getPanel(spec.id)
    if (!panel) {
      continue
    }
    panel.api.setSize({
      ...(spec.initialHeight ? { height: spec.initialHeight } : {}),
      ...(spec.initialWidth ? { width: spec.initialWidth } : {}),
    })
  }
}

function buildDefaultLayout(api: DockviewApi, specs: DockPanelSpec[]): void {
  let previousId: string | undefined
  for (const spec of specs) {
    addSpecPanel(api, spec, previousId)
    previousId = spec.id
  }
  applyPreferredSizes(api, specs)
}

/**
 * Adds any panel the grid is missing, keeping the declared order: a new panel
 * goes after the nearest preceding panel that already exists, or above the
 * nearest following one when it is the first to appear.
 */
function syncMissingPanels(api: DockviewApi, wanted: DockPanelSpec[]): DockPanelSpec[] {
  const added: DockPanelSpec[] = []
  wanted.forEach((spec, index) => {
    if (api.getPanel(spec.id)) {
      return
    }
    let previousId: string | undefined
    for (let i = index - 1; i >= 0; i -= 1) {
      if (api.getPanel(wanted[i].id)) {
        previousId = wanted[i].id
        break
      }
    }
    let successorId: string | undefined
    for (let i = index + 1; i < wanted.length; i += 1) {
      if (api.getPanel(wanted[i].id)) {
        successorId = wanted[i].id
        break
      }
    }
    addSpecPanel(api, spec, previousId, successorId)
    added.push(spec)
  })
  return added
}

export interface WorkspaceDockProps {
  /** Persistence scope; one arrangement is remembered per screen. */
  layoutKey: string
  specs: DockPanelSpec[]
  themeMode: 'light' | 'dark'
  height?: number | string
}

/**
 * Renders a screen's panels as a Dockview grid.
 *
 * Panels are reconciled imperatively rather than through `fromJSON` on every
 * change: a screen adds and removes detail panels as the operator selects rows,
 * and rebuilding the grid each time would discard the user's arrangement and
 * remount healthy panels.
 */
export function WorkspaceDock({ layoutKey, specs, themeMode, height }: WorkspaceDockProps) {
  const apiRef = useRef<DockviewApi | null>(null)
  const specsRef = useRef<DockPanelSpec[]>(specs)
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const disposablesRef = useRef<{ dispose(): void }[]>([])
  const readyRef = useRef(false)

  specsRef.current = specs

  const signature = useMemo(
    () => specs.map((spec) => `${spec.id}:${spec.title}:${spec.placement}`).join('|'),
    [specs],
  )

  useEffect(
    () => () => {
      if (saveTimer.current) {
        clearTimeout(saveTimer.current)
      }
      for (const disposable of disposablesRef.current) {
        disposable.dispose()
      }
      disposablesRef.current = []
      apiRef.current = null
      readyRef.current = false
    },
    [],
  )

  useEffect(() => {
    const rebuild = () => {
      const api = apiRef.current
      if (!api) {
        return
      }
      clearLayout(layoutKey)
      api.clear()
      buildDefaultLayout(api, specsRef.current)
    }
    return registerDockReset(rebuild)
  }, [layoutKey])

  useEffect(
    () =>
      registerDockReveal((panelId) => {
        const panel = apiRef.current?.getPanel(panelId)
        if (!panel) {
          return false
        }
        panel.api.setActive()
        return true
      }),
    [],
  )

  // Reconcile whenever the screen's panel set changes.
  useEffect(() => {
    const api = apiRef.current
    if (!api || !readyRef.current) {
      return
    }
    const wanted = specsRef.current
    const wantedIds = new Set(wanted.map((spec) => spec.id))

    for (const panel of [...api.panels]) {
      if (!wantedIds.has(panel.id)) {
        api.removePanel(panel)
      }
    }

    for (const spec of wanted) {
      const existing = api.getPanel(spec.id)
      if (existing && existing.title !== spec.title) {
        existing.api.setTitle(spec.title)
      }
    }
    // Only newly created panels get a preferred size; resizing the rest would
    // undo whatever the operator has arranged.
    applyPreferredSizes(api, syncMissingPanels(api, wanted))
  }, [signature])

  const onReady = (event: DockviewReadyEvent) => {
    apiRef.current = event.api
    readyRef.current = true

    disposablesRef.current.push(
      event.api.onDidLayoutChange(() => {
        // Fires repeatedly while a sash or a tab is dragged.
        if (saveTimer.current) {
          clearTimeout(saveTimer.current)
        }
        saveTimer.current = setTimeout(() => {
          if (apiRef.current) {
            writeLayout(layoutKey, apiRef.current)
          }
        }, 400)
      }),
    )

    const wanted = specsRef.current
    const saved = readLayout(layoutKey)
    if (saved) {
      try {
        event.api.fromJSON(saved)
        const known = new Set(wanted.map((spec) => spec.id))
        // A stale arrangement may reference panels this screen no longer
        // renders; drop those and append anything the saved layout predates.
        for (const panel of [...event.api.panels]) {
          if (!known.has(panel.id)) {
            event.api.removePanel(panel)
          }
        }
        applyPreferredSizes(event.api, syncMissingPanels(event.api, wanted))
        if (event.api.panels.length > 0) {
          return
        }
      } catch {
        // Fall through to a clean default layout.
      }
      event.api.clear()
    }

    buildDefaultLayout(event.api, wanted)
  }

  return (
    <Box
      data-testid="workspace-dock"
      sx={{
        // The grid must be bounded; Dockview cannot size itself from content.
        height: height ?? 'clamp(560px, calc(100vh - 280px), 1400px)',
        minHeight: 0,
        width: '100%',
        borderRadius: 1,
        overflow: 'hidden',
        border: 1,
        borderColor: 'divider',
        bgcolor: 'background.paper',
      }}
    >
      <DockSpecsContext.Provider value={specs}>
        <DockviewReact
          components={COMPONENTS}
          tabComponents={TAB_COMPONENTS}
          rightHeaderActionsComponent={MaximizeAction}
          onReady={onReady}
          disableFloatingGroups
          theme={themeMode === 'dark' ? themeDark : themeLight}
        />
      </DockSpecsContext.Provider>
    </Box>
  )
}
