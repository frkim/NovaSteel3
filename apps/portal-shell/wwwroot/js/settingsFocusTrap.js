const traps = new WeakMap()

const selector = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(',')

function focusableElements(dialog) {
  return Array.from(dialog.querySelectorAll(selector)).filter((element) => {
    const style = window.getComputedStyle(element)
    return style.visibility !== 'hidden' && style.display !== 'none' && element.getClientRects().length > 0
  })
}

export function activateFocusTrap(dialog) {
  if (!dialog) {
    return
  }

  deactivateFocusTrap(dialog)

  const handler = (event) => {
    if (event.key !== 'Tab') {
      return
    }

    const focusable = focusableElements(dialog)
    if (focusable.length === 0) {
      event.preventDefault()
      dialog.focus()
      return
    }

    const first = focusable[0]
    const last = focusable[focusable.length - 1]
    const active = document.activeElement

    if (active === dialog) {
      event.preventDefault()
      ;(event.shiftKey ? last : first).focus()
      return
    }

    if (event.shiftKey && active === first) {
      event.preventDefault()
      last.focus()
      return
    }

    if (!event.shiftKey && active === last) {
      event.preventDefault()
      first.focus()
    }
  }

  dialog.addEventListener('keydown', handler)
  traps.set(dialog, handler)
}

export function deactivateFocusTrap(dialog) {
  const handler = traps.get(dialog)
  if (!handler) {
    return
  }

  dialog.removeEventListener('keydown', handler)
  traps.delete(dialog)
}
