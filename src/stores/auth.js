import { defineStore } from 'pinia'
import { api } from 'boot/axios'

// TEMP: Mock user for testing without backend
const TEMP_MOCK_USER = {
  id: 1,
  email: 'test@gridlog.com',
  full_name: 'Test User',
  role: 'supervisor',
  is_first_login: false,
  avatar: null
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: TEMP_MOCK_USER, // Set mock user by default for testing
    token: localStorage.getItem('access_token') || 'mock-token-for-testing',
    refreshToken: localStorage.getItem('refresh_token'),
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
      
      if (user.is_first_login) {
        return { firstLogin: true }
      }
      
      return { success: true }
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
      this.user.is_first_login = false
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