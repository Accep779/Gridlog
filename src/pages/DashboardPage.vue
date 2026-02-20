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
        <div class="hero-actions">
          <q-btn
            color="primary"
            label="Submit Report"
            icon="add"
            unelevated
            class="hero-btn"
            @click="submitReport"
          />
        </div>
      </div>
      <!-- Background Decoration -->
      <div class="hero-decoration"></div>
    </div>

    <!-- Stats Cards - Vercel Style -->
    <div class="stats-grid q-mb-lg">
      <div class="stat-card stagger-item" v-for="(stat, index) in statsCards" :key="stat.label">
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
    <div class="content-grid">
      <!-- Left Column -->
      <div class="content-column">
        <!-- Deadline Countdown - Only for Employees -->
        <q-card v-if="isEmployee" class="countdown-card" :class="countdownClass">
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

        <!-- Quick Actions -->
        <q-card class="actions-card">
          <q-card-section>
            <div class="section-title q-mb-md">
              <q-icon name="flash_on" class="q-mr-sm" color="primary" />
              Quick Actions
            </div>
            <div class="actions-grid">
              <div
                class="action-item"
                v-for="action in quickActions"
                :key="action.label"
                @click="action.handler"
              >
                <div class="action-icon" :style="{ background: action.bgColor }">
                  <q-icon :name="action.icon" :color="action.iconColor" size="20px" />
                </div>
                <div class="action-label">{{ action.label }}</div>
              </div>
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
              <q-btn flat color="primary" label="Create your first report" @click="submitReport" class="q-mt-sm" />
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
                <q-item-section side>
                  <q-badge
                    :color="item.statusColor"
                    :label="item.status"
                    class="activity-badge"
                  />
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
      label: 'My Reports',
      value: stats.value.myReports,
      icon: 'assignment',
      bgColor: 'rgba(var(--color-primary-rgb), 0.1)',
      iconColor: 'primary',
      trend: 12
    },
    {
      label: 'Pending Review',
      value: stats.value.pendingReview,
      icon: 'hourglass_empty',
      bgColor: 'rgba(245, 158, 11, 0.1)',
      iconColor: 'warning',
      trend: null
    },
    {
      label: 'Reviewed',
      value: stats.value.reviewed,
      icon: 'check_circle',
      bgColor: 'rgba(16, 185, 129, 0.1)',
      iconColor: 'positive',
      trend: 8
    }
  ]

  if (isAdmin.value && orgStats.value) {
    cards.push({
      label: 'Org Submission Rate',
      value: orgStats.value.submissionRate + '%',
      icon: 'query_stats',
      bgColor: 'rgba(99, 102, 241, 0.15)',
      iconColor: 'primary',
      trend: orgStats.value.trend?.[0]?.rate ? Math.round(orgStats.value.submissionRate - orgStats.value.trend[0].rate) : null
    })
  } else {
    cards.push({
      label: 'Drafts',
      value: stats.value.draft || 0,
      icon: 'edit_note',
      bgColor: 'rgba(100, 116, 139, 0.1)',
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
    reviewed: 'positive'
  }
  return colors[status] || 'grey'
}

const getActivityIcon = (status) => {
  const icons = {
    draft: 'edit',
    submitted: 'send',
    reviewed: 'check_circle'
  }
  return icons[status] || 'assignment'
}

const getActivityColor = (status) => {
  const colors = {
    draft: 'grey-5',
    submitted: 'info',
    reviewed: 'positive'
  }
  return colors[status] || 'primary'
}

// Quick actions
const quickActions = computed(() => {
  const actions = [
    {
      label: 'New Report',
      icon: 'add',
      bgColor: 'rgba(var(--color-primary-rgb), 0.1)',
      iconColor: 'primary',
      handler: () => submitReport()
    },
    {
      label: 'My Reports',
      icon: 'assignment',
      bgColor: 'rgba(139, 92, 246, 0.1)',
      iconColor: 'secondary',
      handler: () => router.push('/reports')
    }
  ]

  if (isSupervisor.value) {
    actions.push({
      label: 'Review',
      icon: 'rate_review',
      bgColor: 'rgba(245, 158, 11, 0.1)',
      iconColor: 'warning',
      handler: () => router.push('/reports?review=1')
    })
  }

  if (isAdmin.value) {
    actions.push({
      label: 'Users',
      icon: 'people',
      bgColor: 'rgba(16, 185, 129, 0.1)',
      iconColor: 'positive',
      handler: () => router.push('/users')
    })
  }

  return actions
})

// Methods
const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString()
}

