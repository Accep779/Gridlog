<template>
  <q-layout view="lHh Lpr lFf" class="login-layout">
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
              <q-icon name="grid_view" size="48px" class="gradient-text" />
            </div>
            <h1 class="text-h4 text-weight-bold gradient-text q-mb-xs">Gridlog</h1>
            <p class="text-subtitle2 text-grey-7">Intelligence & Performance Tracking</p>
          </q-card-section>

          <q-card-section class="q-pa-lg">
            <q-form @submit="handleLogin" class="q-gutter-md">
              <div class="input-group">
                <q-input
                  v-model="email"
                  type="email"
                  label="Email"
                  outlined
                  dense
                  hide-bottom-space
                  class="premium-input"
                  :rules="[val => !!val || 'Email is required', val => /.+@.+\..+/.test(val) || 'Invalid email']"
                >
                  <template v-slot:prepend>
                    <q-icon name="mail_outline" size="20px" color="primary" />
                  </template>
                </q-input>
              </div>

              <div class="input-group">
                <q-input
                  v-model="password"
                  :type="isPwd ? 'password' : 'text'"
                  label="Password"
                  outlined
                  dense
                  hide-bottom-space
                  class="premium-input"
                  :rules="[val => !!val || 'Password is required']"
                >
                  <template v-slot:prepend>
                    <q-icon name="lock_outline" size="20px" color="primary" />
                  </template>
                  <template v-slot:append>
                    <q-icon
                      :name="isPwd ? 'visibility_off' : 'visibility'"
                      size="20px"
                      class="cursor-pointer text-grey-6"
                      @click="isPwd = !isPwd"
                    />
                  </template>
                </q-input>
              </div>

              <div class="row justify-between items-center q-pt-sm">
                <q-checkbox v-model="rememberMe" label="Remember me" dense size="sm" class="text-grey-7" />
                <q-btn flat no-caps label="Forgot password?" color="primary" dense size="sm" />
              </div>

              <q-btn
                label="Sign In"
                type="submit"
                unelevated
                class="full-width login-btn q-mt-md"
                :loading="loading"
              />
            </q-form>
          </q-card-section>

          <q-card-section v-if="error" class="login-error q-mx-lg q-mb-lg q-pa-sm rounded-borders">
            <q-icon name="error_outline" size="20px" class="q-mr-sm" />
            <span>{{ error }}</span>
          </q-card-section>

          <q-card-section class="text-center q-pt-none q-pb-lg">
            <div class="text-caption text-grey-6">
              Don't have an account? <span class="text-primary text-weight-bold cursor-pointer">Contact Administrator</span>
            </div>
          </q-card-section>
        </q-card>
      </q-page>
    </q-page-container>
  </q-layout>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from 'stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const email = ref('')
const password = ref('')
const rememberMe = ref(false)
const isPwd = ref(true)
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  loading.value = true
  error.value = ''
  
  try {
    const result = await authStore.login(email.value, password.value)
    
    if (result.firstLogin) {
      router.push('/first-login')
    } else {
      router.push('/dashboard')
    }
  } catch (err) {
    error.value = err.response?.data?.detail || 'Invalid email or password. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.login-page {
  background: var(--color-bg-dark);
  min-height: 100vh;
  position: relative;
  overflow: hidden;
}

.login-atmosphere {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
  z-index: 0;

  .atmosphere-orb {
    position: absolute;
    filter: blur(80px);
    border-radius: 50%;
    opacity: 0.15;
    animation: orbFloat 20s infinite alternate;

    &--1 {
      top: -10%;
      left: -5%;
      width: 40vw;
      height: 40vw;
      background: var(--color-primary);
    }

    &--2 {
      bottom: -15%;
      right: -5%;
      width: 50vw;
      height: 50vw;
      background: var(--color-secondary);
      animation-delay: -5s;
    }
  }
}

@keyframes orbFloat {
  from { transform: translate(0, 0) scale(1); }
  to { transform: translate(5%, 5%) scale(1.1); }
}

.login-card {
  width: 440px;
  max-width: 90vw;
  background: rgba(var(--color-surface-rgb), 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(var(--color-border-rgb), 0.2);
  border-radius: var(--radius-xl);
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  z-index: 10;
}

.gradient-text {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.premium-input {
  :deep(.q-field__control) {
    background: rgba(var(--color-bg-rgb), 0.4);
    transition: all var(--transition-base);

    &:hover {
      background: rgba(var(--color-bg-rgb), 0.6);
    }
  }

  &.q-field--focused {
    :deep(.q-field__control) {
      background: var(--color-surface);
      box-shadow: 0 0 0 4px rgba(var(--color-primary-rgb), 0.1);
    }
  }
}

.login-btn {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-hover) 100%);
  color: white;
  font-weight: 700;
  height: 48px;
  font-size: 1rem;
  letter-spacing: 0.01em;
  transition: all var(--transition-base);

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 20px -10px rgba(var(--color-primary-rgb), 0.5);
  }
}

.login-error {
  display: flex;
  align-items: center;
  background: rgba(var(--color-error-rgb), 0.1);
  border: 1px solid rgba(var(--color-error-rgb), 0.2);
  color: var(--color-error);
  font-size: 0.875rem;
}
</style>