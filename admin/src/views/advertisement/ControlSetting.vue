<template>
  <div class="page-container">
    <el-tabs v-model="activeTab">
      <el-tab-pane label="风控配置" name="config">
        <div class="ls-card">
          <el-form :model="configForm" label-width="140px" v-loading="loading">
            <el-form-item label="风控开关">
              <el-switch v-model="configForm.ad_risk_enabled" active-value="1" inactive-value="0" />
            </el-form-item>
            <el-form-item label="每日广告上限">
              <el-input-number v-model="configForm.daily_ad_limit" :min="1" :max="999" />
            </el-form-item>
            <el-form-item label="最低提现金额">
              <el-input-number v-model="configForm.min_withdraw" :min="1" />
            </el-form-item>
            <el-form-item label="Taku Publisher Key">
              <el-input v-model="configForm.taku_publisher_key" type="password" show-password placeholder="用于同步 Taku 应用与报表" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveConfigForm">保存配置</el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>

      <el-tab-pane label="Taku 应用" name="taku">
        <div class="ls-card">
          <div class="toolbar">
            <el-button type="primary" @click="loadTakuApps">刷新列表</el-button>
            <el-button @click="showSyncDialog = true">手动同步应用</el-button>
          </div>
          <el-table :data="takuApps" class="m-t-8">
            <el-table-column prop="app_id" label="App ID" />
            <el-table-column prop="app_name" label="应用名称" />
            <el-table-column prop="platform" label="平台" width="100">
              <template #default="{ row }">{{ row.platform === 1 ? 'Android' : 'iOS' }}</template>
            </el-table-column>
            <el-table-column prop="package_name" label="包名" />
            <el-table-column prop="synced_at" label="同步时间" width="180" />
          </el-table>
        </div>
      </el-tab-pane>

      <el-tab-pane label="风控日志" name="risk">
        <div class="ls-card">
          <el-table :data="riskLogs" v-loading="riskLoading">
            <el-table-column prop="uid" label="UID" width="120" />
            <el-table-column prop="reason" label="原因" />
            <el-table-column prop="action" label="动作" width="100" />
            <el-table-column prop="created_at" label="时间" width="180" />
          </el-table>
        </div>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="showSyncDialog" title="同步 Taku 应用" width="480px">
      <el-form :model="syncForm" label-width="100px">
        <el-form-item label="App ID"><el-input v-model="syncForm.app_id" /></el-form-item>
        <el-form-item label="应用名称"><el-input v-model="syncForm.app_name" /></el-form-item>
        <el-form-item label="平台">
          <el-select v-model="syncForm.platform">
            <el-option label="Android" :value="1" />
            <el-option label="iOS" :value="2" />
          </el-select>
        </el-form-item>
        <el-form-item label="包名"><el-input v-model="syncForm.package_name" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSyncDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSync">同步</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getConfig, saveConfig, getTakuApps, syncTakuApp, getContainmentLog } from '@/api'

const activeTab = ref('config')
const loading = ref(false)
const riskLoading = ref(false)
const configForm = reactive({
  ad_risk_enabled: '1',
  daily_ad_limit: 50,
  min_withdraw: 10,
  taku_publisher_key: '',
})
const takuApps = ref([])
const riskLogs = ref([])
const showSyncDialog = ref(false)
const syncForm = reactive({
  app_id: '',
  app_name: '',
  platform: 2,
  package_name: '',
})

async function loadConfig() {
  loading.value = true
  try {
    const res = await getConfig()
    const data = res.data || res
    Object.assign(configForm, {
      ad_risk_enabled: data.ad_risk_enabled || '1',
      daily_ad_limit: Number(data.daily_ad_limit || 50),
      min_withdraw: Number(data.min_withdraw || 10),
      taku_publisher_key: data.taku_publisher_key || '',
    })
  } finally {
    loading.value = false
  }
}

async function saveConfigForm() {
  await saveConfig({
    ad_risk_enabled: String(configForm.ad_risk_enabled),
    daily_ad_limit: String(configForm.daily_ad_limit),
    min_withdraw: String(configForm.min_withdraw),
    taku_publisher_key: configForm.taku_publisher_key,
  })
  ElMessage.success('配置已保存')
}

async function loadTakuApps() {
  const res = await getTakuApps()
  takuApps.value = res.list || res.data?.list || []
}

async function loadRiskLogs() {
  riskLoading.value = true
  try {
    const res = await getContainmentLog({ page: 1, limit: 50 })
    riskLogs.value = res.list || []
  } finally {
    riskLoading.value = false
  }
}

async function handleSync() {
  await syncTakuApp({ ...syncForm })
  ElMessage.success('同步成功')
  showSyncDialog.value = false
  loadTakuApps()
}

onMounted(() => {
  loadConfig()
  loadTakuApps()
  loadRiskLogs()
})
</script>

<style scoped>
.toolbar {
  display: flex;
  gap: 12px;
}

.m-t-8 {
  margin-top: 8px;
}
</style>