const submitReport = () => router.push('/reports?new=1')
const viewReport = (item) => router.push(`/reports/${item.id}`)

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
  background: var(--color-surface);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  padding: 32px;
  position: relative;
  overflow: hidden;

  // Subtle gradient overlay for depth
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 100px;
    background: linear-gradient(180deg, rgba(var(--color-primary-rgb), 0.015) 0%, transparent 100%);
    pointer-events: none;
  }

  // Atmospheric orb
  &::after {
    content: '';
    position: absolute;
    top: -60px;
    right: -60px;
    width: 240px;
    height: 240px;
    background: radial-gradient(circle, rgba(var(--color-primary-rgb), 0.05) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
  }

  > * {
    position: relative;
    z-index: 1;
  }
}

// Hero Section - Adaptive
.hero-section {
  position: relative;
  background: linear-gradient(135deg, rgba(var(--color-surface-rgb), 0.98) 0%, rgba(var(--color-bg-rgb), 0.95) 100%);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(var(--color-surface-rgb), 0.5);
  border-radius: var(--radius-xl);
  padding: 32px;
  overflow: hidden;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);

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
    color: var(--color-primary);
    margin: 0 0 8px 0;
  }

  .welcome-subtitle {
    font-size: 1rem;
    color: var(--color-text-secondary);
    margin: 0;
  }

  .hero-btn {
    background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-hover) 100%);
    color: white;
    font-weight: 600;
    box-shadow: 0 2px 8px rgba(var(--color-primary-rgb), 0.3);

    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 20px rgba(var(--color-primary-rgb), 0.35);
    }
  }

  .hero-decoration {
    position: absolute;
    top: -30%;
    right: -5%;
    width: 300px;
    height: 300px;
    background: radial-gradient(circle, rgba(var(--color-primary-rgb), 0.08) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
  }

  .hero-decoration-2 {
    position: absolute;
    bottom: -20%;
    left: -5%;
    width: 200px;
    height: 200px;
    background: radial-gradient(circle, rgba(139, 92, 246, 0.06) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
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
  background: var(--color-surface);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-lg);
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 20px;
  transition: all var(--transition-base);
  box-shadow: var(--shadow-md);
  position: relative;
  overflow: hidden;

  // Blue IQ Accent
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    bottom: 0;
    width: 0;
    background: linear-gradient(to bottom, var(--color-primary), var(--color-secondary));
    transition: width var(--transition-base);
  }

  &:hover {
    box-shadow: var(--shadow-lg);
    border-color: rgba(var(--color-primary-rgb), 0.2);
    transform: translateY(-4px);

    &::before {
      width: 4px;
    }

    .stat-icon {
      transform: scale(1.1);
      box-shadow: 0 4px 12px rgba(var(--color-primary-rgb), 0.2);
    }
  }

  .stat-icon {
    width: 56px;
    height: 56px;
    border-radius: var(--radius-md);
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--color-surface);
    border: 1px solid var(--color-border-light);
    box-shadow: var(--shadow-sm);
    transition: all var(--transition-base);
  }

  .stat-content {
    flex: 1;
  }

  .stat-value {
    font-size: 1.75rem;
    font-weight: 700;
    color: var(--color-text-primary);
    line-height: 1.2;
    font-family: 'JetBrains Mono', monospace;
  }

  .stat-label {
    font-size: 0.875rem;
    color: var(--color-text-secondary);
    margin-top: 2px;
  }

  .stat-trend {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 0.75rem;
    font-weight: 600;
  }
}

