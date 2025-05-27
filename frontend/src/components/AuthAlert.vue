<!-- Auth status alert component -->
<template>
  <v-alert
    v-if="showAlert"
    :type="alertType"
    :text="alertText"
    class="auth-alert"
    closable
    @click:close="clearError"
    border="start"
    elevation="2"
    variant="tonal"
    position="fixed"
    location="top"
  >
    {{ alertText }}
    <template v-if="isTokenError && authStore.token">
      <v-btn variant="text" color="primary" @click="handleRefreshToken" :loading="authStore.refreshingToken">
        Refresh Token
      </v-btn>
    </template>
  </v-alert>
</template>

<script setup>
import { computed, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

const showAlert = computed(() => {
  return !!authStore.error || authStore.refreshingToken
})

const alertType = computed(() => {
  if (authStore.refreshingToken) return 'info'
  if (authStore.error) return 'error'
  return 'success'
})

const alertText = computed(() => {
  if (authStore.refreshingToken) return 'Refreshing authentication...'
  return authStore.error || ''
})

const isTokenError = computed(() => {
  const error = authStore.error || ''
  return error.includes('token') || error.includes('unauthorized') || error.includes('401')
})

const clearError = () => {
  authStore.setError('')
}

const handleRefreshToken = async () => {
  try {
    await authStore.refreshToken()
    authStore.setError('')
  } catch (error) {
    console.error('Authentication refresh failed')
  }
}

watch(() => authStore.token, (newToken) => {
  if (!newToken && authStore.error) {
    // If token is cleared and there's an error, clear it after 5 seconds
    setTimeout(() => {
      clearError()
    }, 5000)
  }
})
</script>

<style scoped>
.auth-alert {
  z-index: 9999;
  max-width: 100%;
  width: 400px;
  right: 20px;
  top: 20px;
}
</style> 