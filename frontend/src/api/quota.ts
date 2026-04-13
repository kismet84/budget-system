import axios from 'axios'
import type { AISearchResponse } from '../types/quota'

const api = axios.create({
  baseURL: '',
  timeout: 15000,
})

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
