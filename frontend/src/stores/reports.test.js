import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

// Use vi.hoisted to define mocks before hoisting
const { mockApi } = vi.hoisted(() => {
  return {
    mockApi: {
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn()
    }
  }
})

vi.mock('../../src/boot/axios', () => ({
  api: mockApi
}))

import { useReportsStore } from '../../src/stores/reports'

describe('Reports Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.clearAllMocks()
  })

  describe('initial state', () => {
    it('should have empty reports array', () => {
      const store = useReportsStore()
      expect(store.reports).toEqual([])
    })

    it('should have null currentReport initially', () => {
      const store = useReportsStore()
      expect(store.currentReport).toBeNull()
    })

    it('should have loading set to false', () => {
      const store = useReportsStore()
      expect(store.loading).toBe(false)
    })

    it('should have default stats', () => {
      const store = useReportsStore()
      expect(store.stats).toEqual({
        myReports: 0,
        pendingReview: 0,
        approved: 0,
        rejected: 0,
        draft: 0
      })
    })
  })

  describe('fetchReports', () => {
    it('should fetch reports successfully', async () => {
      const mockReports = [
        { id: 1, title: 'Report 1', status: 'draft' },
        { id: 2, title: 'Report 2', status: 'approved' }
      ]

      mockApi.get.mockResolvedValue({
        data: { results: mockReports, count: 2 }
      })

      const store = useReportsStore()
      await store.fetchReports()

      expect(store.reports).toEqual(mockReports)
      expect(store.loading).toBe(false)
    })

    it('should handle pagination response', async () => {
      mockApi.get.mockResolvedValue({
        data: {
          results: [{ id: 1 }],
          count: 100,
          next: '/api/v1/reports/?page=2',
          previous: null
        }
      })

      const store = useReportsStore()
      await store.fetchReports()

      expect(store.pagination.count).toBe(100)
      expect(store.pagination.next).toBe('/api/v1/reports/?page=2')
    })

    it('should handle fetch error', async () => {
      mockApi.get.mockRejectedValue({
        response: { data: { detail: 'Not found' } }
      })

      const store = useReportsStore()

      await expect(store.fetchReports()).rejects.toThrow()
      expect(store.error).toBe('Not found')
    })
  })

  describe('fetchDashboardStats', () => {
    it('should fetch stats from API', async () => {
      const mockStats = {
        myReports: 10,
        pendingReview: 2,
        approved: 5,
        rejected: 1,
        draft: 2
      }

      mockApi.get.mockResolvedValue({ data: mockStats })

      const store = useReportsStore()
      const result = await store.fetchDashboardStats()

      expect(store.stats).toEqual(mockStats)
      expect(result).toEqual(mockStats)
    })

    it('should calculate stats from reports if API fails', async () => {
      mockApi.get.mockRejectedValue({})

      const store = useReportsStore()
      store.reports = [
        { status: 'draft' },
        { status: 'draft' },
        { status: 'pending' },
        { status: 'approved' },
        { status: 'approved' },
        { status: 'approved' },
        { status: 'rejected' }
      ]

      const result = await store.fetchDashboardStats()

      expect(result.draft).toBe(2)
      expect(result.pendingReview).toBe(1)
      expect(result.approved).toBe(3)
      expect(result.rejected).toBe(1)
      expect(result.myReports).toBe(7)
    })
  })

  describe('fetchRecentActivity', () => {
    it('should fetch recent activity from API', async () => {
      const mockActivity = [
        { id: 1, title: 'Report 1', status: 'approved' }
      ]

      mockApi.get.mockResolvedValue({ data: mockActivity })

      const store = useReportsStore()
      await store.fetchRecentActivity()

      expect(store.recentActivity).toEqual(mockActivity)
    })

    it('should derive activity from reports if API fails', async () => {
      mockApi.get.mockRejectedValue({})

      const store = useReportsStore()
      store.reports = [
        { id: 1, week_number: 5, year: 2026, status: 'approved', updated_at: '2026-02-01' },
        { id: 2, week_number: 4, year: 2026, status: 'pending', submitted_at: '2026-01-25' }
      ]

      await store.fetchRecentActivity()

      expect(store.recentActivity).toHaveLength(2)
      expect(store.recentActivity[0].icon).toBe('check_circle')
      expect(store.recentActivity[1].icon).toBe('hourglass_empty')
    })
  })

  describe('CRUD operations', () => {
    it('should create a report', async () => {
      const newReport = { id: 1, title: 'New Report', status: 'draft' }
      mockApi.post.mockResolvedValue({ data: newReport })

      const store = useReportsStore()
      const result = await store.createReport({ title: 'New Report' })

      expect(store.reports).toHaveLength(1)
      expect(store.reports[0]).toEqual(newReport)
      expect(result).toEqual(newReport)
    })

    it('should update a report', async () => {
      const store = useReportsStore()
      store.reports = [{ id: 1, title: 'Old Title', status: 'draft' }]

      mockApi.put.mockResolvedValue({
        data: { id: 1, title: 'New Title', status: 'draft' }
      })

      await store.updateReport(1, { title: 'New Title' })

      expect(store.reports[0].title).toBe('New Title')
    })

    it('should delete a report', async () => {
      const store = useReportsStore()
      store.reports = [
        { id: 1, title: 'Report 1' },
        { id: 2, title: 'Report 2' }
      ]

      mockApi.delete.mockResolvedValue({})

      await store.deleteReport(1)

      expect(store.reports).toHaveLength(1)
      expect(store.reports[0].id).toBe(2)
    })
  })

  describe('workflow actions', () => {
    it('should submit a report', async () => {
      const store = useReportsStore()
      store.reports = [{ id: 1, title: 'Report', status: 'draft' }]

      mockApi.post.mockResolvedValue({ data: { id: 1, status: 'pending' } })

      await store.submitReport(1)

      expect(store.reports[0].status).toBe('pending')
    })

    it('should approve a report', async () => {
      const store = useReportsStore()
      store.reports = [{ id: 1, title: 'Report', status: 'pending' }]

      mockApi.post.mockResolvedValue({ data: { id: 1, status: 'approved' } })

      await store.approveReport(1)

      expect(store.reports[0].status).toBe('approved')
    })

    it('should reject a report with feedback', async () => {
      const store = useReportsStore()
      store.reports = [{ id: 1, title: 'Report', status: 'pending' }]

      mockApi.post.mockResolvedValue({ data: { id: 1, status: 'rejected' } })

      await store.rejectReport(1, 'Needs more detail')

      expect(store.reports[0].status).toBe('rejected')
      expect(store.reports[0].feedback).toBe('Needs more detail')
    })
  })

  describe('getters', () => {
    it('should filter pending reports', () => {
      const store = useReportsStore()
      store.reports = [
        { status: 'draft' },
        { status: 'pending' },
        { status: 'pending' }
      ]

      expect(store.pendingReports).toHaveLength(2)
    })

    it('should filter approved reports', () => {
      const store = useReportsStore()
      store.reports = [
        { status: 'draft' },
        { status: 'approved' },
        { status: 'approved' }
      ]

      expect(store.approvedReports).toHaveLength(2)
    })
  })

  describe('helper methods', () => {
    it('should return correct icon for status', () => {
      const store = useReportsStore()

      expect(store.getActivityIcon('draft')).toBe('edit')
      expect(store.getActivityIcon('pending')).toBe('hourglass_empty')
      expect(store.getActivityIcon('approved')).toBe('check_circle')
      expect(store.getActivityIcon('rejected')).toBe('reply')
    })

    it('should return correct color for status', () => {
      const store = useReportsStore()

      expect(store.getActivityColor('draft')).toBe('grey')
      expect(store.getActivityColor('pending')).toBe('warning')
      expect(store.getActivityColor('approved')).toBe('positive')
      expect(store.getActivityColor('rejected')).toBe('negative')
    })
  })
})
