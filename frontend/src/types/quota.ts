export interface QuotaResult {
  quota_id: string
  project_name: string | null
  section: string
  category: string
  unit: string
  total_cost: number
  labor_fee: number | null
  material_fee: number | null
  machinery_fee: number | null
  management_fee: number | null
  tax: number | null
  work_content?: string
  similarity: number
  rerank_score: number
}

export interface AISearchResponse {
  query: string
  results: QuotaResult[]
  total: number
  warning?: string
}

export interface CartItem {
  quota_id: string
  project_name: string
  section: string
  unit: string
  quantity: number
  total_cost: number
  labor_fee: number | null
  material_fee: number | null
  machinery_fee: number | null
  management_fee: number | null
  tax: number | null
  addedAt: number
}
