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
  Router.beforeEach((to, from, next) => {
    // Check authentication
    const token = localStorage.getItem('access_token')
    const authStore = useAuthStore()
    const userRole = authStore.user?.role || authStore.user?.role

    const requiresAuth = to.matched.some(record => record.meta.requiresAuth !== false)

    // Redirect to login if auth required and no token
    if (requiresAuth && !token) {
      return next('/login')
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
        // User doesn't have required role - redirect to dashboard
        return next('/dashboard')
      }
    }

    // Admin-only routes
    if (requiresAdmin) {
      if (userRole !== 'admin') {
        return next('/dashboard')
      }
    }

    // Employee-only routes (e.g., create new report)
    if (requiresEmployee) {
      if (userRole !== 'employee') {
        return next('/dashboard')
      }
    }

    next()
  })

  return Router
}