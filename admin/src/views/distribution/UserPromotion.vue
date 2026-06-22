<template>
  <div class="page-container">
    <div class="ls-card">
      <el-table :data="list" v-loading="loading">
        <el-table-column prop="uid" label="UID" width="120" />
        <el-table-column prop="nickname" label="昵称" />
        <el-table-column prop="agent_type" label="类型" width="90">
          <template #default="{ row }">{{ row.agent_type === 2 ? '团长' : '代理' }}</template>
        </el-table-column>
        <el-table-column prop="total_revenue" label="累计收益" width="120" />
        <el-table-column prop="today_revenue" label="今日收益" width="120" />
        <el-table-column prop="ad_count" label="广告次数" width="100" />
      </el-table>
      <el-pagination
        class="m-t-16"
        v-model:current-page="page"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="loadData"
      />
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { getMemberPromotion } from '@/api'

const loading = ref(false)
const list = ref([])
const total = ref(0)
const page = ref(1)

async function loadData() {
  loading.value = true
  try {
    const res = await getMemberPromotion({ page: page.value, limit: 20 })
    list.value = res.list || []
    total.value = res.total || 0
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.m-t-16 {
  margin-top: 16px;
}
</style>
