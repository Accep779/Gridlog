<template>
  <q-page class="report-detail-page">
    <div class="page-content">
      <div v-if="loading" class="text-center q-pa-xl">
        <q-spinner color="primary" size="3em" />
        <div class="q-mt-md text-grey-7">Loading secure report data...</div>
      </div>

      <div v-else-if="report" class="detail-container">
        <!-- Header Section -->
        <div class="detail-header q-mb-xl">
          <div class="info-block">
            <h1 class="period-subtitle">Weekly Report</h1>
            <div class="period-title">{{ formatPeriod(report.period) }}</div>
            <div class="author-info">
              <q-avatar size="24px" color="primary" text-color="white" class="q-mr-sm">
                {{ getInitials(report.employee_name) }}
              </q-avatar>
              <span class="user-name">{{ report.employee_name }}</span>
              <span class="separator-dot"></span>
              <q-badge :color="getStatusColor(report.status)" :label="report.status" class="status-pill" />
              <span v-if="report.is_late" class="late-tag">
                <q-icon name="schedule" size="14px" color="negative" />
                Submitted Late
              </span>
            </div>
          </div>
          
          <div class="action-block">
            <q-btn flat icon="arrow_back" label="Back to List" @click="$router.push('/reports')" class="back-btn" />
            
            <div class="row q-gutter-sm q-mt-md justify-end">
              <q-btn
                v-if="canEdit"
                color="secondary"
                icon="edit"
                label="Edit Draft"
                unelevated
                @click="$router.push(`/reports/${report.id}/edit`)"
                class="iq-btn"
              />
              <q-btn
                v-if="canSubmit"
                color="positive"
                icon="send"
                label="Submit for Review"
                unelevated
                @click="submitReport"
                class="iq-btn"
              />
              <q-btn
                v-if="canReview"
                color="positive"
                icon="check_circle"
                label="Mark as Reviewed"
                unelevated
                @click="reviewReport"
                class="iq-btn"
              />
            </div>
          </div>
        </div>

        <div class="detail-grid">
          <!-- Primary Content -->
          <div class="main-column">
            <!-- Accomplishments -->
            <div class="detail-section">
              <div class="section-label">01 Accomplishments</div>
              <div class="section-card">
                <div class="content-text">{{ report.accomplishments }}</div>
              </div>
            </div>

            <!-- Goals Next Week -->
            <div class="detail-section">
              <div class="section-label">02 Goals for Next Week</div>
              <div class="section-card">
                <div class="content-text">{{ report.goals_next_week }}</div>
              </div>
            </div>

            <!-- Blockers -->
            <div class="detail-section" v-if="report.blockers">
              <div class="section-label">03 Blockers & Challenges</div>
              <div class="section-card blocker-card">
                <div class="content-text">{{ report.blockers }}</div>
              </div>
            </div>
          </div>

          <!-- Sidebar Content -->
          <div class="side-column">
            <!-- Progress Rating -->
            <div class="detail-section">
              <div class="section-label">System Assessment</div>
              <div class="assessment-card" :class="report.progress_rating">
                <div class="rating-vitals">
                  <q-icon 
                    :name="getProgressIcon(report.progress_rating)" 
                    :color="getProgressColor(report.progress_rating)" 
                    size="32px" 
                  />
                  <div class="rating-meta">
                    <div class="rating-label">{{ getProgressLabel(report.progress_rating) }}</div>
                    <div class="rating-status">Verified Trajectory</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Support Needed -->
            <div class="detail-section" v-if="report.support_needed">
              <div class="section-label">Support Requested</div>
              <div class="support-card">
                <div class="content-text">{{ report.support_needed }}</div>
              </div>
            </div>

            <!-- Additional Notes -->
            <div class="detail-section" v-if="report.additional_notes">
              <div class="section-label">Contextual Notes</div>
              <div class="notes-card">
                <div class="content-text">{{ report.additional_notes }}</div>
              </div>
            </div>

            <!-- Submission Details -->
            <div class="detail-section">
              <div class="section-label">Workflow Integrity</div>
              <div class="workflow-card">
                <div class="workflow-item">
                  <div class="item-icon"><q-icon name="add" /></div>
                  <div class="item-meta">
                    <div class="item-title">Created</div>
                    <div class="item-date">{{ formatDate(report.created_at) }}</div>
                  </div>
                </div>
                <div class="workflow-item" v-if="report.submitted_at">
                  <div class="item-icon success"><q-icon name="send" /></div>
                  <div class="item-meta">
                    <div class="item-title">Submitted</div>
                    <div class="item-date">{{ formatDate(report.submitted_at) }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Not Found State -->
      <div v-else class="text-center q-pa-xl">
        <q-icon name="error_outline" size="4em" color="negative" />
        <h2 class="text-h5 q-mt-md">Report Access Denied</h2>
        <p class="text-grey-7">Building doesn't exist or you lack sufficient clearance.</p>
        <q-btn color="primary" label="Return to Hub" @click="$router.push('/reports')" class="q-mt-lg iq-btn" />
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import { useAuthStore } from '../stores/auth'
import { useReportsStore } from '../stores/reports'

const route = useRoute()
const router = useRouter()
const $q = useQuasar()
const authStore = useAuthStore()
const reportsStore = useReportsStore()

const loading = ref(true)
const report = ref(null)

const currentUserId = computed(() => authStore.user?.id)
const isSupervisor = computed(() => authStore.isSupervisor)
const isAdmin = computed(() => authStore.user?.role === 'admin')

const canEdit = computed(() => {
  if (!report.value) return false
  return report.value.status === 'draft' && 
         (report.value.employee === currentUserId.value || isAdmin.value)
})

const canSubmit = computed(() => {
  if (!report.value) return false
  return report.value.status === 'draft' && report.value.employee === currentUserId.value
})

const canReview = computed(() => {
  if (!report.value) return false
  return report.value.status === 'submitted' && (isSupervisor.value || isAdmin.value)
})

const getStatusColor = (status) => {
  const colors = { draft: 'grey-7', submitted: 'blue-5', reviewed: 'positive' }
  return colors[status] || 'grey'
}

const getProgressIcon = (rating) => {
  const icons = { on_track: 'check_circle', at_risk: 'warning', behind: 'error', completed_early: 'fast_forward' }
  return icons[rating] || 'help'
}

const getProgressColor = (rating) => {
  const colors = { on_track: 'positive', at_risk: 'orange', behind: 'negative', completed_early: 'primary' }
  return colors[rating] || 'grey'
}

const getProgressLabel = (rating) => {
  const labels = { on_track: 'On Track', at_risk: 'At Risk', behind: 'Behind', completed_early: 'Completed Early' }
  return labels[rating] || rating
}

const getInitials = (name) => {
  if (!name) return '?'
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatPeriod = (period) => {
  if (!period) return 'Reporting Period'
  const start = new Date(period.start_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
  const end = new Date(period.end_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
  return `${start} — ${end}`
}

const loadReport = async () => {
  loading.value = true
  try {
    report.value = await reportsStore.fetchReport(route.params.id)
  } catch (error) {
    $q.notify({ color: 'negative', message: 'Synchronization breakdown', icon: 'error' })
  } finally {
    loading.value = false
  }
}

const submitReport = async () => {
  try {
    await reportsStore.submitReport(report.value.id)
    $q.notify({ color: 'positive', message: 'Report submitted for review', icon: 'send' })
    loadReport()
  } catch (error) {
    $q.notify({ color: 'negative', message: 'Submission failed', icon: 'error' })
  }
}

const reviewReport = async () => {
  try {
    await reportsStore.reviewReport(report.value.id)
    $q.notify({ color: 'positive', message: 'Report verified and reviewed', icon: 'check_circle' })
    loadReport()
  } catch (error) {
    $q.notify({ color: 'negative', message: 'Verification failed', icon: 'error' })
  }
}

onMounted(() => loadReport())
</script>

<style lang="scss" scoped>
.report-detail-page {
  padding: 24px;
  background: transparent;
}

.page-content {
  background: var(--color-surface);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  padding: 48px;
  position: relative;
  overflow: hidden;

  // Blue IQ Frame
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    bottom: 0;
    width: 6px;
    background: linear-gradient(to bottom, var(--color-primary), var(--color-secondary));
    z-index: 10;
  }
}

.period-subtitle {
  font-size: 0.875rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-primary);
  margin: 0 0 8px 0;
}

.period-title {
  font-size: 2.25rem;
  font-weight: 800;
  color: var(--color-text-primary);
  margin: 0 0 16px 0;
  letter-spacing: -0.03em;
}

.author-info {
  display: flex;
  align-items: center;
  font-size: 0.95rem;
  color: var(--color-text-secondary);

  .user-name {
    font-weight: 600;
    color: var(--color-text-primary);
  }

  .separator-dot {
    width: 4px;
    height: 4px;
    border-radius: 50%;
    background: var(--color-border);
    margin: 0 12px;
  }

  .status-pill {
    padding: 6px 12px;
    border-radius: 8px;
    font-weight: 700;
    font-size: 0.7rem;
    text-transform: uppercase;
  }

  .late-tag {
    margin-left: 12px;
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--color-negative);
    background: rgba(var(--color-negative-rgb), 0.1);
    padding: 4px 8px;
    border-radius: 6px;
  }
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  border-bottom: 1px solid var(--color-border-light);
  padding-bottom: 32px;
}

.back-btn {
  color: var(--color-text-tertiary);
  font-weight: 600;
  &:hover {
    color: var(--color-primary);
  }
}

.iq-btn {
  border-radius: 12px;
  font-weight: 700;
  padding: 8px 20px;
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 48px;
}

.detail-section {
  margin-bottom: 40px;

  .section-label {
    font-size: 0.75rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--color-text-tertiary);
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    
    &::after {
      content: '';
      flex: 1;
      height: 1px;
      background: var(--color-border-light);
      margin-left: 12px;
    }
  }
}

