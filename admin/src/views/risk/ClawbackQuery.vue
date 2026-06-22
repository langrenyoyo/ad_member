<template>
  <div class="page-container">
    <div class="ls-card">
      <div class="toolbar">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
          style="width: 260px"
        />
        <el-input v-model="query.uid" placeholder="UID" clearable style="width: 130px" />
        <el-button type="primary" @click="loadAll">查询</el-button>
      </div>

      <div class="stat-grid m-t-16" v-loading="summaryLoading">
        <div class="stat-item">
          <div class="label">涉及用户数</div>
          <div class="value">{{ summary.affected_users || 0 }}</div>
        </div>
        <div class="stat-item highlight-danger">
          <div class="label">核减总金额</div>
          <div class="value danger">{{ fmt(summary.total_deduction) }}</div>
        </div>
        <div class="stat-item">
          <div class="label">已扣回</div>
          <div class="value">{{ fmt(summary.clawback_amount) }}</div>
          <div class="sub">{{ summary.clawback_count || 0 }} 笔</div>
        </div>
        <div class="stat-item">
          <div class="label">风控拒绝</div>
          <div class="value">{{ fmt(summary.rejected_amount) }}</div>
          <div class="sub">{{ summary.rejected_count || 0 }} 笔</div>
        </div>
        <div class="stat-item">
          <div class="label">双回调未齐</div>
          <div class="value">{{ fmt(summary.pending_lost_amount) }}</div>
          <div class="sub">{{ summary.pending_lost_count || 0 }} 笔</div>
        </div>
      </div>
    </div>

    <div class="ls-card">
      <div class="card-title">被核减用户列表</div>
      <el-table :data="list" v-loading="loading" class="m-t-16">
        <el-table-column prop="uid" label="UID" width="100" />
        <el-table-column prop="nickname" label="昵称" width="110" />
        <el-table-column prop="mobile" label="手机号" width="120" />
        <el-table-column prop="total_deduction" label="核减合计" width="100">
          <template #default="{ row }">
            <span class="danger-text">{{ fmt(row.total_deduction) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="clawback_amount" label="已扣回" width="90" />
        <el-table-column prop="rejected_amount" label="风控拒绝" width="90" />
        <el-table-column prop="pending_lost_amount" label="回调未齐" width="90" />
        <el-table-column prop="deduction_rate" label="核减率" width="90">
          <template #default="{ row }">{{ (row.deduction_rate * 100).toFixed(1) }}%</template>
        </el-table-column>
        <el-table-column prop="estimated_balance" label="当前预估" width="90" />
        <el-table-column prop="confirmed_balance" label="已确认" width="90" />
        <el-table-column prop="last_at" label="最近事务" width="170" />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="showDetail(row)">明细</el-button>
          </template>
        </el-table-column>
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

    <el-dialog v-model="detailVisible" :title="`核减明细 - ${detailUid}`" width="780px">
      <el-table :data="detailList" size="small" v-loading="detailLoading">
        <el-table-column prop="trans_id" label="事务ID" min-width="140" show-overflow-tooltip />
        <el-table-column prop="deduction_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="typeTag(row.deduction_type)" size="small">
              {{ typeLabel(row.deduction_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="user_reward" label="金额" width="80" />
        <el-table-column prop="reason" label="原因" min-width="160" show-overflow-tooltip />
        <el-table-column label="双回调" width="100">
          <template #default="{ row }">
            <el-tag :type="row.kuaishou_verified ? 'success' : 'info'" size="small">快手</el-tag>
            <el-tag :type="row.taku_verified ? 'success' : 'info'" size="small" class="m-l-4">Taku</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="device_id" label="设备" width="100" show-overflow-tooltip />
        <el-table-column prop="created_at" label="时间" width="165" />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { getClawbackSummary, getClawbackUsers, getClawbackDetail } from '@/api'
import { deductionTypeLabel, deductionTypeTag } from '@/utils/statusLabels'

const loading = ref(false)
const summaryLoading = ref(false)
const detailLoading = ref(false)
const list = ref([])
const total = ref(0)
const summary = ref({})
const dateRange = ref([])
const query = reactive({ page: 1, limit: 20, uid: '' })

const detailVisible = ref(false)
const detailUid = ref('')
const detailList = ref([])

function fmt(n) {
  return Number(n || 0).toFixed(2)
}

function dateParams() {
  const start = dateRange.value?.[0] || ''
  const end = dateRange.value?.[1] || ''
  return { date_start: start, date_end: end }
}

function typeLabel(t) {
  return deductionTypeLabel(t)
}

function typeTag(t) {
  return deductionTypeTag(t)
}

async function loadSummary() {
  summaryLoading.value = true
  try {
    const res = await getClawbackSummary(dateParams())
    summary.value = res.data || res
  } finally {
    summaryLoading.value = false
  }
}

async function loadList() {
  loading.value = true
  try {
    const res = await getClawbackUsers({
      page: query.page,
      limit: query.limit,
      uid: query.uid,
      ...dateParams(),
    })
    list.value = res.list || []
    total.value = res.total || 0
  } finally {
    loading.value = false
  }
}

function loadAll() {
  query.page = 1
  loadSummary()
  loadList()
}

function onPage(p) {
  query.page = p
  loadList()
}

async function showDetail(row) {
  detailUid.value = row.uid
  detailVisible.value = true
  detailLoading.value = true
  try {
    const res = await getClawbackDetail({
      uid: row.uid,
      page: 1,
      limit: 50,
      ...dateParams(),
    })
    detailList.value = res.list || []
  } finally {
    detailLoading.value = false
  }
}

onMounted(() => {
  const end = new Date()
  const start = new Date()
  start.setDate(start.getDate() - 30)
  dateRange.value = [
    start.toISOString().split('T')[0],
    end.toISOString().split('T')[0],
  ]
  loadAll()
})
</script>

<style scoped>
.toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
}

.m-t-16 {
  margin-top: 16px;
}

.m-l-4 {
  margin-left: 4px;
}

.stat-item .sub {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.highlight-danger .value.danger,
.danger-text {
  color: #f56c6c;
}

.highlight-danger .value {
  color: #f56c6c;
}
</style>
