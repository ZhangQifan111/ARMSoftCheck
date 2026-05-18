<template>
  <div>
    <h3 style="margin-bottom:16px">操作日志</h3>
    <el-card shadow="never" style="margin-bottom:12px">
      <el-form inline :model="query" @submit.prevent="load">
        <el-form-item label="业务类型">
          <el-select v-model="query.business_type" clearable style="width:160px">
            <el-option v-for="t in businessTypes" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="操作">
          <el-input v-model="query.action" placeholder="操作关键词" clearable style="width:140px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="load">查询</el-button>
          <el-button @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    <el-table :data="list" stripe v-loading="loading" row-key="id">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="operator_name" label="操作人" width="100" />
      <el-table-column prop="business_type" label="业务类型" width="140" />
      <el-table-column prop="action" label="动作" width="100">
        <template #default="{ row }">
          <el-tag size="small">{{ row.action }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="business_no" label="关联编号" width="170" />
      <el-table-column prop="detail" label="详情" min-width="300" show-overflow-tooltip />
      <el-table-column prop="ip_address" label="IP" width="130" />
      <el-table-column prop="created_at" label="时间" width="160">
        <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
      </el-table-column>
    </el-table>
    <el-pagination
      v-model:current-page="query.page"
      v-model:page-size="query.page_size"
      :total="total"
      :page-sizes="[20, 50, 100]"
      layout="total, sizes, prev, pager, next"
      style="margin-top:16px;justify-content:center"
      @size-change="load"
      @current-change="load"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from "vue"
import { logApi } from "@/api"
import type { OperationLog } from "@/api/types"
import dayjs from "dayjs"

const loading = ref(false)
const list = ref<OperationLog[]>([])
const total = ref(0)
const businessTypes = ["USER", "PROJECT", "RISK_MODULE", "TEST_ITEM", "MODULE_TEST_MAP", "CHECKLIST"]

const query = reactive({
  page: 1,
  page_size: 20,
  business_type: "",
  action: "",
})

onMounted(load)

async function load() {
  loading.value = true
  try {
    const res = await logApi.list(query)
    list.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function resetQuery() {
  query.business_type = ""
  query.action = ""
  query.page = 1
  load()
}

function formatDate(d: string) {
  return d ? dayjs(d).format("YYYY-MM-DD HH:mm:ss") : "-"
}
</script>