.section-card {
  background: var(--color-bg);
  border: 1px solid var(--color-border-light);
  border-radius: 16px;
  padding: 24px;
  line-height: 1.7;
  color: var(--color-text-primary);
  font-size: 1.05rem;
  white-space: pre-wrap;
  
  &.blocker-card {
    border-left: 4px solid var(--color-negative);
    background: rgba(var(--color-negative-rgb), 0.015);
  }
}

.assessment-card {
  background: var(--color-bg);
  border: 1px solid var(--color-border-light);
  border-radius: 20px;
  padding: 24px;
  transition: all 0.3s ease;

  .rating-vitals {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .rating-label {
    font-size: 1.125rem;
    font-weight: 800;
    color: var(--color-text-primary);
  }

  .rating-status {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--color-text-tertiary);
    text-transform: uppercase;
  }

  &.on_track { border-left: 4px solid var(--color-positive); }
  &.at_risk { border-left: 4px solid var(--color-orange); }
  &.behind { border-left: 4px solid var(--color-negative); }
}

.support-card, .notes-card {
  padding: 20px;
  background: rgba(var(--color-primary-rgb), 0.03);
  border: 1px solid rgba(var(--color-primary-rgb), 0.1);
  border-radius: 16px;
  font-size: 0.95rem;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.workflow-card {
  background: var(--color-bg);
  border: 1px solid var(--color-border-light);
  border-radius: 16px;
  padding: 8px;

  .workflow-item {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 12px 16px;
    
    .item-icon {
      width: 32px;
      height: 32px;
      border-radius: 8px;
      background: rgba(var(--color-text-primary-rgb), 0.05);
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--color-text-secondary);
      
      &.success {
        background: rgba(var(--color-positive-rgb), 0.1);
        color: var(--color-positive);
      }
    }

    .item-title {
      font-size: 0.75rem;
      font-weight: 700;
      color: var(--color-text-tertiary);
      text-transform: uppercase;
    }

    .item-date {
      font-size: 0.875rem;
      font-weight: 600;
      color: var(--color-text-primary);
    }
  }
}
</style>
