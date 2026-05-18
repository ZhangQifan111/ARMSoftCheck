# 种子数据说明

## 目录结构

```
seeds/              # 实际使用的种子数据文件
seed_templates/     # 缺失时自动生成的模板
```

## 文件列表

| 文件名 | 用途 | 是否必选 |
|--------|------|---------|
| projects_seed.csv | 项目/产品线初始化 | ✅ |
| risk_modules_seed.csv | 风险模块初始化 | ✅ |
| test_items_seed.csv | 测试项字典初始化 | ✅ |
| module_test_map_seed.csv | 模块-测试项映射 | ✅ |
| users_seed.csv | 用户账号初始化 | ✅ |
| ui_theme_config.json | 前端主题配置 | ❌ |
| env.sample | 环境变量模板 | ❌ |

## 导入方式

后端启动时自动检测并导入（幂等操作）。

```bash
# 手动触发导入
cd backend && python -m seeds.import_seed
```

## 字段说明

### projects_seed.csv

| 字段 | 类型 | 说明 |
|------|------|------|
| project_name | string | 项目名称 |
| product_model | string | 产品型号 |
| is_active | int | 是否启用(1/0) |

### risk_modules_seed.csv

| 字段 | 类型 | 说明 |
|------|------|------|
| module_code | string | 模块代码(唯一) |
| module_name | string | 模块中文名 |
| risk_level | enum | HIGH/MEDIUM/LOW |
| description | string | 描述 |
| sort_order | int | 排序号 |
| is_active | int | 是否启用 |

### test_items_seed.csv

| 字段 | 类型 | 说明 |
|------|------|------|
| test_code | string | 测试项代码(唯一) |
| test_name | string | 测试项名称 |
| default_level | enum | REQUIRED/RECOMMENDED |
| default_risk_level | enum | HIGH/MEDIUM/LOW |
| description | string | 描述 |
| sort_order | int | 排序号 |
| is_active | int | 是否启用 |

### module_test_map_seed.csv

| 字段 | 类型 | 说明 |
|------|------|------|
| module_code | string | 关联模块代码 |
| test_code | string | 关联测试项代码 |
| is_required | int | 是否必做(1/0) |
| sort_order | int | 排序号 |
| remark | string | 备注 |
| is_active | int | 是否启用 |

### users_seed.csv

| 字段 | 类型 | 说明 |
|------|------|------|
| username | string | 登录账号(唯一) |
| password | string | 密码(明文,导入时bcrypt加密) |
| real_name | string | 真实姓名 |
| email | string | 邮箱 |
| role | enum | ADMIN/DEVELOPER/REVIEWER/TESTER |
| status | int | 状态(1正常/0禁用) |

## 幂等说明

所有 seed 导入使用 `INSERT ... ON DUPLICATE KEY UPDATE` 语义，
重复导入不会产生重复数据。
