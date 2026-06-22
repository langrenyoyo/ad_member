<template>
  <div class="page-container">
    <div class="ls-card">
      <div class="toolbar">
        <el-input v-model="keyword" placeholder="搜索 UID/昵称/手机号" clearable style="width: 240px" @clear="loadData" />
        <el-button type="primary" @click="loadData">搜索</el-button>
      </div>

      <el-table :data="list" v-loading="loading" class="m-t-8">
        <el-table-column prop="uid" label="UID" width="120" />
        <el-table-column prop="nickname" label="昵称" />
        <el-table-column prop="mobile" label="手机号" width="130" />
        <el-table-column prop="device_model" label="设备型号" width="120" show-overflow-tooltip>
          <template #default="{ row }">{{ row.device_model || '—' }}</template>
        </el-table-column>
        <el-table-column prop="device_unique_id" label="设备唯一值" min-width="130" show-overflow-tooltip>
          <template #default="{ row }">{{ row.device_unique_id || '—' }}</template>
        </el-table-column>
        <el-table-column prop="agent_type" label="类型" width="90">
          <template #default="{ row }">
            {{ agentLabel(row.agent_type) }}
          </template>
        </el-table-column>
        <el-table-column prop="total_revenue" label="累计收益" width="100" />
        <el-table-column prop="estimated_balance" label="预估" width="80" />
        <el-table-column prop="confirmed_balance" label="已确认" width="80" />
        <el-table-column prop="withdrawable_balance" label="可提现" width="80" />
        <el-table-column prop="pending_balance" label="待确认" width="80" />
        <el-table-column prop="today_revenue" label="今日收益" width="100" />
        <el-table-column prop="ad_count" label="广告次数" width="90" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'" size="small">
              {{ row.status === 1 ? '正常' : '冻结' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="showDeviceLog(row)">设备记录</el-button>
            <el-button link type="primary" @click="showAdLog(row)">广告明细</el-button>
            <el-button v-if="row.status === 1" link type="warning" @click="handleFreeze(row)">冻结</el-button>
            <el-button v-else link type="success" @click="handleOpen(row)">启用</el-button>
            <el-button link type="danger" @click="handleBlacklist(row)">拉黑</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        class="m-t-16"
        v-model:current-page="page"
        v-model:page-size="limit"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="loadData"
      />
    </div>

    <el-dialog v-model="deviceDialogVisible" :title="`设备绑定 - ${deviceUid}`" width="640px">
      <el-table :data="deviceLogs" size="small">
        <el-table-column prop="device_model" label="设备型号" />
        <el-table-column prop="device_unique_id" label="唯一值" min-width="140">
          <template #default="{ row }">{{ row.device_unique_id || '—' }}</template>
        </el-table-column>
        <el-table-column prop="platform" label="平台" width="80">
          <template #default="{ row }">
            {{ platformLabel(row.platform) }}
          </template>
        </el-table-column>
        <el-table-column prop="source" label="来源" width="80">
          <template #default="{ row }">{{ deviceSourceLabel(row.source) }}</template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="170" />
      </el-table>
    </el-dialog>

    <el-dialog v-model="adDialogVisible" title="广告观看明细" width="700px">
      <el-table :data="adLogs" size="small">
        <el-table-column prop="app_name" label="应用" />
        <el-table-column prop="placement" label="广告位" />
        <el-table-column prop="revenue" label="收益" width="80" />
        <el-table-column prop="action" label="动作" width="80">
          <template #default="{ row }">{{ adActionLabel(row.action) }}</template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="170" />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getMemberList,
  getMemberAdverLog,
  getMemberDevices,
  freezeMember,
  openMember,
  blacklistMember,
} from '@/api'
import {
  adActionLabel,
  deviceSourceLabel,
  platformLabel,
} from '@/utils/statusLabels'

const route = useRoute()
const agent = computed(() => route.meta.agent ?? undefined)

const loading = ref(false)
const list = ref([])
const total = ref(0)
const page = ref(1)
const limit = ref(20)
const keyword = ref('')

const adDialogVisible = ref(false)
const adLogs = ref([])
const deviceDialogVisible = ref(false)
const deviceUid = ref('')
const deviceLogs = ref([])

function agentLabel(t) {
  return t === 1 ? '代理' : '普通'
}

async function loadData() {
  loading.value = true
  try {
    const params = { page: page.value, limit: limit.value, keyword: keyword.value || undefined }
    if (agent.value !== undefined) params.agent = agent.value
    const res = await getMemberList(params)
    list.value = res.list || []
    total.value = res.total || 0
  } finally {
    loading.value = false
  }
}

async function showAdLog(row) {
  const res = await getMemberAdverLog({ uid: row.uid, page: 1, limit: 50 })
  adLogs.value = res.list || []
  adDialogVisible.value = true
}

async function showDeviceLog(row) {
  deviceUid.value = row.uid
  const res = await getMemberDevices(row.uid)
  deviceLogs.value = res.list || []
  deviceDialogVisible.value = true
}

async function handleFreeze(row) {
  await ElMessageBox.confirm(`确定冻结用户 ${row.uid}？`)
  await freezeMember(row.uid)
  ElMessage.success('已冻结')
  loadData()
}

async function handleOpen(row) {
  await openMember(row.uid)
  ElMessage.success('已启用')
  loadData()
}

async function handleBlacklist(row) {
  await ElMessageBox.confirm(`确定拉黑用户 ${row.uid}？`, '警告', { type: 'warning' })
  await blacklistMember(row.uid)
  ElMessage.success('已拉黑')
  loadData()
}

onMounted(loadData)
</script>

<style scoped>
.toolbar {
  display: flex;
  gap: 12px;
}

.m-t-8 {
  margin-top: 8px;
}

.m-t-16 {
  margin-top: 16px;
}
</style>