// Content Grid
.content-grid {
  display: grid;
  grid-template-columns: 1fr 1.5fr;
  gap: 24px;

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

// Countdown Card - Enhanced Glass
.countdown-card {
  border-radius: var(--radius-lg);
  background: rgba(var(--color-surface-rgb), 0.95);
  backdrop-filter: blur(12px);
  border: 1px solid var(--color-border-light);
  transition: all var(--transition-base);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);

  &.countdown-warning {
    border-color: var(--color-warning);
    background: rgba(var(--color-surface-rgb), 0.95);
    box-shadow: 0 0 0 1px rgba(245, 158, 11, 0.2), 0 4px 12px rgba(245, 158, 11, 0.1);
  }

  &.countdown-urgent {
    border-color: var(--color-error);
    background: rgba(var(--color-surface-rgb), 0.95);
    box-shadow: 0 0 0 1px rgba(239, 68, 68, 0.2), 0 4px 12px rgba(239, 68, 68, 0.1);
    animation: pulse-urgent 2s infinite;
  }

  .countdown-header {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 20px;
    color: var(--color-text-primary);

    .q-icon {
      color: var(--color-primary);
    }
  }

  .countdown-title {
    .text-subtitle1 {
      margin-bottom: 2px;
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
    background: linear-gradient(135deg, rgba(var(--color-primary-rgb), 0.06) 0%, rgba(var(--color-secondary-rgb, 139, 92, 246), 0.04) 100%);
    border: 1px solid var(--color-border-light);
    border-radius: var(--radius-md);
    padding: 16px 24px;
    min-width: 80px;

    .countdown-number {
      font-size: 2rem;
      font-weight: 700;
      color: var(--color-primary);
      line-height: 1;
      font-family: 'JetBrains Mono', monospace;
    }

    .countdown-unit {
      font-size: 0.75rem;
      color: var(--color-text-tertiary);
      margin-top: 4px;
      text-transform: uppercase;
    }
  }

  .countdown-separator {
    font-size: 2rem;
    font-weight: 700;
    color: var(--color-text-tertiary);
  }

  .countdown-footer {
    text-align: center;
    padding-top: 16px;
    border-top: 1px solid var(--color-border-light);

    .next-deadline {
      font-size: 0.875rem;
      color: var(--color-text-secondary);
    }
  }
}

@keyframes pulse-urgent {
  0%, 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.15); }
  50% { box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }
}

// Actions Card - Glass Enhanced
.actions-card {
  border-radius: var(--radius-lg);
  background: rgba(var(--color-surface-rgb), 0.95);
  backdrop-filter: blur(12px);
  border: 1px solid var(--color-border-light);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);

  .actions-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
    gap: 12px;
  }

  .action-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    padding: 16px;
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: all var(--transition-fast);

    &:hover {
      background: linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(139, 92, 246, 0.04) 100%);
      transform: translateY(-2px);

      .action-icon {
        transform: scale(1.1);
        box-shadow: 0 4px 12px rgba(var(--color-primary-rgb), 0.2);
      }
    }

    .action-icon {
      width: 48px;
      height: 48px;
      border-radius: var(--radius-md);
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all var(--transition-fast);
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
    }

    .action-label {
      font-size: 0.875rem;
      font-weight: 500;
      color: var(--color-text-secondary);
      text-align: center;
    }
  }
}

// Activity Card - Glass Enhanced
.activity-card {
  border-radius: var(--radius-lg);
  background: rgba(var(--color-surface-rgb), 0.95);
  backdrop-filter: blur(12px);
  border: 1px solid var(--color-border-light);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);

  .activity-list {
    .activity-item {
      border-radius: var(--radius-md);
      margin-bottom: 8px;
      transition: all var(--transition-fast);

      &:hover {
        background: linear-gradient(135deg, rgba(var(--color-primary-rgb), 0.06) 0%, rgba(var(--color-secondary-rgb, 139, 92, 246), 0.03) 100%);
        transform: translateX(4px);
      }

      .activity-title {
        font-weight: 500;
        color: var(--color-text-primary);
      }

      .activity-badge {
        font-size: 0.7rem;
        padding: 4px 8px;
      }
    }
  }

  .empty-state {
    text-align: center;
    padding: 32px;
  }
}
</style>
