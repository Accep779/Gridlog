<template>
  <q-page class="report-form-page">
    <div class="page-content">
      <div class="row justify-between items-center q-mb-xl">
        <div>
          <h1 class="page-title">{{ editMode ? 'Edit Report' : 'New Weekly Report' }}</h1>
          <p class="page-subtitle">Submit your progress for the current reporting period</p>
        </div>
        <div class="row items-center q-gutter-sm">
          <span v-if="autoSaveStatus" class="autosave-status text-caption">
            <q-icon name="save" size="14px" class="q-mr-xs" />
            {{ autoSaveStatus }}
          </span>
          <q-btn flat icon="arrow_back" label="Back" @click="confirmCancel" class="back-btn" />
        </div>
      </div>

      <q-form @submit="onSubmit" class="report-form">
        <!-- Accomplishments (Required) -->
        <div class="form-section">
          <div class="section-badge">01</div>
          <div class="section-content">
            <h2 class="section-title">Accomplishments <span class="required">*</span></h2>
            <p class="section-hint">Progress, milestones, and key achievements from this week</p>
            <q-input
              v-model="form.accomplishments"
              type="textarea"
              outlined
              placeholder="What did you achieve this week? Use bullet points for clarity."
              rows="6"
              counter
              maxlength="3000"
              :rules="[val => !!val || 'Accomplishments are required']"
              class="iq-input"
            />
          </div>
        </div>

        <!-- Goals Next Week (Required) -->
        <div class="form-section">
          <div class="section-badge">02</div>
          <div class="section-content">
            <h2 class="section-title">Goals for Next Week <span class="required">*</span></h2>
            <p class="section-hint">Planned focus areas and deliverables for the upcoming period</p>
            <q-input
              v-model="form.goals_next_week"
              type="textarea"
              outlined
              placeholder="What are your objectives for next week?"
              rows="4"
              counter
              maxlength="2000"
              :rules="[val => !!val || 'Goals are required']"
              class="iq-input"
            />
          </div>
        </div>

        <!-- Progress Rating (Required) -->
        <div class="form-section">
          <div class="section-badge">03</div>
          <div class="section-content">
            <h2 class="section-title">Overall Progress Rating <span class="required">*</span></h2>
            <p class="section-hint">Honest assessment of your current trajectory</p>
            <div class="rating-grid">
              <div 
                v-for="opt in progressRatingOptions" 
                :key="opt.value"
                class="rating-option"
                :class="{ active: form.progress_rating === opt.value }"
                @click="form.progress_rating = opt.value"
              >
                <q-icon :name="opt.icon" :color="opt.color" size="24px" />
                <div class="rating-label">{{ opt.label }}</div>
                <div class="rating-desc">{{ opt.description }}</div>
                <div class="selection-indicator"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Blockers -->
        <div class="form-section">
          <div class="section-badge">04</div>
          <div class="section-content">
            <h2 class="section-title">Blockers & Challenges</h2>
            <p class="section-hint">Impediments requiring attention or mitigation</p>
            <q-input
              v-model="form.blockers"
              type="textarea"
              outlined
              placeholder="Any issues slowing you down?"
              rows="3"
              counter
              maxlength="1500"
              class="iq-input"
            />
          </div>
        </div>

        <!-- Support Needed -->
        <div class="form-section">
          <div class="section-badge">05</div>
          <div class="section-content">
            <h2 class="section-title">Support Needed</h2>
            <p class="section-hint">Specific requests for your supervisor or other teams</p>
            <q-input
              v-model="form.support_needed"
              outlined
              placeholder="How can we help you succeed?"
              counter
              maxlength="1000"
              class="iq-input"
            />
          </div>
        </div>

        <!-- Additional Notes -->
        <div class="form-section">
          <div class="section-badge">06</div>
          <div class="section-content">
            <h2 class="section-title">Additional Notes</h2>
            <p class="section-hint">Any other relevant context or information</p>
            <q-input
              v-model="form.additional_notes"
              type="textarea"
              outlined
              placeholder="Misc. updates or context..."
              rows="2"
              counter
              maxlength="1000"
              class="iq-input"
            />
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="row justify-end q-gutter-md q-mt-xl">
          <q-btn flat label="Cancel" @click="confirmCancel" class="cancel-btn" />
          <q-btn
            color="primary"
            label="Save as Draft"
            type="submit"
            :loading="loading"
            class="save-btn"
          />
          <q-btn
            v-if="!editMode"
            color="positive"
            label="Save & Submit"
            @click="handleSubmitClick"
            :loading="loading"
            :disable="!isValidForSubmit"
            class="submit-btn"
          />
        </div>
      </q-form>
    </div>
  </q-page>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import { useReportsStore } from '../stores/reports'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const $q = useQuasar()
