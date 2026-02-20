<template>
  <q-layout view="lHh Lpr lFf" class="app-layout">
    <!-- Sidebar - Fixed Spine -->
    <q-drawer
      v-model="leftDrawerOpen"
      :width="sidebarWidth"
      :mini="sidebarCollapsed"
      :mini-width="SIDEBAR_COLLAPSED"
      :breakpoint="1024"
      bordered
      class="sidebar-spine"
      :behavior="'desktop'"
    >
      <q-scroll-area class="fit">
        <!-- Sidebar Brand Archive -->
        <div class="sidebar-brand-container q-pa-md" :class="{ 'mini': sidebarCollapsed }">
          <div class="sidebar-brand row items-center no-wrap" :class="{ 'justify-center': sidebarCollapsed }">
            <div class="logo-icon" :class="{ 'mini': sidebarCollapsed }" @click="toggleSidebar" style="cursor: pointer">
              <q-icon name="grid_view" size="28px" class="premium-icon" />
            </div>
            <div class="logo-text text-weight-bold text-h6 q-ml-sm" v-if="!sidebarCollapsed">
              Gridlog
            </div>
          </div>
        </div>

        <q-list class="nav-list" :class="{ 'mini': sidebarCollapsed }">
          <!-- MAIN Section -->
          <div v-if="!sidebarCollapsed" class="nav-section-header">Core Intelligence</div>
          <q-item
            clickable
            v-ripple
            :to="{ path: '/dashboard' }"
            exact
            active-class="nav-item-active"
            class="nav-item"
          >
            <q-item-section avatar>
              <q-icon name="dashboard" />
              <q-tooltip v-if="sidebarCollapsed" anchor="center right" self="center left">Dashboard</q-tooltip>
            </q-item-section>
            <q-item-section v-if="!sidebarCollapsed">Command Center</q-item-section>
          </q-item>

          <!-- OPERATIONS Section -->
          <div class="nav-section-header" v-if="!sidebarCollapsed">Operations</div>
          <q-item
            clickable
            v-ripple
            :to="{ path: '/reports' }"
            active-class="nav-item-active"
            class="nav-item"
          >
            <q-item-section avatar>
              <q-icon name="assignment" />
              <q-tooltip v-if="sidebarCollapsed" anchor="center right" self="center left">Weekly Reports</q-tooltip>
            </q-item-section>
            <q-item-section v-if="!sidebarCollapsed">Weekly Reports</q-item-section>
          </q-item>

          <!-- Create Report - Employee Only -->
          <q-item
            v-if="isEmployee"
            clickable
            v-ripple
            :to="{ path: '/reports/new' }"
            active-class="nav-item-active"
            class="nav-item"
          >
            <q-item-section avatar>
              <q-icon name="add_circle" />
              <q-tooltip v-if="sidebarCollapsed" anchor="center right" self="center left">Create Report</q-tooltip>
            </q-item-section>
            <q-item-section v-if="!sidebarCollapsed">Create Report</q-item-section>
          </q-item>

          <!-- MANAGEMENT Section -->
          <div v-if="(isAdmin || isSupervisor) && !sidebarCollapsed" class="nav-section-header">Management</div>
          <q-item
            v-if="isAdmin || isSupervisor"
            clickable
            v-ripple
            :to="{ path: '/users' }"
            active-class="nav-item-active"
            class="nav-item"
          >
            <q-item-section avatar>
              <q-icon name="people" />
              <q-tooltip v-if="sidebarCollapsed" anchor="center right" self="center left">Team Oversight</q-tooltip>
            </q-item-section>
            <q-item-section v-if="!sidebarCollapsed">Team Oversight</q-item-section>
          </q-item>

          <q-item
            v-if="isAdmin"
            clickable
            v-ripple
            :to="{ path: '/audit-log' }"
            active-class="nav-item-active"
            class="nav-item"
          >
            <q-item-section avatar>
              <q-icon name="history" />
              <q-tooltip v-if="sidebarCollapsed" anchor="center right" self="center left">Audit Intelligence</q-tooltip>
            </q-item-section>
            <q-item-section v-if="!sidebarCollapsed">Audit Intelligence</q-item-section>
          </q-item>
        </q-list>

        <!-- Bottom Section - Quick Stats & Profile -->
        <div class="sidebar-footer" :class="{ 'mini': sidebarCollapsed }">
          <div class="quick-stats" v-if="!sidebarCollapsed">
            <div class="stat-item">
              <span class="stat-value">{{ stats.myReports }}</span>
              <span class="stat-label">My Reports</span>
            </div>
            <div class="stat-item">
              <span class="stat-value text-warning">{{ stats.pendingReview }}</span>
              <span class="stat-label">Pending</span>
            </div>
          </div>
          
          <q-separator class="q-my-sm bg-grey-3" v-if="!sidebarCollapsed" />
          
          <div class="user-profile-sidebar" :class="{ 'q-pa-sm': !sidebarCollapsed, 'text-center': sidebarCollapsed }">
            <div class="row items-center no-wrap" :class="{ 'justify-center': sidebarCollapsed }">
              <q-avatar :size="sidebarCollapsed ? '32px' : '40px'" class="user-avatar shadow-sm cursor-pointer" @click="sidebarCollapsed = false">
                <img v-if="userAvatar" :src="userAvatar" />
                <span v-else class="avatar-initials">{{ userInitials }}</span>
                <q-menu v-if="sidebarCollapsed">
                  <q-list style="min-width: 150px">
                    <q-item>
                      <q-item-section>
                        <q-item-label class="text-weight-bold">{{ userName }}</q-item-label>
                        <q-item-label caption>{{ userEmail }}</q-item-label>
                      </q-item-section>
                    </q-item>
                    <q-separator />
                    <q-item clickable v-close-popup @click="logout">
                      <q-item-section avatar><q-icon name="logout" /></q-item-section>
                      <q-item-section>Logout</q-item-section>
                    </q-item>
                  </q-list>
                </q-menu>
              </q-avatar>
              
              <div class="user-info q-ml-md" v-if="!sidebarCollapsed">
                <div class="text-weight-bold text-subtitle2 truncate-text">{{ userName }}</div>
                <div class="text-caption text-grey-6 truncate-text">{{ userEmail }}</div>
              </div>
              
              <q-space v-if="!sidebarCollapsed" />
              
              <q-btn v-if="!sidebarCollapsed" flat round dense icon="logout" color="grey-7" @click="logout" size="sm">
                <q-tooltip>Logout</q-tooltip>
              </q-btn>
            </div>
          </div>
        </div>
      </q-scroll-area>
    </q-drawer>

    <!-- Header - Dynamic position based on sidebar -->
    <q-header
      elevated
      class="header-glass text-dark"
      :style="headerStyle"
    >
      <q-toolbar class="q-py-sm">
        <!-- Hamburger Menu / Sidebar Toggle -->
        <q-btn
          dense
          flat
          round
          :icon="menuIcon"
          @click="toggleSidebar"
          class="menu-toggle"
        />

        <q-breadcrumbs class="breadcrumb-nav q-ml-md" gutter="sm" v-if="!$q.screen.lt.sm">
          <template v-slot:separator>
            <q-icon
              size="1em"
              name="chevron_right"
              color="grey-4"
            />
          </template>
          <q-breadcrumbs-el 
            v-for="crumb in breadcrumbs" 
            :key="crumb.path"
            :icon="crumb.icon"
            :to="crumb.to"
            class="breadcrumb-item"
            :class="{ 'breadcrumb-active': crumb.active }"
          >
            <span class="q-ml-xs">{{ crumb.label }}</span>
          </q-breadcrumbs-el>
        </q-breadcrumbs>

        <q-space />


        <!-- Right Section -->
        <div class="row items-center q-gutter-sm">
          <!-- Theme Toggle -->
          <q-btn
            dense
            flat
            round
            :icon="$q.dark.isActive ? 'light_mode' : 'dark_mode'"
            @click="toggleDarkMode"
            class="theme-toggle-btn"
          >
            <q-tooltip>{{ $q.dark.isActive ? 'Switch to Light Mode' : 'Switch to Dark Mode' }}</q-tooltip>
          </q-btn>

          <!-- Notification Bell - Linear Style -->
          <q-btn dense flat round icon="notifications" class="notification-btn">
            <q-badge
              color="negative"
              floating
              rounded
              v-if="unreadCount > 0"
              class="notification-badge"
            >
              {{ unreadCount > 9 ? '9+' : unreadCount }}
            </q-badge>
            <q-menu
              v-model="notificationMenuOpen"
              anchor="bottom right"
              self="top right"
              class="notification-menu"
            >
              <div class="notification-header row items-center justify-between q-pa-md">
                <div class="text-subtitle1 text-weight-bold">Notifications</div>
                <q-btn
                  v-if="unreadCount > 0"
                  flat
                  dense
                  size="sm"
                  label="Mark all read"
                  color="primary"
                  @click="notificationsStore.markAllAsRead()"
                />
              </div>

              <q-separator />

              <q-list style="max-height: 400px; overflow-y: auto" class="notification-list">
                <template v-if="recentNotifications.length > 0">
                  <q-item
                    v-for="notification in recentNotifications"
                    :key="notification.id"
                    clickable
                    :to="notification.report_id ? `/reports/${notification.report_id}` : undefined"
                    v-close-popup
                    @click="notificationsStore.markAsRead(notification.id)"
                    :class="['notification-item', { 'unread': !notification.is_read }]"
                  >
                    <q-item-section avatar>
                      <q-avatar
                        :color="notificationsStore.notificationColor(notification.type)"
                        text-color="white"
                        size="md"
                        class="notification-avatar"
                      >
                        <q-icon
                          :name="notificationsStore.notificationIcon(notification.type)"
                          size="sm"
                        />
                      </q-avatar>
                    </q-item-section>
                    <q-item-section>
                      <q-item-label
                        :class="['notification-title', { 'text-weight-bold': !notification.is_read }]"
                      >
                        {{ notification.title }}
                      </q-item-label>
                      <q-item-label caption lines="2" class="notification-message">
                        {{ notification.message }}
                      </q-item-label>
                      <q-item-label caption class="notification-time">
                        {{ formatTimeAgo(notification.created_at) }}
                      </q-item-label>
                    </q-item-section>
                    <q-item-section side v-if="!notification.is_read">
                      <div class="unread-dot"></div>
                    </q-item-section>
                  </q-item>
                </template>
                <q-item v-else class="empty-notifications">
                  <q-item-section class="text-center text-grey-6 q-pa-md">
                    <q-icon name="notifications_none" size="2rem" class="q-mb-sm" />
                    <div>No notifications</div>
                  </q-item-section>
                </q-item>
              </q-list>
            </q-menu>
          </q-btn>

          <!-- Role Badge -->
          <q-badge
            v-if="userRole"
            :color="roleBadgeColor"
            class="role-badge"
            rounded
          >
            {{ userRole }}
          </q-badge>
        </div>
      </q-toolbar>
    </q-header>

    <!-- Main Content -->
    <q-page-container>
      <!-- Atmospheric Background -->
      <div class="page-atmosphere">
        <div class="atmosphere-orb atmosphere-orb--1"></div>
        <div class="atmosphere-orb atmosphere-orb--2"></div>
      </div>
      <router-view v-slot="{ Component }">
        <transition name="page-fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </q-page-container>
  </q-layout>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useQuasar } from 'quasar'
