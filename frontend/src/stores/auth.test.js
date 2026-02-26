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

import { useAuthStore } from '../../src/stores/auth'

describe('Auth Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.clearAllMocks()
  })

  describe('initial state', () => {
    it('should have null user initially', () => {
      const store = useAuthStore()
      expect(store.user).toBeNull()
    })

    it('should not be authenticated initially', () => {
      const store = useAuthStore()
      expect(store.isAuthenticated).toBe(false)
    })

    it('should not be admin initially', () => {
      const store = useAuthStore()
      expect(store.isAdmin).toBe(false)
    })
  })

  describe('login', () => {
    it('should set user data on successful login', async () => {
      const mockUser = {
        id: 1,
        email: 'test@example.com',
        role: 'employee',
        full_name: 'Test User',
        is_first_login: false
      }

      mockApi.post.mockResolvedValue({
        data: {
          access: 'access-token',
          refresh: 'refresh-token',
          user: mockUser
        }
      })

      const store = useAuthStore()
      const result = await store.login('test@example.com', 'password')

      expect(store.token).toBe('access-token')
      expect(store.refreshToken).toBe('refresh-token')
      expect(store.user).toEqual(mockUser)
      expect(result).toEqual({ success: true })
    })

    it('should return firstLogin flag when user is on first login', async () => {
      const mockUser = {
        id: 1,
        email: 'test@example.com',
        role: 'employee',
        full_name: 'Test User',
        is_first_login: true
      }

      mockApi.post.mockResolvedValue({
        data: {
          access: 'access-token',
          refresh: 'refresh-token',
          user: mockUser
        }
      })

      const store = useAuthStore()
      const result = await store.login('test@example.com', 'password')

      expect(result).toEqual({ firstLogin: true })
    })

    it('should handle login failure', async () => {
      mockApi.post.mockRejectedValue({
        response: { data: { detail: 'Invalid credentials' } }
      })

      const store = useAuthStore()

      await expect(store.login('test@example.com', 'wrongpassword'))
        .rejects.toEqual(expect.objectContaining({
          response: { data: { detail: 'Invalid credentials' } }
        }))
    })
  })

  describe('logout', () => {
    it('should clear user data and tokens on logout', async () => {
      const store = useAuthStore()

      // Set some state
      store.user = { id: 1, name: 'Test' }
      store.token = 'some-token'
      store.refreshToken = 'some-refresh'

      store.logout()

      expect(store.user).toBeNull()
      expect(store.token).toBeNull()
      expect(store.refreshToken).toBeNull()
    })
  })

  describe('role getters', () => {
    it('should correctly identify employee role', () => {
      const store = useAuthStore()
      store.user = { role: 'employee' }

      expect(store.isEmployee).toBe(true)
      expect(store.isSupervisor).toBe(false)
      expect(store.isAdmin).toBe(false)
    })

    it('should correctly identify supervisor role', () => {
      const store = useAuthStore()
      store.user = { role: 'supervisor' }

      expect(store.isEmployee).toBe(false)
      expect(store.isSupervisor).toBe(true)
      expect(store.isAdmin).toBe(false)
    })

    it('should correctly identify admin role', () => {
      const store = useAuthStore()
      store.user = { role: 'admin' }

      expect(store.isEmployee).toBe(false)
      expect(store.isSupervisor).toBe(false)
      expect(store.isAdmin).toBe(true)
    })
  })

  describe('refreshTokenAction', () => {
    it('should update access token on successful refresh', async () => {
      const store = useAuthStore()
      store.refreshToken = 'old-refresh'

      mockApi.post.mockResolvedValue({
        data: { access: 'new-access-token' }
      })

      const result = await store.refreshTokenAction()

      expect(result).toBe(true)
      expect(store.token).toBe('new-access-token')
    })

    it('should logout on failed refresh', async () => {
      const store = useAuthStore()
      store.refreshToken = 'invalid-refresh'
      store.user = { id: 1 }

      mockApi.post.mockRejectedValue({})

      const result = await store.refreshTokenAction()

      expect(result).toBe(false)
      expect(store.user).toBeNull()
    })
  })
})
