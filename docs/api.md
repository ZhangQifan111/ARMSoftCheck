# API 接口文档

Base URL: `/api/v1`

认证方式: `Authorization: Bearer <JWT_TOKEN>`

## 通用响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

| code | 说明 |
|------|------|
| 0 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 500 | 服务器错误 |

---

## 认证模块 `/auth`

### POST /api/v1/auth/login
登录

**Body:**
```json
{
  "username": "admin",
  "password": "Admin@123"
}
```
**Response:**
```json
{
  "code": 0,
  "data": {
    "access_token": "eyJ...",
    "token_type": "bearer",
    "expires_in": 43200,
    "user": { "id": 1, "username": "admin", "real_name": "管理员", "role": "ADMIN" }
  }
}
```

### GET /api/v1/auth/me
获取当前用户信息

---

## 用户模块 `/users`

### GET /api/v1/users
列表 (分页)

**Query:** `page, page_size, keyword, role, status`

### POST /api/v1/users
创建用户

### PUT /api/v1/users/{id}
更新用户

### DELETE /api/v1/users/{id}
删除用户

---

## 项目模块 `/projects`

### GET /api/v1/projects
列表

### POST /api/v1/projects
创建

### PUT /api/v1/projects/{id}
更新

### DELETE /api/v1/projects/{id}
删除

---

## 风险模块 `/risk-modules`

### GET /api/v1/risk-modules
列表

### POST /api/v1/risk-modules
创建

### PUT /api/v1/risk-modules/{id}
更新

### DELETE /api/v1/risk-modules/{id}
删除

---

## 测试项 `/test-items`

### GET /api/v1/test-items
列表

### POST /api/v1/test-items
创建

### PUT /api/v1/test-items/{id}
更新

### DELETE /api/v1/test-items/{id}
删除

---

## 模块-测试项映射 `/module-test-maps`

### GET /api/v1/module-test-maps
列表 (支持按 module_code 或 test_code 筛选)

### POST /api/v1/module-test-maps
创建

### PUT /api/v1/module-test-maps/{id}
更新

### DELETE /api/v1/module-test-maps/{id}
删除

### GET /api/v1/module-test-maps/by-modules
根据模块列表获取映射的测试项 (用于自检单生成)

**Query:** `module_codes` (逗号分隔)

---

## 自检单 `/checklists`

### GET /api/v1/checklists
列表 (分页, 角色过滤)

**Query:** `page, page_size, status, risk_level, project_id, date_from, date_to, keyword`

### POST /api/v1/checklists
创建草稿

### GET /api/v1/checklists/{id}
详情 (包含模块和测试结果)

### PUT /api/v1/checklists/{id}
更新 (仅草稿/退回状态)

### DELETE /api/v1/checklists/{id}
删除 (仅草稿)

### POST /api/v1/checklists/generate-test-items
根据选中模块生成测试项 (返回测试项列表)

**Body:**
```json
{
  "module_codes": ["BOOT", "UPGRADE"]
}
```

### POST /api/v1/checklists/{id}/submit
提交自检单 (生成编号)

### POST /api/v1/checklists/{id}/review
审核自检单

**Body:**
```json
{
  "action": "APPROVE",
  "comment": "同意合入"
}
```

---

## 操作日志 `/operation-logs`

### GET /api/v1/operation-logs
列表 (分页)

**Query:** `page, page_size, operator_id, business_type, date_from, date_to`

---

## 数据字典

### 变更类型 (change_type)
- `BUGFIX` - Bug修复
- `FEATURE` - 新功能
- `REFACTOR` - 重构
- `OPTIMIZATION` - 优化
- `OTHER` - 其他

### 风险等级 (risk_level)
- `HIGH` - 高风险
- `MEDIUM` - 中风险
- `LOW` - 低风险

### 测试项级别 (test_level)
- `REQUIRED` - 必做
- `RECOMMENDED` - 建议

### 执行结果 (test_result)
- `YES` - 已执行
- `NO` - 未执行
- `NA` - 不适用

### 测试结果 (result)
- `PASS` - 通过
- `FAIL` - 失败
- `NA` - 不适用

### 自检单状态 (status)
- `DRAFT` - 草稿
- `SUBMITTED` - 已提交
- `RETURNED` - 退回修改
- `APPROVED` - 审核通过
- `CLOSED` - 已关闭

### 操作类型 (action)
- `CREATE` - 创建
- `UPDATE` - 更新
- `DELETE` - 删除
- `SUBMIT` - 提交
- `APPROVE` - 审核通过
- `RETURN` - 退回
