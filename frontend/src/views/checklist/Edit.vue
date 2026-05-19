<template>
  <div class="edit-container" v-loading="pageLoading">
    <el-page-header @back="router.back()" :title="'返回列表'" content="编辑自检单" style="margin-bottom:16px" />

    <el-form :model="form" :rules="rules" ref="formRef" label-width="130px" class="checklist-form">
      <!-- 基础信息 -->
      <el-card title="基础信息" shadow="never">
        <template #header>
          <span style="font-weight:600">基础信息</span>
        </template>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="标题" prop="title">
              <el-input v-model="form.title" placeholder="本次变更简述" maxlength="200" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="项目" prop="project_id">
              <el-select v-model="form.project_id" placeholder="请选择项目" style="width:100%">
                <el-option v-for="p in projects" :key="p.id" :label="p.project_name" :value="p.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="版本号" prop="version_no">
              <el-input v-model="form.version_no" placeholder="如 V1.2.3" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="变更类型" prop="change_type">
              <el-select v-model="form.change_type" placeholder="变更类型" style="width:100%">
                <el-option label="Bug修复" value="BUGFIX" />
                <el-option label="新功能" value="FEATURE" />
                <el-option label="重构" value="REFACTOR" />
                <el-option label="优化" value="OPTIMIZATION" />
                <el-option label="其他" value="OTHER" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="分支名">
              <el-input v-model="form.branch_name" placeholder="如 main" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="Commit ID">
              <el-input v-model="form.commit_id" placeholder="如 abc1234" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="MR/PR 链接">
              <el-input v-model="form.mr_pr_link" placeholder="代码合并链接" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="需求/缺陷号">
              <el-input v-model="form.requirement_no" placeholder="如 JIRA-123" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="变更概述" prop="change_summary">
          <el-input v-model="form.change_summary" type="textarea" :rows="3" placeholder="详细描述本次变更内容" />
        </el-form-item>
        <el-form-item label="风险说明">
          <el-input v-model="form.risk_description" type="textarea" :rows="2" placeholder="描述可能存在的风险点" />
        </el-form-item>
      </el-card>

      <!-- 改动模块 -->
      <el-card title="改动模块" shadow="never" style="margin-top:16px">
        <template #header>
          <span style="font-weight:600">改动模块（选择后自动生成测试项）</span>
        </template>
        <div v-if="form.status !== 'DRAFT' && form.status !== 'RETURNED'" style="color:#999">
          当前状态不允许修改模块
        </div>
        <el-checkbox-group v-model="selectedModuleIds" :disabled="form.status !== 'DRAFT' && form.status !== 'RETURNED'">
          <el-checkbox
            v-for="m in riskModules"
            :key="m.id"
            :value="m.id"
            style="margin-bottom:8px;margin-right:16px"
          >
            {{ m.module_name }}
            <el-tag size="small" :class="`risk-${m.risk_level}`" style="margin-left:4px">
              {{ riskLabel(m.risk_level) }}
            </el-tag>
          </el-checkbox>
        </el-checkbox-group>
        <div style="margin-top:12px">
          <el-button
            v-if="selectedModuleIds.length > 0"
            type="primary"
            :disabled="form.status !== 'DRAFT' && form.status !== 'RETURNED'"
            @click="generateTestItems"
            :loading="generating"
          >
            根据选中模块生成测试项 ({{ selectedModuleIds.length }} 个模块)
          </el-button>
          <span v-else-if="riskModules.length > 0" style="color:#999">请先勾选改动模块</span>
        </div>
      </el-card>

      <!-- 测试项 -->
      <el-card v-if="testResults.length > 0" title="测试项" shadow="never" style="margin-top:16px">
        <template #header>
          <span style="font-weight:600">测试项（必做项橙色高亮）</span>
        </template>
        <el-table :data="testResults" border stripe row-class-name="test-row">
          <el-table-column type="index" label="#" width="50" />
          <el-table-column prop="test_name" label="测试项" min-width="180">
            <template #default="{ row }">
              {{ row.test_name }}
              <el-tag v-if="row.is_required" size="small" type="danger" style="margin-left:4px">必做</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="source_modules" label="来源模块" width="160" />
          <el-table-column prop="test_level" label="级别" width="100">
            <template #default="{ row }">
              <el-tag size="small" :class="`level-${row.test_level}`">
                {{ row.test_level === 'REQUIRED' ? '必做' : '建议' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="执行情况" width="140">
            <template #default="{ row, $index }">
              <el-select
                v-model="row.executed"
                placeholder="请选择"
                size="small"
                style="width:100%"
                :disabled="isReadonly"
              >
                <el-option label="已执行" value="YES" />
                <el-option label="未执行" value="NO" />
                <el-option label="不适用" value="NA" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="测试结果" width="120">
            <template #default="{ row }">
              <el-select
                v-model="row.result"
                placeholder="请选择"
                size="small"
                style="width:100%"
                :disabled="isReadonly || row.executed !== 'YES'"
              >
                <el-option label="通过" value="PASS" />
                <el-option label="失败" value="FAIL" />
                <el-option label="不适用" value="NA" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="备注" min-width="160">
            <template #default="{ row }">
              <el-input
                v-model="row.remark"
                placeholder="未执行/失败时必填"
                size="small"
                :disabled="isReadonly"
              />
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 操作按钮 -->
      <div class="action-bar">
        <el-button @click="router.back()">取消</el-button>
        <el-button v-if="!isReadonly" @click="saveDraft" :loading="saving">保存草稿</el-button>
        <el-button
          v-if="!isReadonly && (form.status === 'DRAFT' || form.status === 'RETURNED')"
          type="primary"
          @click="handleSubmit"
          :loading="submitting"
        >
          提交自检单
        </el-button>
      </div>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from "vue"
import { useRoute, useRouter } from "vue-router"
import { ElMessage, ElMessageBox } from "element-plus"
import { checklistApi, projectApi, riskModuleApi } from "@/api"
import { useAuthStore } from "@/stores/auth"
import type { Project, RiskModule, GenerateTestItem } from "@/api/types"

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const isEdit = computed(() => !!route.params.id)
const isReadonly = computed(() =>
  auth.isDeveloper && form.status !== "DRAFT" && form.status !== "RETURNED"
)

const pageLoading = ref(false)
const saving = ref(false)
const submitting = ref(false)
const generating = ref(false)
const formRef = ref()
const projects = ref<Project[]>([])
const riskModules = ref<RiskModule[]>([])
const selectedModuleIds = ref<number[]>([])
const testResults = ref<any[]>([])

const form = reactive({
  title: "",
  project_id: null as number | null,
  version_no: "",
  branch_name: "",
  commit_id: "",
  mr_pr_link: "",
  requirement_no: "",
  change_type: "BUGFIX" as any,
  change_summary: "",
  risk_description: "",
  status: "DRAFT",
})

const rules = {
  title: [{ required: true, message: "请输入标题", trigger: "blur" }],
  project_id: [{ required: true, message: "请选择项目", trigger: "change" }],
  version_no: [{ required: true, message: "请输入版本号", trigger: "blur" }],
  change_type: [{ required: true, message: "请选择变更类型", trigger: "change" }],
  change_summary: [{ required: true, message: "请输入变更概述", trigger: "blur" }],
}

onMounted(async () => {
  await Promise.all([loadProjects(), loadModules()])
  if (isEdit.value) {
    await loadChecklist()
  }
})

async function loadProjects() {
  const res = await projectApi.list({ page_size: 200 })
  projects.value = res.items
}

async function loadModules() {
  const res = await riskModuleApi.list({ page_size: 200, is_active: true })
  riskModules.value = res.items
}

async function loadChecklist() {
  pageLoading.value = true
  try {
    const id = Number(route.params.id)
    const data = await checklistApi.get(id)
    Object.assign(form, {
      title: data.title,
      project_id: data.project_id,
      version_no: data.version_no,
      branch_name: data.branch_name || "",
      commit_id: data.commit_id || "",
      mr_pr_link: data.mr_pr_link || "",
      requirement_no: data.requirement_no || "",
      change_type: data.change_type,
      change_summary: data.change_summary || "",
      risk_description: data.risk_description || "",
      status: data.status,
    })
    selectedModuleIds.value = data.selected_modules.map(m => m.id)
    testResults.value = data.test_results.map(tr => ({
      id: tr.id,
      test_item_id: tr.test_item_id,
      test_name: tr.test_item.test_name,
      source_modules: tr.source_modules,
      test_level: tr.test_level,
      is_required: tr.is_required,
      executed: tr.executed,
      result: tr.result,
      remark: tr.remark || "",
    }))
  } finally {
    pageLoading.value = false
  }
}

async function generateTestItems() {
  generating.value = true
  try {
    let items: any[] = []
    if (isEdit.value) {
      await checklistApi.selectModules(Number(route.params.id), selectedModuleIds.value)
      const data = await checklistApi.get(Number(route.params.id))
      testResults.value = data.test_results.map((tr: any) => ({
        id: tr.id,
        test_item_id: tr.test_item_id,
        test_name: tr.test_item.test_name,
        source_modules: tr.source_modules,
        test_level: tr.test_level,
        is_required: tr.is_required,
        executed: tr.executed,
        result: tr.result,
        remark: tr.remark || "",
      }))
    } else {
      testResults.value = []
      items = await checklistApi.generateTestItems(selectedModuleIds.value)
      testResults.value = items.map((item: any) => ({
        test_item_id: item.test_item_id,
        test_name: item.test_name,
        source_modules: item.module_name,
        test_level: item.test_level,
        is_required: item.is_required,
        executed: undefined,
        result: undefined,
        remark: "",
      }))
    }
    ElMessage.success("测试项已更新")
  } finally {
    generating.value = false
  }
}

async function saveDraft() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    if (isEdit.value) {
      await checklistApi.update(Number(route.params.id), form)
      // 更新模块和测试项
      if (selectedModuleIds.value.length > 0) {
        await checklistApi.selectModules(Number(route.params.id), selectedModuleIds.value)
        await updateTestResults()
      }
    } else {
      const created = await checklistApi.create(form)
      if (selectedModuleIds.value.length > 0) {
        await checklistApi.selectModules(created.id, selectedModuleIds.value)
        await updateTestResults(created.id)
      }
      router.replace(`/checklists/${created.id}/edit`)
    }
    ElMessage.success("保存成功")
  } finally {
    saving.value = false
  }
}

