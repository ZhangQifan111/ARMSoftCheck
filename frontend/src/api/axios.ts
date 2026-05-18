import axios from "axios"
import { ElMessage } from "element-plus"
import router from "@/router"

const request = axios.create({
  baseURL: "/api/v1",
  timeout: 30000,
})

// 请求拦截器：注入 token
request.interceptors.request.use((config) => {
  const token = localStorage.getItem("prrc_token")
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器
request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const status = error.response?.status
    const message = error.response?.data?.detail || error.message

    if (status === 401) {
      localStorage.removeItem("prrc_token")
      localStorage.removeItem("prrc_user")
      router.push("/login")
      ElMessage.error("登录已过期，请重新登录")
    } else if (status === 403) {
      ElMessage.error("权限不足: " + message)
    } else if (status === 400) {
      ElMessage.error(message)
    } else if (status >= 500) {
      ElMessage.error("服务器错误: " + message)
    } else {
      ElMessage.error(message || "请求失败")
    }

    return Promise.reject(error)
  }
)

export default request
