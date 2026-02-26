<template>
  <q-page class="dashboard-page">
    <!-- Content Container - The "Stage" -->
    <div class="dashboard-content">
      <!-- Hero Section -->
    <div class="hero-section q-mb-lg">
      <div class="hero-content">
        <div class="welcome-text">
          <h1 class="welcome-title">Welcome back, {{ userName }}</h1>
          <p class="welcome-subtitle">{{ welcomeMessage }}</p>
        </div>
        <div class="hero-actions row q-gutter-sm">
          <q-btn
            v-for="(action, index) in quickActions"
            :key="action.label"
            :color="index === 0 ? 'primary' : 'white'"
            :text-color="index === 0 ? 'white' : 'primary'"
            :label="action.label"
            :icon="action.icon"
            unelevated
            class="hero-btn"
            :class="{ 'secondary-hero-btn': index !== 0 }"
            @click="action.handler"
          />
        </div>
      </div>
    </div>

    <!-- Stats Cards - Enterprise Style -->
    <div class="stats-grid q-mb-lg">
      <div class="stat-card" v-for="(stat, index) in statsCards" :key="stat.label">
        <div class="stat-icon" :style="{ background: stat.bgColor }">
          <q-icon :name="stat.icon" :color="stat.iconColor" size="24px" />
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </div>
        <div class="stat-trend" v-if="stat.trend">
          <q-icon :name="stat.trend > 0 ? 'trending_up' : 'trending_down'" :color="stat.trend > 0 ? 'positive' : 'negative'" size="16px" />
          <span :class="stat.trend > 0 ? 'text-positive' : 'text-negative'">{{ Math.abs(stat.trend) }}%</span>
        </div>
      </div>
    </div>

    <!-- Main Content Grid -->
    <div class="content-grid" :class="{ 'single-column': !isEmployee }">
      <!-- Left Column -->
      <div class="content-column" v-if="isEmployee">
        <!-- Deadline Countdown - Only for Employees -->
        <q-card class="countdown-card" :class="countdownClass">
          <q-card-section>
            <div class="countdown-header">
              <q-icon name="schedule" size="28px" />
              <div class="countdown-title">
                <div class="text-subtitle1 text-weight-bold">Weekly Report Deadline</div>
                <div class="text-caption">Submit your report before Friday 5 PM</div>
              </div>
            </div>
            <div class="countdown-display">
              <div class="countdown-item">
                <span class="countdown-number">{{ countdown.days }}</span>
                <span class="countdown-unit">Days</span>
              </div>
              <div class="countdown-separator">:</div>
              <div class="countdown-item">
                <span class="countdown-number">{{ countdown.hours }}</span>
                <span class="countdown-unit">Hours</span>
              </div>
              <div class="countdown-separator">:</div>
              <div class="countdown-item">
                <span class="countdown-number">{{ countdown.minutes }}</span>
                <span class="countdown-unit">Minutes</span>
              </div>
            </div>
            <div class="countdown-footer">
              <span class="next-deadline">Next deadline: {{ nextDeadline }}</span>
            </div>
          </q-card-section>
        </q-card>

      </div>

      <!-- Right Column -->
      <div class="content-column">
        <!-- Recent Activity -->
        <q-card class="activity-card">
          <q-card-section>
            <div class="section-title q-mb-md">
              <q-icon name="history" class="q-mr-sm" color="primary" />
              Recent Activity
            </div>
            <div v-if="recentActivity.length === 0" class="empty-state">
              <q-icon name="inbox" size="48px" color="grey-4" />
              <div class="text-grey-6 q-mt-md">No recent activity</div>
              <q-btn v-if="isEmployee" flat color="primary" label="Create your first report" @click="submitReport" class="q-mt-sm" />
              <q-btn v-else flat color="primary" label="Refresh Dashboard" @click="loadDashboardData" class="q-mt-sm" />
            </div>
            <q-list v-else class="activity-list">
              <q-item
                v-for="item in recentActivity"
                :key="item.id"
                clickable
                @click="viewReport(item)"
                class="activity-item"
              >
                <q-item-section avatar>
                  <q-avatar :color="item.color" text-color="white" size="40px">
                    <q-icon :name="item.icon" size="20px" />
                  </q-avatar>
                </q-item-section>
                <q-item-section>
                  <q-item-label class="activity-title">{{ item.title }}</q-item-label>
                  <q-item-label caption>{{ formatDate(item.date) }}</q-item-label>
                </q-item-section>

              </q-item>
            </q-list>
          </q-card-section>
        </q-card>
      </div>
    </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from 'stores/auth'
