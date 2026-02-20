<template>
  <q-page class="reports-page">
    <div class="page-content">
      <div class="page-header q-mb-xl">
        <div class="header-content">
          <div>
            <h1 class="page-title">{{ viewTitle }}</h1>
            <p class="page-subtitle">Standardized 7-field reporting system</p>
          </div>
          <div class="header-actions">
            <q-btn-toggle
              v-if="isSupervisor || isAdmin"
              v-model="viewMode"
              toggle-color="primary"
              :options="viewModeOptions"
              class="view-toggle"
            />
            <q-btn-dropdown v-if="isAdmin" color="secondary" icon="download" label="Export" class="export-btn">
              <q-list>
                <q-item clickable v-close-popup @click="exportCSV">
                  <q-item-section avatar><q-icon name="table_chart" /></q-item-section>
                  <q-item-section>Export CSV</q-item-section>
                </q-item>
                <q-item clickable v-close-popup @click="exportPDF">
                  <q-item-section avatar><q-icon name="picture_as_pdf" /></q-item-section>
                  <q-item-section>Export PDF</q-item-section>
                </q-item>
              </q-list>
            </q-btn-dropdown>
            <q-btn v-if="isEmployee" color="primary" icon="add" label="New Report" unelevated @click="createNewReport" class="new-report-btn" />
          </div>
        </div>
      </div>

      <!-- Filters -->
      <q-card class="filters-card q-mb-lg">
        <q-card-section class="filters-section">
          <div class="filters-row">
            <div class="filter-search">
              <q-input
                v-model="searchQuery"
                outlined
                dense
                placeholder="Search accomplishments..."
                clearable
                class="search-field"
              >
                <template v-slot:prepend>
                  <q-icon name="search" />
                </template>
              </q-input>
            </div>

            <q-select
              v-model="statusFilter"
              :options="statusOptions"
              label="Status"
              outlined
              dense
              emit-value
              map-options
              class="filter-select"
            />

            <q-btn flat icon="clear" @click="clearFilters" title="Clear filters" class="clear-btn" />
          </div>
        </q-card-section>
      </q-card>

      <!-- Table -->
      <q-card class="table-card">
        <q-table
          :rows="filteredReports"
          :columns="tableColumns"
          row-key="id"
          :loading="loading"
          flat
          @row-click="viewReport"
          class="reports-table"
        >
          <template v-slot:body-cell-period="props">
            <q-td :props="props">
              <div class="period-cell">
                <q-icon name="calendar_today" size="xs" color="grey-7" class="q-mr-xs" />
                {{ formatPeriod(props.row.period) }}
              </div>
            </q-td>
          </template>

          <template v-slot:body-cell-employee="props">
            <q-td :props="props">
              <div class="user-cell">
                <q-avatar size="24px" color="primary" text-color="white" class="user-avatar">
                  {{ getInitials(props.value) }}
                </q-avatar>
                <span class="user-name">{{ props.value }}</span>
              </div>
            </q-td>
          </template>

          <template v-slot:body-cell-status="props">
            <q-td :props="props" align="center">
              <q-badge :color="getStatusColor(props.value)" :label="props.value" class="status-badge" />
            </q-td>
          </template>

          <template v-slot:body-cell-rating="props">
            <q-td :props="props" align="center">
              <q-icon
                :name="getProgressIcon(props.value)"
                :color="getProgressColor(props.value)"
                size="sm"
              >
                <q-tooltip>{{ getProgressLabel(props.value) }}</q-tooltip>
              </q-icon>
            </q-td>
          </template>

          <template v-slot:body-cell-actions="props">
            <q-td :props="props" class="actions-cell">
              <q-btn flat dense round icon="visibility" color="primary" @click.stop="viewReport(props.row)">
                <q-tooltip>View Details</q-tooltip>
              </q-btn>
              <q-btn
                v-if="props.row.status === 'draft' && (props.row.employee === currentUserId || isAdmin)"
                flat
                dense
                round
                icon="edit"
                color="secondary"
                @click.stop="editReport(props.row)"
              >
                <q-tooltip>Edit Draft</q-tooltip>
              </q-btn>
              <q-btn
                v-if="props.row.status === 'submitted' && (isSupervisor || isAdmin)"
                flat
                dense
                round
                icon="thumb_up"
                color="positive"
                @click.stop="quickApprove(props.row)"
              >
                <q-tooltip>Mark as Reviewed</q-tooltip>
              </q-btn>
            </q-td>
          </template>

          <template v-slot:no-data>
            <div class="empty-state">
              <q-icon name="assignment" size="64px" color="grey-4" />
              <div class="empty-title">No reports found</div>
              <div class="empty-description">Create your first report to track your weekly progress</div>
              <q-btn v-if="isEmployee" color="primary" label="Create Report" icon="add" @click="createNewReport" class="q-mt-md" />
            </div>
          </template>
        </q-table>
      </q-card>
    </div>
  </q-page>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useQuasar } from 'quasar'
import { useAuthStore } from '../stores/auth'
import { useReportsStore } from '../stores/reports'

const router = useRouter()
const route = useRoute()
const $q = useQuasar()
const authStore = useAuthStore()
const reportsStore = useReportsStore()

const loading = ref(false)
const searchQuery = ref('')
const statusFilter = ref('all')
const viewMode = ref('mine')

const currentUserId = computed(() => authStore.user?.id)
const isEmployee = computed(() => authStore.isEmployee)
const isSupervisor = computed(() => authStore.isSupervisor)
const isAdmin = computed(() => authStore.user?.role === 'admin')

