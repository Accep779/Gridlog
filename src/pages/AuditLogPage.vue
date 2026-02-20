<template>
  <q-page class="audit-page">
    <!-- Content Container -->
    <div class="page-content">
    <div class="row justify-between items-center q-mb-md">
      <div class="text-h5">Audit Log</div>
      <q-btn flat icon="refresh" @click="loadLogs" :loading="loading" />
    </div>

    <!-- Filters -->
    <div class="row q-col-gutter-md q-mb-md">
      <div class="col-12 col-md-3">
        <q-input v-model="filters.search" outlined dense placeholder="Search..." clearable>
          <template v-slot:prepend>
            <q-icon name="search" />
          </template>
        </q-input>
      </div>
      <div class="col-6 col-md-2">
        <q-select v-model="filters.action" :options="actionOptions" outlined dense emit-value map-options clearable label="Action" />
      </div>
      <div class="col-6 col-md-2">
        <q-select v-model="filters.user" :options="userOptions" outlined dense emit-value map-options clearable label="User" />
      </div>
      <div class="col-6 col-md-2">
        <q-input v-model="filters.dateFrom" type="date" outlined dense label="From Date" />
      </div>
      <div class="col-6 col-md-2">
        <q-input v-model="filters.dateTo" type="date" outlined dense label="To Date" />
      </div>
      <div class="col-12 col-md-1">
        <q-btn flat icon="clear" @click="clearFilters" title="Clear filters" />
      </div>
    </div>

    <!-- Audit Log Table -->
    <q-table
      :rows="filteredLogs"
      :columns="columns"
      row-key="id"
      :loading="loading"
      flat
      bordered
      :pagination="{ rowsPerPage: 20 }"
    >
      <template v-slot:body-cell-action="props">
        <q-td :props="props">
          <q-badge :color="getActionColor(props.value)" :label="props.value" />
        </q-td>
      </template>

      <template v-slot:body-cell-timestamp="props">
        <q-td :props="props">
          {{ formatDate(props.value) }}
        </q-td>
      </template>

      <template v-slot:body-cell-details="props">
        <q-td :props="props">
          <q-btn v-if="props.row.details" flat dense color="primary" icon="info" @click="showDetails(props.row)">
            <q-tooltip>View Details</q-tooltip>
          </q-btn>
        </q-td>
      </template>

      <template v-slot:no-data>
        <div class="full-width text-center q-pa-lg">
          <q-icon name="history" size="3em" color="grey-5" />
          <div class="text-grey-7 q-mt-sm">No audit logs found</div>
        </div>
      </template>
    </q-table>

    <!-- Details Dialog -->
    <q-dialog v-model="showDetailsDialog">
      <q-card style="min-width: 400px">
        <q-card-section>
          <div class="text-h6">Audit Log Details</div>
        </q-card-section>
        <q-card-section>
          <div v-if="selectedLog">
            <q-list>
              <q-item>
                <q-item-section>
                  <q-item-label caption>Action</q-item-label>
                  <q-item-label>{{ selectedLog.action }}</q-item-label>
                </q-item-section>
              </q-item>
              <q-item>
                <q-item-section>
                  <q-item-label caption>User</q-item-label>
                  <q-item-label>{{ selectedLog.user_name || selectedLog.user }}</q-item-label>
                </q-item-section>
              </q-item>
              <q-item>
                <q-item-section>
                  <q-item-label caption>Timestamp</q-item-label>
                  <q-item-label>{{ formatDate(selectedLog.timestamp) }}</q-item-label>
                </q-item-section>
              </q-item>
              <q-item v-if="selectedLog.target">
                <q-item-section>
                  <q-item-label caption>Target</q-item-label>
                  <q-item-label>{{ selectedLog.target }}</q-item-label>
                </q-item-section>
              </q-item>
              <q-item v-if="selectedLog.ip_address">
                <q-item-section>
                  <q-item-label caption>IP Address</q-item-label>
                  <q-item-label>{{ selectedLog.ip_address }}</q-item-label>
                </q-item-section>
              </q-item>
              <q-item v-if="selectedLog.details">
                <q-item-section>
                  <q-item-label caption>Details</q-item-label>
                  <q-item-label class="q-mt-sm">
                    <pre style="white-space: pre-wrap; font-size: 12px;">{{ JSON.stringify(selectedLog.details, null, 2) }}</pre>
                  </q-item-label>
                </q-item-section>
              </q-item>
            </q-list>
          </div>
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Close" color="primary" v-close-popup />
        </q-card-actions>
      </q-card>
    </q-dialog>
    </div>
  </q-page>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { api } from 'boot/axios'

const $q = useQuasar()

const loading = ref(false)
const logs = ref([])
const showDetailsDialog = ref(false)
const selectedLog = ref(null)

