<template>
  <div class="page-container">
    <div class="ls-card">
      <div class="toolbar">
        <el-button type="primary" @click="sync">同步广告位</el-button>
        <el-button @click="load">刷新</el-button>
      </div>
      <el-table :data="placements" class="m-t-16" v-loading="loading">
        <el-table-column prop="placement_id" label="广告位 ID" min-width="180" show-overflow-tooltip />
        <el-table-column prop="placement_name" label="广告位名称" min-width="160" />
        <el-table-column prop="app_id" label="App ID" min-width="150" show-overflow-tooltip />
        <el-table-column prop="ad_format" label="广告类型" width="130" />
        <el-table-column prop="platform" label="平台" width="100" />
        <el-table-column label="状态" width="100"><template #default="{ row }"><el-tag :type="row.status === 'active' ? 'success' : 'info'">{{ row.status }}</el-tag></template></el-table-column>
        <el-table-column prop="synced_at" label="同步时间" width="180" />
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getTakuPlacements, syncTakuPlacements } from '@/api'

const placements = ref([])
const loading = ref(false)

async function loadApps() {
  const res = await getTakuApps()
  apps.value = res.list || res.data?.list || []
}
async function load() {
  loading.value = true
  try {
    const res = await getTakuPlacements()
    placements.value = res.list || res.data?.list || []
  } finally { loading.value = false }
}
async function sync() {
  const res = await syncTakuPlacements({})
  if (res.code && res.code !== 0) throw new Error(res.msg || '同步失败')
  ElMessage.success(`已同步 ${res.count ?? res.data?.count ?? 0} 个广告位`)
  await load()
}
onMounted(load)
</script>

<style scoped>
.toolbar { display: flex; gap: 12px; align-items: center; }
.m-t-16 { margin-top: 16px; }
</style>
