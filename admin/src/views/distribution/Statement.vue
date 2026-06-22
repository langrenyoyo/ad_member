<template>
  <div class="page-container">
    <div class="ls-card">
      <el-form inline>
        <el-form-item label="日期">
          <el-date-picker v-model="date" type="date" value-format="YYYY-MM-DD" @change="loadReport" />
        </el-form-item>
      </el-form>
      <div class="stat-grid m-t-8" v-if="report">
        <div class="stat-item">
          <div class="label">当日收益</div>
          <div class="value">{{ report.total_revenue?.toFixed(2) }}</div>
        </div>
        <div class="stat-item">
          <div class="label">广告次数</div>
          <div class="value">{{ report.ad_count }}</div>
        </div>
        <div class="stat-item">
          <div class="label">活跃用户</div>
          <div class="value">{{ report.active_users }}</div>
        </div>
        <div class="stat-item">
          <div class="label">风控拦截</div>
          <div class="value">{{ report.risk_blocked }}</div>
        </div>
      </div>
    </div>

    <div class="ls-card">
      <div class="card-title">广告日志</div>
      <el-table :data="adLogs" v-loading="loading" class="m-t-8" size="small">
        <el-table-column prop="uid" label="UID" width="120" />
        <el-table-column prop="app_name" label="应用" />
        <el-table-column prop="placement" label="广告位" />
        <el-table-column prop="revenue" label="收益" width="80" />
        <el-table-column prop="action" label="动作" width="80">
          <template #default="{ row }">{{ adActionLabel(row.action) }}</template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="180" />
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { getDailyReport, getAdverLog } from '@/api'
import { adActionLabel } from '@/utils/statusLabels'

const date = ref(new Date().toISOString().split('T')[0])
const report = ref(null)
const adLogs = ref([])
const loading = ref(false)

async function loadReport() {
  const res = await getDailyReport({ date_str: date.value })
  report.value = res.data || res
}

async function loadAdLogs() {
  loading.value = true
  try {
    const res = await getAdverLog({ page: 1, limit: 50 })
    adLogs.value = res.list || []
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadReport()
  loadAdLogs()
})
</script>

<style scoped>
.card-title {
  font-size: 16px;
  font-weight: 600;
}

.m-t-8 {
  margin-top: 8px;
}
</style>