const filters = ref({
  search: '',
  action: null,
  user: null,
  dateFrom: '',
  dateTo: ''
})

const actionOptions = [
  { label: 'Login', value: 'login' },
  { label: 'Logout', value: 'logout' },
  { label: 'Create Report', value: 'create_report' },
  { label: 'Update Report', value: 'update_report' },
  { label: 'Submit Report', value: 'submit_report' },
  { label: 'Approve Report', value: 'approve_report' },
  { label: 'Reject Report', value: 'reject_report' },
  { label: 'Create User', value: 'create_user' },
  { label: 'Update User', value: 'update_user' },
  { label: 'Delete User', value: 'delete_user' }
]

const columns = [
  { name: 'timestamp', label: 'Timestamp', field: 'timestamp', align: 'left', sortable: true },
  { name: 'user_name', label: 'User', field: 'user_name', align: 'left', sortable: true },
  { name: 'action', label: 'Action', field: 'action', align: 'center' },
  { name: 'target', label: 'Target', field: 'target', align: 'left' },
  { name: 'ip_address', label: 'IP Address', field: 'ip_address', align: 'left' },
  { name: 'details', label: 'Details', field: 'details', align: 'center' }
]

const userOptions = computed(() => {
  const users = new Set()
  logs.value.forEach(l => {
    if (l.user_name) users.add(l.user_name)
  })
  return Array.from(users).map(u => ({ label: u, value: u }))
})

const filteredLogs = computed(() => {
  let result = logs.value

  if (filters.value.search) {
    const q = filters.value.search.toLowerCase()
    result = result.filter(l =>
      l.user_name?.toLowerCase().includes(q) ||
      l.action?.toLowerCase().includes(q) ||
      l.target?.toLowerCase().includes(q)
    )
  }

  if (filters.value.action) {
    result = result.filter(l => l.action === filters.value.action)
  }

  if (filters.value.user) {
    result = result.filter(l => l.user_name === filters.value.user)
  }

  if (filters.value.dateFrom) {
    result = result.filter(l => new Date(l.timestamp) >= new Date(filters.value.dateFrom))
  }

  if (filters.value.dateTo) {
    result = result.filter(l => new Date(l.timestamp) <= new Date(filters.value.dateTo + 'T23:59:59'))
  }

  return result
})

const getActionColor = (action) => {
  const colors = {
    login: 'positive',
    logout: 'grey',
    create_report: 'primary',
    update_report: 'secondary',
    submit_report: 'warning',
    approve_report: 'positive',
    reject_report: 'negative',
    create_user: 'primary',
    update_user: 'secondary',
    delete_user: 'negative'
  }
  return colors[action] || 'grey'
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString()
}

const clearFilters = () => {
  filters.value = { search: '', action: null, user: null, dateFrom: '', dateTo: '' }
}

const loadLogs = async () => {
  loading.value = true
  try {
    // Backend: /api/v1/auth/audit-logs/ -> call as /auth/audit-logs/
    const response = await api.get('/auth/audit-logs/')
    logs.value = response.data.results || response.data
  } catch (error) {
    // Generate mock data for demo
    logs.value = generateMockLogs()
    $q.notify({ color: 'info', message: 'Showing demo audit logs' })
  } finally {
    loading.value = false
  }
}

const showDetails = (row) => {
  selectedLog.value = row
  showDetailsDialog.value = true
}

const generateMockLogs = () => {
  const actions = ['login', 'create_report', 'submit_report', 'approve_report', 'update_user']
  const users = ['John Doe', 'Jane Smith', 'Bob Wilson', 'Admin User']
  const logs = []

  for (let i = 0; i < 20; i++) {
    const date = new Date()
    date.setDate(date.getDate() - Math.floor(Math.random() * 30))

    logs.push({
      id: i + 1,
      timestamp: date.toISOString(),
      user_name: users[Math.floor(Math.random() * users.length)],
      action: actions[Math.floor(Math.random() * actions.length)],
      target: `Report #${Math.floor(Math.random() * 100)}`,
      ip_address: `192.168.1.${Math.floor(Math.random() * 255)}`,
      details: { browser: 'Chrome', os: 'Windows' }
    })
  }

  return logs.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
}

onMounted(() => {
  loadLogs()
})
</script>

<style lang="scss" scoped>
.audit-page {
  padding: 24px;
  background: transparent;
  min-height: 100vh;
  position: relative;
  z-index: 1;
}

// New: Content Container - The "Stage"
.page-content {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-xl);
  padding: 32px;
  position: relative;
  overflow: hidden;

  // Blue IQ Frame
  &::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    bottom: 0;
    width: 6px;
    background: linear-gradient(to bottom, var(--color-primary), var(--color-secondary));
  }

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
    background: radial-gradient(circle, rgba(99, 102, 241, 0.05) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
  }

  > * {
    position: relative;
    z-index: 1;
  }
}
</style>
