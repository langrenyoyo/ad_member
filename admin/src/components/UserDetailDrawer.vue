<template>
  <el-drawer
    :model-value="visible"
    :title="`用户详情 · ${uid}`"
    size="720px"
    destroy-on-close
    @close="emit('close')"
  >
    <div v-loading="loading">
      <template v-if="detail">
        <!-- 状态与操作 -->
        <div class="detail-header">
          <div class="user-meta">
            <span class="nickname">{{ detail.nickname || '未设置昵称' }}</span>
            <el-tag size="small" :type="roleTag(detail.agent_type)">{{ roleLabel(detail.agent_type) }}</el-tag>
            <el-tag v-if="detail.is_black" size="small" type="danger">拉黑</el-tag>
            <el-tag v-else-if="detail.status === 0" size="small" type="warning">冻结</el-tag>
            <el-tag v-else size="small" type="success">正常</el-tag>
          </div>
          <div class="actions">
            <el-button v-if="detail.status === 1" size="small" @click="handleFreeze">冻结</el-button>
            <el-button v-else size="small" type="success" @click="handleOpen">启用</el-button>
            <el-button size="small" type="danger" @click="handleBlacklist">拉黑</el-button>
          </div>
        </div>

        <!-- 收益卡片 -->
        <div class="balance-grid">
          <div class="balance-item primary">
            <div class="label">可提现</div>
            <div class="val">{{ fmt(detail.withdrawable_balance) }}</div>
          </div>
          <div class="balance-item">
            <div class="label">待确认</div>
            <div class="val">{{ fmt(detail.pending_balance) }}</div>
          </div>
          <div class="balance-item">
            <div class="label">已确认</div>
            <div class="val">{{ fmt(detail.confirmed_balance) }}</div>
          </div>
          <div class="balance-item">
            <div class="label">预估余额</div>
            <div class="val">{{ fmt(detail.estimated_balance) }}</div>
          </div>
        </div>

        <!-- 基础信息 -->
        <el-descriptions :column="2" border size="small" class="m-t-16">
          <el-descriptions-item label="UID">{{ detail.uid }}</el-descriptions-item>
          <el-descriptions-item label="手机号">{{ detail.mobile || '—' }}</el-descriptions-item>
          <el-descriptions-item label="等级">{{ detail.level_name || '—' }}</el-descriptions-item>
          <el-descriptions-item label="今日收益">{{ fmt(detail.today_revenue) }}</el-descriptions-item>
          <el-descriptions-item label="累计收益">{{ fmt(detail.total_revenue) }}</el-descriptions-item>
          <el-descriptions-item label="广告次数">{{ detail.ad_count }}</el-descriptions-item>
          <el-descriptions-item label="设备型号">{{ detail.device_model || '—' }}</el-descriptions-item>
          <el-descriptions-item label="设备唯一值">{{ detail.device_unique_id || '—' }}</el-descriptions-item>
          <el-descriptions-item label="注册时间">{{ detail.created_at }}</el-descriptions-item>
          <el-descriptions-item label="最后活跃">{{ detail.last_active }}</el-descriptions-item>
        </el-descriptions>

        <!-- 风控摘要 -->
        <div class="risk-summary m-t-16">
          <el-tag type="info">激励 pending {{ detail.tx_pending || 0 }}</el-tag>
          <el-tag type="success">confirmed {{ detail.tx_confirmed || 0 }}</el-tag>
          <el-tag type="danger">核减 {{ detail.tx_clawback || 0 }} / {{ fmt(detail.clawback_amount) }}</el-tag>
          <el-tag type="warning">风控拦截 {{ detail.risk_blocks || 0 }}</el-tag>
        </div>

        <el-tabs v-model="tab" class="m-t-16">
          <el-tab-pane label="激励事务" name="incentive">
            <el-table :data="incentives" size="small" max-height="320">
              <el-table-column prop="trans_id" label="事务ID" min-width="120" show-overflow-tooltip />
              <el-table-column prop="user_reward" label="奖励" width="70" />
              <el-table-column prop="status" label="状态" width="90">
                <template #default="{ row }">
                  <el-tag :type="txTag(row.status)" size="small">{{ row.status }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="双回调" width="90">
                <template #default="{ row }">
                  <span :class="row.kuaishou_verified ? 'ok' : 'no'">K</span>
                  <span :class="row.taku_verified ? 'ok' : 'no'">T</span>
                </template>
              </el-table-column>
              <el-table-column prop="created_at" label="时间" width="155" />
            </el-table>
          </el-tab-pane>
          <el-tab-pane label="广告记录" name="ads">
            <el-table :data="adLogs" size="small" max-height="320">
              <el-table-column prop="app_name" label="应用" />
              <el-table-column prop="placement" label="广告位" />
              <el-table-column prop="revenue" label="收益" width="70" />
              <el-table-column prop="action" label="动作" width="80" />
              <el-table-column prop="created_at" label="时间" width="155" />
            </el-table>
          </el-tab-pane>
          <el-tab-pane label="设备绑定" name="devices">
            <el-table :data="devices" size="small" max-height="320">
              <el-table-column prop="device_model" label="型号" />
              <el-table-column prop="device_unique_id" label="唯一值">
                <template #default="{ row }">{{ row.device_unique_id || '—' }}</template>
              </el-table-column>
              <el-table-column prop="platform" label="平台" width="70">
                <template #default="{ row }">
                  {{ row.platform === 1 ? 'Android' : row.platform === 2 ? 'iOS' : '—' }}
                </template>
              </el-table-column>
              <el-table-column prop="source" label="来源" width="70" />
              <el-table-column prop="updated_at" label="更新" width="155" />
            </el-table>
          </el-tab-pane>
          <el-tab-pane label="核减记录" name="clawback">
            <el-table :data="clawbacks" size="small" max-height="320">
              <el-table-column prop="trans_id" label="事务ID" min-width="120" show-overflow-tooltip />
              <el-table-column prop="user_reward" label="金额" width="70" />
              <el-table-column prop="deduction_type" label="类型" width="90" />
              <el-table-column prop="reason" label="原因" show-overflow-tooltip />
              <el-table-column prop="created_at" label="时间" width="155" />
            </el-table>
          </el-tab-pane>
        </el-tabs>
      </template>
    </div>
  </el-drawer>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getMemberDetail,
  getMemberAdverLog,
  getMemberDevices,
  getIncentiveTransactions,
  getClawbackDetail,
  freezeMember,
  openMember,
  blacklistMember,
} from '@/api'

