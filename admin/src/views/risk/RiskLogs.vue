<template>
  <div class="page-container">
    <el-tabs v-model="tab">
      <el-tab-pane label="风控决策" name="decisions">
        <div class="ls-card">
          <el-table :data="decisions" v-loading="loadingDecisions">
            <el-table-column prop="uid" label="UID" width="100" />
            <el-table-column prop="trans_id" label="事务ID" min-width="140" show-overflow-tooltip />
            <el-table-column prop="rule_name" label="规则" width="140" />
            <el-table-column prop="score_delta" label="加分" width="70" />
            <el-table-column prop="total_score" label="总分" width="70" />
            <el-table-column prop="action" label="动作" width="80">
              <template #default="{ row }">
                <el-tag :type="row.action === 'block' ? 'danger' : 'success'" size="small">{{ row.action }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="detail" label="详情" />
            <el-table-column prop="created_at" label="时间" width="170" />
          </el-table>
        </div>
      </el-tab-pane>

      <el-tab-pane label="处置日志" name="containment">
        <div class="ls-card">
          <el-table :data="containment" v-loading="loadingContainment">
            <el-table-column prop="uid" label="UID" width="100" />
            <el-table-column prop="reason" label="原因" />
            <el-table-column prop="action" label="动作" width="100" />
            <el-table-column prop="created_at" label="时间" width="170" />
          </el-table>
        </div>
      </el-tab-pane>

      <el-tab-pane label="回调日志" name="callbacks">
        <div class="ls-card">
          <el-table :data="callbacks" v-loading="loadingCallbacks">
            <el-table-column prop="source" label="来源" width="90" />
            <el-table-column prop="trans_id" label="事务ID" min-width="140" show-overflow-tooltip />
            <el-table-column prop="sign_ok" label="验签" width="80">
              <template #default="{ row }">
                <el-tag :type="row.sign_ok ? 'success' : 'danger'" size="small">
                  {{ row.sign_ok ? '通过' : '失败' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="raw_body" label="内容" min-width="200" show-overflow-tooltip />
            <el-table-column prop="created_at" label="时间" width="170" />
          </el-table>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { getCallbackLogs, getContainmentLog, getRiskDecisions } from '@/api'

const tab = ref('decisions')
const loadingDecisions = ref(false)
const loadingContainment = ref(false)
const loadingCallbacks = ref(false)
const decisions = ref([])
const containment = ref([])
const callbacks = ref([])

async function loadDecisions() {
  loadingDecisions.value = true
  try {
    const res = await getRiskDecisions({ page: 1, limit: 50 })
    decisions.value = res.list || []
  } finally {
    loadingDecisions.value = false
  }
}

async function loadContainment() {
  loadingContainment.value = true
  try {
    const res = await getContainmentLog({ page: 1, limit: 50 })
    containment.value = res.list || []
  } finally {
    loadingContainment.value = false
  }
}

async function loadCallbacks() {
  loadingCallbacks.value = true
  try {
    const res = await getCallbackLogs({ page: 1, limit: 50 })
    callbacks.value = res.list || []
  } finally {
    loadingCallbacks.value = false
  }
}

watch(tab, (v) => {
  if (v === 'decisions') loadDecisions()
  if (v === 'containment') loadContainment()
  if (v === 'callbacks') loadCallbacks()
})

onMounted(loadDecisions)
</script>
