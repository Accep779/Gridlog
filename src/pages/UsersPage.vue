<template>
  <q-page class="users-page">
    <!-- Content Container -->
    <div class="page-content">
      <div class="q-gutter-md">
      <div class="row justify-between items-center">
        <div class="text-h4">User Management</div>
        <div class="row items-center q-gutter-sm">
          <q-btn outline color="primary" label="Bulk Import" icon="upload_file" @click="showBulkImport = true" />
          <q-btn color="primary" label="Add User" icon="person_add" @click="showAddUser = true" />
        </div>
      </div>

      <!-- Users Table -->
      <q-card>
        <q-table
          :rows="users"
          :columns="columns"
          row-key="id"
          :loading="loading"
          flat
          bordered
        >
          <template v-slot:body-cell-role="props">
            <q-td :props="props">
              <q-badge :color="getRoleColor(props.value)">{{ props.value }}</q-badge>
            </q-td>
          </template>

          <template v-slot:body-cell-is_active="props">
            <q-td :props="props">
              <q-badge :color="props.value ? 'positive' : 'negative'">
                {{ props.value ? 'Active' : 'Inactive' }}
              </q-badge>
            </q-td>
          </template>

          <template v-slot:body-cell-actions="props">
            <q-td :props="props">
              <q-btn flat dense color="primary" icon="edit" @click="editUser(props.row)">
                <q-tooltip>Edit</q-tooltip>
              </q-btn>
              <q-btn flat dense :color="props.row.active ? 'warning' : 'positive'" 
                     :icon="props.row.active ? 'block' : 'check'" 
                     @click="toggleUserStatus(props.row)">
                <q-tooltip>{{ props.row.active ? 'Deactivate' : 'Activate' }}</q-tooltip>
              </q-btn>
            </q-td>
          </template>
        </q-table>
      </q-card>
    </div>

    <!-- Add/Edit User Dialog -->
    <q-dialog v-model="showAddUser" persistent>
      <q-card style="min-width: 400px; max-width: 90vw">
        <q-card-section class="row items-center q-pb-none">
          <div class="text-h6">{{ editingUser ? 'Edit' : 'Add' }} User</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>

        <q-card-section>
          <q-form @submit="saveUser">
            <q-input
              v-model="formData.email"
              label="Email"
              type="email"
              outlined
              :rules="[val => !!val || 'Email is required', val => /.+@.+\..+/.test(val) || 'Invalid email']"
              class="q-mb-md"
            />

            <q-input
              v-model="formData.full_name"
              label="Full Name"
              outlined
              :rules="[val => !!val || 'Name is required']"
              class="q-mb-md"
            />

            <q-select
              v-model="formData.role"
              :options="roleOptions"
              label="Role"
              outlined
              :rules="[val => !!val || 'Role is required']"
              class="q-mb-md"
            />

            <q-select
              v-if="formData.role === 'employee'"
              v-model="formData.supervisor"
              :options="supervisors"
              option-label="full_name"
              option-value="id"
              label="Supervisor"
              outlined
              emit-value
              map-options
              class="q-mb-md"
            />

            <q-input
              v-if="!editingUser"
              v-model="formData.password"
              label="Temporary Password"
              :type="showPassword ? 'text' : 'password'"
              outlined
              :rules="[
                val => !!val || 'Password is required', 
                val => val.length >= 8 || 'Min 8 characters',
                val => /[A-Z]/.test(val) || 'Must contain uppercase letter',
                val => /[0-9]/.test(val) || 'Must contain number',
                val => /[!@#$%^&*()_+\-=[\]{}|;:,.<>?]/.test(val) || 'Must contain special char'
              ]"
              class="q-mb-md"
            >
              <template v-slot:append>
                <q-icon
                  :name="showPassword ? 'visibility' : 'visibility_off'"
                  class="cursor-pointer"
                  @click="showPassword = !showPassword"
                />
              </template>
            </q-input>

            <q-input
              v-if="!editingUser"
              v-model="formData.confirm_password"
              label="Confirm Password"
              :type="showConfirmPassword ? 'text' : 'password'"
              outlined
              :rules="[val => !!val || 'Confirmation is required', val => val === formData.password || 'Passwords must match']"
              class="q-mb-md"
            >
              <template v-slot:append>
                <q-icon
                  :name="showConfirmPassword ? 'visibility' : 'visibility_off'"
                  class="cursor-pointer"
                  @click="showConfirmPassword = !showConfirmPassword"
                />
              </template>
            </q-input>

            <div class="row q-gutter-sm q-mt-md">
              <q-btn label="Cancel" color="grey" v-close-popup />
              <q-btn label="Save" type="submit" color="primary" :loading="saving" />
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>
    <!-- Bulk Import Dialog -->
    <q-dialog v-model="showBulkImport" persistent>
      <q-card style="min-width: 400px">
        <q-card-section class="row items-center q-pb-none">
          <div class="text-h6">Bulk User Import</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>

        <q-card-section>
          <div class="text-body2 q-mb-md">
            Upload a CSV file with columns: <b>email, full_name, role, supervisor_email</b>.<br>
            Roles: employee, supervisor, admin.
          </div>
          <q-file
            v-model="bulkFile"
            label="Choose CSV File"
            outlined
            accept=".csv"
            :loading="importing"
          >
            <template v-slot:prepend>
              <q-icon name="attach_file" />
            </template>
          </q-file>
        </q-card-section>

        <q-card-actions align="right" class="bg-white text-teal">
          <q-btn flat label="Cancel" v-close-popup color="grey" />
          <q-btn flat label="Upload & Import" @click="handleBulkImport" :loading="importing" color="primary" />
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
const saving = ref(false)
const showAddUser = ref(false)
const showBulkImport = ref(false)
const importing = ref(false)
const bulkFile = ref(null)
const editingUser = ref(null)

