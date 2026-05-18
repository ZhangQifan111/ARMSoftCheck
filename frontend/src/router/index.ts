import { createRouter, createWebHistory } from "vue-router"
import { useAuthStore } from "@/stores/auth"

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/login",
      name: "Login",
      component: () => import("@/views/auth/Login.vue"),
      meta: { guest: true },
    },
    {
      path: "/",
      component: () => import("@/views/home/Layout.vue"),
      meta: { requiresAuth: true },
      children: [
        { path: "", redirect: "/checklists" },
        {
          path: "checklists",
          name: "ChecklistList",
          component: () => import("@/views/checklist/List.vue"),
        },
        {
          path: "checklists/create",
          name: "ChecklistCreate",
          component: () => import("@/views/checklist/Edit.vue"),
        },
        {
          path: "checklists/:id/edit",
          name: "ChecklistEdit",
          component: () => import("@/views/checklist/Edit.vue"),
        },
        {
          path: "checklists/:id",
          name: "ChecklistDetail",
          component: () => import("@/views/checklist/Detail.vue"),
        },
        // 管理页
        {
          path: "admin/projects",
          name: "AdminProjects",
          component: () => import("@/views/admin/Projects.vue"),
          meta: { admin: true },
        },
        {
          path: "admin/risk-modules",
          name: "AdminRiskModules",
          component: () => import("@/views/admin/RiskModules.vue"),
          meta: { admin: true },
        },
        {
          path: "admin/test-items",
          name: "AdminTestItems",
          component: () => import("@/views/admin/TestItems.vue"),
          meta: { admin: true },
        },
        {
          path: "admin/maps",
          name: "AdminMaps",
          component: () => import("@/views/admin/Maps.vue"),
          meta: { admin: true },
        },
        {
          path: "admin/users",
          name: "AdminUsers",
          component: () => import("@/views/admin/Users.vue"),
          meta: { admin: true },
        },
        {
          path: "admin/logs",
          name: "AdminLogs",
          component: () => import("@/views/logs/Logs.vue"),
          meta: { admin: true },
        },
        {
          path: "guide",
          name: "Guide",
          component: () => import("@/views/Guide.vue"),
          meta: { requiresAuth: true },
        },
      ],
    },
  ],
})

router.beforeEach((to, _from, next) => {
  const auth = useAuthStore()

  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    next("/login")
  } else if (to.meta.guest && auth.isLoggedIn) {
    next("/")
  } else if (to.meta.admin && !auth.isAdmin) {
    next("/")
  } else {
    next()
  }
})

export default router
