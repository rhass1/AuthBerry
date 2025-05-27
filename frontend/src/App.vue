<template>
  <v-app class="auth-berry-app">

    <v-main>
      <v-container fluid class="main-content">
        <transition name="fade" mode="out-in">
          <router-view></router-view>
        </transition>
      </v-container>
    </v-main>

    <Footer :is-admin="authStore.isAdmin" />
    
    <NotificationsManager />
  </v-app>
</template>

<script setup>
import { ref, computed, onMounted, watch, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useSplashStore } from '@/stores/splash'
import Footer from '@/components/Footer.vue'
import NotificationsManager from '@/components/NotificationsManager.vue'
import axios from 'axios'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const splashStore = useSplashStore()

onMounted(async () => {
  await authStore.init();
  
  try {
    if (authStore.token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${authStore.token}`;
    }
    
    const usersExist = await authStore.checkIfUsersExist();
    
    if (!usersExist && route.name !== 'setup') {
      router.push('/setup');
      return;
    }
    
    if (authStore.token) {
      await authStore.refreshUserData();
    }
    
    if (authStore.isAuthenticated && route.path === '/') {
      router.push('/dashboard');
    }
  } catch (error) {
    // Error during app initialization (console.error removed)
  }
})

watch(() => authStore.anyUsersExist, (usersExist) => {
  if (usersExist === false && route.name !== 'setup') {
    router.push('/setup')
  }
})

watch(() => authStore.isAuthenticated, (isAuthenticated) => {
  if (isAuthenticated && route.path === '/') {
    router.push('/dashboard')
  }
})

const handleLogout = async () => {
  splashStore.resetSplashState()
  
  try {
    await authStore.logout()
    router.push('/')
  } catch (error) {
    // Logout error (console.error removed)
  }
}
</script>

<style>
.auth-berry-app {
  background-color: var(--v-background-base, #0A0E14) !important;
  color: rgba(255, 255, 255, 0.8); 
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

.main-content {
  display: flex;
  flex-direction: column;
  flex: 1 1 auto;
  padding: 0 !important;
  overflow-y: auto;
  position: relative;
}

.v-main {
  display: flex;
  flex-direction: column;
  flex: 1 1 auto;
  overflow: hidden;
}

.custom-glass {
  background: rgba(16, 23, 35, 0.7) !important;
  backdrop-filter: blur(10px) !important;
  -webkit-backdrop-filter: blur(10px) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  border-radius: 8px !important;
}

@media (max-width: 767px) {
  .custom-glass,
  .v-overlay,
  .v-menu__content,
  .v-overlay__content,
  .v-overlay__scrim {
    backdrop-filter: none !important;
    -webkit-backdrop-filter: none !important;
  }
  
  .v-overlay {
    z-index: 9999 !important;
  }
  
  .v-menu__content {
    background: rgba(15, 22, 32, 0.95) !important;
    box-shadow: 0 0 20px rgba(0, 0, 0, 0.6) !important;
  }
  
  .v-overlay {
    touch-action: none !important;
  }
  
  .v-list-item {
    min-height: 48px !important;
  }
  
  .v-overlay__scrim {
    pointer-events: none !important;
  }
}

.border-top {
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.text-white-80 {
  color: rgba(255, 255, 255, 0.8);
}

/* Apply click sound directive to all buttons */
.v-btn {
  min-width: 0;
  padding-left: 16px;
  padding-right: 16px;
  width: auto;
}

:deep(.v-field__input) {
  background-color: transparent !important;
}

:deep(.v-field__outline) {
  --v-field-border-opacity: 0.1;
}

:deep(.v-text-field) {
  background-color: transparent !important;
}

:deep(.v-field--variant-filled .v-field__overlay) {
  background-color: transparent !important;
}

:deep(.v-field--variant-outlined .v-field__outline) {
  opacity: 0.1;
}

:deep(.v-field--variant-plain, .v-field--variant-underlined) {
  opacity: 0.9;
}

:deep(.v-field) {
  background-color: transparent !important;
}

:deep(.v-field__overlay) {
  background-color: transparent !important;
  opacity: 0 !important;
}

:deep(.v-field__field) {
  background-color: transparent !important;
}

:deep(.v-field--focused) {
  background-color: transparent !important;
}

:deep(.v-field--active) {
  background-color: transparent !important;
}

:deep(.v-select) {
  background-color: transparent !important;
}

:deep(.v-select__selection) {
  background-color: transparent !important;
}

:deep(.v-textarea) {
  background-color: transparent !important;
}

:deep(.v-file-input) {
  background-color: transparent !important;
}

:deep(.v-combobox) {
  background-color: transparent !important;
}

:deep(.v-input) {
  background-color: transparent !important;
}

:deep(.v-input__slot) {
  background-color: transparent !important;
}

:deep(.v-input__control) {
  background-color: transparent !important;
}

:deep(.form-field),
:deep(.form-field:focus-within),
:deep(.form-field:hover),
:deep(.form-field:active) {
  background: transparent !important;
}

:deep(.v-input__control),
:deep(.v-field),
:deep(.v-input),
:deep(.v-selection-control),
:deep(.v-selection-control__wrapper),
:deep(.v-selection-control__input),
:deep(.v-field__field),
:deep(.v-text-field__slot),
:deep(.v-field__input),
:deep(.v-field__outline),
:deep(.v-field__loader),
:deep(.v-field--active),
:deep(.v-field--focused),
:deep(.v-field--variant-outlined),
:deep(.v-field--variant-filled),
:deep(.v-field--variant-solo),
:deep(.v-field--variant-plain) {
  background-color: transparent !important;
  background-image: none !important;
}

:deep(.v-field__overlay) {
  opacity: 0 !important;
  display: none !important;
}

:deep([class*='v-']) {
  background-color: transparent;
}

:deep(.v-input .v-input__control .v-input__slot),
:deep(.v-input .v-input__control .v-field),
:deep(.v-text-field .v-input__control .v-input__slot),
:deep(.v-text-field .v-input__control .v-field) {
  background-color: transparent !important;
  box-shadow: none !important;
}

html, body {
  height: 100%;
  margin: 0;
  padding: 0;
  overflow: hidden;
  background-color: #0f1620;
}

#app {
  height: 100%;
  display: flex;
  flex-direction: column;
}
</style>