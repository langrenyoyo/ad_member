<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-left">
        <div class="login-illustration">
          <el-icon :size="80"><DataAnalysis /></el-icon>
          <p>用户 · 广告收益 · 风控管理</p>
        </div>
      </div>
      <div class="login-right">
        <h2>后台管理系统</h2>
        <el-form :model="form" @submit.prevent="handleLogin">
          <el-form-item>
            <el-input v-model="form.username" placeholder="账号" size="large" prefix-icon="User" />
          </el-form-item>
          <el-form-item>
            <el-input
              v-model="form.password"
              type="password"
              placeholder="密码"
              size="large"
              prefix-icon="Lock"
              show-password
            />
          </el-form-item>
          <el-form-item>
            <el-checkbox v-model="remember">记住账号</el-checkbox>
          </el-form-item>
          <el-button type="primary" size="large" :loading="loading" style="width: 100%" @click="handleLogin">
            登录
          </el-button>
        </el-form>
        <p class="hint">默认账号 admin / 123456 或 qdmin / 1234156</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const remember = ref(false)

const form = reactive({
  username: localStorage.getItem('remember_username') || 'admin',
  password: '',
})

async function handleLogin() {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入账号和密码')
    return
  }
  loading.value = true
  try {
    await userStore.login({ username: form.username, password: form.password })
    if (remember.value) {
      localStorage.setItem('remember_username', form.username)
    }
    ElMessage.success('登录成功')
    router.replace('/distribution/overview')
  } catch {
    // error handled by interceptor
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  display: flex;
  width: 800px;
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.login-left {
  width: 45%;
  background: linear-gradient(135deg, #4073fa, #6b9bff);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.login-illustration {
  text-align: center;
  padding: 40px;
}

.login-illustration p {
  margin-top: 16px;
  font-size: 14px;
  opacity: 0.9;
}

.login-right {
  flex: 1;
  padding: 48px 40px;
}

.login-right h2 {
  margin-bottom: 32px;
  font-size: 22px;
  text-align: center;
}

.hint {
  margin-top: 16px;
  font-size: 12px;
  color: #909399;
  text-align: center;
}
</style>
