import { defineStore } from 'pinia'
import { api } from '../boot/axios'

export const useReportsStore = defineStore('reports', {
  state: () => ({
    reports: [],
    currentReport: null,
    loading: false,
    error: null,
    stats: {
      myReports: 0,
      pendingReview: 0,
      reviewed: 0,
      draft: 0
    },
    recentActivity: [],
    pagination: {
      count: 0,
      next: null,
      previous: null
    }
  }),

  getters: {
    myReports: (state) => state.reports.filter(r => r.status !== 'submitted'),
    pendingReports: (state) => state.reports.filter(r => r.status === 'submitted'),
    draftReports: (state) => state.reports.filter(r => r.status === 'draft'),
    reviewedReports: (state) => state.reports.filter(r => r.status === 'reviewed')
  },

  actions: {
    async fetchReports(endpoint = '/reports/') {
      this.loading = true
      this.error = null
      try {
        const response = await api.get(endpoint)
        if (response.data.results) {
          this.reports = response.data.results
          this.pagination = {
            count: response.data.count,
            next: response.data.next,
            previous: response.data.previous
          }
        } else {
          this.reports = response.data
        }
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to fetch reports'
        throw error
      } finally {
        this.loading = false
      }
    },

    async fetchMyReports() {
      // Backend: /reports/my-reports/ -> call as /reports/my-reports/
      return this.fetchReports('/reports/my-reports/')
    },

    async fetchPendingApproval() {
      // Backend: /reports/pending-approval/ -> call as /reports/pending-approval/
      return this.fetchReports('/reports/pending-approval/')
    },

    async fetchTeamReports() {
      // Backend: /reports/team-reports/ -> call as /reports/team-reports/
      return this.fetchReports('/reports/team-reports/')
    },

    async fetchAllReports() {
      // Backend: /reports/all-reports/ -> call as /reports/all-reports/
      return this.fetchReports('/reports/all-reports/')
    },

    async fetchEmployees() {
      try {
        // Backend: /auth/employees/ -> call as /auth/employees/
        const response = await api.get('/auth/employees/')
        return response.data
      } catch (error) {
        // Fallback: extract from reports
        const employees = new Map()
        this.reports.forEach(r => {
          if (r.user && r.user_name) {
            employees.set(r.user, r.user_name)
          }
        })
        return Array.from(employees.entries()).map(([id, name]) => ({ id, full_name: name }))
      }
    },

    async fetchReport(id) {
      this.loading = true
      try {
        const response = await api.get(`/reports/${id}/`)
        this.currentReport = response.data
        return response.data
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to fetch report'
        throw error
      } finally {
        this.loading = false
      }
    },

    async createReport(reportData) {
      try {
        const response = await api.post('/reports/', reportData)
        this.reports.unshift(response.data)
        return response.data
      } catch (error) {
        this.error = error.response?.data || 'Failed to create report'
        throw error
      }
    },

    async updateReport(id, reportData) {
      try {
        const response = await api.put(`/reports/${id}/`, reportData)
        const index = this.reports.findIndex(r => r.id === id)
        if (index !== -1) {
          this.reports[index] = response.data
        }
        return response.data
      } catch (error) {
        this.error = error.response?.data || 'Failed to update report'
        throw error
      }
    },

    async deleteReport(id) {
      try {
        await api.delete(`/reports/${id}/`)
        this.reports = this.reports.filter(r => r.id !== id)
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to delete report'
        throw error
      }
    },

    async submitReport(id) {
      try {
        const response = await api.post(`/reports/${id}/submit/`)
        const index = this.reports.findIndex(r => r.id === id)
        if (index !== -1) {
          this.reports[index].status = 'submitted'
          this.reports[index].submitted_at = new Date().toISOString()
        }
        return response.data
      } catch (error) {
        this.error = error.response?.data?.error || 'Failed to submit report'
        throw error
      }
    },

    async reviewReport(id) {
      try {
        await api.post(`/reports/${id}/review/`)
        this.fetchPendingApproval() // Refresh pending reports after review
      } catch (error) {
        this.error = error.response?.data?.error || 'Failed to review report'
        throw error
      }
    },

    async fetchDashboardStats() {
      this.loading = true
      try {
        const response = await api.get('/reports/dashboard-stats/')
        this.stats = response.data
        return response.data
      } catch (error) {
        // If endpoint doesn't exist, calculate from reports
        this.stats = {
          myReports: this.reports.length,
          pendingReview: this.reports.filter(r => r.status === 'submitted').length,
          reviewed: this.reports.filter(r => r.status === 'reviewed').length,
          draft: this.reports.filter(r => r.status === 'draft').length
        }
        return this.stats
      } finally {
        this.loading = false
      }
    },

    async fetchRecentActivity() {
      try {
        const response = await api.get('/reports/recent-activity/')
        this.recentActivity = response.data
        return response.data
      } catch (error) {
        // If endpoint doesn't exist, derive from reports
        this.recentActivity = this.reports.slice(0, 5).map(r => ({
          id: r.id,
          title: `Week ${r.week_number}/${r.year} Report`,
          date: r.updated_at || r.submitted_at || r.created_at,
          status: r.status,
          icon: this.getActivityIcon(r.status),
          color: this.getActivityColor(r.status)
        }))
        return this.recentActivity
      }
    },

    getActivityIcon(status) {
      const icons = {
        draft: 'edit',
        submitted: 'send',
        reviewed: 'check_circle'
      }
      return icons[status] || 'assignment'
    },

    getActivityColor(status) {
      const colors = {
        draft: 'grey',
        submitted: 'info',
        reviewed: 'positive'
      }
      return colors[status] || 'primary'
    },

    // Comments
    async fetchComments(reportId) {
      try {
        const response = await api.get(`/reports/${reportId}/comments/`)
        return response.data
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to fetch comments'
        throw error
      }
    },

    async addComment(reportId, comment) {
      try {
        const response = await api.post(`/reports/${reportId}/comments/`, { comment })
        return response.data
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to add comment'
        throw error
      }
    },

    async exportReports(type = 'csv', filters = {}) {
      try {
        const endpoint = type === 'csv' ? '/reports/export-csv/' : '/reports/export-pdf/'
        const response = await api.get(endpoint, {
          params: filters,
          responseType: 'blob'
        })

        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        const filename = `gridlog_reports_${new Date().toISOString().split('T')[0]}.${type}`
        link.setAttribute('download', filename)
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)
      } catch (error) {
        console.error(`Failed to export ${type}:`, error)
        throw error
      }
    },

    async fetchOrganizationStats() {
      try {
        const response = await api.get('/reports/organization-stats/')
        return response.data
      } catch (error) {
        console.error('Failed to fetch organization stats:', error)
        throw error
      }
    }
  }
})
