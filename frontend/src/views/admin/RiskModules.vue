<template>
  <div>
    <div style="margin-bottom:16px;display:flex;justify-content:space-between">
      <h3>风险模块管理</h3>
      <el-button type="primary" @click="showDialog=true;editing=null;Object.assign(form,formDefault())">
        <el-icon><Plus /></el-icon> 新建模块
      </el-button>
    </div>
    <el-table :data="list" stripe v-loading="loading" row-key="id">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="module_code" label="代码" width="120" />
      <el-table-column prop="module_name" label="名称" />
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

    <el-dialog v-model="showDialog" :title="editing ? '编辑模块' : '新建模块'" width="550px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="模块代码" prop="module_code">
          <el-input v-model="form.module_code" :disabled="!!editing" />
        </el-form-item>
        <el-form-item label="模块名称" prop="module_name">
          <el-input v-model="form.module_name" />
        </el-form-item>
        <el-form-item label="风险等级" prop="risk_level">
          <el-select v-model="form.risk_level" style="width:100%">
            <el-option label="高风险" value="HIGH" />
            <el-option label="中风险" value="MEDIUM" />
            <el-option label="低风险" value="LOW" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="排序号">
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
import { riskModuleApi } from "@/api"
import type { RiskModule } from "@/api/types"

const loading = ref(false)
const list = ref<RiskModule[]>([])
const total = ref(0)
const page = ref(1)
const showDialog = ref(false)
const editing = ref<RiskModule | null>(null)
const saving = ref(false)
const formRef = ref()

function formDefault() { return { module_code: "", module_name: "", risk_level: "MEDIUM", description: "", sort_order: 0, is_active: true } }
const form = reactive(formDefault())
const rules = { module_code: [{ required: true, message: "必填", trigger: "blur" }], module_name: [{ required: true, message: "必填", trigger: "blur" }] }

onMounted(load)
async function load() { loading.value = true; try { const r = await riskModuleApi.list({ page: page.value, page_size: 20 }); list.value = r.items; total.value = r.total } finally { loading.value = false } }

function handleEdit(row: RiskModule) {
  editing.value = row
  Object.assign(form, { module_code: row.module_code, module_name: row.module_name, risk_level: row.risk_level, description: row.description || "", sort_order: row.sort_order, is_active: row.is_active })
  showDialog.value = true
}

async function handleSave() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    if (editing.value) await riskModuleApi.update(editing.value.id, form)
    else await riskModuleApi.create(form)
    ElMessage.success("保存成功")
    showDialog.value = false
    load()
  } finally { saving.value = false }
}

async function handleDelete(id: number) { await riskModuleApi.delete(id); ElMessage.success("删除成功"); load() }
</script>
