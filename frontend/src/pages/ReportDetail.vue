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
                <q-icon name="warning" size="14px" color="negative" />
                Submitted Late
              </span>
            </div>
          </div>
          
          <div class="action-block">
              <q-btn flat icon="arrow_back" label="Back to List" @click="$router.push('/reports')" class="back-btn" />
                <q-btn flat round icon="visibility" @click="toggleRaw" class="eye-btn" />
                <div v-if="showRaw" class="raw-json">
                  {{ JSON.stringify(report, null, 2) }}
                </div>
            
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
                icon="check_circle"
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
              <q-btn
                v-if="isSupervisor && report.status === 'submitted'"
                color="orange-8"
                outline
                icon="history_edu"
                label="Request Revision"
                @click="confirmRequestRevision"
                class="iq-btn"
              />
              <q-btn
                v-if="isAdmin && report && report.status !== 'draft'"
                color="negative"
                outline
                icon="undo"
                label="Reset to Draft"
                @click="confirmResetToDraft"
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
                  <div class="item-icon success"><q-icon name="check_circle" /></div>
                  <div class="item-meta">
                    <div class="item-title">Submitted</div>
                    <div class="item-date">{{ formatDate(report.submitted_at) }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Inline Comment Panel -->
          <div class="comment-panel">
            <div class="comment-panel-header">
              <q-icon name="chat" size="18px" color="primary" />
              <span class="comment-panel-title">Comments</span>
              <q-badge v-if="comments.length" :label="comments.length" color="primary" class="q-ml-sm" />
            </div>

            <!-- Comment List -->
            <div class="comment-list" v-if="comments.length">
              <div v-for="comment in comments" :key="comment.id" class="comment-thread">
                <div class="comment-item">
                  <q-avatar size="28px" color="primary" text-color="white" class="comment-avatar">
                    {{ getInitials(comment.author) }}
                  </q-avatar>
                  <div class="comment-body">
                    <div class="comment-meta">
                      <span class="comment-author">{{ comment.author }}</span>
                      <span class="comment-time">{{ formatDate(comment.created_at) }}</span>
                    </div>
                    <div class="comment-text">{{ comment.body }}</div>
                    <q-btn
                      flat dense size="xs" label="Reply"
                      class="reply-btn"
                      @click="replyTo = replyTo === comment.id ? null : comment.id"
                    />
                  </div>
                </div>

                <!-- Replies -->
                <div v-if="comment.replies && comment.replies.length" class="replies-list">
                  <div v-for="reply in comment.replies" :key="reply.id" class="comment-item reply-item">
                    <q-avatar size="22px" color="secondary" text-color="white" class="comment-avatar">
                      {{ getInitials(reply.author) }}
                    </q-avatar>
                    <div class="comment-body">
                      <div class="comment-meta">
                        <span class="comment-author">{{ reply.author }}</span>
                        <span class="comment-time">{{ formatDate(reply.created_at) }}</span>
                      </div>
                      <div class="comment-text">{{ reply.body }}</div>
                    </div>
                  </div>
                </div>

                <!-- Inline Reply Input -->
                <div v-if="replyTo === comment.id" class="reply-input-row">
                  <q-input
                    v-model="replyText"
                    dense outlined
                    placeholder="Write a reply..."
                    class="reply-input"
                    @keyup.enter="postComment(comment.id)"
                  >
                    <template v-slot:append>
                      <q-btn flat dense round icon="send" color="primary" @click="postComment(comment.id)" />
                    </template>
                  </q-input>
                </div>
              </div>
            </div>

            <div v-else class="comment-empty">
              <q-icon name="chat_bubble_outline" size="32px" color="grey-4" />
              <div class="text-grey-6 text-caption q-mt-sm">No comments yet</div>
            </div>

            <!-- New Comment Input -->
            <div class="comment-input-row">
              <q-input
                v-model="newComment"
                outlined dense
                placeholder="Add a comment..."
                class="comment-input"
                maxlength="2000"
                @keyup.enter="postComment(null)"
              >
                <template v-slot:append>
                  <q-btn flat dense round icon="send" color="primary" :disable="!newComment.trim()" @click="postComment(null)" />
                </template>
              </q-input>
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

const report = ref(null)
const showRaw = ref(false)
function toggleRaw(){
  showRaw.value = !showRaw.value
}
const loading = ref(true)
const comments = ref([])
const newComment = ref('')
const replyTo = ref(null)
const replyText = ref('')

const currentUserId = computed(() => authStore.user?.id)
const isSupervisor = computed(() => authStore.isSupervisor)
const isAdmin = computed(() => authStore.user?.role === 'admin')

const canEdit = computed(() => {
  if (!report.value) return false
  return (report.value.status === 'draft' || report.value.status === 'revision_requested') && 
         (Number(report.value.employee) === Number(currentUserId.value) || isAdmin.value)
})

const canSubmit = computed(() => {
  if (!report.value) return false
  return report.value.status === 'draft' && Number(report.value.employee) === Number(currentUserId.value)
})

const canReview = computed(() => {
  if (!report.value) return false
  return report.value.status === 'submitted' && isSupervisor.value
})

const getStatusColor = (status) => {
  const colors = { 
    draft: 'grey-7', 
    submitted: 'blue-5', 
    reviewed: 'positive',
    revision_requested: 'orange-8'
  }
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
    await loadComments()
  } catch (error) {
    $q.notify({ color: 'negative', message: 'Synchronization breakdown', icon: 'error' })
  } finally {
    loading.value = false
  }
}

