import type { CaptureLanguage } from '../types'

/**
 * Durable store for recordings that could not be uploaded (connectivity loss).
 * Plain IndexedDB — no extra dependency. A recording is never silently lost:
 * the wizard writes here before/after a failed upload and lists pending items
 * so the operator can retry later.
 */

const DB_NAME = 'ns-operator-capture'
const DB_VERSION = 1
const STORE = 'pending-recordings'

export interface PendingRecording {
  id: string
  createdAt: number
  operatorRef: string
  title: string
  domain: string
  language: CaptureLanguage
  durationSeconds: number
  sessionId?: string
  blob: Blob
}

export interface PendingRecordingMeta extends Omit<PendingRecording, 'blob'> {
  sizeBytes: number
}

function hasIndexedDb(): boolean {
  return typeof indexedDB !== 'undefined'
}

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION)
    request.onupgradeneeded = () => {
      const db = request.result
      if (!db.objectStoreNames.contains(STORE)) {
        db.createObjectStore(STORE, { keyPath: 'id' })
      }
    }
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error ?? new Error('IndexedDB open failed'))
  })
}

function tx<T>(mode: IDBTransactionMode, run: (store: IDBObjectStore) => IDBRequest<T>): Promise<T> {
  return openDb().then(
    (db) =>
      new Promise<T>((resolve, reject) => {
        const transaction = db.transaction(STORE, mode)
        const store = transaction.objectStore(STORE)
        const request = run(store)
        request.onsuccess = () => resolve(request.result)
        request.onerror = () => reject(request.error ?? new Error('IndexedDB request failed'))
        transaction.oncomplete = () => db.close()
      }),
  )
}

export async function savePending(record: PendingRecording): Promise<void> {
  if (!hasIndexedDb()) {
    return
  }
  await tx('readwrite', (store) => store.put(record))
}

export async function getPending(id: string): Promise<PendingRecording | undefined> {
  if (!hasIndexedDb()) {
    return undefined
  }
  return tx<PendingRecording | undefined>('readonly', (store) => store.get(id) as IDBRequest<PendingRecording | undefined>)
}

export async function deletePending(id: string): Promise<void> {
  if (!hasIndexedDb()) {
    return
  }
  await tx('readwrite', (store) => store.delete(id))
}

export async function listPending(): Promise<PendingRecordingMeta[]> {
  if (!hasIndexedDb()) {
    return []
  }
  const all = await tx<PendingRecording[]>('readonly', (store) => store.getAll() as IDBRequest<PendingRecording[]>)
  return all
    .map(({ blob, ...meta }) => ({ ...meta, sizeBytes: blob?.size ?? 0 }))
    .sort((a, b) => b.createdAt - a.createdAt)
}
