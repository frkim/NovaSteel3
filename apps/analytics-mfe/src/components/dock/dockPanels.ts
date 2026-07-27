import { Children, isValidElement, type ReactElement, type ReactNode } from 'react'
import type { DockAwareComponent, DockPanelSpec, DockRole } from './dockTypes'

/**
 * Depth limit for the passthrough walk. Layout wrappers nest two or three deep
 * at most; the bound simply guarantees termination on an unexpected structure.
 */
const MAX_DEPTH = 6

interface PanelCardLikeProps {
  id?: string
  title?: string
  onDockClose?: () => void
  dockWidth?: number
  dockHeight?: number
  dockBleed?: boolean
}

interface OpaqueProps {
  dockId?: string
  dockTitle?: string
  'data-dock-id'?: string
  'data-dock-title'?: string
  dockHeight?: number
  'data-dock-height'?: number
  dockBleed?: boolean
  'data-dock-bleed'?: boolean
}

interface SplitLikeProps {
  main?: ReactNode
  side?: ReactNode
  sideWidth?: number
}

/**
 * A component whose children is a render function is opaque to this walk, so it
 * may name itself with `dockTitle` / `dockId` rather than fall back to a
 * positional label. Host elements use the `data-dock-*` spelling, which is
 * valid to put on the DOM. The search descends because screens often wrap that
 * boundary in a plain element to keep a scroll anchor.
 */
function selfDescribed(
  node: ReactNode,
  depth = 0,
): { id?: string; title?: string; height?: number; bleed?: boolean } | undefined {
  if (!isValidElement(node) || depth > MAX_DEPTH) {
    return undefined
  }
  const props = node.props as OpaqueProps | null
  const title = props?.dockTitle ?? props?.['data-dock-title']
  const id = props?.dockId ?? props?.['data-dock-id']
  const height = props?.dockHeight ?? props?.['data-dock-height']
  const bleed = props?.dockBleed ?? props?.['data-dock-bleed']
  if (title || id) {
    return { id, title, height, bleed }
  }
  for (const child of Children.toArray(childrenOf(node))) {
    const found = selfDescribed(child, depth + 1)
    if (found) {
      return found
    }
  }
  return undefined
}

function dockRoleOf(node: ReactElement): DockRole | undefined {
  const type = node.type as unknown
  if (typeof type === 'function' || (typeof type === 'object' && type !== null)) {
    return (type as DockAwareComponent).dockRole
  }
  return undefined
}

function childrenOf(node: ReactElement): ReactNode | undefined {
  const props = node.props as { children?: ReactNode } | null
  const children = props?.children
  // StateBoundary and friends take a render function; there is nothing to walk
  // and the element must be treated as an opaque panel.
  return typeof children === 'function' ? undefined : children
}

class SpecBuilder {
  private used = new Set<string>()

  private sequence = 0

  uniqueId(preferred: string | undefined, fallbackPrefix: string): string {
    const base = preferred && preferred.trim().length > 0 ? preferred : `${fallbackPrefix}-${this.sequence++}`
    if (!this.used.has(base)) {
      this.used.add(base)
      return base
    }
    let index = 2
    while (this.used.has(`${base}-${index}`)) {
      index += 1
    }
    const unique = `${base}-${index}`
    this.used.add(unique)
    return unique
  }
}