// Password visibility state
const showPassword = ref(false)
const showConfirmPassword = ref(false)

const formData = ref({
  email: '',
  full_name: '',
  role: '',
  supervisor: null,
  password: '',
  confirm_password: ''
})

const roleOptions = ['employee', 'supervisor', 'admin']

const users = ref([])
const supervisors = ref([])

const columns = [
  { name: 'full_name', label: 'Name', field: 'full_name', align: 'left', sortable: true },
  { name: 'email', label: 'Email', field: 'email', align: 'left', sortable: true },
  { name: 'role', label: 'Role', field: 'role', align: 'center' },
  { name: 'supervisor_name', label: 'Supervisor', field: 'supervisor_name', align: 'left' },
  { name: 'is_active', label: 'Status', field: 'is_active', align: 'center' },
  { name: 'actions', label: 'Actions', field: 'actions', align: 'center' },
]

function getRoleColor(role) {
  const colors = { employee: 'grey', supervisor: 'primary', admin: 'negative' }
  return colors[role] || 'grey'
}

async function loadUsers() {
  loading.value = true
  try {
    // Backend: /auth/ (empty prefix with UserViewSet)
    const response = await api.get('/auth/')
    users.value = response.data.results || response.data
  } catch (error) {
    $q.notify({ type: 'negative', message: 'Failed to load users' })
  } finally {
    loading.value = false
  }
}

async function loadSupervisors() {
  try {
    // Backend doesn't have /supervisors endpoint, filter from users
    const response = await api.get('/auth/')
    supervisors.value = (response.data.results || response.data).filter(u => u.role === 'supervisor')
  } catch (error) {
    // Fallback: filter from users
    supervisors.value = users.value.filter(u => u.role === 'supervisor')
  }
}

async function saveUser() {
  saving.value = true
  try {
    if (editingUser.value) {
      // Backend: /auth/{id}/
      await api.patch(`/auth/${editingUser.value.id}/`, formData.value)
      $q.notify({ type: 'positive', message: 'User updated!' })
    } else {
      // Backend: /auth/ (POST to create)
      await api.post('/auth/', formData.value)
      $q.notify({ type: 'positive', message: 'User created!' })
    }
    showAddUser.value = false
    resetForm()
    loadUsers()
  } catch (error) {
    const msg = error.response?.data?.email?.[0] || 'Failed to save user'
    $q.notify({ type: 'negative', message: msg })
  } finally {
    saving.value = false
  }
}

function editUser(user) {
  editingUser.value = user
  formData.value = {
    email: user.email,
    full_name: user.full_name,
    role: user.role,
    supervisor: user.supervisor,
    supervisor: user.supervisor,
    password: '',
    confirm_password: ''
  }
  showAddUser.value = true
}

function toggleUserStatus(user) {
  $q.dialog({
    title: user.active ? 'Deactivate User' : 'Activate User',
    message: `${user.active ? 'Deactivate' : 'Activate'} ${user.full_name}?`,
    cancel: true,
    persistent: true
  }).onOk(async () => {
    try {
      // Backend: /auth/{id}/
      await api.patch(`/auth/${user.id}/`, { is_active: !user.active })
      $q.notify({ type: 'positive', message: `User ${user.active ? 'deactivated' : 'activated'}` })
      loadUsers()
    } catch (error) {
      $q.notify({ type: 'negative', message: 'Failed to update user' })
    }
  })
}

async function handleBulkImport() {
  if (!bulkFile.value) {
    $q.notify({ type: 'warning', message: 'Please select a file' })
    return
  }

  importing.value = true
  const formData = new FormData()
  formData.append('csv_file', bulkFile.value)

  try {
    const response = await api.post('/auth/bulk-import/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
    $q.notify({
      type: 'positive',
      message: response.data.message,
      multiLine: true,
      actions: [{ label: 'Dismiss', color: 'white' }]
    })
    
    if (response.data.errors.length > 0) {
      console.error('Import errors:', response.data.errors)
    }

    showBulkImport.value = false
    bulkFile.value = null
    loadUsers()
  } catch (error) {
    $q.notify({ type: 'negative', message: 'Import failed: ' + (error.response?.data?.error || 'Unknown error') })
  } finally {
    importing.value = false
  }
}

function resetForm() {
  formData.value = { email: '', full_name: '', role: '', supervisor: null, password: '', confirm_password: '' }
  editingUser.value = null
}

onMounted(() => {
  loadUsers()
  loadSupervisors()
})
</script>

<style lang="scss" scoped>
.users-page {
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