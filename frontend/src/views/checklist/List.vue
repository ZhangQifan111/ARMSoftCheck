<template>
  <div>
    <!-- 操作栏 -->
    <el-card shadow="never" class="filter-card">
      <el-form inline :model="query" @submit.prevent="loadData">
        <el-form-item label="状态">
          <el-select v-model="query.status" clearable placeholder="全部" style="width:140px">
            <el-option label="草稿" value="DRAFT" />
            <el-option label="已提交" value="SUBMITTED" />
            <el-option label="退回修改" value="RETURNED" />
            <el-option label="审核通过" value="APPROVED" />
          </el-select>
        </el-form-item>
        <el-form-item label="风险等级">
          <el-select v-model="query.risk_level" clearable placeholder="全部" style="width:140px">
            <el-option label="高风险" value="HIGH" />
            <el-option label="中风险" value="MEDIUM" />
            <el-option label="低风险" value="LOW" />
          </el-select>
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="query.keyword" placeholder="标题/编号/变更说明" clearable style="width:180px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">查询</el-button>
          <el-button @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>
      <div style="margin-top:8px">
        <el-button v-if="auth.isAdmin || auth.isDeveloper" type="primary" @click="router.push('/checklists/create')">
          <el-icon><Plus /></el-icon> 新建自检单
        </el-button>
      </div>
    </el-card>

    <!-- 列表 -->
    <el-card shadow="never" style="margin-top:12px">
      <el-table :data="list" stripe v-loading="loading" row-key="id">
        <el-table-column prop="checklist_no" label="编号" width="180">
          <template #default="{ row }">
            <el-link type="primary" @click="router.push(`/checklists/${row.id}`)">
              {{ row.checklist_no || "草稿" }}
            </el-link>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="project_id" label="项目" width="120">
          <template #default="{ row }">
            {{ getProjectName(row.project_id) }}
          </template>
        </el-table-column>
        <el-table-column prop="change_type" label="变更类型" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ changeTypeLabel(row.change_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="risk_level" label="风险" width="90">
          <template #default="{ row }">
            <el-tag size="small" :class="`risk-${row.risk_level}`">
              {{ riskLabel(row.risk_level) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="110">
          <template #default="{ row }">
            <el-tag size="small" :class="`status-${row.status}`">
              {{ statusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="creator_id" label="创建人" width="90">
          <template #default="{ row }">
            {{ getCreatorName(row.creator_id) }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <div class="action-btns">
              <el-button type="primary" link size="small" @click="router.push(`/checklists/${row.id}`)">
                查看
              </el-button>
              <el-button
                v-if="canEdit(row)"
                type="primary" link size="small"
                @click="router.push(`/checklists/${row.id}/edit`)"
              >
                编辑
              </el-button>
              <el-popconfirm
                v-if="auth.isAdmin || row.status === 'DRAFT' || row.status === 'RETURNED'"
                title="确认删除该自检单？"
                @confirm="handleDelete(row.id)"
              >
                <template #reference>
                  <el-button type="danger" link size="small">删除</el-button>
                </template>
              </el-popconfirm>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="query.page"
        v-model:page-size="query.page_size"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        style="margin-top:16px;justify-content:center"
        @size-change="loadData"
        @current-change="loadData"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from "vue"
import { useRouter } from "vue-router"
import { ElMessage } from "element-plus"
import { checklistApi, projectApi } from "@/api"
import { useAuthStore } from "@/stores/auth"
import type { Checklist, Project } from "@/api/types"
import dayjs from "dayjs"

const router = useRouter()
const auth = useAuthStore()
const loading = ref(false)
const list = ref<Checklist[]>([])
const total = ref(0)
const projects = ref<Project[]>([])
const creatorMap = ref<Record<number, string>>({})

const query = reactive({
  page: 1,
  page_size: 20,
  status: "",
  risk_level: "",
  keyword: "",
})

onMounted(() => {
  loadData()
  loadProjects()
})

async function loadData() {
  loading.value = true
  try {
    // 过滤掉空字符串，避免 FastAPI enum 校验失败（422）
    const params: any = {}
    for (const [k, v] of Object.entries(query)) {
      if (v !== "" && v !== null && v !== undefined) {
        params[k] = v
      }
    }
    const res = await checklistApi.list(params)
    list.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

async function loadProjects() {
  const res = await projectApi.list({ page_size: 200 })
  projects.value = res.items
  // 构建创建人映射
  // 从列表中提取 creator 信息... 用 last 活跃时间的方式
}

function getProjectName(id: number) {
  return projects.value.find(p => p.id === id)?.project_name || String(id)
}

function getCreatorName(id: number) {
  return creatorMap.value[id] || String(id)
}

function resetQuery() {
  query.status = ""
  query.risk_level = ""
  query.keyword = ""
  query.page = 1
  loadData()
}

function canEdit(row: Checklist) {
  if (row.status === "DRAFT" || row.status === "RETURNED") {
    return auth.isAdmin || (auth.isDeveloper && row.creator_id === auth.user?.id)
  }
  return false
}

async function handleDelete(id: number) {
  await checklistApi.delete(id)
  ElMessage.success("删除成功")
  loadData()
}

function formatDate(d: string) {
  return d ? dayjs(d).format("YYYY-MM-DD HH:mm") : "-"
}

function statusLabel(s: string) {
  return { DRAFT: "草稿", SUBMITTED: "已提交", RETURNED: "退回", APPROVED: "通过", CLOSED: "关闭" }[s] || s
}
function riskLabel(r: string) {
  return { HIGH: "高", MEDIUM: "中", LOW: "低" }[r] || r
}
function changeTypeLabel(c: string) {
  return { BUGFIX: "Bug修复", FEATURE: "新功能", REFACTOR: "重构", OPTIMIZATION: "优化", OTHER: "其他" }[c] || c
}
</script>

<style scoped>
.filter-card :deep(.el-card__body) { padding-bottom: 0; }
</style>
