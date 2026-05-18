<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <h2>评审前风险自检系统</h2>
        <p style="color:#909399;font-size:13px">PRRC - Pre-Review Risk Checklist</p>
      </template>
      <el-form :model="form" :rules="rules" ref="formRef" label-width="0">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名" prefix-icon="User" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="密码"
            prefix-icon="Lock" show-password @keyup.enter="handleLogin" />
        </el-form-item>
        <el-button type="primary" :loading="loading" style="width:100%" @click="handleLogin">
          登 录
        </el-button>
      </el-form>
      <el-divider />
      <div style="font-size:12px;color:#999">
        演示账号：<br />
        admin / Admin@123 (管理员)<br />
        dev1 / Dev@123 (开发)<br />
        review1 / Review@123 (评审)
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue"
import { useRouter } from "vue-router"
import { ElMessage } from "element-plus"
import { useAuthStore } from "@/stores/auth"

const router = useRouter()
const auth = useAuthStore()
const formRef = ref()
const loading = ref(false)

const form = ref({ username: "", password: "" })
const rules = {
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  password: [{ required: true, message: "请输入密码", trigger: "blur" }],
}

async function handleLogin() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await auth.login(form.value.username, form.value.password)
    ElMessage.success("登录成功")
    router.push("/")
  } catch {
    // error handled by axios interceptor
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.login-card {
  width: 400px;
}
</style>
