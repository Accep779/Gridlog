import { defineStore } from 'pinia'
import { api } from 'boot/axios'

export const useAdminStore = defineStore('admin', {
    state: () => ({
        employees: [],
        auditLogs: [],
        periods: [],
        loading: false,
        error: null
    }),

    actions: {
        async fetchEmployees() {
            try {
                this.loading = true
                // Backend: /api/v1/auth/employees/ -> call as /auth/employees/
                const response = await api.get('/auth/employees/')
                this.employees = response.data
            } catch (error) {
                this.error = error.response?.data?.detail || 'Failed to fetch employees'
                throw error
            } finally {
                this.loading = false
            }
        },

        async fetchAuditLogs() {
            try {
                this.loading = true
                // Backend: /api/v1/auth/audit-logs/ -> call as /auth/audit-logs/
                const response = await api.get('/auth/audit-logs/')
                this.auditLogs = response.data
            } catch (error) {
                this.error = error.response?.data?.detail || 'Failed to fetch audit logs'
                throw error
            } finally {
                this.loading = false
            }
        },

        async fetchPeriods() {
            try {
                this.loading = true
                // Backend: /api/v1/reports/periods/ -> call as /reports/periods/
                const response = await api.get('/reports/periods/')
                this.periods = response.data.results || response.data
            } catch (error) {
                this.error = error.response?.data?.detail || 'Failed to fetch periods'
                throw error
            } finally {
                this.loading = false
            }
        },

        async createPeriod(periodData) {
            try {
                // Backend: /api/v1/reports/periods/ -> call as /reports/periods/
                const response = await api.post('/reports/periods/', periodData)
                this.periods.unshift(response.data)
                return response.data
            } catch (error) {
                this.error = error.response?.data?.detail || 'Failed to create period'
                throw error
            }
        },

        async closePeriod(id) {
            try {
                // Backend: /api/v1/reports/periods/{id}/close/ -> call as /reports/periods/{id}/close/
                const response = await api.post(`/reports/periods/${id}/close/`)
                const index = this.periods.findIndex(p => p.id === id)
                if (index !== -1) {
                    this.periods[index] = response.data
                }
                return response.data
            } catch (error) {
                this.error = error.response?.data?.detail || 'Failed to close period'
                throw error
            }
        }
    }
})
