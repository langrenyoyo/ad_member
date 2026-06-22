import { defineStore } from 'pinia'
import { getAdminInfo, login as loginApi, logout as logoutApi } from '@/api'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    userInfo: {},
  }),
  actions: {
    async login(form) {
      const res = await loginApi(form)
      const token = res.token || res.data?.token
      if (token) {
        this.token = token
        localStorage.setItem('token', token)
      }
      return res
    },
    async fetchUser() {
      const res = await getAdminInfo()
      this.userInfo = res.data || res
    },
    async logout() {
      try {
        await logoutApi()
      } finally {
        this.token = ''
        this.userInfo = {}
        localStorage.removeItem('token')
      }
    },
  },
})