const loadComments = async () => {
  try {
    comments.value = await reportsStore.fetchComments(route.params.id)
  } catch {
    // Comments may not be available, silently ignore
  }
}

const postComment = async (parentId = null) => {
  const body = parentId ? replyText.value.trim() : newComment.value.trim()
  if (!body) return
  try {
    const payload = parentId
      ? await reportsStore.addComment(route.params.id, body, parentId)
      : await reportsStore.addComment(route.params.id, body)
    await loadComments()
    if (parentId) {
      replyText.value = ''
      replyTo.value = null
    } else {
      newComment.value = ''
    }
    $q.notify({ color: 'positive', message: 'Comment added', icon: 'chat' })
  } catch {
    $q.notify({ color: 'negative', message: 'Failed to add comment', icon: 'error' })
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

const confirmRequestRevision = () => {
  $q.dialog({
    title: 'Request Revision',
    message: 'Provide feedback to the employee about required changes:',
    prompt: {
      model: '',
      type: 'text'
    },
    cancel: { label: 'Cancel', flat: true },
    ok: { label: 'Send Feedback', color: 'orange-8', unelevated: true },
    persistent: true
  }).onOk(async (data) => {
    try {
      await reportsStore.requestRevision(report.value.id, data)
      $q.notify({ color: 'warning', message: 'Revision requested from employee', icon: 'history_edu' })
      loadReport()
    } catch (error) {
      $q.notify({ color: 'negative', message: 'Failed to request revision', icon: 'error' })
    }
  })
}

const confirmResetToDraft = () => {
  $q.dialog({
    title: 'Reset to Draft',
    message: 'This will move the report back to Draft status so the employee can edit and resubmit. Are you sure?',
    cancel: { label: 'Cancel', flat: true },
    ok: { label: 'Reset', color: 'negative', unelevated: true },
    persistent: true
  }).onOk(async () => {
    try {
      await reportsStore.resetToDraft(report.value.id)
      $q.notify({ color: 'positive', message: 'Report reset to Draft', icon: 'undo' })
      loadReport()
    } catch (error) {
      $q.notify({ color: 'negative', message: 'Failed to reset report', icon: 'error' })
    }
  })
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
  grid-template-columns: 1fr 300px 320px;
  gap: 32px;
  align-items: start;
}

// Comment Panel
.comment-panel {
  border-left: 1px solid var(--color-border-light);
  padding-left: 32px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-height: 80vh;
  position: sticky;
  top: 24px;
}

.comment-panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.75rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-text-tertiary);
  padding-bottom: 12px;
  border-bottom: 1px solid var(--color-border-light);
}

.comment-panel-title {
  flex: 1;
}

.comment-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-right: 4px;
}

.comment-thread {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.comment-item {
  display: flex;
  gap: 10px;
  align-items: flex-start;

  &.reply-item {
    padding-left: 38px;
  }
}

.comment-avatar {
  flex-shrink: 0;
  font-size: 0.625rem;
  font-weight: 700;
}

.comment-body {
  flex: 1;
  background: var(--color-bg);
  border: 1px solid var(--color-border-light);
  border-radius: 12px;
  padding: 10px 14px;
}

.comment-meta {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.comment-author {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--color-text-primary);
}

.comment-time {
  font-size: 0.7rem;
  color: var(--color-text-tertiary);
}

.comment-text {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  line-height: 1.5;
  white-space: pre-wrap;
}

.reply-btn {
  font-size: 0.7rem;
  color: var(--color-text-tertiary);
  margin-top: 4px;
  padding: 0;
}

.replies-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.reply-input-row {
  padding-left: 38px;
}

.comment-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px 0;
}

.comment-input-row {
  border-top: 1px solid var(--color-border-light);
  padding-top: 12px;
}


.detail-section {
  margin-bottom: 40px;

  .section-label {
    font-size: 0.75rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--color-text-secondary); // Darkened from tertiary
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    
    &::after {
      content: '';
      flex: 1;
      height: 1px;
      background: var(--color-border); // Darkened from border-light
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

  &.on_track { border-top: 4px solid var(--color-positive); }
  &.at_risk { border-top: 4px solid var(--color-warning); }
  &.blocked { border-top: 4px solid var(--color-negative); }
}

.support-card, .notes-card {
  background: white;
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
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
