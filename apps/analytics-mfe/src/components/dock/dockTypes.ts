import type { ReactNode } from 'react'

/** Where a panel is placed relative to its reference panel. */
export type DockPlacement = 'below' | 'right'

export interface DockPanelSpec {
  id: string
  title: string
  content: ReactNode
  /**
   * Only closable panels render an X on their tab. Primary panels — the KPI
   * band, the main table of a screen — are structural: closing them would
   * leave the screen empty with no obvious way back, so their tab shows no
   * close affordance at all.
   */
  closable: boolean
  /**
   * Invoked instead of Dockview's own close handling. The owning screen clears
   * the state that produced the panel; the panel then disappears through the
   * normal reconciliation pass, keeping React state the single source of truth.
   */
  onClose?: () => void
  placement: DockPlacement
  /** Panel this one is positioned against; defaults to the preceding panel. */
  reference?: string
  initialWidth?: number
  initialHeight?: number
  /**
   * Renders the panel body without the usual inset. The corporate website
   * pages are full-bleed by design — a hero band that stops 8px short of the
   * panel edge reads as a broken page rather than a website.
   */
  bleed?: boolean
}

export type DockRole = 'panel' | 'kpi' | 'split'

/**
 * Layout primitives tag themselves with a dock role so the collector can
 * recognise them without importing them, which would otherwise create a cycle
 * (common.tsx -> WorkspaceDock -> dockPanels -> common.tsx).
 */
export interface DockAwareComponent {
  dockRole?: DockRole
}
