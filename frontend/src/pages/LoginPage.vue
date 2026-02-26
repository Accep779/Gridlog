<template>
  <q-layout view="lHh Lpr lFf" class="login-layout">
    <q-page-container>
      <q-page class="login-page row">
        
        <!-- Left Side: Brand Imagery -->
        <div class="col-12 col-md-6 flex flex-center brand-section relative-position">
          <!-- Background Effects -->
          <div class="brand-bg"></div>
          <div class="brand-glow"></div>
          
          <div class="brand-content text-white q-pa-xl z-top">
            <div class="row items-center q-mb-xl stagger-1">
              <q-icon name="radar" size="56px" class="q-mr-md" />
              <div class="text-h3 text-weight-bolder tracking-tight">Gridlog</div>
            </div>
            
            <h2 class="text-h2 text-weight-bold q-mb-lg stagger-2 leading-tight">
              Enterprise <br/>
              <span class="text-transparent bg-clip-text text-gradient">Intelligence</span>
            </h2>
            
            <p class="text-h6 text-weight-regular text-blue-2 q-mb-xl max-w-md stagger-3" style="opacity: 0.9; line-height: 1.6;">
              Secure, role-based weekly performance tracking for government and corporate organizations.
            </p>

            <div class="feature-pills row q-gutter-sm stagger-4">
              <q-chip outline color="white" text-color="white" class="premium-chip">End-to-End Encrypted</q-chip>
              <q-chip outline color="white" text-color="white" class="premium-chip">Role-Based Access</q-chip>
              <q-chip outline color="white" text-color="white" class="premium-chip">Audit Ready</q-chip>
            </div>
          </div>
        </div>

        <!-- Right Side: Login Form -->
        <div class="col-12 col-md-6 flex flex-center form-section">
          <div class="form-container q-pa-xl">
            <div class="q-mb-xl text-center">
              <h1 class="text-h4 text-weight-bolder text-dark q-mb-sm">Welcome Back</h1>
              <p class="text-subtitle1 text-grey-6">Sign in to your secure workspace</p>
            </div>

            <q-form @submit="handleLogin" class="q-gutter-lg">
              <div class="input-wrapper">
                <label class="text-weight-bold text-dark q-mb-xs block">Official Email</label>
                <q-input
                  v-model="email"
                  type="email"
                  placeholder="name@organization.gov"
                  outlined
                  class="premium-input-light"
                  hide-bottom-space
                  :rules="[val => !!val || 'Email is required', val => /.+@.+\..+/.test(val) || 'Invalid email format']"
                >
                  <template v-slot:prepend>
                    <q-icon name="mail" color="grey-5" />
                  </template>
                </q-input>
              </div>

              <div class="input-wrapper">
                <div class="row justify-between items-center q-mb-xs">
                  <label class="text-weight-bold text-dark block">Password</label>
                  <q-btn flat no-caps label="Forgot Password?" color="primary" dense size="sm" class="forgot-link text-weight-bold" />
                </div>
                <q-input
                  v-model="password"
                  :type="isPwd ? 'password' : 'text'"
                  placeholder="••••••••"
                  outlined
                  class="premium-input-light"
                  hide-bottom-space
                  :rules="[val => !!val || 'Password is required']"
                >
                  <template v-slot:prepend>
                    <q-icon name="lock" color="grey-5" />
                  </template>
                  <template v-slot:append>
                    <q-icon
                      :name="isPwd ? 'visibility_off' : 'visibility'"
                      class="cursor-pointer text-grey-5 hover-primary transition"
                      @click="isPwd = !isPwd"
                    />
                  </template>
                </q-input>
              </div>

              <div class="row items-center q-mt-md">
                <q-checkbox v-model="rememberMe" label="Keep me signed in for 30 days" dense color="primary" class="text-grey-8 text-weight-medium" />
              </div>

              <q-btn
                label="Authenticate Session"
                type="submit"
                unelevated
                class="full-width login-btn-premium q-mt-lg"
                size="lg"
                :loading="loading"
              >
                <template v-slot:loading>
                  <q-spinner-dots class="on-left" />
                  Authenticating...
                </template>
              </q-btn>
            </q-form>

            <!-- Error Banner -->
            <transition name="slide-fade">
              <div v-if="error" class="error-banner row items-center q-mt-lg q-pa-md rounded-borders">
                <q-icon name="error" color="negative" size="24px" class="q-mr-md" />
                <div class="text-negative text-weight-medium" style="flex: 1">{{ error }}</div>
              </div>
            </transition>
            
            <div class="q-mt-xl text-center text-caption text-grey-5">
              <q-icon name="security" size="16px" class="q-mr-xs" style="transform: translateY(-2px)" />
              Protected by Gridlog Enterprise Security. <br/>
              Unauthorized access is strictly prohibited.
            </div>
          </div>
        </div>

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
    error.value = err.response?.data?.detail || 'Invalid credentials. Please verify your email and password.'
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
/* Core Layout */
.login-page {
  min-height: 100vh;
  background: #f8fafc;
}

