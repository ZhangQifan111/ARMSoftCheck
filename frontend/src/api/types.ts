// 类型定义
export interface User {
  id: number
  username: string
  real_name: string
  email: string
  role: "ADMIN" | "DEVELOPER" | "REVIEWER" | "TESTER"
  status: boolean
  created_at: string
}

export interface Project {
  id: number
  project_name: string
  product_model: string | null
  is_active: boolean
  created_at: string
}

export interface RiskModule {
  id: number
  module_code: string
  module_name: string
  risk_level: "HIGH" | "MEDIUM" | "LOW"
  description: string | null
  sort_order: number
  is_active: boolean
  created_at: string
}

export interface TestItem {
  id: number
  test_code: string
  test_name: string
  module_id: number
  default_risk_level: "HIGH" | "MEDIUM" | "LOW"
  is_required: boolean
  description: string | null
  sort_order: number
  created_at: string
}

export interface ModuleTestMap {
  id: number
  module_code: string
  test_code: string
  is_required: boolean
  sort_order: number
  remark: string | null
  is_active: boolean
  created_at: string
}

export interface GenerateTestItem {
  test_item_id: number
  test_code: string
  test_name: string
  module_id: number
  module_name: string
  module_code: string
  is_required: boolean
  test_level: "REQUIRED" | "RECOMMENDED"
  description: string | null
}

export interface ChecklistTestResult {
  id: number
  test_item_id: number
  module_id: number
  is_required: boolean
  test_level: "REQUIRED" | "RECOMMENDED"
  source_modules: string | null
  executed: "YES" | "NO" | "NA" | null
  result: "PASS" | "FAIL" | "NA" | null
  remark: string | null
  created_at: string
  updated_at: string
  test_item: TestItem
  module: RiskModule
}

export interface Checklist {
  id: number
  checklist_no: string | null
  title: string
  project_id: number
  product_model: string | null
  version_no: string
  branch_name: string | null
  commit_id: string | null
  mr_pr_link: string | null
  requirement_no: string | null
  change_type: "BUGFIX" | "FEATURE" | "REFACTOR" | "OPTIMIZATION" | "OTHER"
  change_summary: string | null
  risk_description: string | null
  risk_level: "HIGH" | "MEDIUM" | "LOW"
  status: "DRAFT" | "SUBMITTED" | "RETURNED" | "APPROVED" | "CLOSED"
  creator_id: number
  reviewer_id: number | null
  review_comment: string | null
  review_time: string | null
  created_at: string
  updated_at: string
  submitted_at: string | null
}

export interface ChecklistDetail extends Checklist {
  selected_modules: RiskModule[]
  test_results: ChecklistTestResult[]
  creator: User
  reviewer: User | null
  project: Project
}

export interface OperationLog {
  id: number
  operator_id: number
  operator_name: string
  business_type: string
  business_id: number | null
  business_no: string | null
  action: string
  detail: string | null
  ip_address: string | null
  created_at: string
}

export interface PageResponse<T = any> {
  total: number
  page: number
  page_size: number
  items: T[]
}
