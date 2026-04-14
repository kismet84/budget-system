import api from './auth'

export interface Project {
  id: number
  name: string
  description: string
  region: string
  budget_period: string
  notes: string
  status: string
  created_by: string
  created_at: string
  updated_at: string | null
  quota_count: number
  total_cost: number
}

export interface ProjectQuotaItem {
  quota_id: string
  project_name: string | null
  section: string | null
  unit: string | null
  quantity: number
  total_cost: number
  labor_fee: number | null
  material_fee: number | null
  machinery_fee: number | null
  management_fee: number | null
  tax: number | null
}

export interface ProjectDetail extends Project {
  items: ProjectQuotaItem[]
}

export interface ProjectCreate {
  name: string
  description?: string
  region?: string
  budget_period?: string
  notes?: string
  status?: string
}

export interface ProjectUpdate {
  name?: string
  description?: string
  region?: string
  budget_period?: string
  notes?: string
  status?: string
}

// 获取项目列表
export async function listProjects(params?: { skip?: number; limit?: number; status?: string }): Promise<Project[]> {
  const res = await api.get<Project[]>('/api/v1/projects/', { params })
  return res.data
}

// 获取项目详情
export async function getProject(projectId: number): Promise<ProjectDetail> {
  const res = await api.get<ProjectDetail>(`/api/v1/projects/${projectId}`)
  return res.data
}

// 创建项目
export async function createProject(data: ProjectCreate): Promise<Project> {
  const res = await api.post<Project>('/api/v1/projects/', data)
  return res.data
}

// 更新项目
export async function updateProject(projectId: number, data: ProjectUpdate): Promise<Project> {
  const res = await api.patch<Project>(`/api/v1/projects/${projectId}`, data)
  return res.data
}

// 删除项目
export async function deleteProject(projectId: number): Promise<void> {
  await api.delete(`/api/v1/projects/${projectId}`)
}

// 添加定额到项目
export async function addQuotaToProject(projectId: number, quotaId: string, quantity: number = 1): Promise<ProjectQuotaItem> {
  const res = await api.post<ProjectQuotaItem>(`/api/v1/projects/${projectId}/quotas`, {
    quota_id: quotaId,
    quantity,
  })
  return res.data
}

// 从项目移除定额
export async function removeQuotaFromProject(projectId: number, quotaId: string): Promise<void> {
  await api.delete(`/api/v1/projects/${projectId}/quotas/${quotaId}`)
}

// 更新项目中定额数量
export async function updateQuotaQuantity(projectId: number, quotaId: string, quantity: number): Promise<void> {
  await api.patch(`/api/v1/projects/${projectId}/quotas/${quotaId}`, null, {
    params: { quantity },
  })
}
