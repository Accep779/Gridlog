<template>
  <q-page padding class="page-container">
    <div class="row items-center q-mb-xl page-header fade-in">
      <div>
        <h1 class="text-h4 text-weight-bolder q-ma-none text-dark">Team Oversight</h1>
        <p class="text-subtitle1 text-grey-7 q-mt-sm q-mb-none">Monitor and manage your direct reports</p>
      </div>
      <q-space />
      <q-btn
        unelevated
        color="primary"
        icon="refresh"
        label="Refresh Data"
        class="action-btn"
        @click="loadData"
        :loading="loading"
      />
    </div>

    <!-- Summary Cards -->
    <div class="row q-col-gutter-lg q-mb-xl fade-in-delay-1">
      <div class="col-12 col-md-3">
        <q-card class="metric-card glass-panel" flat bordered>
          <q-card-section>
            <div class="row items-center no-wrap">
              <div class="col">
                <div class="text-subtitle2 text-grey-7 text-uppercase text-weight-bold">Team Members</div>
                <div class="text-h4 text-weight-bolder q-mt-sm">{{ stats.total_members }}</div>
              </div>
              <div class="col-auto">
                <q-avatar size="56px" color="primary" text-color="white" class="shadow-3">
                  <q-icon name="groups" size="32px" />
                </q-avatar>
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <!-- Team Members Table -->
    <div class="row fade-in-delay-2">
      <div class="col-12">
        <q-card class="content-card glass-panel" flat bordered>
          <q-table
            :rows="stats.members"
            :columns="columns"
            row-key="id"
            :loading="loading"
            flat
            class="bg-transparent"
            :pagination="{ rowsPerPage: 15 }"
          >
            <!-- Custom header styling -->
            <template v-slot:header="props">
              <q-tr :props="props" class="bg-grey-1 text-primary">
                <q-th v-for="col in props.cols" :key="col.name" :props="props" class="text-weight-bold" style="font-size: 13px">
                  {{ col.label }}
                </q-th>
              </q-tr>
            </template>

            <!-- Custom Status Body Cell -->
            <template v-slot:body-cell-current_status="props">
              <q-td :props="props">
                <q-badge :color="getStatusColor(props.value)" class="text-weight-medium q-pa-sm" rounded>
                  {{ props.value }}
                </q-badge>
              </q-td>
            </template>

            <!-- Custom Actions Body Cell -->
            <template v-slot:body-cell-actions="props">
              <q-td :props="props">
                <q-btn flat round color="primary" icon="history" size="sm" @click="handleMemberHistory(props.row.id)">
                  <q-tooltip>View Report History</q-tooltip>
                </q-btn>
              </q-td>
            </template>
          </q-table>
        </q-card>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useReportsStore } from 'stores/reports'
import { useQuasar } from 'quasar'

const router = useRouter()
const reportsStore = useReportsStore()
const $q = useQuasar()

const loading = ref(false)
const stats = ref({
  total_members: 0,
  members: []
})

const columns = [
  { name: 'name', required: true, label: 'Employee Name', align: 'left', field: r => r.name, sortable: true, classes: 'text-weight-bold' },
  { name: 'email', label: 'Email', align: 'left', field: r => r.email, sortable: true, classes: 'text-grey-7' },
  { name: 'total_reports', label: 'Total Reports', align: 'center', field: r => r.total_reports, sortable: true },
  { name: 'pending_review', label: 'Pending Review', align: 'center', field: r => r.pending_review, sortable: true, classes: 'text-warning text-weight-bold' },
  { name: 'reviewed', label: 'Reviewed', align: 'center', field: r => r.reviewed, sortable: true, classes: 'text-positive' },
  { name: 'current_status', label: 'Current Period Status', align: 'center', field: r => r.current_status, sortable: true },
  { name: 'actions', label: 'Actions', align: 'center', sortable: false }
]

const loadData = async () => {
  loading.value = true
  try {
    const data = await reportsStore.fetchTeamOversightStats()
    stats.value = data
  } catch (error) {
    console.error(error)
    $q.notify({
      type: 'negative',
      message: 'Failed to load team oversight data',
      icon: 'warning'
    })
  } finally {
    loading.value = false
  }
}

const getStatusColor = (status) => {
  if (!status) return 'grey'
  const s = status.toLowerCase()
  if (s.includes('not started')) return 'grey'
  if (s.includes('draft')) return 'info'
  if (s.includes('submit')) return 'warning'
  if (s.includes('review')) return 'positive'
  return 'primary'
}

const handleMemberHistory = (employeeId) => {
  // Can filter report view to show only reports from this employee using query params natively supported by Quasar Tables
  router.push(`/reports?view=team&employee=${employeeId}`)
}

onMounted(() => {
  loadData()
})
</script>

<style lang="scss" scoped>
.page-container {
  max-width: 1400px;
  margin: 0 auto;
}

// Fade in animations
.fade-in { animation: fadeIn 0.6s ease-out forwards; }
.fade-in-delay-1 { animation: fadeIn 0.6s ease-out 0.1s forwards; opacity: 0; }
.fade-in-delay-2 { animation: fadeIn 0.6s ease-out 0.2s forwards; opacity: 0; }
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

// Cards styling matching Blue IQ Theme
.glass-panel {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(15, 76, 129, 0.08);
  border-radius: var(--radius-xl);
  box-shadow: 0 4px 20px rgba(15, 23, 42, 0.03);
  transition: all var(--transition-base);

  &:hover {
    box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
    transform: translateY(-2px);
  }
}

.content-card {
  border-radius: var(--radius-xl);
  overflow: hidden;

  // Customizing Quasar Table within Glass Card
  :deep(.q-table__container) {
    background: transparent;
  }
  
  :deep(.q-table th) {
    border-bottom: 2px solid rgba(15, 76, 129, 0.06);
  }
}

.action-btn {
  border-radius: var(--radius-md);
  padding: 8px 24px;
  font-weight: 600;
  letter-spacing: 0.3px;
  box-shadow: 0 4px 12px rgba(15, 76, 129, 0.2);
  transition: all var(--transition-fast);

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(15, 76, 129, 0.3);
  }
}
</style>
