<template>
  <q-page class="periods-page">
    <div class="page-content">
      <div class="page-header">
        <h1 class="page-title">Reporting Periods</h1>
        <p class="page-subtitle">Manage reporting periods and deadlines</p>
      </div>

      <q-table
        :rows="periods"
        :columns="columns"
        row-key="id"
        :loading="loading"
        flat
        class="periods-table"
      >
        <template v-slot:body-cell-status="props">
          <q-td :props="props">
            <q-badge
              :color="props.row.is_closed ? 'negative' : 'positive'"
              :label="props.row.is_closed ? 'Closed' : 'Active'"
            />
          </q-td>
        </template>

        <template v-slot:body-cell-deadline="props">
          <q-td :props="props">
            {{ formatDate(props.row.deadline) }}
          </q-td>
        </template>

        <template v-slot:body-cell-actions="props">
          <q-td :props="props">
            <q-btn
              v-if="!props.row.is_closed"
              flat
              dense
              color="negative"
              icon="block"
              label="Close"
              @click="closePeriod(props.row)"
            />
            <q-btn
              v-else
              flat
              dense
              color="positive"
              icon="replay"
              label="Reopen"
              @click="reopenPeriod(props.row)"
            />
          </q-td>
        </template>
      </q-table>
    </div>
  </q-page>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { useReportsStore } from 'stores/reports'

const $q = useQuasar()
const reportsStore = useReportsStore()

const periods = ref([])
const loading = ref(false)

const columns = [
  { name: 'id', label: 'ID', field: 'id', align: 'left' },
  { name: 'start_date', label: 'Start Date', field: 'start_date', align: 'left', format: val => formatDate(val) },
  { name: 'end_date', label: 'End Date', field: 'end_date', align: 'left', format: val => formatDate(val) },
  { name: 'deadline', label: 'Deadline', field: 'deadline', align: 'left' },
  { name: 'status', label: 'Status', field: 'is_closed', align: 'center' },
  { name: 'actions', label: 'Actions', field: 'actions', align: 'center' }
]

const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString()
}

const fetchPeriods = async () => {
  loading.value = true
  try {
    periods.value = await reportsStore.fetchPeriods()
  } catch (error) {
    $q.notify({ color: 'negative', message: 'Failed to fetch periods', icon: 'error' })
  } finally {
    loading.value = false
  }
}

const closePeriod = async (period) => {
  try {
    await reportsStore.closePeriod(period.id)
    $q.notify({ color: 'positive', message: 'Period closed', icon: 'check' })
    fetchPeriods()
  } catch (error) {
    $q.notify({ color: 'negative', message: 'Failed to close period', icon: 'error' })
  }
}

const reopenPeriod = async (period) => {
  try {
    await reportsStore.reopenPeriod(period.id)
    $q.notify({ color: 'positive', message: 'Period reopened', icon: 'check' })
    fetchPeriods()
  } catch (error) {
    $q.notify({ color: 'negative', message: 'Failed to reopen period', icon: 'error' })
  }
}

onMounted(() => {
  fetchPeriods()
})
</script>

<style lang="scss" scoped>
.periods-page {
  padding: 24px;
  background: transparent;
  min-height: 100vh;
  position: relative;
  z-index: 1;
}

.page-content {
  background: var(--color-surface);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  padding: 40px;
}

.page-header {
  margin-bottom: 32px;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 8px 0;
}

.page-subtitle {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0;
}

.periods-table {
  margin-top: 24px;
}
</style>
