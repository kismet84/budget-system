import axios from 'axios'

const api = axios.create({
  baseURL: '',
  timeout: 60000,
})

export interface ImportReport {
  imported_at: string
  filename: string
  total_rows: number
  success_count: number
  skipped_count: number
  error_count: number
  errors: { row: number; quota_id?: string; error: string }[]
  section_distribution: Record<string, number>
}

export interface DbStats {
  quota_count: number
  material_count: number
  section_distribution: Record<string, number>
}

export interface ImportReportResponse {
  latest_import: ImportReport | null
  db_stats: DbStats
}

export async function importQuotaExcel(file: File): Promise<ImportReport> {
  const formData = new FormData()
  formData.append('file', file)
  const res = await api.post<ImportReport>('/api/v1/admin/quota/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return res.data
}

export async function getImportReport(): Promise<ImportReportResponse> {
  const res = await api.get<ImportReportResponse>('/api/v1/admin/quota/report')
  return res.data
}
