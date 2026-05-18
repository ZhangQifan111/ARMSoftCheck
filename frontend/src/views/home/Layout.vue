<template>
  <el-container class="layout-container">
    <!-- 左侧菜单 -->
    <el-aside :width="isCollapse ? '64px' : '220px'" class="aside">
      <div class="logo-area">
        <span v-if="!isCollapse" style="font-size:18px;font-weight:700;color:#fff">PRRC</span>
        <span v-else style="font-size:18px;font-weight:700;color:#fff">P</span>
      </div>
      <el-menu
        :default-active="currentRoute"
        :collapse="isCollapse"
        router
        background-color="#1a1a2e"
        text-color="#a0a0b0"
        active-text-color="#409EFF"
        class="side-menu"
      >
        <el-menu-item index="/checklists">
          <el-icon><Document /></el-icon>
          <span>自检单</span>
        </el-menu-item>

        <el-menu-item index="/guide">
          <el-icon><Reading /></el-icon>
          <span>使用手册</span>
        </el-menu-item>

        <!-- 管理员菜单 -->
        <el-sub-menu v-if="auth.isAdmin" index="admin">
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>系统管理</span>
          </template>
          <el-menu-item index="/admin/projects">项目管理</el-menu-item>
          <el-menu-item index="/admin/risk-modules">风险模块</el-menu-item>
          <el-menu-item index="/admin/test-items">测试项</el-menu-item>
          <el-menu-item index="/admin/maps">模块-测试映射</el-menu-item>
          <el-menu-item index="/admin/users">用户管理</el-menu-item>
          <el-menu-item index="/admin/logs">操作日志</el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>

    <el-container>
      <!-- 顶部导航 -->
      <el-header class="header">
        <div class="header-left">
          <el-icon class="collapse-btn" @click="isCollapse = !isCollapse">
            <Expand v-if="isCollapse" /><Fold v-else />
          </el-icon>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ pageTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-icon><User /></el-icon>
              {{ auth.user?.real_name }}
              <el-tag size="small" style="margin-left:4px">{{ roleLabel }}</el-tag>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 主内容 -->
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed } from "vue"
import { useRoute, useRouter } from "vue-router"
import { useAuthStore } from "@/stores/auth"
import { ElMessage } from "element-plus"

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const isCollapse = ref(false)

const currentRoute = computed(() => route.path)
const pageTitle = computed(() => {
  const map: Record<string, string> = {
    "/checklists": "自检单列表",
    "/checklists/create": "新建自检单",
    "/admin/projects": "项目管理",
    "/admin/risk-modules": "风险模块管理",
    "/admin/test-items": "测试项管理",
    "/admin/maps": "模块-测试映射",
    "/admin/users": "用户管理",
    "/admin/logs": "操作日志",
  }
  if (route.path.startsWith("/checklists/") && route.path.endsWith("/edit")) return "编辑自检单"
  if (route.path.match(/^\/checklists\/\d+$/)) return "自检单详情"
  return map[route.path] || ""
})

const roleLabel = computed(() => {
  const m: Record<string, string> = {
    ADMIN: "管理员", DEVELOPER: "开发", REVIEWER: "评审", TESTER: "测试"
  }
  return m[auth.user?.role || ""] || ""
})

function handleCommand(cmd: string) {
  if (cmd === "logout") {
    auth.logout()
    ElMessage.success("已退出登录")
    router.push("/login")
  }
}
</script>

<style scoped>
.layout-container { height: 100vh; }
.aside {
  background: #1a1a2e;
  transition: width 0.3s;
  overflow-x: hidden;
  overflow-y: auto;
}
.logo-area {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #16213e;
  border-bottom: 1px solid #2a2a4a;
}
.side-menu {
  border-right: none;
}
.header {
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  border-bottom: 1px solid #e8e8e8;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.header-left { display: flex; align-items: center; gap: 12px; }
.collapse-btn { font-size: 18px; cursor: pointer; color: #666; }
.header-right { display: flex; align-items: center; gap: 8px; }
.user-info {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
}
.user-info:hover { background: #f5f5f5; }
.main-content { padding: 20px; overflow-y: auto; }
</style>