import { useReportsStore } from 'stores/reports'

const router = useRouter()
const authStore = useAuthStore()
const reportsStore = useReportsStore()

// Reactive state
const countdownKey = ref(0)
let countdownTimer = null
const orgStats = ref(null)

// Computed properties
const userName = computed(() => authStore.user?.full_name?.split(' ')[0] || 'User')

const welcomeMessage = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning! Ready to tackle your tasks?'
  if (hour < 17) return 'Good afternoon! Keep up the great work!'
  return 'Good evening! How was your day?'
})

const isSupervisor = computed(() => authStore.isSupervisor)
const isEmployee = computed(() => authStore.isEmployee)
const isAdmin = computed(() => authStore.user?.role === 'admin')



// Stats cards
const statsCards = computed(() => {
  const cards = [
    {
      label: isSupervisor.value ? 'Team Reports' : 'My Reports',
      value: stats.value.myReports,
      icon: 'assignment',
      bgColor: '#F1F5F9',
      iconColor: 'primary',
      trend: 12
    },
    {
      label: 'Pending Review',
      value: stats.value.pendingReview,
      icon: 'hourglass_empty',
      bgColor: '#FFFBEB',
      iconColor: 'warning',
      trend: null
    },
    {
      label: 'Reviewed',
      value: stats.value.reviewed,
      icon: 'check_circle',
      bgColor: '#ECFDF5',
      iconColor: 'positive',
      trend: 8
    }
  ]

  if (isAdmin.value && orgStats.value) {
    cards.push({
      label: 'Org Submission Rate',
      value: orgStats.value.submissionRate + '%',
      icon: 'query_stats',
      bgColor: '#EFF6FF',
      iconColor: 'primary',
      trend: orgStats.value.trend?.[0]?.rate ? Math.round(orgStats.value.submissionRate - orgStats.value.trend[0].rate) : null
    })
  } else {
    cards.push({
      label: 'Drafts',
      value: stats.value.draft || 0,
      icon: 'edit_note',
      bgColor: '#F8FAFC',
      iconColor: 'grey-7',
      trend: null
    })
  }

  return cards
})

const stats = computed(() => reportsStore.stats)

// Countdown logic
const deadline = computed(() => {
  countdownKey.value
  const now = new Date()
  const day = now.getDay()
  const friday = new Date(now)
  friday.setDate(now.getDate() + (5 - day + 7) % 7)
  friday.setHours(17, 0, 0, 0)
  if (now > friday) {
    friday.setDate(friday.getDate() + 7)
  }
  return friday
})

const countdown = computed(() => {
  const now = new Date()
  const diff = deadline.value - now

  if (diff <= 0) {
    return { days: '00', hours: '00', minutes: '00' }
  }

  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))

  return {
    days: String(days).padStart(2, '0'),
    hours: String(hours).padStart(2, '0'),
    minutes: String(minutes).padStart(2, '0')
  }
})

const countdownClass = computed(() => {
  const diff = deadline.value - new Date()
  const hours = diff / (1000 * 60 * 60)
  if (hours < 24) return 'countdown-urgent'
  if (hours < 48) return 'countdown-warning'
  return ''
})

const nextDeadline = computed(() => {
  return deadline.value.toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit'
  })
})

// Recent activity
const recentActivity = computed(() => {
  return reportsStore.recentActivity.map(item => ({
    ...item,
    status: item.status?.charAt(0).toUpperCase() + item.status?.slice(1) || item.status,
    statusColor: getStatusColor(item.status),
    icon: getActivityIcon(item.status),
    color: getActivityColor(item.status)
  }))
})

