<template>
  <div class="page-container user-center">
    <!-- 统计概览 -->
    <div class="stat-grid" v-loading="statsLoading">
      <div class="stat-item" @click="resetFilters">
        <div class="label">总用户</div>
        <div class="value">{{ stats.total || 0 }}</div>
      </div>
      <div class="stat-item">
        <div class="label">今日活跃</div>
        <div class="value">{{ stats.today_active || 0 }}</div>
      </div>
      <div class="stat-item clickable" @click="filterPromoter">
        <div class="label">代理/团长</div>
        <div class="value">{{ stats.promoters || 0 }}</div>
      </div>
      <div class="stat-item clickable" @click="filterAbnormal">
        <div class="label">异常账号</div>
        <div class="value warn">{{ (stats.frozen || 0) + (stats.black || 0) }}</div>
        <div class="sub">冻结 {{ stats.frozen || 0 }} · 拉黑 {{ stats.black || 0 }}</div>
      </div>
      <div class="stat-item">
        <div class="label">全站待确认</div>
        <div class="value">{{ fmt(stats.pending_total) }}</div>
      </div>
      <div class="stat-item">
        <div class="label">全站可提现</div>
        <div class="value primary">{{ fmt(stats.withdrawable_total) }}</div>
      </div>
    </div>

  <div class="ls-card m-t-16">
      <div class="filter-bar">
        <el-input
          v-model="filters.keyword"
          placeholder="UID / 昵称 / 手机 / 设备唯一值"
          clearable
          style="width: 220px"
          @keyup.enter="search"
        />
        <el-select v-model="filters.role" placeholder="角色" clearable style="width: 120px">
          <el-option label="全部角色" value="" />
          <el-option label="普通用户" value="0" />
          <el-option label="代理" value="1" />
          <el-option label="团长" value="2" />
          <el-option label="全部推广员" value="promoter" />
        </el-select>
        <el-select v-model="filters.status" placeholder="账号状态" clearable style="width: 120px">
          <el-option label="全部状态" :value="null" />
          <el-option label="正常" :value="1" />
          <el-option label="冻结" :value="0" />
        </el-select>
        <el-select v-model="filters.is_black" placeholder="拉黑" clearable style="width: 110px">
          <el-option label="全部" :value="null" />
          <el-option label="已拉黑" :value="1" />
          <el-option label="未拉黑" :value="0" />
        </el-select>
        <el-select v-model="filters.sort" style="width: 130px">
          <el-option label="最近活跃" value="last_active" />
          <el-option label="可提现最高" value="withdrawable_balance" />
          <el-option label="待确认最高" value="pending_balance" />
          <el-option label="今日收益" value="today_revenue" />
          <el-option label="累计收益" value="total_revenue" />
        </el-select>
        <el-button type="primary" @click="search">查询</el-button>
        <el-button @click="resetFilters">重置</el-button>
      </div>

      <el-table :data="list" v-loading="loading" class="m-t-16" row-key="uid" @row-click="openDetail">
        <el-table-column prop="uid" label="UID" width="108" fixed />
        <el-table-column label="用户" min-width="140">
          <template #default="{ row }">
            <div class="cell-user">
              <span class="name">{{ row.nickname || '—' }}</span>
              <span class="mobile">{{ row.mobile || '无手机号' }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="角色/状态" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="roleTag(row.agent_type)">{{ roleLabel(row.agent_type) }}</el-tag>
            <el-tag v-if="row.is_black" size="small" type="danger" class="m-l-4">拉黑</el-tag>
            <el-tag v-else-if="row.status === 0" size="small" type="warning" class="m-l-4">冻结</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="收益(元)" width="200">
          <template #default="{ row }">
            <div class="money-cell">
              <span class="withdraw">可提现 <b>{{ fmt(row.withdrawable_balance) }}</b></span>
              <span class="muted">待确认 {{ fmt(row.pending_balance) }} · 今日 {{ fmt(row.today_revenue) }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="设备" min-width="150">
          <template #default="{ row }">
            <div class="device-cell">
              <span>{{ row.device_model || '—' }}</span>
              <span class="muted">{{ row.device_unique_id ? shortId(row.device_unique_id) : '无唯一值' }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="ad_count" label="广告次" width="72" align="center" />
        <el-table-column prop="last_active" label="最后活跃" width="165" />
        <el-table-column label="操作" width="88" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click.stop="openDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        class="m-t-16"
        v-model:current-page="page"
        v-model:page-size="limit"
        :total="total"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        @current-change="loadList"
        @size-change="onSizeChange"
      />
    </div>

    <UserDetailDrawer
      :visible="detailVisible"
      :uid="detailUid"
      @close="detailVisible = false"
      @changed="onDetailChanged"
    />
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import UserDetailDrawer from '@/components/UserDetailDrawer.vue'
import { getMemberList, getMemberStats } from '@/api'

const statsLoading = ref(false)
const loading = ref(false)
const stats = ref({})
const list = ref([])
const total = ref(0)
const page = ref(1)
const limit = ref(20)

const filters = reactive({
  keyword: '',
  role: '',
  status: null,
  is_black: null,
  abnormal: null,
  sort: 'last_active',
})

const detailVisible = ref(false)
const detailUid = ref('')

function fmt(n) {
  return Number(n || 0).toFixed(2)
}

function roleLabel(t) {
  return t === 2 ? '团长' : t === 1 ? '代理' : '普通'
}

function roleTag(t) {
  return t === 2 ? 'danger' : t === 1 ? 'warning' : 'info'
}

function shortId(id) {
  if (!id) return '—'
  return id.length > 16 ? `${id.slice(0, 8)}…${id.slice(-6)}` : id
}

function buildParams() {
  const p = {
    page: page.value,
    limit: limit.value,
    sort: filters.sort,
  }
  if (filters.keyword) p.keyword = filters.keyword
  if (filters.role) p.agent = filters.role
  if (filters.status !== null) p.status = filters.status
  if (filters.is_black !== null) p.is_black = filters.is_black
  if (filters.abnormal) p.abnormal = 1
  return p
}

async function loadStats() {
  statsLoading.value = true
  try {
    const res = await getMemberStats()
    stats.value = res.data || res
  } finally {
    statsLoading.value = false
  }
}

async function loadList() {
  loading.value = true
  try {
    const res = await getMemberList(buildParams())
    list.value = res.list || []
    total.value = res.total || 0
  } finally {
    loading.value = false
  }
}

function search() {
  page.value = 1
  loadList()
}

function filterPromoter() {
  filters.role = 'promoter'
  filters.status = null
  filters.is_black = null
  filters.abnormal = null
  search()
}

function filterAbnormal() {
  filters.role = ''
  filters.status = null
  filters.is_black = null
  filters.abnormal = 1
  search()
}

function resetFilters() {
  filters.keyword = ''
  filters.role = ''
  filters.status = null
  filters.is_black = null
  filters.abnormal = null
  filters.sort = 'last_active'
  search()
}

function openDetail(row) {
  detailUid.value = row.uid
  detailVisible.value = true
}

function onDetailChanged() {
  loadList()
  loadStats()
}

function onSizeChange() {
  page.value = 1
  loadList()
}

onMounted(() => {
  loadStats()
  loadList()
})
</script>

<style scoped>
.user-center .stat-item.clickable {
  cursor: pointer;
}

.user-center .stat-item.clickable:hover {
  background: #eef2ff;
}

.stat-item .sub {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.stat-item .value.warn {
  color: #e6a23c;
}

.stat-item .value.primary {
  color: var(--primary);
}

.m-t-16 {
  margin-top: 16px;
}

.filter-bar {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  align-items: center;
}

.cell-user .name {
  font-weight: 500;
}

.cell-user .mobile {
  font-size: 12px;
  color: #909399;
}

.money-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 12px;
}

.money-cell .withdraw b {
  color: var(--primary);
  font-size: 14px;
}

.money-cell .muted,
.device-cell .muted {
  color: #909399;
  font-size: 12px;
}

.device-cell {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 13px;
}

.m-l-4 {
  margin-left: 4px;
}

:deep(.el-table__row) {
  cursor: pointer;
}
</style>
