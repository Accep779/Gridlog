import { boot } from 'quasar/wrappers'
import axios from 'axios'
import { Notify, Loading, QSpinnerAudio } from 'quasar'

// API Configuration - requires environment variables
const API_URL = import.meta.env.VITE_API_URL
const API_PREFIX = import.meta.env.VITE_API_PREFIX || '/api/v1'

// Validate required environment variables
if (!API_URL) {
  throw new Error('VITE_API_URL environment variable is required. Add it to your .env file.')
}

const api = axios.create({ baseURL: `${API_URL}${API_PREFIX}` })

// Flag to prevent multiple simultaneous token refresh attempts
let isRefreshing = false
let failedQueue = []

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  failedQueue = []
}

// Request interceptor - adds auth token
api.interceptors.request.use(config => {
  // Show global loading state for all API requests
  Loading.show({
    spinner: QSpinnerAudio,
    spinnerColor: 'primary',
    messageColor: 'white',
    backgroundColor: 'dark',
    message: 'Processing Secure Request...',
    boxClass: 'bg-grey-9 text-white'
  })

  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  // Log request in development
  if (process.env.DEV) {
    console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`)
  }

  return config
}, error => {
  return Promise.reject(error)
})

// Response interceptor - handles errors and token refresh
api.interceptors.response.use(
  response => {
    Loading.hide()
    // Log response in development
    if (process.env.DEV) {
      console.log(`[API Response] ${response.status} ${response.config.url}`)
    }
    return response
  },
  async error => {
    Loading.hide()
    const originalRequest = error.config

    // Handle 401 - Token expired
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then(token => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            return api(originalRequest)
          })
          .catch(err => Promise.reject(err))
      }

      originalRequest._retry = true
      isRefreshing = true

      const refreshToken = localStorage.getItem('refresh_token')

      if (!refreshToken) {
        // No refresh token, force logout
        handleAuthError('Session expired. Please login again.')
        return Promise.reject(error)
      }

      try {
        const response = await axios.post(`${API_URL}${API_PREFIX}/auth/token/refresh/`, {
          refresh: refreshToken
        })

        const { access } = response.data
        localStorage.setItem('access_token', access)

        processQueue(null, access)
        originalRequest.headers.Authorization = `Bearer ${access}`

        return api(originalRequest)
      } catch (refreshError) {
        processQueue(refreshError, null)
        handleAuthError('Session expired. Please login again.')
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    // Handle other errors
    const errorMessage = error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      'An error occurred'

    // Don't show notification for 401 (already handled above)
    if (error.response?.status !== 401) {
      Notify.create({
        type: 'negative',
        message: errorMessage,
        icon: 'error',
        position: 'top-right',
        timeout: 5000,
        actions: [
          { icon: 'close', color: 'white' }
        ]
      })
    }

    // Log error in development
    if (process.env.DEV) {
      console.error(`[API Error] ${error.response?.status} ${error.config?.url}:`, errorMessage)
    }

    return Promise.reject(error)
  }
)

// Helper function for auth errors
function handleAuthError(message) {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')

  Notify.create({
    type: 'negative',
    message,
    icon: 'warning',
    position: 'top-right',
    timeout: 5000,
    actions: [
      { icon: 'close', color: 'white' }
    ]
  })

  // Redirect to login after a short delay
  setTimeout(() => {
    window.location.href = '/login'
  }, 1500)
}

export default boot(({ app }) => {
  app.config.globalProperties.$axios = axios
  app.config.globalProperties.$api = api
})

export { api }