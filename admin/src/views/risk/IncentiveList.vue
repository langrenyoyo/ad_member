<template>
  <div class="page-container">
    <div class="ls-card">
      <div class="toolbar">
        <el-input v-model="query.uid" placeholder="UID" clearable style="width: 140px" />
        <el-select v-model="query.status" placeholder="状态" clearable style="width: 140px">
          <el-option label="待确认" value="pending" />
          <el-option label="已确认" value="confirmed" />
          <el-option label="已扣回" value="clawback" />
          <el-option label="已拒绝" value="rejected" />
        </el-select>
        <el-button type="primary" @click="load">查询</el-button>
      </div>

      <el-table :data="list" v-loading="loading" class="m-t-16">
        <el-table-column prop="trans_id" label="事务ID" min-width="160" show-overflow-tooltip />
        <el-table-column prop="uid" label="UID" width="100" />
        <el-table-column prop="user_reward" label="用户奖励" width="90" />
        <el-table-column prop="revenue" label="平台收益" width="90" />
        <el-table-column label="双回调" width="120">
          <template #default="{ row }">
            <el-tag :type="row.kuaishou_verified ? 'success' : 'info'" size="small">快手</el-tag>
            <el-tag :type="row.taku_verified ? 'success' : 'info'" size="small" class="m-l-4">Taku</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="incentiveStatusType(row.status)" size="small">
              {{ incentiveStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="risk_score" label="风险分" width="80" />
        <el-table-column prop="device_id" label="设备" min-width="100" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column prop="confirmed_at" label="确认时间" width="170" />
      </el-table>

      <el-pagination
        class="m-t-16"
        layout="total, prev, pager, next"
        :total="total"
        :page-size="query.limit"
        :current-page="query.page"
        @current-change="onPage"
      />
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { getIncentiveTransactions } from '@/api'
import { incentiveStatusLabel, incentiveStatusType } from '@/utils/statusLabels'

const loading = ref(false)
const list = ref([])
const total = ref(0)
const query = reactive({ page: 1, limit: 20, uid: '', status: '' })

async function load() {
  loading.value = true
  try {
    const res = await getIncentiveTransactions({ ...query })
    list.value = res.list || []
    total.value = res.total || 0
  } finally {
    loading.value = false
  }
}

function onPage(p) {
  query.page = p
  load()
}

onMounted(load)
</script>

<style scoped>
.toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
}

.m-t-16 {
  margin-top: 16px;
}

.m-l-4 {
  margin-left: 4px;
}
</style>
