import { useCallback, useEffect, useRef, useState } from 'react'
import type { Loaded } from '../api/dataClient'
import type { DataSource } from '../api/domain'
import { DataClientError } from '../api/envelope'

export type ResourceStatus = 'loading' | 'ready' | 'error'

export interface ResourceState<T> {
  status: ResourceStatus
  data: T | null
  error: DataClientError | null
  source: DataSource | null
  asOf: string | null
  reload: () => void
  refreshing: boolean
}

/**
 * Runs an async loader that returns a {@link Loaded} envelope and exposes the
 * loading/ready/error lifecycle plus a manual reload. `refreshing` stays true
 * during a background reload so surfaces can keep last-good data visible
 * (STATE-STALE) instead of collapsing to a skeleton.
 */
export function useResource<T>(
  loader: () => Promise<Loaded<T>>,
  deps: ReadonlyArray<unknown>,
): ResourceState<T> {
  const [status, setStatus] = useState<ResourceStatus>('loading')
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<DataClientError | null>(null)
  const [source, setSource] = useState<DataSource | null>(null)
  const [asOf, setAsOf] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState(false)
  const [reloadToken, setReloadToken] = useState(0)
  const mounted = useRef(true)
  const hasData = useRef(false)

  const reload = useCallback(() => setReloadToken((token) => token + 1), [])

  useEffect(() => {
    mounted.current = true
    return () => {
      mounted.current = false
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    if (hasData.current) {
      setRefreshing(true)
    } else {
      setStatus('loading')
    }
    loader()
      .then((result) => {
        if (cancelled || !mounted.current) {
          return
        }
        setData(result.value)
        setSource(result.source)
        setAsOf(result.asOf)
        setError(null)
        setStatus('ready')
        hasData.current = true
      })
      .catch((caught: unknown) => {
        if (cancelled || !mounted.current) {
          return
        }
        setError(
          caught instanceof DataClientError
            ? caught
            : new DataClientError({ code: 'UNKNOWN', message: String(caught) }),
        )
        setStatus('error')
      })
      .finally(() => {
        if (!cancelled && mounted.current) {
          setRefreshing(false)
        }
      })
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reloadToken, ...deps])

  return { status, data, error, source, asOf, reload, refreshing }
}
