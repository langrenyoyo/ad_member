<template>
  <div class="page-container">
    <div class="ls-card">
      <div class="toolbar">
        <el-date-picker
          v-model="runDate"
          type="date"
          placeholder="对账日期"
          value-format="YYYY-MM-DD"
          style="width: 160px"
        />
        <el-button type="primary" @click="handleRun" :loading="running">执行对账</el-button>
        <el-button @click="load">刷新列表</el-button>
      </div>
      <p class="hint">每日对比预估与已确认收益，GAP 超阈值标记为告警；同时释放 T+N 可提现余额。</p>

      <el-table :data="list" v-loading="loading" class="m-t-16">
        <el-table-column prop="date" label="日期" width="120" />
        <el-table-column prop="estimated_revenue" label="预估收益" width="110" />
        <el-table-column prop="confirmed_revenue" label="已确认" width="110" />
        <el-table-column prop="gap_amount" label="GAP 金额" width="100" />
        <el-table-column prop="gap_rate" label="GAP 率" width="90">
          <template #default="{ row }">{{ (row.gap_rate * 100).toFixed(2) }}%</template>
        </el-table-column>
        <el-table-column prop="kuaishou_revenue" label="快手侧" width="100" />
        <el-table-column prop="taku_revenue" label="Taku侧" width="100" />
        <el-table-column prop="transaction_count" label="事务数" width="80" />
        <el-table-column prop="confirmed_count" label="确认数" width="80" />
        <el-table-column prop="clawback_amount" label="扣回" width="80" />
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="reconcileStatusType(row.status)" size="small">
              {{ reconcileStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="170" />
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getReconcileDaily, runReconcile } from '@/api'
import { reconcileStatusLabel, reconcileStatusType } from '@/utils/statusLabels'

const loading = ref(false)
const running = ref(false)
const list = ref([])
const runDate = ref('')

async function load() {
  loading.value = true
  try {
    const res = await getReconcileDaily({ page: 1, limit: 30 })
    list.value = res.list || []
  } finally {
    loading.value = false
  }
}

async function handleRun() {
  running.value = true
  try {
    await runReconcile(runDate.value || '')
    ElMessage.success('对账完成')
    load()
  } finally {
    running.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
}

.hint {
  margin-top: 12px;
  color: #909399;
  font-size: 13px;
}

.m-t-16 {
  margin-top: 16px;
}
</style>
