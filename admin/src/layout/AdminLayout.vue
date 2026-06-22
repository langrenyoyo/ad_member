<template>
  <el-container class="admin-layout">
    <el-aside :width="asideWidth" class="aside">
      <div class="logo">
        <div class="logo-icon">
          <el-icon><Monitor /></el-icon>
        </div>
        <span class="logo-text">用户管理</span>
      </div>
      <el-menu
        class="side-menu"
        :default-active="activeMenu"
        router
      >
        <el-sub-menu index="distribution">
          <template #title>
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </template>
          <el-menu-item index="/distribution/overview">数据概览</el-menu-item>
          <el-menu-item index="/distribution/statement">数据报表</el-menu-item>
          <el-menu-item index="/distribution/userList">用户列表</el-menu-item>
          <el-menu-item index="/distribution/distribution_userList_proxy">代理列表</el-menu-item>
          <el-menu-item index="/distribution/userPromotion">推广数据</el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="risk">
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>广告联盟与风控</span>
          </template>
          <el-menu-item index="/risk/config">风控配置</el-menu-item>
          <el-menu-item index="/risk/incentive">激励事务</el-menu-item>
          <el-menu-item index="/risk/reconcile">收益对账</el-menu-item>
          <el-menu-item index="/risk/clawback">核减查询</el-menu-item>
          <el-menu-item index="/risk/taku">Taku 应用</el-menu-item>
          <el-menu-item index="/risk/logs">风控日志</el-menu-item>
        </el-sub-menu>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-title">{{ pageTitle }}</div>
        <div class="header-right">
          <span class="username">{{ userStore.userInfo?.name || '管理员' }}</span>
          <el-button type="primary" link @click="handleLogout">退出登录</el-button>
        </div>
      </el-header>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const asideWidth = 'var(--aside-width)'
const activeMenu = computed(() => route.path)
const pageTitle = computed(() => {
  const parent = route.meta.parent
  const title = route.meta.title
  return parent ? `${parent} / ${title}` : title || '后台管理'
})

onMounted(() => {
  if (userStore.token) {
    userStore.fetchUser()
  }
})

async function handleLogout() {
  await userStore.logout()
  router.push('/account/login')
}
</script>

<style scoped>
.admin-layout {
  height: 100vh;
}

.aside {
  background: linear-gradient(180deg, var(--sidebar-bg) 0%, var(--sidebar-bg-deep) 100%);
  border-right: 1px solid rgba(255, 255, 255, 0.06);
  box-shadow: 2px 0 12px rgba(0, 0, 0, 0.12);
}

.logo {
  height: var(--header-height);
  display: flex;
  align-items: center;
  padding: 0 16px;
  gap: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(0, 0, 0, 0.15);
}

.logo-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
  flex-shrink: 0;
}

.logo-text {
  color: #f1f5f9;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 0.02em;
  line-height: 1.3;
}

.side-menu {
  border-right: none;
  background: transparent !important;
  padding: 8px 0;
}

.side-menu :deep(.el-menu-item),
.side-menu :deep(.el-sub-menu__title) {
  height: 44px;
  line-height: 44px;
  color: var(--sidebar-text) !important;
  font-size: 14px;
  margin: 2px 10px;
  border-radius: 8px;
}

.side-menu :deep(.el-sub-menu .el-menu-item) {
  min-width: auto;
  padding-left: 48px !important;
  height: 40px;
  line-height: 40px;
  font-size: 13px;
}

.side-menu :deep(.el-menu-item .el-icon),
.side-menu :deep(.el-sub-menu__title .el-icon) {
  color: var(--sidebar-text-muted);
  font-size: 17px;
}

.side-menu :deep(.el-menu-item:hover),
.side-menu :deep(.el-sub-menu__title:hover) {
  background: var(--sidebar-hover-bg) !important;
  color: #fff !important;
}

.side-menu :deep(.el-menu-item:hover .el-icon),
.side-menu :deep(.el-sub-menu__title:hover .el-icon) {
  color: var(--primary-light);
}

.side-menu :deep(.el-menu-item.is-active) {
  background: var(--sidebar-active-bg) !important;
  color: #fff !important;
  font-weight: 600;
  box-shadow: inset 3px 0 0 var(--primary-light);
}

.side-menu :deep(.el-menu-item.is-active .el-icon) {
  color: var(--primary-light);
}

.side-menu :deep(.el-sub-menu.is-opened > .el-sub-menu__title) {
  color: #fff !important;
}

.side-menu :deep(.el-sub-menu.is-opened > .el-sub-menu__title .el-icon) {
  color: var(--primary-light);
}

.side-menu :deep(.el-menu--inline) {
  background: rgba(0, 0, 0, 0.18) !important;
  border-radius: 8px;
  margin: 0 10px 6px;
  padding: 4px 0;
}

.side-menu :deep(.el-sub-menu__icon-arrow) {
  color: var(--sidebar-text-muted);
}

.header {
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  border-bottom: 1px solid #ebeef5;
  height: var(--header-height);
}

.header-title {
  font-size: 16px;
  font-weight: 500;
  color: #1f2937;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.username {
  color: #606266;
}

.main {
  background: #f0f2f5;
  padding: 0;
}
</style>
