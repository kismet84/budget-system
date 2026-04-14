import api from './auth'

export interface DevLogEntry {
  id: string
  title: string
  content: string
  summary: string | null
  type: string
  version: string | null
  tags: string[]
  author: string
  source: string
  file_path: string | null
  project: string
  commit_hash: string | null
  quality: number
  created_at: number
  needs_summary: boolean
}

export interface DevLogStats {
  total: number
  by_type: Record<string, number>
  by_source: Record<string, number>
  daily: Array<{ date: string; count: number }>
}

export interface DevLogListResponse {
  total: number
  entries: DevLogEntry[]
}

export async function fetchDevLogs(params: {
  limit?: number
  offset?: number
  type?: string
  source?: string
  q?: string
}): Promise<DevLogListResponse> {
  const res = await api.get<DevLogListResponse>('/api/v1/devlog/', { params })
  return res.data
}

export async function fetchDevLogStats(): Promise<DevLogStats> {
  const res = await api.get<DevLogStats>('/api/v1/devlog/stats')
  return res.data
}

export async function fetchDevLogTypes(): Promise<string[]> {
  const res = await api.get<string[]>('/api/v1/devlog/types')
  return res.data
}

export async function fetchDevLogEntry(id: string): Promise<DevLogEntry> {
  const res = await api.get<DevLogEntry>(`/api/v1/devlog/${id}`)
  return res.data
}
