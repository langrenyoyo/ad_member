<template>
  <div class="page-container">
    <div class="ls-card">
      <div class="card-title">分销数据概览</div>
      <div class="stat-grid m-t-8" v-loading="loading">
        <div class="stat-item highlight">
          <div class="label">预估余额（含待确认）</div>
          <div class="value">{{ fmt(data.estimated_balance) }}</div>
        </div>
        <div class="stat-item">
          <div class="label">已确认余额</div>
          <div class="value">{{ fmt(data.confirmed_balance) }}</div>
        </div>
        <div class="stat-item highlight">
          <div class="label">可提现余额</div>
          <div class="value">{{ fmt(data.withdrawable_balance) }}</div>
        </div>
        <div class="stat-item">
          <div class="label">待确认余额</div>
          <div class="value">{{ fmt(data.pending_balance) }}</div>
        </div>
        <div class="stat-item">
          <div class="label">今日激励待确认</div>
          <div class="value">{{ data.today_tx_pending || 0 }}</div>
        </div>
        <div class="stat-item">
          <div class="label">今日激励已确认</div>
          <div class="value">{{ data.today_tx_confirmed || 0 }}</div>
        </div>
        <div class="stat-item">
          <div class="label">累计广告收益</div>
          <div class="value">{{ fmt(data.total_revenue) }}</div>
        </div>
        <div class="stat-item">
          <div class="label">本月广告收益</div>
          <div class="value">{{ fmt(data.month_revenue) }}</div>
        </div>
        <div class="stat-item">
          <div class="label">昨日广告收益</div>
          <div class="value">{{ fmt(data.yesterday_revenue) }}</div>
        </div>
        <div class="stat-item">
          <div class="label">今日广告收益</div>
          <div class="value">{{ fmt(data.today_revenue) }}</div>
        </div>
        <div class="stat-item">
          <div class="label">用户总数</div>
          <div class="value">{{ data.Member_count || 0 }}</div>
        </div>
        <div class="stat-item">
          <div class="label">昨日活跃用户</div>
          <div class="value">{{ data.yesterday_active || 0 }}</div>
        </div>
        <div class="stat-item">
          <div class="label">今日活跃用户</div>
          <div class="value link" @click="showActiveDialog">{{ data.today_active || 0 }}</div>
        </div>
      </div>
    </div>

    <el-dialog v-model="dialogVisible" title="今日活跃用户" width="720px">
      <el-table :data="activeMembers" size="small">
        <el-table-column prop="uid" label="UID" width="100" />
        <el-table-column prop="nickname" label="昵称" />
        <el-table-column prop="estimated_balance" label="预估" width="80" />
        <el-table-column prop="confirmed_balance" label="已确认" width="80" />
        <el-table-column prop="withdrawable_balance" label="可提现" width="80" />
        <el-table-column prop="pending_balance" label="待确认" width="80" />
        <el-table-column prop="ad_count" label="广告次数" width="90" />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { getOverview, getActiveMembers } from '@/api'

const loading = ref(false)
const data = ref({})
const dialogVisible = ref(false)
const activeMembers = ref([])

function fmt(n) {
  return Number(n || 0).toFixed(2)
}

async function loadData() {
  loading.value = true
  try {
    const res = await getOverview()
    data.value = res.data || res
  } finally {
    loading.value = false
  }
}

async function showActiveDialog() {
  const today = new Date().toISOString().split('T')[0]
  const res = await getActiveMembers(today)
  activeMembers.value = res.list || []
  dialogVisible.value = true
}

onMounted(loadData)
</script>

<style scoped>
.card-title {
  font-size: 16px;
  font-weight: 600;
}

.link {
  cursor: pointer;
  text-decoration: underline;
}

.highlight .value {
  color: var(--primary);
}
</style>