const reportsStore = useReportsStore()
const authStore = useAuthStore()

const props = defineProps({
  editMode: { type: Boolean, default: false },
  reportId: { type: [String, Number], default: null }
})

const loading = ref(false)
const submitAfterSave = ref(false)
const autoSaveStatus = ref('')
const reportId = ref(props.reportId) // track the saved report ID for auto-save
let autoSaveInterval = null

const progressRatingOptions = [
  { label: 'On Track', value: 'on_track', icon: 'trending_up', color: 'positive', description: 'Progressing as expected' },
  { label: 'At Risk', value: 'at_risk', icon: 'report_problem', color: 'orange', description: 'May need assistance' },
  { label: 'Behind', value: 'behind', icon: 'priority_high', color: 'negative', description: 'Behind schedule' },
  { label: 'Completed Early', value: 'completed_early', icon: 'stars', color: 'primary', description: 'Finished ahead of schedule' }
]

const form = ref({
  accomplishments: '',
  goals_next_week: '',
  blockers: '',
  support_needed: '',
  progress_rating: null,
  additional_notes: ''
})

const isValidForSubmit = computed(() => {
  return (
    form.value.accomplishments?.trim().length > 0 &&
    form.value.goals_next_week?.trim().length > 0 &&
    form.value.progress_rating
  )
})

const loadReport = async () => {
  if (!props.editMode || !props.reportId) return

  loading.value = true
  try {
    const report = await reportsStore.fetchReport(props.reportId)
    form.value = {
      accomplishments: report.accomplishments || '',
      goals_next_week: report.goals_next_week || '',
      blockers: report.blockers || '',
      support_needed: report.support_needed || '',
      progress_rating: report.progress_rating || null,
      additional_notes: report.additional_notes || ''
    }
  } catch (error) {
    $q.notify({ color: 'negative', message: 'Failed to load report', icon: 'priority_high' })
    router.back()
  } finally {
    loading.value = false
  }
}

const onSubmit = async () => {
  await saveReport()
}

const handleSubmitClick = async () => {
  if (!isValidForSubmit.value) {
    $q.notify({ color: 'warning', message: 'Please fill in all required fields (*) before submitting', icon: 'report_problem' })
    return
  }
  submitAfterSave.value = true
  await saveReport()
}

const saveReport = async () => {
  loading.value = true
  try {
    let savedReport
    if (props.editMode) {
      savedReport = await reportsStore.updateReport(props.reportId, form.value)
      $q.notify({ color: 'positive', message: 'Report draft updated', icon: 'check' })
    } else {
      savedReport = await reportsStore.createReport(form.value)
      $q.notify({ color: 'positive', message: 'Report draft created', icon: 'check' })
    }

    if (submitAfterSave.value && savedReport) {
      await reportsStore.submitReport(savedReport.id)
      $q.notify({ color: 'positive', message: 'Report submitted for review', icon: 'send' })
    }

    router.push('/reports')
  } catch (error) {
    console.error('Save failed:', error)
    const errorData = error.response?.data
    let message = 'Failed to save report'
    
    if (typeof errorData === 'string') {
      message = errorData
    } else if (errorData?.error) {
      message = errorData.error
    } else if (errorData?.detail) {
      message = errorData.detail
    } else if (typeof errorData === 'object') {
      message = Object.values(errorData).flat().join(' ')
    }

    $q.notify({
      color: 'negative',
      message: message,
      icon: 'error',
      position: 'top',
      timeout: 5000
    })
  } finally {
    loading.value = false
    submitAfterSave.value = false
  }
}

const confirmCancel = () => {
  $q.dialog({
    title: 'Discard Changes',
    message: 'Are you sure you want to discard your changes and leave?',
    cancel: true,
    persistent: true
  }).onOk(() => {
    router.back()
  })
}

