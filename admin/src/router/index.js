import { createRouter, createWebHistory } from 'vue-router'
import AdminLayout from '@/layout/AdminLayout.vue'

const routes = [
  {
    path: '/account/login',
    name: 'login',
    component: () => import('@/views/login/Login.vue'),
    meta: { title: '登录', public: true },
  },
  {
    path: '/',
    component: AdminLayout,
    redirect: '/distribution/overview',
    children: [
      {
        path: 'distribution/overview',
        name: 'overview',
        component: () => import('@/views/distribution/Overview.vue'),
        meta: { title: '数据概览', parent: '用户管理' },
      },
      {
        path: 'distribution/statement',
        name: 'statement',
        component: () => import('@/views/distribution/Statement.vue'),
        meta: { title: '数据报表', parent: '用户管理' },
      },
      {
        path: 'distribution/userList',
        name: 'userList',
        component: () => import('@/views/distribution/UserList.vue'),
        meta: { title: '用户列表', parent: '用户管理', agent: 0 },
      },
      {
        path: 'distribution/distribution_userList_proxy',
        name: 'userList_proxy',
        component: () => import('@/views/distribution/UserList.vue'),
        meta: { title: '代理列表', parent: '用户管理', agent: 1 },
      },
      {
        path: 'distribution/userPromotion',
        name: 'userPromotion',
        component: () => import('@/views/distribution/UserPromotion.vue'),
        meta: { title: '推广数据', parent: '用户管理' },
      },
      {
        path: 'risk/config',
        name: 'risk_config',
        component: () => import('@/views/risk/RiskConfig.vue'),
        meta: { title: '风控配置', parent: '广告联盟与风控' },
      },
      {
        path: 'risk/incentive',
        name: 'risk_incentive',
        component: () => import('@/views/risk/IncentiveList.vue'),
        meta: { title: '激励事务', parent: '广告联盟与风控' },
      },
      {
        path: 'risk/reconcile',
        name: 'risk_reconcile',
        component: () => import('@/views/risk/Reconcile.vue'),
        meta: { title: '收益对账', parent: '广告联盟与风控' },
      },
      {
        path: 'risk/clawback',
        name: 'risk_clawback',
        component: () => import('@/views/risk/ClawbackQuery.vue'),
        meta: { title: '核减查询', parent: '广告联盟与风控' },
      },
      {
        path: 'risk/taku',
        name: 'risk_taku',
        component: () => import('@/views/risk/TakuApps.vue'),
        meta: { title: 'Taku 应用', parent: '广告联盟与风控' },
      },
      {
        path: 'risk/logs',
        name: 'risk_logs',
        component: () => import('@/views/risk/RiskLogs.vue'),
        meta: { title: '风控日志', parent: '广告联盟与风控' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  if (!to.meta.public && !token) {
    return '/account/login'
  }
  if (to.path === '/account/login' && token) {
    return '/distribution/overview'
  }
})

export default router