/* Typography Utilities */
.tracking-tight { letter-spacing: -0.04em; }
.leading-tight { line-height: 1.1; }
.max-w-md { max-width: 480px; }
.block { display: block; }
.transition { transition: all 0.3s ease; }

/* Left Side: Brand Section */
.brand-section {
  background: linear-gradient(145deg, #0a3a63 0%, #0F4C81 100%);
  overflow: hidden;
  
  &::before {
    content: '';
    position: absolute;
    top: 0; right: 0; bottom: 0; left: 0;
    background: url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCI+CiAgPGNpcmNsZSBjeD0iMSIgY3k9IjEiIHI9IjEiIGZpbGw9InJnYmEoMjU1LDI1NSwyNTUsMC4wNSkiLz4KPC9zdmc+') repeat;
    opacity: 0.4;
  }
}

.brand-glow {
  position: absolute;
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, rgba(var(--color-primary-rgb, 59,130,246), 0.4) 0%, transparent 60%);
  top: -20%;
  left: -20%;
  filter: blur(60px);
  animation: pulse-glow 8s ease-in-out infinite alternate;
}

@keyframes pulse-glow {
  0% { transform: scale(1) translate(0, 0); opacity: 0.5; }
  100% { transform: scale(1.2) translate(5%, 5%); opacity: 0.8; }
}

.brand-content {
  width: 100%;
  max-width: 600px;
  padding: 0 40px;
}

.text-gradient {
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-image: linear-gradient(90deg, #FFFFFF 0%, rgba(255, 255, 255, 0.6) 100%);
}

.premium-chip {
  background: rgba(255, 255, 255, 0.1) !important;
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.3) !important;
  font-weight: 600;
  letter-spacing: 0.5px;
  padding: 8px 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* Animations loading in */
.stagger-1 { animation: fade-up 0.8s ease-out 0.1s both; }
.stagger-2 { animation: fade-up 0.8s ease-out 0.2s both; }
.stagger-3 { animation: fade-up 0.8s ease-out 0.3s both; }
.stagger-4 { animation: fade-up 0.8s ease-out 0.4s both; }

@keyframes fade-up {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Right Side: Form Section */
.form-section {
  background: #ffffff;
}

.form-container {
  width: 100%;
  max-width: 480px;
}

.input-wrapper {
  label {
    font-size: 0.9rem;
    color: #334155;
  }
}

.premium-input-light {
  :deep(.q-field__control) {
    background: #f8fafc;
    border-radius: 12px;
    height: 56px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    
    &:before {
      border: 1px solid #e2e8f0;
    }
    
    &:hover:before {
      border-color: #cbd5e1;
    }
  }

  &.q-field--focused {
    :deep(.q-field__control) {
      background: #ffffff;
      box-shadow: 0 0 0 4px rgba(var(--color-primary-rgb, 37, 99, 235), 0.1);
      
      &:before {
        border-color: var(--color-primary, #2563eb);
        border-width: 2px;
      }
    }
  }
  
  :deep(.q-field__prepend), :deep(.q-field__append) {
    height: 56px;
  }
}

.hover-primary:hover {
  color: var(--color-primary, #2563eb) !important;
}

.forgot-link {
  transition: opacity 0.2s;
  &:hover { opacity: 0.8; }
}

.login-btn-premium {
  background: var(--color-primary, #2563eb);
  color: white;
  border-radius: 12px;
  font-weight: 800;
  letter-spacing: 0.5px;
  height: 56px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 6px -1px rgba(var(--color-primary-rgb, 37, 99, 235), 0.1), 0 2px 4px -1px rgba(var(--color-primary-rgb, 37, 99, 235), 0.06);

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 15px -3px rgba(var(--color-primary-rgb, 37, 99, 235), 0.2), 0 4px 6px -2px rgba(var(--color-primary-rgb, 37, 99, 235), 0.1);
    background: var(--color-primary-hover, #1d4ed8);
  }
  
  &:active {
    transform: translateY(0);
  }
}

.error-banner {
  background: #fef2f2;
  border: 1px solid #fecaca;
}

/* Transitions */
.slide-fade-enter-active { transition: all 0.3s ease-out; }
.slide-fade-leave-active { transition: all 0.2s cubic-bezier(1, 0.5, 0.8, 1); }
.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateY(-10px);
  opacity: 0;
}

/* Responsive Overrides */
@media (max-width: 1023px) {
  .brand-section {
    min-height: 400px;
    padding: 60px 20px;
  }
  .form-container {
    padding: 40px 20px;
  }
}
</style>