const viewModeOptions = computed(() => {
  const options = [{ label: 'My Reports', value: 'mine' }]
  if (isSupervisor.value) options.push({ label: 'Team Activity', value: 'team' })
  if (isAdmin.value) options.push({ label: 'System Wide', value: 'all' })
  return options
})

const viewTitle = computed(() => {
  if (viewMode.value === 'all') return 'Organization-Wide Reports'
  if (viewMode.value === 'team') return 'Team Progress'
  return 'My Weekly Reports'
})

const statusOptions = [
  { label: 'All Statuses', value: 'all' },
  { label: 'Draft', value: 'draft' },
  { label: 'Submitted', value: 'submitted' },
  { label: 'Reviewed', value: 'reviewed' }
]

const tableColumns = computed(() => {
  const cols = [
    { name: 'period', label: 'Reporting Period', field: row => row.period, align: 'left', sortable: true },
    { name: 'employee', label: 'Employee', field: 'employee_name', align: 'left', sortable: true },
    { name: 'rating', label: 'Progress', field: 'progress_rating', align: 'center' },
    { name: 'status', label: 'Status', field: 'status', align: 'center', sortable: true },
    { name: 'submitted_at', label: 'Submission Date', field: 'submitted_at', align: 'left', format: val => val ? new Date(val).toLocaleDateString() : '-', sortable: true },
    { name: 'actions', label: 'Actions', field: 'actions', align: 'center' }
  ]
  return cols
})

const filteredReports = computed(() => {
  let reports = reportsStore.reports
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    reports = reports.filter(r => 
      r.accomplishments?.toLowerCase().includes(query) ||
      r.employee_name?.toLowerCase().includes(query)
    )
  }
  if (statusFilter.value !== 'all') {
    reports = reports.filter(r => r.status === statusFilter.value)
  }
  return reports
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

const formatPeriod = (period) => {
  if (!period) return '-'
  const start = new Date(period.start_date)
  const end = new Date(period.end_date)
  const options = { month: 'short', day: 'numeric' }
  return `${start.toLocaleDateString(undefined, options)} - ${end.toLocaleDateString(undefined, options)}`
}

const clearFilters = () => {
  searchQuery.value = ''
  statusFilter.value = 'all'
}

const loadReports = async () => {
  loading.value = true
  try {
    if (viewMode.value === 'all') await reportsStore.fetchAllReports()
    else if (viewMode.value === 'team') await reportsStore.fetchTeamReports()
    else await reportsStore.fetchMyReports()
  } catch (error) {
    $q.notify({ color: 'negative', message: 'Failed to synchronize reports', icon: 'error' })
  } finally {
    loading.value = false
  }
}

watch(viewMode, () => loadReports())

const createNewReport = () => router.push('/reports/new')
const viewReport = (row) => router.push(`/reports/${row.id}`)
const editReport = (row) => router.push(`/reports/${row.id}/edit`)

const quickApprove = async (row) => {
  try {
    await reportsStore.reviewReport(row.id)
    $q.notify({ color: 'positive', message: 'Report marked as reviewed', icon: 'check' })
    loadReports()
  } catch (error) {
    $q.notify({ color: 'negative', message: 'Failed to update status', icon: 'error' })
  }
}

const exportCSV = async () => {
  try {
    $q.loading.show({ message: 'Compiling CSV Data...' })
    await reportsStore.exportReports('csv')
    $q.notify({ color: 'positive', message: 'CSV Exported' })
  } catch (error) {
    $q.notify({ color: 'negative', message: 'Export failed' })
  } finally {
    $q.loading.hide()
  }
}

const exportPDF = async () => {
  try {
    $q.loading.show({ message: 'Generating PDF Report...' })
    await reportsStore.exportReports('pdf')
    $q.notify({ color: 'positive', message: 'PDF Exported' })
  } catch (error) {
    $q.notify({ color: 'negative', message: 'Export failed' })
  } finally {
    $q.loading.hide()
  }
}

onMounted(() => loadReports())
</script>

<style lang="scss" scoped>
.reports-page {
  padding: 24px;
  background: transparent;
}

.page-content {
  background: var(--color-surface);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  padding: 40px;
  position: relative;
  overflow: hidden;

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
  margin-top: 4px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 24px;
}

.new-report-btn {
  font-weight: 700;
  border-radius: 12px;
  padding: 12px 24px;
  box-shadow: 0 4px 12px rgba(var(--color-primary-rgb), 0.2);
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(var(--color-primary-rgb), 0.3);
  }
}

.filters-card {
  border-radius: 16px;
  border: 1px solid var(--color-border-light);
  background: var(--color-bg);
  box-shadow: none;
}

.table-card {
  border-radius: 16px;
  border: 1px solid var(--color-border-light);
  background: var(--color-bg);
  box-shadow: none;
  overflow: hidden;

  .reports-table {
    :deep(thead tr th) {
      background: rgba(var(--color-text-primary-rgb), 0.02);
      font-weight: 700;
      color: var(--color-text-secondary);
      text-transform: uppercase;
      font-size: 0.75rem;
      letter-spacing: 0.05em;
    }

    :deep(tbody tr) {
      cursor: pointer;
      &:hover {
        background: rgba(var(--color-primary-rgb), 0.02) !important;
      }
    }
  }
}

.period-cell {
  font-weight: 600;
  color: var(--color-text-primary);
  display: flex;
  align-items: center;
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 12px;
  .user-name {
    font-weight: 500;
    color: var(--color-text-secondary);
  }
}

.status-badge {
  padding: 6px 12px;
  border-radius: 6px;
  font-weight: 700;
  font-size: 0.7rem;
  text-transform: uppercase;
}
</style>
