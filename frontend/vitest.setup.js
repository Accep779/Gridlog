import { beforeAll, vi } from 'vitest'

// Mock Quasar
vi.mock('quasar', () => ({
  Notify: {
    create: vi.fn()
  },
  Dialog: {
    create: vi.fn(() => ({
      onOk: vi.fn(),
      onCancel: vi.fn()
    }))
  },
  Loading: {
    show: vi.fn(),
    hide: vi.fn()
  }
}))

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
}
global.localStorage = localStorageMock

// Mock window.location
delete window.location
window.location = {
  href: '',
  pathname: ''
}
