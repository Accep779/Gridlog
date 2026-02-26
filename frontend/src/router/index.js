import { createRouter, createMemoryHistory, createWebHistory, createWebHashHistory } from 'vue-router'
import routes from './routes'
import { useAuthStore } from 'stores/auth'

export default function (/* { store, ssrContext } */) {
  const createHistory = process.env.SERVER
    ? createMemoryHistory
    : process.env.VUE_ROUTER_MODE === 'history'
      ? createWebHistory
      : createWebHashHistory

  const Router = createRouter({
    scrollBehavior: () => ({ left: 0, top: 0 }),
    routes,
    history: createHistory(process.env.VUE_ROUTER_BASE),
  })

  // Enable auth and role-based guards
  Router.beforeEach(async (to, from, next) => {
    const authStore = useAuthStore()

    if (authStore.token && !authStore.user) {
      await authStore.fetchUser()
    }

    // Check authentication
    const token = authStore.token
    const userRole = authStore.user?.role
    const isFirstLogin = authStore.user?.is_first_login || authStore.user?.password_reset_required

    const requiresAuth = to.matched.some(record => record.meta.requiresAuth !== false)

    // Redirect to login if auth required and no token
    if (requiresAuth && !token) {
      return next('/login')
    }

    // Force password reset flow
    if (requiresAuth && isFirstLogin && to.path !== '/first-login') {
      return next('/first-login')
    }

    // Prevent access to /first-login if not required
    if (to.path === '/first-login' && !isFirstLogin && token) {
      return next('/dashboard')
    }

    // Redirect to dashboard if already logged in and trying to access login
    if (to.path === '/login' && token) {
      return next('/dashboard')
    }

    // Check role-based access
    const requiredRoles = to.meta.roles
    const requiresAdmin = to.meta.requiresAdmin
    const requiresEmployee = to.meta.requiresEmployee

    // If route has role restrictions
    if (requiredRoles && requiredRoles.length > 0) {
      if (!userRole || !requiredRoles.includes(userRole)) {
        // User doesn't have required role - redirect to dashboard (or login if already going to dashboard)
        if (to.path !== '/dashboard') {
          return next('/dashboard')
        } else {
          return next('/login')
        }
      }
    }

    // Admin-only routes
    if (requiresAdmin) {
      if (userRole !== 'admin') {
        if (to.path !== '/dashboard') return next('/dashboard')
        return next('/')
      }
    }

    // Employee-only routes (e.g., create new report)
    if (requiresEmployee) {
      if (userRole !== 'employee') {
        if (to.path !== '/dashboard') return next('/dashboard')
        return next('/')
      }
    }

    next()
  })

  return Router
}