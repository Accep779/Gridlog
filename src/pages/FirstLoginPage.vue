<template>
  <q-layout view="lHh Lpr lFf">
    <q-page-container>
      <q-page class="flex flex-center bg-grey-10">
        <q-card class="q-pa-lg" style="width: 400px; max-width: 90vw">
          <q-card-section class="text-center">
            <div class="text-h5 q-mb-md">Set Your Password</div>
            <div class="text-subtitle2 text-grey-7">First-time login security requirement</div>
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
                  val => val.length >= 8 || 'Minimum 8 characters'
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

          <q-card-section v-if="error" class="bg-negative text-white q-pa-sm rounded-borders">
            {{ error }}
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
    error.value = err.response?.data?.new_password?.[0] || 'Failed to set password'
  } finally {
    loading.value = false
  }
}
</script>