const props = defineProps({
  visible: Boolean,
  uid: String,
})
const emit = defineEmits(['close', 'changed'])

const loading = ref(false)
const detail = ref(null)
const tab = ref('incentive')
const incentives = ref([])
const adLogs = ref([])
const devices = ref([])
const clawbacks = ref([])

function fmt(n) {
  return Number(n || 0).toFixed(2)
}

function roleLabel(t) {
  return t === 2 ? '团长' : t === 1 ? '代理' : '普通用户'
}

function roleTag(t) {
  return t === 2 ? 'danger' : t === 1 ? 'warning' : 'info'
}

function txTag(s) {
  return { pending: 'warning', confirmed: 'success', clawback: 'danger', rejected: 'info' }[s] || 'info'
}

async function loadAll() {
  if (!props.uid) return
  loading.value = true
  try {
    const res = await getMemberDetail(props.uid)
    detail.value = res.data || res

    const [tx, ads, dev, cb] = await Promise.all([
      getIncentiveTransactions({ uid: props.uid, page: 1, limit: 30 }),
      getMemberAdverLog({ uid: props.uid, page: 1, limit: 30 }),
      getMemberDevices(props.uid),
      getClawbackDetail({ uid: props.uid, page: 1, limit: 30 }),
    ])
    incentives.value = tx.list || []
    adLogs.value = ads.list || []
    devices.value = dev.list || []
    clawbacks.value = cb.list || []
  } finally {
    loading.value = false
  }
}

async function handleFreeze() {
  await ElMessageBox.confirm(`冻结用户 ${props.uid}？`)
  await freezeMember(props.uid)
  ElMessage.success('已冻结')
  emit('changed')
  loadAll()
}

async function handleOpen() {
  await openMember(props.uid)
  ElMessage.success('已启用')
  emit('changed')
  loadAll()
}

async function handleBlacklist() {
  await ElMessageBox.confirm(`拉黑用户 ${props.uid}？`, '警告', { type: 'warning' })
  await blacklistMember(props.uid)
  ElMessage.success('已拉黑')
  emit('changed')
  loadAll()
}

watch(
  () => [props.visible, props.uid],
  ([v, uid]) => {
    if (v && uid) {
      tab.value = 'incentive'
      loadAll()
    }
  },
)
</script>

<style scoped>
.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.user-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.nickname {
  font-size: 18px;
  font-weight: 600;
}

.actions {
  display: flex;
  gap: 8px;
}

.balance-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-top: 16px;
}

.balance-item {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 12px;
}

.balance-item.primary {
  background: linear-gradient(135deg, #4073fa15, #4073fa08);
  border: 1px solid #4073fa30;
}

.balance-item .label {
  font-size: 12px;
  color: #909399;
}

.balance-item .val {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin-top: 4px;
}

.balance-item.primary .val {
  color: var(--primary);
}

.risk-summary {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.m-t-16 {
  margin-top: 16px;
}

.ok {
  color: #67c23a;
  font-weight: 600;
  margin-right: 4px;
}

.no {
  color: #c0c4cc;
  margin-right: 4px;
}
</style>