import { useAuthStore } from 'stores/auth'
import { useNotificationsStore } from 'stores/notifications'
import { useReportsStore } from 'stores/reports'

const router = useRouter()
const route = useRoute()
const $q = useQuasar()
const authStore = useAuthStore()
const notificationsStore = useNotificationsStore()
const reportsStore = useReportsStore()

const leftDrawerOpen = ref(true)
const notificationMenuOpen = ref(false)
const windowWidth = ref(window.innerWidth)

// Sidebar width constants
const SIDEBAR_EXPANDED = 220
const SIDEBAR_COLLAPSED = 60
const MOBILE_BREAKPOINT = 1024

// Sidebar collapse state
const sidebarCollapsed = ref(false)

// Mobile detection
const isMobile = computed(() => windowWidth.value < MOBILE_BREAKPOINT)

// Menu icon based on state
const menuIcon = computed(() => {
  if (isMobile.value) {
    return leftDrawerOpen.value ? 'menu_open' : 'menu'
  }
  return sidebarCollapsed.value ? 'chevron_right' : 'chevron_left'
})

// Breadcrumbs Logic
const breadcrumbs = computed(() => {
  const path = route.path
  const parts = path.split('/').filter(p => p)
  const crumbs = [
    { label: 'Intelligence', icon: 'grid_view', to: '/dashboard', active: path === '/dashboard' }
  ]

  if (parts.length > 0 && parts[0] === 'reports') {
    crumbs.push({ label: 'Weekly Reports', icon: 'assignment', to: '/reports', active: parts.length === 1 })
    if (parts.length > 1) {
      if (parts[1] === 'new') {
        crumbs.push({ label: 'New Entry', icon: 'add', active: true })
      } else if (parts[2] === 'edit') {
        crumbs.push({ label: 'Edit Report', icon: 'edit', active: true })
      } else {
        crumbs.push({ label: 'Report Detail', icon: 'visibility', active: true })
      }
    }
  } else if (parts.length > 0 && parts[0] === 'users') {
    crumbs.push({ label: 'Team Members', icon: 'people', to: '/users', active: true })
  } else if (parts.length > 0 && parts[0] === 'audit-log') {
    crumbs.push({ label: 'Audit Intelligence', icon: 'history', to: '/audit-log', active: true })
  }

  return crumbs
})

