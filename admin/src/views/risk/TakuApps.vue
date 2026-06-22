<template>
  <div class="page-container">
    <div class="ls-card">
      <div class="toolbar">
        <el-button type="primary" @click="load">刷新列表</el-button>
        <el-button @click="showDialog = true">手动同步应用</el-button>
      </div>
      <el-table :data="apps" class="m-t-16">
        <el-table-column prop="app_id" label="App ID" min-width="140" />
        <el-table-column prop="app_name" label="应用名称" />
        <el-table-column prop="platform" label="平台" width="90">
          <template #default="{ row }">{{ row.platform === 1 ? 'Android' : 'iOS' }}</template>
        </el-table-column>
        <el-table-column prop="package_name" label="包名" min-width="160" show-overflow-tooltip />
        <el-table-column prop="kuaishou_security_key" label="快手 SecurityKey" min-width="140" show-overflow-tooltip />
        <el-table-column prop="synced_at" label="同步时间" width="170" />
      </el-table>
    </div>

    <el-dialog v-model="showDialog" title="同步 Taku 应用" width="520px">
      <el-form :model="form" label-width="130px">
        <el-form-item label="App ID"><el-input v-model="form.app_id" /></el-form-item>
        <el-form-item label="应用名称"><el-input v-model="form.app_name" /></el-form-item>
        <el-form-item label="平台">
          <el-select v-model="form.platform">
            <el-option label="Android" :value="1" />
            <el-option label="iOS" :value="2" />
          </el-select>
        </el-form-item>
        <el-form-item label="包名"><el-input v-model="form.package_name" /></el-form-item>
        <el-form-item label="快手 SecurityKey">
          <el-input v-model="form.kuaishou_security_key" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSync">同步</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getTakuApps, syncTakuApp } from '@/api'

const apps = ref([])
const showDialog = ref(false)
const form = reactive({
  app_id: '',
  app_name: '',
  platform: 2,
  package_name: '',
  kuaishou_security_key: '',
})

async function load() {
  const res = await getTakuApps()
  apps.value = res.list || res.data?.list || []
}

async function handleSync() {
  await syncTakuApp({ ...form })
  ElMessage.success('同步成功')
  showDialog.value = false
  load()
}

onMounted(load)
</script>

<style scoped>
.toolbar {
  display: flex;
  gap: 12px;
}

.m-t-16 {
  margin-top: 16px;
}
</style>