function collectNode(node: ReactNode, builder: SpecBuilder, depth: number): DockPanelSpec[] {
  if (!isValidElement(node)) {
    return []
  }

  const role = dockRoleOf(node)

  if (role === 'panel') {
    const props = node.props as PanelCardLikeProps
    return [
      {
        id: builder.uniqueId(props.id, 'panel'),
        title: props.title && props.title.trim().length > 0 ? props.title : 'Details',
        content: node,
        closable: typeof props.onDockClose === 'function',
        onClose: props.onDockClose,
        placement: 'below',
        initialWidth: props.dockWidth,
        initialHeight: props.dockHeight,
        bleed: props.dockBleed,
      },
    ]
  }

  if (role === 'kpi') {
    const props = node.props as PanelCardLikeProps
    return [
      {
        id: builder.uniqueId(props.id ?? 'kpi-band', 'kpi'),
        title: props.title && props.title.trim().length > 0 ? props.title : 'Key metrics',
        content: node,
        closable: false,
        placement: 'below',
        initialHeight: 210,
      },
    ]
  }

  if (role === 'split') {
    const props = node.props as SplitLikeProps
    const main = collectMany(props.main, builder, depth + 1)
    const side = collectMany(props.side, builder, depth + 1)
    // A column whose content is opaque (a state boundary, typically) still
    // deserves its own resizable panel rather than being folded into a single
    // undifferentiated block.
    const mainSpecs = main.length > 0 ? main : opaquePanels(props.main, builder, 'Overview')
    const sideSpecs = side.length > 0 ? side : opaquePanels(props.side, builder, 'Details')
    if (mainSpecs.length === 0 || sideSpecs.length === 0) {
      return [...mainSpecs, ...sideSpecs]
    }
    // The side column docks to the right of the main column; anything stacked
    // inside the side column then goes below the first side panel.
    sideSpecs[0] = {
      ...sideSpecs[0],
      placement: 'right',
      reference: mainSpecs[mainSpecs.length - 1].id,
      initialWidth: props.sideWidth ?? 360,
    }
    return [...mainSpecs, ...sideSpecs]
  }

  if (depth >= MAX_DEPTH) {
    return []
  }

  return collectMany(childrenOf(node), builder, depth + 1)
}

function collectMany(nodes: ReactNode, builder: SpecBuilder, depth: number): DockPanelSpec[] {
  const specs: DockPanelSpec[] = []
  for (const child of Children.toArray(nodes)) {
    specs.push(...collectNode(child, builder, depth))
  }
  return specs
}

/** Wraps content the walk could not see into panels of its own. */
function opaquePanels(nodes: ReactNode, builder: SpecBuilder, fallbackTitle: string): DockPanelSpec[] {
  return Children.toArray(nodes)
    .filter(isValidElement)
    .map((child) => {
      const described = selfDescribed(child)
      return {
        id: builder.uniqueId(described?.id, 'section'),
        title: described?.title ?? fallbackTitle,
        content: child,
        closable: false,
        placement: 'below' as const,
        initialHeight: described?.height,
        bleed: described?.bleed,
      }
    })
}

/**
 * Derives the dock panels for a screen from the JSX it already declares.
 *
 * Screens compose `SectionStack > KpiBand | PanelCard | TwoColumn`, so the
 * layout tree already carries every piece of metadata a panel needs: a stable
 * id, a human title, and — through `onDockClose` — whether the panel is
 * dismissible. Deriving the panels instead of asking each screen to declare
 * them twice keeps the 22 existing screens untouched and prevents the two
 * descriptions from drifting apart.
 *
 * A child that exposes no recognisable panel (typically a `StateBoundary`,
 * whose children is a render function) becomes a panel in its own right, so
 * nothing a screen renders can be silently dropped.
 */
export function collectDockPanels(children: ReactNode): DockPanelSpec[] {
  const builder = new SpecBuilder()
  const specs: DockPanelSpec[] = []

  Children.toArray(children).forEach((child, index) => {
    const found = collectNode(child, builder, 0)
    if (found.length > 0) {
      specs.push(...found)
      return
    }
    const described = selfDescribed(child)
    specs.push({
      id: builder.uniqueId(described?.id, 'section'),
      // The opaque leading child is, in every current screen, the guarded KPI
      // band; later ones are supporting detail.
      title: described?.title ?? (index === 0 ? 'Key metrics' : 'Details'),
      content: child,
      closable: false,
      placement: 'below',
      initialHeight: described?.height ?? (index === 0 ? 210 : undefined),
      bleed: described?.bleed,
    })
  })

  return specs
}