const getStatusColor = (status) => {
  const colors = {
    draft: 'grey-5',
    submitted: 'info',
    reviewed: 'positive',
    revision_requested: 'orange-8'
  }
  return colors[status] || 'grey'
}

const getActivityIcon = (status) => {
  const icons = {
    draft: 'edit',
    submitted: 'send',
    reviewed: 'check_circle',
    revision_requested: 'history_edu'
  }
  return icons[status] || 'assignment'
}

const getActivityColor = (status) => {
  const colors = {
    draft: 'grey-5',
    submitted: 'info',
    reviewed: 'positive',
    revision_requested: 'orange-8'
  }
  return colors[status] || 'primary'
}

// Quick actions
const quickActions = computed(() => {
  const actions = []

  if (isEmployee.value) {
    actions.push(
      {
        label: 'Submit Report',
        icon: 'description',
        bgColor: '#F1F5F9',
        iconColor: 'primary',
        handler: () => submitReport()
      },
      {
        label: 'My Reports',
        icon: 'folder_open',
        bgColor: '#FFFBEB',
        iconColor: 'warning',
        handler: () => router.push('/reports')
      }
    )
  } else if (isSupervisor.value) {
    actions.push(
      {
        label: 'Review Team Reports',
        icon: 'verified_user',
        bgColor: '#F1F5F9',
        iconColor: 'primary',
        handler: () => router.push('/reports?review=1')
      },
      {
        label: 'Team Dashboard',
        icon: 'supervisor_account',
        bgColor: '#ECFDF5',
        iconColor: 'positive',
        handler: () => router.push('/team-oversight')
      }
    )
  } else if (isAdmin.value) {
    actions.push(
      {
        label: 'Manage Periods',
        icon: 'event_available',
        bgColor: '#F1F5F9',
        iconColor: 'primary',
        handler: () => router.push('/periods')
      },
      {
        label: 'System Admin',
        icon: 'admin_panel_settings',
        bgColor: '#ECFDF5',
        iconColor: 'positive',
        handler: () => window.open('http://localhost:8000/admin/', '_blank')
      }
    )
  }

  return actions
})

// Methods
const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString()
}

const submitReport = () => router.push('/reports?new=1')
const viewReport = (item) => {
  if (item.id) {
    router.push(`/reports/${item.id}`)
  }
}

// Lifecycle
const loadDashboardData = async () => {
  try {
    const promises = [
      reportsStore.fetchMyReports(),
      reportsStore.fetchDashboardStats(),
      reportsStore.fetchRecentActivity()
    ]
    if (isAdmin.value) {
      promises.push(reportsStore.fetchOrganizationStats().then(data => orgStats.value = data))
    }
    await Promise.all(promises)
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
  }
}

onMounted(() => {
  loadDashboardData()
  countdownTimer = setInterval(() => {
    countdownKey.value++
  }, 60000)
})

onUnmounted(() => {
  if (countdownTimer) clearInterval(countdownTimer)
})
</script>

<style lang="scss" scoped>
.dashboard-page {
  padding: 24px;
  background: transparent;
  min-height: 100vh;
  position: relative;
  z-index: 1;
}

// New: Content Container - The "Stage"
.dashboard-content {
  position: relative;
  z-index: 1;
  max-width: 1440px;
  margin: 0 auto;
}

// Hero Section - Adaptive
.hero-section {
  position: relative;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.4);
  border-radius: var(--radius-lg);
  padding: 32px;
  overflow: hidden;
  box-shadow: 0 4px 24px rgba(15, 76, 129, 0.04);

  .hero-content {
    position: relative;
    z-index: 1;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .welcome-title {
    font-size: 1.75rem;
    font-weight: 700;
    color: #0F172A;
    margin: 0 0 8px 0;
  }

  .welcome-subtitle {
    font-size: 1rem;
    color: #475569;
    margin: 0;
  }

  .hero-btn {
    background: #0F4C81;
    color: white;
    font-weight: 600;

    &:hover {
      background: #1E3A8A;
      transform: translateY(-1px);
    }
  }
}

