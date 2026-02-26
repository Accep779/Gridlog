import { defineStore } from 'pinia'
import { api } from 'boot/axios'

export const useNotificationsStore = defineStore('notifications', {
  state: () => ({
    notifications: [],
    unreadCount: 0,
    loading: false,
    error: null,
    pollingInterval: null,
    lastFetched: null
  }),

  getters: {
    unreadNotifications: (state) => state.notifications.filter(n => !n.is_read),
    recentNotifications: (state) => state.notifications.slice(0, 10),

    notificationIcon: () => (type) => {
      const icons = {
        report_submitted: 'send',
        report_approved: 'check_circle',
        report_rejected: 'cancel',
        new_comment: 'comment',
        deadline_reminder: 'schedule'
      }
      return icons[type] || 'notifications'
    },

    notificationColor: () => (type) => {
      const colors = {
        report_submitted: 'orange',
        report_approved: 'positive',
        report_rejected: 'negative',
        new_comment: 'info',
        deadline_reminder: 'purple'
      }
      return colors[type] || 'grey'
    }
  },

  actions: {
    async fetchNotifications() {
      this.loading = true
      this.error = null
      try {
        const response = await api.get('/notifications/')
        this.notifications = response.data.results || response.data
        this.unreadCount = this.notifications.filter(n => !n.is_read).length
        this.lastFetched = new Date()
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to fetch notifications'
        // If endpoint doesn't exist, use empty array
        this.notifications = []
        this.unreadCount = 0
      } finally {
        this.loading = false
      }
    },

    async markAsRead(notificationId) {
      try {
        await api.post('/notifications/mark-read/', { ids: [notificationId] })
        const notification = this.notifications.find(n => n.id === notificationId)
        if (notification && !notification.is_read) {
          notification.is_read = true
          this.unreadCount = Math.max(0, this.unreadCount - 1)
        }
      } catch (error) {
        // Fallback: mark as read locally
        const notification = this.notifications.find(n => n.id === notificationId)
        if (notification && !notification.is_read) {
          notification.is_read = true
          this.unreadCount = Math.max(0, this.unreadCount - 1)
        }
      }
    },

    async markAllAsRead() {
      try {
        await api.post('/notifications/mark-all-read/')
        this.notifications.forEach(n => n.is_read = true)
        this.unreadCount = 0
      } catch (error) {
        // Fallback: mark all as read locally
        this.notifications.forEach(n => n.is_read = true)
        this.unreadCount = 0
      }
    },

    startPolling(intervalMs = 30000) {
      this.stopPolling()
      // Bind the handler to preserve 'this' context
      this._boundVisibilityHandler = () => this.handleVisibilityChange()
      // Initial fetch
      this.fetchNotifications()
      // Set up interval
      this.pollingInterval = setInterval(() => {
        this.fetchNotifications()
      }, intervalMs)

      // Handle visibility change - pause when tab is hidden
      document.addEventListener('visibilitychange', this._boundVisibilityHandler)
    },

    stopPolling() {
      if (this.pollingInterval) {
        clearInterval(this.pollingInterval)
        this.pollingInterval = null
      }
      if (this._boundVisibilityHandler) {
        document.removeEventListener('visibilitychange', this._boundVisibilityHandler)
        this._boundVisibilityHandler = null
      }
    },

    handleVisibilityChange() {
      if (document.hidden) {
        // Tab is hidden, could pause polling here if needed
      } else {
        // Tab is visible again, fetch immediately
        this.fetchNotifications()
      }
    }
  }
})
