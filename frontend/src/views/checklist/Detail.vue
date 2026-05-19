<template>
  <div v-loading="loading">
    <el-page-header @back="router.back()" :title="'返回列表'" content="自检单详情" style="margin-bottom:16px" />

    <template v-if="data">
      <!-- 基础信息卡 -->
      <el-card shadow="never" class="info-card">
        <template #header>
          <div style="display:flex;justify-content:space-between;align-items:center">
            <span style="font-weight:600;font-size:16px">
              {{ data.checklist_no || "草稿" }} — {{ data.title }}
            </span>
            <div style="display:flex;gap:8px;align-items:center">
              <el-tag :class="`risk-${data.risk_level}`">{{ riskLabel(data.risk_level) }}风险</el-tag>
              <el-tag :class="`status-${data.status}`">{{ statusLabel(data.status) }}</el-tag>
            </div>
          </div>
        </template>
        <el-descriptions :column="3" border size="small">
          <el-descriptions-item label="项目">{{ data.project?.project_name }}</el-descriptions-item>
          <el-descriptions-item label="版本号">{{ data.version_no }}</el-descriptions-item>
          <el-descriptions-item label="变更类型">{{ changeTypeLabel(data.change_type) }}</el-descriptions-item>
          <el-descriptions-item label="分支">{{ data.branch_name || "-" }}</el-descriptions-item>
          <el-descriptions-item label="Commit">{{ data.commit_id || "-" }}</el-descriptions-item>
          <el-descriptions-item label="创建人">{{ data.creator?.real_name }}</el-descriptions-item>
          <el-descriptions-item label="MR/PR" :span="2">
            <a v-if="data.mr_pr_link" :href="data.mr_pr_link" target="_blank" style="color:#409EFF">
              {{ data.mr_pr_link }}
            </a>
            <span v-else>-</span>
          </el-descriptions-item>
          <el-descriptions-item label="需求号">{{ data.requirement_no || "-" }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDate(data.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="提交时间">{{ formatDate(data.submitted_at) }}</el-descriptions-item>
        </el-descriptions>
        <el-divider />
        <div v-if="data.change_summary">
          <div style="font-weight:600;margin-bottom:8px">变更概述</div>
          <pre style="white-space:pre-wrap;color:#333">{{ data.change_summary }}</pre>
        </div>
        <div v-if="data.risk_description" style="margin-top:12px">
          <div style="font-weight:600;margin-bottom:8px">风险说明</div>
          <pre style="white-space:pre-wrap;color:#666">{{ data.risk_description }}</pre>
        </div>
      </el-card>

      <!-- 改动模块 -->
      <el-card shadow="never" style="margin-top:16px">
        <template #header><span style="font-weight:600">改动模块</span></template>
        <el-tag
          v-for="m in data.selected_modules"
          :key="m.id"
          :class="`risk-${m.risk_level}`"
          style="margin-right:8px;margin-bottom:4px"
        >
          {{ m.module_name }}
        </el-tag>
        <span v-if="!data.selected_modules?.length" style="color:#999">无</span>
      </el-card>

      <!-- 测试项 -->
      <el-card shadow="never" style="margin-top:16px">
        <template #header>
          <span style="font-weight:600">测试项（共 {{ data.test_results?.length || 0 }} 项）</span>
        </template>
        <el-table :data="data.test_results" border stripe row-class-name="test-row">
          <el-table-column type="index" label="#" width="50" />
          <el-table-column prop="test_name" label="测试项" min-width="180">
            <template #default="{ row }">
              {{ row.test_item?.test_name || row.test_name }}
              <el-tag v-if="row.is_required" size="small" type="danger" style="margin-left:4px">必做</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="source_modules" label="来源模块" width="160" />
          <el-table-column label="级别" width="100">
            <template #default="{ row }">
              <el-tag size="small" :class="`level-${row.test_level}`">
                {{ row.test_level === 'REQUIRED' ? '必做' : '建议' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="执行" width="100">
            <template #default="{ row }">
              <span :class="`executed-${row.executed}`">
                {{ { YES: '已执行', NO: '未执行', NA: '不适用' }[row.executed || ''] || '-' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="结果" width="100">
            <template #default="{ row }">
              <span :class="`result-${row.result}`">
                {{ { PASS: '通过', FAIL: '失败', NA: '不适用' }[row.result || ''] || '-' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="remark" label="备注" min-width="180" show-overflow-tooltip />
        </el-table>
      </el-card>

      <!-- 审核记录 -->
      <el-card shadow="never" style="margin-top:16px" v-if="reviews.length > 0 || data.status !== 'DRAFT'">
        <template #header><span style="font-weight:600">审核记录</span></template>
        <el-table :data="reviews" stripe size="small">
          <el-table-column prop="reviewer.real_name" label="审核人" width="100" />
          <el-table-column prop="action" label="动作" width="100">
            <template #default="{ row }">
              <el-tag size="small" :type="row.action === 'APPROVED' ? 'success' : 'danger'">
                {{ row.action === 'APPROVED' ? '通过' : '退回' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="comment" label="意见" min-width="300" />
          <el-table-column prop="created_at" label="时间" width="160">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 操作按钮 -->
      <div style="margin-top:20px;display:flex;justify-content:flex-end;gap:12px">
        <el-button @click="router.back()">返回</el-button>
        <el-button
          v-if="canEdit"
          type="primary"
          @click="router.push(`/checklists/${data.id}/edit`)"
        >
          编辑
        </el-button>
        <el-button
          v-if="canReview"
          type="success"
          @click="showReviewDialog = true"
        >
          审核
        </el-button>
      </div>
    </template>

    <!-- 审核对话框 -->
    <el-dialog v-model="showReviewDialog" title="审核自检单" width="500px">
      <el-form :model="reviewForm" :rules="reviewRules" ref="reviewFormRef" label-width="80px">
        <el-form-item label="审核动作" prop="action">
          <el-radio-group v-model="reviewForm.action">
            <el-radio value="APPROVED">通过</el-radio>
            <el-radio value="RETURNED">退回修改</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="审核意见" prop="comment">
          <el-input v-model="reviewForm.comment" type="textarea" :rows="3" placeholder="必填，请输入审核意见" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showReviewDialog = false">取消</el-button>
        <el-button type="primary" :loading="reviewLoading" @click="handleReview">
          确认{{ reviewForm.action === 'APPROVED' ? '通过' : '退回' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from "vue"
import { useRoute, useRouter } from "vue-router"
import { ElMessage } from "element-plus"
import { checklistApi } from "@/api"
import { useAuthStore } from "@/stores/auth"
import type { ChecklistDetail } from "@/api/types"
import dayjs from "dayjs"

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const loading = ref(false)
const data = ref<ChecklistDetail | null>(null)
const reviews = ref<any[]>([])
const showReviewDialog = ref(false)
const reviewLoading = ref(false)
const reviewFormRef = ref()

const reviewForm = reactive({
  action: "APPROVED",
  comment: "",
})
const reviewRules = {
  action: [{ required: true }],
  comment: [{ required: true, message: "请输入审核意见", trigger: "blur" }],
}

const canEdit = computed(() => {
  if (!data.value) return false
  return data.value.status === "DRAFT" || data.value.status === "RETURNED"
    ? (auth.isAdmin || (auth.isDeveloper && data.value.creator_id === auth.user?.id))
    : false
})

const canReview = computed(() => {
  if (!data.value) return false
  return data.value.status === "SUBMITTED" && (auth.isAdmin || auth.isReviewer)
})

onMounted(async () => {
  await loadData()
})

async function loadData() {
  loading.value = true
  try {
    const id = Number(route.params.id)
    data.value = await checklistApi.get(id)
    try {
      reviews.value = await checklistApi.reviews(id)
    } catch { reviews.value = [] }
  } finally {
    loading.value = false
  }
}

async function handleReview() {
  const valid = await reviewFormRef.value?.validate().catch(() => false)
  if (!valid) return

  reviewLoading.value = true
  try {
    const id = Number(route.params.id)
    await checklistApi.review(id, {
      action: reviewForm.action,
      comment: reviewForm.comment,
    })
    ElMessage.success("审核完成")
    showReviewDialog.value = false
    await loadData()
  } finally {
    reviewLoading.value = false
  }
}

function formatDate(d: string) {
  return d ? dayjs(d).format("YYYY-MM-DD HH:mm") : "-"
}
function riskLabel(r: string) {
  return { HIGH: "高", MEDIUM: "中", LOW: "低" }[r] || r
}
function statusLabel(s: string) {
  return { DRAFT: "草稿", SUBMITTED: "已提交", RETURNED: "退回", APPROVED: "通过", CLOSED: "关闭" }[s] || s
}
function changeTypeLabel(c: string) {
  return { BUGFIX: "Bug修复", FEATURE: "新功能", REFACTOR: "重构", OPTIMIZATION: "优化", OTHER: "其他" }[c] || c
}
</script>

<style scoped>
.info-card :deep(.el-card__header) { background: #fafafa; }
.test-row.required-row td { background-color: #fff7ed !important; }
pre { font-family: inherit; font-size: 14px; }
</style>
