import { createContext, useContext } from 'react'

/**
 * True for content rendered inside a dock panel.
 *
 * A dock tab already draws a frame and shows the panel title, so the card
 * chrome the same components use on an undocked page would add a second border
 * and a duplicate heading. Components read this to shed that chrome.
 */
export const DockedContext = createContext(false)

export function useDocked(): boolean {
  return useContext(DockedContext)
}
