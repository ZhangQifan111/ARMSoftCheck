<template>
  <div>
    <div style="margin-bottom:16px;display:flex;justify-content:space-between">
      <h3>模块-测试项映射管理</h3>
      <el-button type="primary" @click="showDialog=true;editing=null;Object.assign(form,formDefault())">
        <el-icon><Plus /></el-icon> 新建映射
      </el-button>
    </div>

    <!-- 筛选 -->
    <el-card shadow="never" style="margin-bottom:12px">
      <el-form inline :model="filter" @submit.prevent="load">
        <el-form-item label="模块">
          <el-select v-model="filter.module_code" clearable placeholder="全部" style="width:160px">
            <el-option v-for="m in modules" :key="m.module_code" :label="m.module_name" :value="m.module_code" />
          </el-select>
        </el-form-item>
        <el-form-item label="测试项">
          <el-select v-model="filter.test_code" clearable placeholder="全部" style="width:160px">
            <el-option v-for="t in testItems" :key="t.test_code" :label="t.test_name" :value="t.test_code" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="load">查询</el-button>
          <el-button @click="filter.module_code='';filter.test_code='';load()">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-table :data="list" stripe v-loading="loading" row-key="id">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="module_code" label="模块" width="180">
        <template #default="{ row }">
          {{ getModuleName(row.module_code) }}
        </template>
      </el-table-column>
      <el-table-column prop="test_code" label="测试项" min-width="200">
        <template #default="{ row }">
          {{ getTestItemName(row.test_code) }}
        </template>
      </el-table-column>
      <el-table-column prop="is_required" label="是否必做" width="90">
        <template #default="{ row }">
          <el-tag :type="row.is_required ? 'danger' : 'default'" size="small">
            {{ row.is_required ? "必做" : "建议" }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="remark" label="备注" show-overflow-tooltip />
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
          <el-button type="primary" link size="small" @click="handleEdit(row)">编辑</el-button>
          <el-popconfirm title="确认删除？" @confirm="handleDelete(row.id)">
            <template #reference>
              <el-button type="danger" link size="small">删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination v-model:current-page="page" :total="total" :page-size="20"
      layout="total, prev, pager, next" style="margin-top:16px;justify-content:center" @current-change="load" />

    <el-dialog v-model="showDialog" :title="editing ? '编辑映射' : '新建映射'" width="550px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="模块" prop="module_code">
          <el-select v-model="form.module_code" :disabled="!!editing" style="width:100%">
            <el-option v-for="m in modules" :key="m.module_code" :label="`${m.module_name}(${m.module_code})`" :value="m.module_code" />
          </el-select>
        </el-form-item>
        <el-form-item label="测试项" prop="test_code">
          <el-select v-model="form.test_code" :disabled="!!editing" style="width:100%">
            <el-option v-for="t in testItems" :key="t.test_code" :label="`${t.test_name}(${t.test_code})`" :value="t.test_code" />
          </el-select>
        </el-form-item>
        <el-form-item label="是否必做">
          <el-switch v-model="form.is_required" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog=false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from "vue"
import { ElMessage } from "element-plus"
import { mapApi, riskModuleApi, testItemApi } from "@/api"
import type { ModuleTestMap, RiskModule, TestItem } from "@/api/types"

const loading = ref(false)
const list = ref<ModuleTestMap[]>([])
const total = ref(0)
const page = ref(1)
const modules = ref<RiskModule[]>([])
const testItems = ref<TestItem[]>([])
const showDialog = ref(false)
const editing = ref<ModuleTestMap | null>(null)
const saving = ref(false)
const formRef = ref()

const filter = reactive({ module_code: "", test_code: "" })

function formDefault() { return { module_code: "", test_code: "", is_required: false, sort_order: 0, remark: "", is_active: true } }
const form = reactive(formDefault())
const rules = { module_code: [{ required: true, message: "必填" }], test_code: [{ required: true, message: "必填" }] }

onMounted(async () => {
  const [mr, tr] = await Promise.all([
    riskModuleApi.list({ page_size: 200 }),
    testItemApi.list({ page_size: 200 }),
  ])
  modules.value = mr.items
  testItems.value = tr.items
  load()
})

async function load() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: 20 }
    if (filter.module_code) params.module_code = filter.module_code
    if (filter.test_code) params.test_code = filter.test_code
    const r = await mapApi.list(params)
    list.value = r.items
    total.value = r.total
  } finally { loading.value = false }
}

function getModuleName(code: string) { return modules.value.find(m => m.module_code === code)?.module_name || code }
function getTestItemName(code: string) { return testItems.value.find(t => t.test_code === code)?.test_name || code }

function handleEdit(row: ModuleTestMap) {
  editing.value = row
  Object.assign(form, { module_code: row.module_code, test_code: row.test_code, is_required: row.is_required, sort_order: row.sort_order, remark: row.remark || "", is_active: row.is_active })
  showDialog.value = true
}

async function handleSave() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    if (editing.value) await mapApi.update(editing.value.id, form)
    else await mapApi.create(form)
    ElMessage.success("保存成功")
    showDialog.value = false
    load()
  } finally { saving.value = false }
}

async function handleDelete(id: number) { await mapApi.delete(id); ElMessage.success("删除成功"); load() }
</script>