async function updateTestResults(checklistId?: number) {
  const id = checklistId || Number(route.params.id)
  const results = testResults.value.map(tr => ({
    test_result_id: tr.id,
    executed: tr.executed || undefined,
    result: tr.result || undefined,
    remark: tr.remark || undefined,
  }))
  await checklistApi.updateResults(id, results)
}

async function handleSubmit() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  // 前置校验
  if (selectedModuleIds.value.length === 0) {
    ElMessage.warning("请至少选择一个改动模块")
    return
  }

  // 校验测试项
  for (const tr of testResults.value) {
    if (tr.is_required) {
      if (!tr.executed) {
        ElMessage.warning(`必做项「${tr.test_name}」未填写执行情况`)
        return
      }
      if ((tr.executed === "NO" || tr.executed === "NA") && !tr.remark) {
        ElMessage.warning(`必做项「${tr.test_name}」未执行/不适用，请填写原因`)
        return
      }
      if (tr.executed === "YES" && !tr.result) {
        ElMessage.warning(`必做项「${tr.test_name}」已执行，请填写测试结果`)
        return
      }
      if (tr.executed === "YES" && tr.result === "FAIL" && !tr.remark) {
        ElMessage.warning(`必做项「${tr.test_name}」测试失败，请填写说明`)
        return
      }
    }
  }

  try {
    await ElMessageBox.confirm(
      "确认提交自检单？提交后将生成唯一编号。",
      "提交确认",
      { type: "warning" }
    )
  } catch {
    return
  }

  submitting.value = true
  try {
    if (isEdit.value) {
      await checklistApi.update(Number(route.params.id), form)
      await updateTestResults()
      await checklistApi.submit(Number(route.params.id))
    } else {
      const created = await checklistApi.create(form)
      await checklistApi.selectModules(created.id, selectedModuleIds.value)
      // selectModules 后重新加载，获取真实数据库 ID
      const data = await checklistApi.get(created.id)
      testResults.value = data.test_results.map((tr: any) => ({
        id: tr.id,
        test_item_id: tr.test_item_id,
        test_name: tr.test_item.test_name,
        source_modules: tr.source_modules,
        test_level: tr.test_level,
        is_required: tr.is_required,
        executed: tr.executed,
        result: tr.result,
        remark: tr.remark || "",
      }))
      await updateTestResults(created.id)
      await checklistApi.submit(created.id)
      ElMessage.success("提交成功！")
      router.push(`/checklists/${created.id}`)
    }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "提交失败")
  } finally {
    submitting.value = false
  }
}

function riskLabel(r: string) {
  return { HIGH: "高", MEDIUM: "中", LOW: "低" }[r] || r
}
</script>

<style scoped>
.edit-container { max-width: 1100px; }
.checklist-form :deep(.el-card__header) { background: #fafafa; padding: 12px 16px; }
.action-bar { margin-top: 20px; display: flex; justify-content: flex-end; gap: 12px; }
.test-row.required-row td { background-color: #fff7ed !important; }
</style>