const autoSave = async () => {
  // Only auto-save if there's content and we're not already saving
  if (loading.value || !form.value.accomplishments) return
  try {
    if (reportId.value) {
      await reportsStore.updateReport(reportId.value, form.value)
    } else {
      const saved = await reportsStore.createReport(form.value)
      reportId.value = saved.id
    }
    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    autoSaveStatus.value = `Auto-saved at ${now}`
  } catch {
    // Silently fail auto-save — user can still manually save
  }
}

onMounted(() => {
  if (!authStore.isEmployee && !authStore.isAdmin) {
    $q.notify({ type: 'negative', message: 'Insufficient permissions' })
    return router.push('/dashboard')
  }
  loadReport()
  autoSaveInterval = setInterval(autoSave, 60000)
})

onUnmounted(() => {
  if (autoSaveInterval) clearInterval(autoSaveInterval)
})
</script>

<style lang="scss" scoped>
.report-form-page {
  padding: 24px;
  background: transparent;
  min-height: 100vh;
}

.page-content {
  background: var(--color-surface);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  padding: 40px;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 120px;
    background: linear-gradient(180deg, rgba(var(--color-primary-rgb), 0.02) 0%, transparent 100%);
    pointer-events: none;
  }
}

.page-title {
  font-size: 2rem;
  font-weight: 800;
  color: var(--color-text-primary);
  margin: 0;
  letter-spacing: -0.02em;
}

.page-subtitle {
  font-size: 1rem;
  color: var(--color-text-secondary);
  margin-top: 8px;
}

.form-section {
  display: flex;
  gap: 24px;
  margin-bottom: 48px;
  position: relative;

  &:last-of-type {
    margin-bottom: 0;
  }

  .section-badge {
    width: 38px;
    height: 38px;
    border-radius: 10px;
    background: rgba(var(--color-primary-rgb), 0.1);
    color: var(--color-primary);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    font-weight: 800;
    flex-shrink: 0;
  }

  .section-content {
    flex: 1;
  }

  .section-title {
    font-size: 1.125rem;
    font-weight: 700;
    color: var(--color-text-primary);
    margin: 0 0 4px 0;

    .required {
      color: var(--color-negative);
      margin-left: 4px;
    }
  }

  .section-hint {
    font-size: 0.9rem;
    color: var(--color-text-secondary); // Darker for accessibility
    margin-bottom: 16px;
    max-width: 600px;
  }
}

.iq-input {
  max-width: 900px; // Constraint for readability on ultra-wide
  :deep(.q-field__control) {
    background: rgba(var(--color-text-primary-rgb), 0.01);
    border-radius: 12px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

    &:hover {
      background: rgba(var(--color-text-primary-rgb), 0.02);
    }
  }

  :deep(.q-field--focused .q-field__control) {
    background: var(--color-surface);
    box-shadow: 0 0 0 3px rgba(var(--color-primary-rgb), 0.1);
  }
}

.rating-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 16px;
}

.rating-option {
  padding: 16px;
  border: 1px solid var(--color-border-light);
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  text-align: center;

  &:hover {
    border-color: var(--color-primary);
    background: rgba(var(--color-primary-rgb), 0.02);
    transform: translateY(-2px);
  }

  &.active {
    border-color: var(--color-primary);
    background: rgba(var(--color-primary-rgb), 0.05);
    box-shadow: 0 4px 12px rgba(var(--color-primary-rgb), 0.1);

    .selection-indicator {
      opacity: 1;
    }
  }

  .rating-label {
    font-weight: 700;
    font-size: 0.875rem;
    margin-top: 8px;
    color: var(--color-text-primary);
  }

  .rating-desc {
    font-size: 0.75rem;
    color: var(--color-text-tertiary);
    margin-top: 4px;
  }

  .selection-indicator {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: var(--color-primary);
    opacity: 0;
    transition: opacity 0.3s ease;
  }
}

.submit-btn {
  padding: 12px 32px;
  font-weight: 700;
  border-radius: 12px;
  box-shadow: var(--shadow-md);
  
  &:not(:disabled):hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
  }
}

.save-btn {
  padding: 12px 24px;
  font-weight: 600;
  border-radius: 12px;
}

.back-btn {
  color: var(--color-text-tertiary);
  &:hover {
    color: var(--color-primary);
  }
}

.cancel-btn {
  color: var(--color-text-tertiary);
}

.autosave-status {
  color: var(--color-text-tertiary);
  display: flex;
  align-items: center;
  font-size: 0.75rem;
  animation: fadeIn 0.4s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-4px); }
  to   { opacity: 1; transform: translateY(0); }
}
</style>
