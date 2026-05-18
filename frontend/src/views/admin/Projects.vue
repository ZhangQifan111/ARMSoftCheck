<template>
  <div>
    <div style="margin-bottom:16px;display:flex;justify-content:space-between">
      <h3>项目管理</h3>
      <el-button type="primary" @click="showDialog = true; editing = null">
        <el-icon><Plus /></el-icon> 新建项目
      </el-button>
    </div>
    <el-table :data="list" stripe v-loading="loading" row-key="id">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="project_name" label="项目名称" />
      <el-table-column prop="product_model" label="产品型号" />
      <el-table-column prop="is_active" label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
            {{ row.is_active ? "启用" : "禁用" }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="160">
        <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
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

    <el-pagination
      v-model:current-page="page" :total="total"
      :page-size="20" layout="total, prev, pager, next"
      style="margin-top:16px;justify-content:center"
      @current-change="load"
    />

    <!-- 新建/编辑对话框 -->
    <el-dialog v-model="showDialog" :title="editing ? '编辑项目' : '新建项目'" width="500px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="项目名称" prop="project_name">
          <el-input v-model="form.project_name" />
        </el-form-item>
        <el-form-item label="产品型号">
          <el-input v-model="form.product_model" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from "vue"
import { ElMessage } from "element-plus"
import { projectApi } from "@/api"
import type { Project } from "@/api/types"
import dayjs from "dayjs"

const loading = ref(false)
const list = ref<Project[]>([])
const total = ref(0)
const page = ref(1)
const showDialog = ref(false)
const editing = ref<Project | null>(null)
const saving = ref(false)
const formRef = ref()

const form = reactive({ project_name: "", product_model: "", is_active: true })
const rules = { project_name: [{ required: true, message: "必填", trigger: "blur" }] }

onMounted(load)

async function load() {
  loading.value = true
  try {
    const res = await projectApi.list({ page: page.value, page_size: 20 })
    list.value = res.items
    total.value = res.total
  } finally { loading.value = false }
}

function handleEdit(row: Project) {
  editing.value = row
  Object.assign(form, { project_name: row.project_name, product_model: row.product_model || "", is_active: row.is_active })
  showDialog.value = true
}

async function handleSave() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    if (editing.value) {
      await projectApi.update(editing.value.id, form)
    } else {
      await projectApi.create(form)
    }
    ElMessage.success("保存成功")
    showDialog.value = false
    load()
  } finally { saving.value = false }
}

async function handleDelete(id: number) {
  await projectApi.delete(id)
  ElMessage.success("删除成功")
  load()
}

function formatDate(d: string) {
  return d ? dayjs(d).format("YYYY-MM-DD") : "-"
}
</script>
