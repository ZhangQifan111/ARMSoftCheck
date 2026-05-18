import { defineStore } from "pinia"
import { ref, computed } from "vue"
import type { User } from "@/api/types"
import { authApi } from "@/api"

export const useAuthStore = defineStore("auth", () => {
  const token = ref<string | null>(localStorage.getItem("prrc_token"))
  const user = ref<User | null>(
    JSON.parse(localStorage.getItem("prrc_user") || "null")
  )

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === "ADMIN")
  const isReviewer = computed(() => user.value?.role === "REVIEWER")
  const isDeveloper = computed(() => user.value?.role === "DEVELOPER")
  const isTester = computed(() => user.value?.role === "TESTER")

  async function login(username: string, password: string) {
    const res: any = await authApi.login({ username, password })
    token.value = res.access_token
    user.value = res.user
    localStorage.setItem("prrc_token", res.access_token)
    localStorage.setItem("prrc_user", JSON.stringify(res.user))
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem("prrc_token")
    localStorage.removeItem("prrc_user")
  }

  async function fetchMe() {
    try {
      const res: any = await authApi.me()
      user.value = res
      localStorage.setItem("prrc_user", JSON.stringify(res))
    } catch {
      logout()
    }
  }

  return {
    token, user, isLoggedIn, isAdmin, isReviewer, isDeveloper, isTester,
    login, logout, fetchMe,
  }
})