// Dynamic sidebar width based on collapse state
const sidebarWidth = computed(() => {
  if (isMobile.value) {
    return SIDEBAR_EXPANDED // Always full width on mobile
  }
  return sidebarCollapsed.value ? SIDEBAR_COLLAPSED : SIDEBAR_EXPANDED
})

// Header styles - dynamic based on sidebar
const headerStyle = computed(() => {
  if (isMobile.value) {
    return {
      left: '0px',
      width: '100%'
    }
  }
  return {
    left: `${sidebarWidth.value}px`,
    width: `calc(100% - ${sidebarWidth.value}px)`
  }
})

// Toggle sidebar (mobile: open/close, desktop: collapse/expand)
function toggleSidebar() {
  if (isMobile.value) {
    leftDrawerOpen.value = !leftDrawerOpen.value
  } else {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }
}

// Handle window resize
function handleResize() {
  windowWidth.value = window.innerWidth
  // On mobile, ensure sidebar is handled properly
  if (isMobile.value && !leftDrawerOpen.value) {
    leftDrawerOpen.value = true
  }
}

// Computed
const userRole = computed(() => authStore.user?.role)
const userName = computed(() => authStore.user?.full_name || 'User')
const userEmail = computed(() => authStore.user?.email || '')
const userAvatar = computed(() => {
  if (authStore.user?.avatar) return authStore.user.avatar
  const name = encodeURIComponent(authStore.user?.full_name || 'User')
  return `https://ui-avatars.com/api/?name=${name}&background=6366F1&color=fff&bold=true`
})
const userInitials = computed(() => {
  const name = authStore.user?.full_name || 'U'
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
})
const isAdmin = computed(() => authStore.isAdmin)
const isEmployee = computed(() => authStore.isEmployee)
const isSupervisor = computed(() => authStore.isSupervisor)

