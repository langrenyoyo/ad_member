<template>
  <div class="page-container">
    <div class="ls-card">
      <div class="card-title">风控与结算配置</div>
      <el-form :model="form" label-width="160px" v-loading="loading" class="m-t-16">
        <el-divider content-position="left">基础风控</el-divider>
        <el-form-item label="风控开关">
          <el-switch v-model="form.ad_risk_enabled" active-value="1" inactive-value="0" />
        </el-form-item>
        <el-form-item label="用户日激励上限">
          <el-input-number v-model="form.daily_ad_limit" :min="1" :max="999" />
        </el-form-item>
        <el-form-item label="设备日激励上限">
          <el-input-number v-model="form.device_daily_limit" :min="1" :max="999" />
        </el-form-item>
        <el-form-item label="IP 日激励上限">
          <el-input-number v-model="form.ip_daily_limit" :min="1" :max="9999" />
        </el-form-item>
        <el-form-item label="拦截风险分阈值">
          <el-input-number v-model="form.risk_block_score" :min="1" :max="100" />
        </el-form-item>

        <el-divider content-position="left">双回调与入账</el-divider>
        <el-form-item label="用户分润系数">
          <el-input-number v-model="form.reward_share_rate" :min="0.1" :max="1" :step="0.01" :precision="2" />
          <span class="hint">预估收益 × 系数，预留核减空间</span>
        </el-form-item>
        <el-form-item label="可提现延迟(T+N)">
          <el-input-number v-model="form.confirm_delay_days" :min="0" :max="30" />
          <span class="hint">已确认收益 N 天后转入可提现</span>
        </el-form-item>
        <el-form-item label="Taku 等待秒数">
          <el-input-number v-model="form.taku_wait_seconds" :min="0" :max="60" />
          <span class="hint">客户端乐观展示参考，后台双验不阻塞 UI</span>
        </el-form-item>
        <el-form-item label="对账 GAP 告警率">
          <el-input-number v-model="form.gap_alert_rate" :min="0.01" :max="1" :step="0.01" :precision="2" />
        </el-form-item>

        <el-divider content-position="left">提现与 Taku</el-divider>
        <el-form-item label="最低提现金额">
          <el-input-number v-model="form.min_withdraw" :min="1" />
        </el-form-item>
        <el-form-item label="Taku Publisher Key">
          <el-input v-model="form.taku_publisher_key" type="password" show-password />
        </el-form-item>

        <el-divider content-position="left">回调地址</el-divider>
        <el-form-item label="快手激励回调">
          <el-input readonly value="/mas/callback/kuaishou/reward" />
        </el-form-item>
        <el-form-item label="Taku S2S 回调">
          <el-input readonly value="/mas/callback/taku/s2s" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSave">保存配置</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getRiskConfig, saveRiskConfig } from '@/api'

const loading = ref(false)
const form = reactive({
  ad_risk_enabled: '1',
  daily_ad_limit: 50,
  device_daily_limit: 30,
  ip_daily_limit: 100,
  risk_block_score: 70,
  reward_share_rate: 0.88,
  confirm_delay_days: 1,
  taku_wait_seconds: 5,
  gap_alert_rate: 0.08,
  min_withdraw: 10,
  taku_publisher_key: '',
})

async function load() {
  loading.value = true
  try {
    const res = await getRiskConfig()
    const data = res.data || res
    Object.assign(form, {
      ad_risk_enabled: data.ad_risk_enabled || '1',
      daily_ad_limit: Number(data.daily_ad_limit || 50),
      device_daily_limit: Number(data.device_daily_limit || 30),
      ip_daily_limit: Number(data.ip_daily_limit || 100),
      risk_block_score: Number(data.risk_block_score || 70),
      reward_share_rate: Number(data.reward_share_rate || 0.88),
      confirm_delay_days: Number(data.confirm_delay_days || 1),
      taku_wait_seconds: Number(data.taku_wait_seconds || 5),
      gap_alert_rate: Number(data.gap_alert_rate || 0.08),
      min_withdraw: Number(data.min_withdraw || 10),
      taku_publisher_key: data.taku_publisher_key || '',
    })
  } finally {
    loading.value = false
  }
}

async function handleSave() {
  await saveRiskConfig({
    ad_risk_enabled: String(form.ad_risk_enabled),
    daily_ad_limit: String(form.daily_ad_limit),
    device_daily_limit: String(form.device_daily_limit),
    ip_daily_limit: String(form.ip_daily_limit),
    risk_block_score: String(form.risk_block_score),
    reward_share_rate: String(form.reward_share_rate),
    confirm_delay_days: String(form.confirm_delay_days),
    taku_wait_seconds: String(form.taku_wait_seconds),
    gap_alert_rate: String(form.gap_alert_rate),
    min_withdraw: String(form.min_withdraw),
    taku_publisher_key: form.taku_publisher_key,
  })
  ElMessage.success('配置已保存')
}

onMounted(load)
</script>

<style scoped>
.card-title {
  font-size: 16px;
  font-weight: 600;
}

.m-t-16 {
  margin-top: 16px;
}

.hint {
  margin-left: 12px;
  color: #909399;
  font-size: 12px;
}
</style>
