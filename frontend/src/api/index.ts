import request from "./axios"
import type {
  User, Project, RiskModule, TestItem, ModuleTestMap,
  Checklist, ChecklistDetail, ChecklistTestResult,
  GenerateTestItem, OperationLog, PageResponse
} from "./types"

// ─── 认证 ──────────────────────────────────────────────────
export const authApi = {
  login: (data: { username: string; password: string }) =>
    request.post<any, any>("/auth/login", data),
  me: () => request.get<any, any>("/auth/me"),
}

// ─── 用户 ──────────────────────────────────────────────────
export const userApi = {
  list: (params: any) => request.get<any, PageResponse<User>>("/users", { params }),
  create: (data: any) => request.post("/users", data),
  update: (id: number, data: any) => request.put(`/users/${id}`, data),
  delete: (id: number) => request.delete(`/users/${id}`),
}

// ─── 项目 ──────────────────────────────────────────────────
export const projectApi = {
  list: (params?: any) => request.get<any, PageResponse<Project>>("/projects", { params }),
  create: (data: any) => request.post("/projects", data),
  update: (id: number, data: any) => request.put(`/projects/${id}`, data),
  delete: (id: number) => request.delete(`/projects/${id}`),
}

// ─── 风险模块 ──────────────────────────────────────────────
export const riskModuleApi = {
  list: (params?: any) => request.get<any, PageResponse<RiskModule>>("/risk-modules", { params }),
  create: (data: any) => request.post("/risk-modules", data),
  update: (id: number, data: any) => request.put(`/risk-modules/${id}`, data),
  delete: (id: number) => request.delete(`/risk-modules/${id}`),
}

// ─── 测试项 ────────────────────────────────────────────────
export const testItemApi = {
  list: (params?: any) => request.get<any, PageResponse<TestItem>>("/test-items", { params }),
  create: (data: any) => request.post("/test-items", data),
  update: (id: number, data: any) => request.put(`/test-items/${id}`, data),
  delete: (id: number) => request.delete(`/test-items/${id}`),
}

// ─── 模块-测试项映射 ────────────────────────────────────────
export const mapApi = {
  list: (params?: any) => request.get<any, PageResponse<ModuleTestMap>>("/module-test-maps", { params }),
  create: (data: any) => request.post("/module-test-maps", data),
  update: (id: number, data: any) => request.put(`/module-test-maps/${id}`, data),
  delete: (id: number) => request.delete(`/module-test-maps/${id}`),
  generate: (module_ids: number[]) =>
    request.post<any, GenerateTestItem[]>("/checklists/generate-test-items", { module_ids }),
}

// ─── 自检单 ────────────────────────────────────────────────
export const checklistApi = {
  list: (params?: any) => request.get<any, PageResponse<Checklist>>("/checklists", { params }),
  get: (id: number) => request.get<any, ChecklistDetail>(`/checklists/${id}`),
  create: (data: any) => request.post("/checklists", data),
  update: (id: number, data: any) => request.put(`/checklists/${id}`, data),
  delete: (id: number) => request.delete(`/checklists/${id}`),
  selectModules: (id: number, module_ids: number[]) =>
    request.post(`/checklists/${id}/select-modules`, { module_ids }),
  updateResults: (id: number, results: any[]) =>
    request.put(`/checklists/${id}/test-results`, { results }),
  submit: (id: number) => request.post(`/checklists/${id}/submit`),
  review: (id: number, data: { action: string; comment: string }) =>
    request.post(`/checklists/${id}/review`, data),
  reviews: (id: number) => request.get<any, any[]>(`/checklists/${id}/reviews`),
  generateTestItems: (module_ids: number[]) =>
    request.post<any, GenerateTestItem[]>(`/checklists/generate-test-items`, { module_ids }),
}

// ─── 操作日志 ──────────────────────────────────────────────
export const logApi = {
  list: (params?: any) => request.get<any, PageResponse<OperationLog>>("/operation-logs", { params }),
}