const stats = computed(() => reportsStore.stats)

const roleBadgeColor = computed(() => {
  const colors = {
    employee: 'grey-5',
    supervisor: 'primary',
    admin: 'accent'
  }
  return colors[authStore.user?.role] || 'grey'
})

// Notifications
const unreadCount = computed(() => notificationsStore.unreadCount)
const recentNotifications = computed(() => notificationsStore.recentNotifications)

// Lifecycle
onMounted(() => {
  window.addEventListener('resize', handleResize)
  
  // Theme initialization
  const savedTheme = localStorage.getItem('darkMode')
  if (savedTheme !== null) {
    $q.dark.set(savedTheme === 'true')
  } else {
    // Default to light mode for "Blue Intelligence" theme
    $q.dark.set(false)
  }

  if (authStore.isAuthenticated) {
    notificationsStore.startPolling(30000)
    reportsStore.fetchDashboardStats()
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  notificationsStore.stopPolling()
})

// Methods
function toggleLeftDrawer() {
  leftDrawerOpen.value = !leftDrawerOpen.value
}

function toggleDarkMode() {
  $q.dark.toggle()
  localStorage.setItem('darkMode', $q.dark.isActive)
}

function logout() {
  authStore.logout()
  notificationsStore.stopPolling()
  router.push('/login')
}

function formatTimeAgo(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  const now = new Date()
  const seconds = Math.floor((now - date) / 1000)

  if (seconds < 60) return 'Just now'
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`
  return date.toLocaleDateString()
}
</script>

<style lang="scss" scoped>
// Layout
.app-layout {
  background: var(--color-bg);
}

// Page Atmosphere - Background effects
.page-atmosphere {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 0;
  overflow: hidden;
}

.atmosphere-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.5;

  &--1 {
    width: 600px;
    height: 600px;
    top: -200px;
    right: -100px;
    background: radial-gradient(circle, rgba(99, 102, 241, 0.12) 0%, transparent 70%);
  }

  &--2 {
    width: 400px;
    height: 400px;
    bottom: -100px;
    left: -100px;
    background: radial-gradient(circle, rgba(139, 92, 246, 0.08) 0%, transparent 70%);
  }
}

// Header - Dynamic position based on sidebar width
.header-glass {
  background: rgba(var(--color-surface-rgb), 0.98) !important;
  backdrop-filter: blur(12px);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  transition: left 0.3s cubic-bezier(0.4, 0, 0.2, 1), width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border-bottom: 1px solid var(--color-border-light);
}

.menu-toggle {
  transition: background var(--transition-fast);

  &:hover {
    background: rgba(99, 102, 241, 0.08);
  }
}


// Notification
.notification-btn {
  position: relative;

  .notification-badge {
    font-size: 10px;
    min-width: 18px;
    height: 18px;
    padding: 0 5px;
  }
}

.notification-menu {
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
  border: 1px solid var(--color-border-light);
  overflow: hidden;
}

.notification-header {
  min-width: 320px;
}

.notification-list {
  .notification-item {
    transition: background var(--transition-fast);
    border-left: 3px solid transparent;
    padding: 12px 16px;

    &.unread {
      background: rgba(99, 102, 241, 0.04);
      border-left-color: var(--color-primary);
    }

    &:hover {
      background: rgba(99, 102, 241, 0.06);
    }
  }

  .notification-avatar {
    font-size: 12px;
  }

  .notification-title {
    font-size: 14px;
    color: var(--color-text-primary);
  }

  .notification-message {
    color: var(--color-text-secondary);
    margin-top: 2px;
  }

  .notification-time {
    color: var(--color-text-tertiary);
    font-size: 11px;
    margin-top: 4px;
  }

  .unread-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--color-primary);
  }

  .empty-notifications {
    padding: 32px;
    color: var(--color-text-tertiary);
  }
}

// Role Badge
.role-badge {
  padding: 4px 12px;
  font-size: 11px;
  font-weight: 600;
  text-transform: capitalize;
}

// User Avatar
.user-avatar {
  border: 2px solid var(--color-surface);
  box-shadow: var(--shadow-sm);
  cursor: pointer;
  transition: transform var(--transition-fast);

  &:hover {
    transform: scale(1.05);
  }

  .avatar-initials {
    font-size: 13px;
    font-weight: 600;
    color: white;
    background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
  }
}

// User Menu
.user-menu-btn {
  margin-left: 4px;
}

// Sidebar - Glass White Theme
.sidebar-spine {
  background: rgba(255, 255, 255, 0.95) !important;
  backdrop-filter: blur(20px);
  border-right: 1px solid var(--color-border-light) !important;
  z-index: 10;
  overflow: visible !important;
  opacity: 1 !important;
  box-shadow: 4px 0 24px rgba(0, 0, 0, 0.04);

  // Remove any overlay effects
  &.q-drawer--mini {
    .q-scrollarea {
      opacity: 1 !important;
    }
  }

  // Make sure scroll area is visible
  :deep(.q-scrollarea) {
    background: transparent;
    opacity: 1 !important;
  }

  :deep(.q-scrollarea__container),
  :deep(.q-scrollarea__content) {
    background: transparent;
    opacity: 1 !important;
  }

  .nav-header {
    display: none;
  }
}

// Sidebar Footer - Glass White Style
.sidebar-footer {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  border-top: 1px solid var(--color-border-light);
  background: rgba(var(--color-bg-rgb), 0.9);
  backdrop-filter: blur(12px);
  padding: 12px;
  transition: all var(--transition-base);

  &.mini {
    padding: 16px 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }

  .quick-stats {
    display: flex;
    gap: 8px;
    margin-bottom: 8px;
  }

  .stat-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    flex: 1;
    padding: 8px;
    background: var(--color-surface);
    border: 1px solid var(--color-border-light);
    border-radius: var(--radius-md);

    .stat-value {
      font-size: 16px;
      font-weight: 700;
      color: var(--color-primary);
    }

    .stat-label {
      font-size: 9px;
      color: var(--color-text-tertiary);
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }
  }

  .user-profile-sidebar {
    border-radius: var(--radius-md);
    transition: all var(--transition-fast);
    width: 100%;

    &:hover {
      background: rgba(99, 102, 241, 0.04);
    }

    .user-info {
      overflow: hidden;
      max-width: 120px;
    }

    .truncate-text {
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
  }
}

// Page Transitions
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.page-fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
