<template>
  <div>
    <div style="margin-bottom:16px;display:flex;justify-content:space-between">
      <h3>用户管理</h3>
      <el-button type="primary" @click="showDialog=true;editing=null;Object.assign(form,formDefault())">
        <el-icon><Plus /></el-icon> 新建用户
      </el-button>
    </div>
    <el-table :data="list" stripe v-loading="loading" row-key="id">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="username" label="用户名" width="150" />
      <el-table-column prop="real_name" label="姓名" />
      <el-table-column prop="email" label="邮箱" />
      <el-table-column prop="role" label="角色" width="100">
        <template #default="{ row }">
          <el-tag size="small">{{ roleLabel(row.role) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.status ? 'success' : 'info'" size="small">
            {{ row.status ? "正常" : "禁用" }}
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
    <el-pagination v-model:current-page="page" :total="total" :page-size="20"
      layout="total, prev, pager, next" style="margin-top:16px;justify-content:center" @current-change="load" />

    <el-dialog v-model="showDialog" :title="editing ? '编辑用户' : '新建用户'" width="550px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="!!editing" />
        </el-form-item>
        <el-form-item label="姓名" prop="real_name">
          <el-input v-model="form.real_name" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" style="width:100%">
            <el-option label="管理员" value="ADMIN" />
            <el-option label="开发" value="DEVELOPER" />
            <el-option label="评审" value="REVIEWER" />
            <el-option label="测试" value="TESTER" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="!editing" label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-form-item v-if="editing" label="重置密码">
          <el-input v-model="form.password" type="password" show-password placeholder="留空则不修改" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.status" />
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
import { userApi } from "@/api"
import type { User } from "@/api/types"
import dayjs from "dayjs"

const loading = ref(false)
const list = ref<User[]>([])
const total = ref(0)
const page = ref(1)
const showDialog = ref(false)
const editing = ref<User | null>(null)
const saving = ref(false)
const formRef = ref()

function formDefault() { return { username: "", real_name: "", email: "", role: "DEVELOPER" as any, password: "", status: true } }
const form = reactive(formDefault())
const rules = { username: [{ required: true, message: "必填", trigger: "blur" }], real_name: [{ required: true, message: "必填", trigger: "blur" }], email: [{ required: true, type: "email", message: "请输入有效邮箱", trigger: "blur" }], password: [{ required: true, min: 6, message: "至少6位", trigger: "blur" }] }

onMounted(load)
async function load() { loading.value = true; try { const r = await userApi.list({ page: page.value, page_size: 20 }); list.value = r.items; total.value = r.total } finally { loading.value = false } }

function handleEdit(row: User) {
  editing.value = row
  Object.assign(form, { username: row.username, real_name: row.real_name, email: row.email, role: row.role, password: "", status: row.status })
  // password 不回显
  showDialog.value = true
}

async function handleSave() {
  const baseValid = await formRef.value?.validate().catch(() => false)
  if (!baseValid) return
  saving.value = true
  try {
    const payload: any = { real_name: form.real_name, email: form.email, role: form.role, status: form.status }
    if (form.password) payload.password = form.password
    if (editing.value) await userApi.update(editing.value.id, payload)
    else await userApi.create({ ...form })
    ElMessage.success("保存成功")
    showDialog.value = false
    load()
  } finally { saving.value = false }
}

async function handleDelete(id: number) { await userApi.delete(id); ElMessage.success("删除成功"); load() }

function roleLabel(r: string) { return { ADMIN: "管理员", DEVELOPER: "开发", REVIEWER: "评审", TESTER: "测试" }[r] || r }
function formatDate(d: string) { return d ? dayjs(d).format("YYYY-MM-DD") : "-" }
</script>
