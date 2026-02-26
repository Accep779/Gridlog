import { defineStore } from 'pinia'
import { api } from 'boot/axios'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: localStorage.getItem('access_token') || null,
    refreshToken: localStorage.getItem('refresh_token') || null,
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    isEmployee: (state) => state.user?.role === 'employee',
    isSupervisor: (state) => state.user?.role === 'supervisor',
    isAdmin: (state) => state.user?.role === 'admin',
  },

  actions: {
    async login(email, password) {
      const response = await api.post('/auth/login/', { email, password })
      const { access, refresh, user } = response.data

      this.token = access
      this.refreshToken = refresh
      this.user = user

      localStorage.setItem('access_token', access)
      localStorage.setItem('refresh_token', refresh)

      if (user.password_reset_required) {
        return { firstLogin: true }
      }

      return { success: true }
    },

    async fetchUser() {
      if (this.token && !this.user) {
        try {
          const response = await api.get('/auth/me/')
          this.user = response.data
          return true
        } catch (error) {
          // If token is invalid or expired, logout will handle cleanup
          this.logout()
          return false
        }
      }
      return !!this.user
    },

    async refreshTokenAction() {
      try {
        const response = await api.post('/auth/token/refresh/', {
          refresh: this.refreshToken
        })
        this.token = response.data.access
        localStorage.setItem('access_token', response.data.access)
        return true
      } catch (error) {
        this.logout()
        return false
      }
    },

    async firstLoginPassword(newPassword, confirmPassword) {
      await api.post('/auth/initial-password-reset/', { new_password: newPassword, confirm_password: confirmPassword })
      if (this.user) {
        this.user.password_reset_required = false
      }
    },

    logout() {
      // Attempt to blacklist the refresh token on backend
      if (this.refreshToken) {
        api.post('/auth/logout/', { refresh: this.refreshToken }).catch(() => {
          // Continue with logout even if backend call fails
        })
      }

      this.user = null
      this.token = null
      this.refreshToken = null
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    },
  },
})