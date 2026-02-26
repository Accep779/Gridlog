<template>
  <q-layout view="lHh Lpr lFf">
    <q-page-container>
      <q-page class="flex flex-center login-page">
        <!-- Atmospheric Background -->
        <div class="login-atmosphere">
          <div class="atmosphere-orb atmosphere-orb--1"></div>
          <div class="atmosphere-orb atmosphere-orb--2"></div>
        </div>

        <q-card class="login-card stagger-item">
          <q-card-section class="text-center q-pb-none">
            <div class="logo-container q-mb-md">
              <q-icon name="lock_reset" size="48px" class="gradient-text" />
            </div>
            <h1 class="text-h4 text-weight-bold gradient-text q-mb-xs">Set Password</h1>
            <p class="text-subtitle2 text-grey-7 q-mb-lg">First-time login security requirement</p>
          </q-card-section>

          <q-card-section class="q-pb-xs">
            <div class="password-rules text-caption text-grey-6 q-mb-md">
              Password must contain:
              <ul class="q-mt-xs">
                <li>At least 8 characters</li>
                <li>One uppercase letter (A-Z)</li>
                <li>One number (0-9)</li>
                <li>One special character (!@#$%^&*...)</li>
              </ul>
            </div>
          </q-card-section>

          <q-card-section>
            <q-form @submit="handleSubmit" class="q-gutter-md">
              <q-input
                v-model="newPassword"
                :type="isPwd ? 'password' : 'text'"
                label="New Password"
                outlined
                :rules="[
                  val => !!val || 'Password is required',
                  val => val.length >= 8 || 'Minimum 8 characters',
                  val => /[A-Z]/.test(val) || 'Must contain an uppercase letter',
                  val => /[0-9]/.test(val) || 'Must contain a number',
                  val => /[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(val) || 'Must contain a special character'
                ]"
              >
                <template v-slot:prepend>
                  <q-icon name="lock" />
                </template>
              </q-input>

              <q-input
                v-model="confirmPassword"
                :type="isPwd ? 'password' : 'text'"
                label="Confirm Password"
                outlined
                :rules="[
                  val => !!val || 'Please confirm your password',
                  val => val === newPassword || 'Passwords do not match'
                ]"
              >
                <template v-slot:prepend>
                  <q-icon name="lock" />
                </template>
              </q-input>

              <q-btn
                label="Set Password"
                type="submit"
                color="primary"
                class="full-width"
                :loading="loading"
              />
            </q-form>
          </q-card-section>

          <q-card-section v-if="error" class="login-error q-mx-lg q-mb-lg q-pa-sm rounded-borders">
            <q-icon name="error_outline" size="20px" class="q-mr-sm" />
            <span>{{ error }}</span>
          </q-card-section>
        </q-card>
      </q-page>
    </q-page-container>
  </q-layout>
</template>

<style lang="scss" scoped>
.login-page {
  min-height: 100vh;
  background: var(--color-bg, #0F172A);
  position: relative;
  overflow: hidden;
}

.login-atmosphere {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.atmosphere-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.15;

  &--1 {
    width: 600px; height: 600px;
    background: radial-gradient(circle, #1976D2, transparent);
    top: -200px; left: -200px;
  }

  &--2 {
    width: 500px; height: 500px;
    background: radial-gradient(circle, #8B5CF6, transparent);
    bottom: -150px; right: -150px;
  }
}

.login-card {
  position: relative;
  z-index: 1;
  width: 420px;
  max-width: 95vw;
  border-radius: 24px;
  padding: 24px 8px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px);
}

.gradient-text {
  background: linear-gradient(135deg, #1976D2, #8B5CF6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.login-error {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  color: #EF4444;
  border-radius: 8px;
  display: flex;
  align-items: center;
}
</style>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from 'stores/auth'
import { useQuasar } from 'quasar'

const router = useRouter()
const authStore = useAuthStore()
const $q = useQuasar()

const newPassword = ref('')
const confirmPassword = ref('')
const isPwd = ref(true)
const loading = ref(false)
const error = ref('')

async function handleSubmit() {
  if (newPassword.value !== confirmPassword.value) {
    error.value = 'Passwords do not match'
    return
  }
  
  loading.value = true
  error.value = ''
  
  try {
    await authStore.firstLoginPassword(newPassword.value, confirmPassword.value)
    
    $q.notify({
      type: 'positive',
      message: 'Password set successfully!'
    })
    
    router.push('/dashboard')
  } catch (err) {
    // Handle the custom exception handler's wrapped error format: { error: { new_password: [...] } }
    const errData = err.response?.data
    if (errData?.error && typeof errData.error === 'object') {
      const details = Object.entries(errData.error)
        .map(([, v]) => Array.isArray(v) ? v.join(', ') : v)
        .join(' ')
      error.value = details
    } else if (errData?.error && typeof errData.error === 'string') {
      error.value = errData.error
    } else {
      error.value = errData?.detail || 'Failed to set password. Check requirements above.'
    }
  } finally {
    loading.value = false
  }
}
</script>