import axios from 'axios'

const api = axios.create({
  baseURL: '',
  timeout: 15000,
})

export interface MaterialPrice {
  id: number
  name: string
  specification: string
  unit: string
  unit_price: number
  price_type: string
  region: string
  publication_date: string
  source: string
  is_active: boolean
  remarks: string
}

export interface MaterialPriceCreate {
  name: string
  specification?: string
  unit: string
  unit_price: number
  price_type?: string
  region?: string
  publication_date?: string
  source?: string
  is_active?: boolean
  remarks?: string
}

export interface MaterialPriceUpdate {
  name?: string
  specification?: string
  unit?: string
  unit_price?: number
  price_type?: string
  region?: string
  publication_date?: string
  source?: string
  is_active?: boolean
  remarks?: string
}

export async function listPrices(params: {
  skip?: number
  limit?: number
  name?: string
  price_type?: string
  region?: string
  is_active?: boolean
}): Promise<MaterialPrice[]> {
  const res = await api.get<MaterialPrice[]>('/api/v1/price/', { params })
  return res.data
}

export async function getPrice(id: number): Promise<MaterialPrice> {
  const res = await api.get<MaterialPrice>(`/api/v1/price/${id}`)
  return res.data
}

export async function createPrice(data: MaterialPriceCreate): Promise<MaterialPrice> {
  const res = await api.post<MaterialPrice>('/api/v1/price/', data)
  return res.data
}

export async function updatePrice(id: number, data: MaterialPriceUpdate): Promise<MaterialPrice> {
  const res = await api.put<MaterialPrice>(`/api/v1/price/${id}`, data)
  return res.data
}

export async function deletePrice(id: number): Promise<void> {
  await api.delete(`/api/v1/price/${id}`)
}
