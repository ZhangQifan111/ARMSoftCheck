<template>
  <div>
    <div style="margin-bottom:16px;display:flex;justify-content:space-between">
      <h3>风险模块管理</h3>
      <el-button type="primary" @click="openModuleDialog()">
        <el-icon><Plus /></el-icon> 新建模块
      </el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="modules" stripe v-loading="loading" row-key="id">
        <el-table-column type="expand" width="50">
          <template #default="{ row }">
            <div style="padding: 8px 48px 16px; background: #fafafa">
              <!-- 模块内的测试项工具栏 -->
              <div style="margin-bottom:10px;display:flex;gap:8px;align-items:center">
                <span style="font-size:13px;color:#666">
                  <strong>{{ row.module_name }}</strong> 下的测试项
                </span>
                <el-button size="small" type="primary" @click="openTestItemDialog(row.id)">
                  <el-icon><Plus /></el-icon> 新增测试项
                </el-button>
              </div>

              <!-- 测试项列表（无数据时显示空状态） -->
              <el-table
                v-if="moduleTestItems[row.id]?.length"
                :data="moduleTestItems[row.id]"
                size="small"
                style="width:100%"
                header-cell-class-name="test-item-header"
              >
                <el-table-column prop="test_code" label="编码" width="140" />
                <el-table-column prop="test_name" label="测试名称" min-width="200" show-overflow-tooltip />
                <el-table-column prop="is_required" label="必做" width="80">
                  <template #default="{ row: ti }">
                    <el-tag :type="ti.is_required ? 'danger' : 'info'" size="small">
                      {{ ti.is_required ? "必做" : "建议" }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="default_level" label="级别" width="90">
                  <template #default="{ row: ti }">
                    <el-tag size="small">{{ ti.default_level === 'REQUIRED' ? '必填' : '建议' }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="description" label="描述" show-overflow-tooltip />
                <el-table-column label="操作" width="120">
                  <template #default="{ row: ti }">
                    <el-button type="primary" link size="small" @click="openTestItemDialog(row.id, ti)">编辑</el-button>
                    <el-popconfirm title="确认删除？" @confirm="deleteTestItem(ti.id, row.id)">
                      <template #reference>
                        <el-button type="danger" link size="small">删除</el-button>
                      </template>
                    </el-popconfirm>
                  </template>
                </el-table-column>
              </el-table>

              <el-empty v-else description="暂无测试项，点击上方按钮添加" :image-size="60" />
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="module_code" label="代码" width="140" />
        <el-table-column prop="module_name" label="名称" min-width="180" />
        <el-table-column prop="risk_level" label="风险等级" width="110">
          <template #default="{ row }">
            <el-tag size="small" :class="`risk-${row.risk_level}`">
              {{ { HIGH: '高', MEDIUM: '中', LOW: '低' }[row.risk_level] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column prop="sort_order" label="排序" width="70" />
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? "启用" : "禁用" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="openModuleDialog(row)">编辑</el-button>
            <el-popconfirm title="确认删除？" @confirm="deleteModule(row.id)">
              <template #reference>
                <el-button type="danger" link size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 模块对话框 -->
    <el-dialog v-model="moduleDialogVisible" :title="moduleEditing ? '编辑模块' : '新建模块'" width="550px">
      <el-form :model="moduleForm" :rules="moduleRules" ref="moduleFormRef" label-width="100px">
        <el-form-item label="模块代码" prop="module_code">
          <el-input v-model="moduleForm.module_code" :disabled="!!moduleEditing" />
        </el-form-item>
        <el-form-item label="模块名称" prop="module_name">
          <el-input v-model="moduleForm.module_name" />
        </el-form-item>
        <el-form-item label="风险等级" prop="risk_level">
          <el-select v-model="moduleForm.risk_level" style="width:100%">
            <el-option label="高风险" value="HIGH" />
            <el-option label="中风险" value="MEDIUM" />
            <el-option label="低风险" value="LOW" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="moduleForm.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="排序号">
          <el-input-number v-model="moduleForm.sort_order" :min="0" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="moduleForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="moduleDialogVisible=false">取消</el-button>
        <el-button type="primary" :loading="moduleSaving" @click="saveModule">保存</el-button>
      </template>
    </el-dialog>

    <!-- 测试项对话框 -->
    <el-dialog v-model="testItemDialogVisible" :title="testItemEditing ? '编辑测试项' : '新增测试项'" width="600px">
      <el-form :model="testItemForm" :rules="testItemRules" ref="testItemFormRef" label-width="100px">
        <el-form-item label="模块" prop="module_id">
          <el-select v-model="testItemForm.module_id" :disabled="!!testItemEditing" style="width:100%">
            <el-option v-for="m in modules" :key="m.id" :label="m.module_name" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="测试编码" prop="test_code">
          <el-input v-model="testItemForm.test_code" :disabled="!!testItemEditing" />
        </el-form-item>
        <el-form-item label="测试名称" prop="test_name">
          <el-input v-model="testItemForm.test_name" />
        </el-form-item>
        <el-form-item label="必做">
          <el-switch v-model="testItemForm.is_required" />
        </el-form-item>
        <el-form-item label="测试级别">
          <el-select v-model="testItemForm.default_level" style="width:100%">
            <el-option label="必填" value="REQUIRED" />
            <el-option label="建议" value="RECOMMENDED" />
          </el-select>
        </el-form-item>
        <el-form-item label="风险等级">
          <el-select v-model="testItemForm.default_risk_level" style="width:100%">
            <el-option label="高" value="HIGH" />
            <el-option label="中" value="MEDIUM" />
            <el-option label="低" value="LOW" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="testItemForm.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="排序号">
          <el-input-number v-model="testItemForm.sort_order" :min="0" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="testItemForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="testItemDialogVisible=false">取消</el-button>
        <el-button type="primary" :loading="testItemSaving" @click="saveTestItem">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from "vue"
import { ElMessage } from "element-plus"
import { riskModuleApi, testItemApi } from "@/api"
import type { RiskModule, TestItem } from "@/api/types"

const loading = ref(false)
const modules = ref<RiskModule[]>([])
const moduleTestItems = ref<Record<number, TestItem[]>>({})

// ─── 模块相关 ────────────────────────────────────────────────
const moduleDialogVisible = ref(false)
const moduleEditing = ref<RiskModule | null>(null)
const moduleSaving = ref(false)
const moduleFormRef = ref()
const moduleForm = reactive({
  module_code: "", module_name: "", risk_level: "MEDIUM",
  description: "", sort_order: 0, is_active: true,
})
const moduleRules = {
  module_code: [{ required: true, message: "必填", trigger: "blur" }],
  module_name: [{ required: true, message: "必填", trigger: "blur" }],
}

function openModuleDialog(row?: RiskModule) {
  moduleEditing.value = row || null
  if (row) {
    Object.assign(moduleForm, {
      module_code: row.module_code, module_name: row.module_name,
      risk_level: row.risk_level, description: row.description || "",
      sort_order: row.sort_order, is_active: row.is_active,
    })
  } else {
    Object.assign(moduleForm, { module_code: "", module_name: "", risk_level: "MEDIUM", description: "", sort_order: 0, is_active: true })
  }
  moduleDialogVisible.value = true
}

async function saveModule() {
  const valid = await moduleFormRef.value?.validate().catch(() => false)
  if (!valid) return
  moduleSaving.value = true
  try {
    if (moduleEditing.value) {
      await riskModuleApi.update(moduleEditing.value.id, moduleForm)
    } else {
      await riskModuleApi.create(moduleForm)
    }
    ElMessage.success("保存成功")
    moduleDialogVisible.value = false
    loadModules()
  } finally { moduleSaving.value = false }
}

async function deleteModule(id: number) {
  await riskModuleApi.delete(id)
  ElMessage.success("删除成功")
  loadModules()
}

async function loadModules() {
  loading.value = true
  try {
    const r = await riskModuleApi.list({ page_size: 200 })
    modules.value = r.items
    // 预加载每个模块的测试项
    for (const m of modules.value) {
      loadTestItemsForModule(m.id)
    }
  } finally { loading.value = false }
}

// ─── 测试项相关 ──────────────────────────────────────────────
const testItemDialogVisible = ref(false)
const testItemEditing = ref<TestItem | null>(null)
const testItemSaving = ref(false)
const testItemFormRef = ref()
const testItemForm = reactive({
  module_id: null as number | null,
  test_code: "", test_name: "", is_required: false,
  default_level: "RECOMMENDED", default_risk_level: "MEDIUM",
  description: "", sort_order: 0, is_active: true,
})
const testItemRules = {
  module_id: [{ required: true, message: "必选", trigger: "change" }],
  test_code: [{ required: true, message: "必填", trigger: "blur" }],
  test_name: [{ required: true, message: "必填", trigger: "blur" }],
}

function openTestItemDialog(moduleId: number, item?: TestItem) {
  testItemEditing.value = item || null
  if (item) {
    Object.assign(testItemForm, {
      module_id: item.module_id, test_code: item.test_code, test_name: item.test_name,
      is_required: item.is_required, default_level: item.default_level,
      default_risk_level: item.default_risk_level, description: item.description || "",
      sort_order: item.sort_order, is_active: item.is_active,
    })
  } else {
    Object.assign(testItemForm, {
      module_id: moduleId, test_code: "", test_name: "", is_required: false,
      default_level: "RECOMMENDED", default_risk_level: "MEDIUM",
      description: "", sort_order: 0, is_active: true,
    })
  }
  testItemDialogVisible.value = true
}

async function saveTestItem() {
  const valid = await testItemFormRef.value?.validate().catch(() => false)
  if (!valid) return
  testItemSaving.value = true
  try {
    if (testItemEditing.value) {
      await testItemApi.update(testItemEditing.value.id, testItemForm)
    } else {
      await testItemApi.create(testItemForm)
    }
    ElMessage.success("保存成功")
    testItemDialogVisible.value = false
    if (testItemForm.module_id) {
      loadTestItemsForModule(testItemForm.module_id)
    }
  } finally { testItemSaving.value = false }
}

async function deleteTestItem(id: number, moduleId: number) {
  await testItemApi.delete(id)
  ElMessage.success("删除成功")
  loadTestItemsForModule(moduleId)
}

async function loadTestItemsForModule(moduleId: number) {
  // 直接筛选属于该模块的测试项
  const r = await testItemApi.list({ module_id: moduleId, page_size: 500 })
  moduleTestItems.value[moduleId] = r.items
}

onMounted(loadModules)
</script>

<style scoped>
:deep(.test-item-header) { background: #f0f0f0 !important; }
</style>
