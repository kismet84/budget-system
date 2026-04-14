import api from './auth'
import type { AISearchResponse, QuotaResult } from '../types/quota'

export async function searchQuotas(
  query: string,
  topK: number = 3,
  sectionPrefix?: string
): Promise<AISearchResponse> {
  const res = await api.post<AISearchResponse>('/api/v1/ai/search', {
    query,
    top_k: topK,
    section_prefix: sectionPrefix || undefined,
  })
  return res.data
}

export async function getQuota(quotaId: string): Promise<QuotaResult> {
  const res = await api.get<QuotaResult>(`/api/v1/quota/${quotaId}`)
  return res.data
}