// Stats Grid
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;

  @media (max-width: 1024px) {
    grid-template-columns: repeat(2, 1fr);
  }

  @media (max-width: 600px) {
    grid-template-columns: 1fr;
  }
}

.stat-card {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.4);
  border-radius: var(--radius-lg);
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 20px;
  position: relative;
  overflow: hidden;
  transition: box-shadow 0.2s;

  &:hover {
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
  }

  .stat-icon {
    width: 48px;
    height: 48px;
    border-radius: var(--radius-md);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .stat-content {
    flex: 1;
  }

  .stat-value {
    font-size: 1.75rem;
    font-weight: 700;
    color: #0F172A;
    line-height: 1.2;
    font-family: 'Inter', sans-serif;
  }

  .stat-label {
    font-size: 0.875rem;
    color: #64748B;
    margin-top: 4px;
    font-weight: 500;
  }

  .stat-trend {
    position: absolute;
    top: 24px;
    right: 24px;
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 0.75rem;
    font-weight: 700;
    color: var(--color-positive);
    background: rgba(var(--color-positive-rgb), 0.1);
    padding: 4px 8px;
    border-radius: 6px;
  }
}

// Content Grid
.content-grid {
  display: grid;
  grid-template-columns: 1fr 1.5fr;
  gap: 24px;

  &.single-column {
    grid-template-columns: 1fr;
  }

  @media (max-width: 900px) {
    grid-template-columns: 1fr;
  }
}

.content-column {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

// Section Title
.section-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text-primary);
  display: flex;
  align-items: center;
  letter-spacing: -0.01em;
}

// Countdown Card - Solid Clean
.countdown-card {
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.4);
  
  &.countdown-warning {
    border-color: rgba(245, 158, 11, 0.5);
    background: rgba(255, 251, 235, 0.6);
  }

  &.countdown-urgent {
    border-color: rgba(239, 68, 68, 0.5);
    background: rgba(254, 242, 242, 0.6);
  }

  .countdown-header {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 20px;
    color: #475569;

    .q-icon {
      color: #0F4C81;
    }
  }

  .countdown-title {
    .text-subtitle1 {
      margin-bottom: 2px;
      color: #0F172A;
    }
  }

  .countdown-display {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 12px;
    padding: 20px 0;
  }

  .countdown-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: var(--radius-md);
    padding: 16px 24px;
    min-width: 80px;

    .countdown-number {
      font-size: 2rem;
      font-weight: 700;
      color: #0F4C81;
      line-height: 1;
      font-family: 'Inter', sans-serif;
    }

    .countdown-unit {
      font-size: 0.75rem;
      color: #64748B;
      margin-top: 4px;
      text-transform: uppercase;
      font-weight: 600;
    }
  }

  .countdown-separator {
    font-size: 2rem;
    font-weight: 700;
    color: #CBD5E1;
  }

  .countdown-footer {
    text-align: center;
    padding-top: 16px;
    border-top: 1px solid #E2E8F0;

    .next-deadline {
      font-size: 0.875rem;
      color: #64748B;
    }
  }
}

  .secondary-hero-btn {
    border: 1px solid var(--color-border-light);
    
    &:hover {
      background: #F8FAFC !important;
    }
  }

// Activity Card - Solid Clean
.activity-card {
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.4);

    .activity-list {
        .activity-item {
          border-radius: var(--radius-md);
          margin-bottom: 8px;
          transition: all var(--transition-fast);
          display: flex;
          align-items: center;
          justify-content: space-between;
        }
        .activity-item .q-item-section[avatar] {
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .activity-item .q-item-section[avatar] .q-avatar {
          margin: 0;
        }
        .activity-item .q-item-section[side] {
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .activity-badge {
          font-size: 0.7rem;
          padding: 0;
          min-width: 24px;
          height: 24px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 50%;
        }
        .activity-title {
          font-weight: 500;
          color: var(--color-text-primary);
        }
      }

  .empty-state {
    text-align: center;
    padding: 32px;
  }
}
</style>
