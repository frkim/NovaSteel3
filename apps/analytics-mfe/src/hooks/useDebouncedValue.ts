import { useEffect, useState } from 'react'

/** Returns a debounced copy of `value` after `delayMs` of no changes (TBL-STD 250ms search). */
export function useDebouncedValue<T>(value: T, delayMs = 250): T {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delayMs)
    return () => clearTimeout(timer)
  }, [value, delayMs])
  return debounced
}
