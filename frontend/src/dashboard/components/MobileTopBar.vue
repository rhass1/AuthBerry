<template>
  <div class="mobile-top-bar">
    <div class="mobile-top-header">
      <div class="mobile-logo">
        <img src="/logo.svg" alt="AuthBerry" height="40" />
      </div>

      <div class="mobile-actions">
        <v-menu offset-y>
          <template v-slot:activator="{ props }">
            <v-avatar
              v-bind="props"
              size="36"
              class="profile-avatar"
              @click.stop
            >
              <v-img
                v-if="authStore.profilePhoto"
                :src="authStore.profilePhoto"
                alt="Profile Photo"
                cover
              ></v-img>
              <v-icon
                v-else
                size="26"
                color="primary"
              >mdi-account-circle</v-icon>
            </v-avatar>
          </template>
          <v-list class="neon-glass-menu">
            <v-list-item @click.stop="goToProfile">
              <template v-slot:prepend>
                <v-icon color="primary">mdi-account</v-icon>
              </template>
              <v-list-item-title>Profile</v-list-item-title>
            </v-list-item>

            <v-list-item v-if="authStore.isAdmin" @click.stop="goToAdmin">
              <template v-slot:prepend>
                <v-icon color="warning">mdi-shield-account</v-icon>
              </template>
              <v-list-item-title>Admin Panel</v-list-item-title>
            </v-list-item>

            <v-list-item @click.stop="handleLogout">
              <template v-slot:prepend>
                <v-icon color="error">mdi-logout</v-icon>
              </template>
              <v-list-item-title>Logout</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>
      </div>
    </div>

    <div class="mobile-search-row">
      <div class="mobile-search-container">
        <v-text-field
          v-model="searchModel"
          prepend-inner-icon="mdi-magnify"
          placeholder="Search Secrets"
          single-line
          hide-details
          density="compact"
          variant="plain"
          class="search-field"
          @update:model-value="updateSearch"
          clearable
          @click.stop
          @focus.stop
        ></v-text-field>
      </div>

      <div class="mobile-action-buttons">
        <v-btn
          v-if="canAddToCurrentFolder"
          color="primary"
          icon="mdi-plus"
          class="neon-btn action-btn"
          size="small"
          aria-label="Create new item"
          @click.stop="openCreateMenu"
        >
          <v-icon>mdi-plus</v-icon>
        </v-btn>

        <v-menu
          v-model="menuOpen"
          offset-y
          location="bottom end"
          :z-index="9999"
          min-width="200"
          :close-on-content-click="false"
          :close-on-click="true"
        >
          <v-list class="neon-glass-menu" @click.stop>
            <v-list-item @click.stop="createSecretAndClose" class="menu-item" active-color="primary">
              <template v-slot:prepend>
                <v-icon color="primary">mdi-file-lock</v-icon>
              </template>
              <v-list-item-title>New Secret</v-list-item-title>
            </v-list-item>

            <v-list-item @click.stop="createFolderAndClose" class="menu-item" active-color="primary">
              <template v-slot:prepend>
                <v-icon color="primary">mdi-folder-lock</v-icon>
              </template>
              <v-list-item-title>New Folder</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useSplashStore } from '@/stores/splash'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const splashStore = useSplashStore()
const router = useRouter()

const props = defineProps({
  search: {
    type: String,
    default: ''
  },
  canAddToCurrentFolder: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:search', 'create-secret', 'create-folder'])

// Local state
const searchModel = ref(props.search || '')
const menuOpen = ref(false)

// Watch for external changes to search
watch(() => props.search, (newVal) => {
  searchModel.value = newVal
})

// Search methods
function updateSearch() {
  emit('update:search', searchModel.value)
}

// Action menu methods
function openCreateMenu() {
  menuOpen.value = true
}

function closeMenu() {
  menuOpen.value = false
}

function createSecretAndClose() {
  menuOpen.value = false
  emit('create-secret')
}

function createFolderAndClose() {
  menuOpen.value = false
  emit('create-folder')
}

// Navigation methods
function goToProfile() {
  router.push({ name: 'profile' })
}

function goToAdmin() {
  router.push({ name: 'admin' })
}

async function handleLogout() {
  try {
    // Show splash before logout
    splashStore.showSplash('Logging out')

    // Perform proper logout through auth system
    const result = await authStore.logout()

    // Clear all auth-related localStorage items as a fallback
    localStorage.removeItem('authToken')
    localStorage.removeItem('authUser')
    localStorage.removeItem('refreshToken')
    localStorage.removeItem('lastTokenRefresh')
    localStorage.removeItem('splashScreenSeen')

    // Force a hard redirect to the home page
    window.location.href = '/'
  } catch (error) {
    // Even if there's an error, clear localStorage and redirect
    localStorage.removeItem('authToken')
    localStorage.removeItem('authUser')
    localStorage.removeItem('refreshToken')
    window.location.href = '/'
  } finally {
    splashStore.hideSplash()
  }
}
</script>

<style scoped>
.mobile-top-bar {
  width: 100%;
  padding: 8px 0;
}

.mobile-top-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 8px 8px;
}

.mobile-logo {
  display: flex;
  align-items: center;
}

.mobile-logo img {
  height: 40px;
  width: auto;
}

.mobile-actions {
  display: flex;
  align-items: center;
}

.profile-avatar {
  cursor: pointer;
  box-shadow: 0 0 8px rgba(0, 255, 156, 0.3);
  border: 1px solid rgba(0, 255, 156, 0.3);
  transition: transform 0.2s ease;
}

.profile-avatar:hover {
  transform: scale(1.05);
}

.mobile-search-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 8px;
}

.mobile-search-container {
  flex-grow: 1;
  margin-right: 8px;
}

.search-field {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 6px;
  transition: all 0.2s ease;
}

.search-field :deep(.v-field) {
  border-radius: 6px;
  box-shadow: 0 0 0 1px rgba(0, 255, 156, 0.2);
}

.search-field :deep(.v-field__input) {
  color: rgba(255, 255, 255, 0.9);
  font-size: 14px;
  font-weight: 500;
  padding: 0 8px !important;
  min-height: 36px !important;
}

.search-field :deep(.v-field__input::placeholder) {
  color: rgba(255, 255, 255, 0.5);
}

.mobile-action-buttons {
  display: flex;
  align-items: center;
}

.action-btn {
  min-width: unset !important;
  border-radius: 6px;
  height: 36px;
  width: 36px;
  padding: 0 !important;
  position: relative;
}

.neon-btn {
  background: linear-gradient(135deg, rgba(0, 255, 156, 0.25), rgba(0, 163, 255, 0.25));
  border: 1px solid rgba(0, 255, 156, 0.3);
  box-shadow:
    0 0 5px rgba(0, 255, 156, 0.5),
    0 0 10px rgba(0, 255, 156, 0.2);
  transition: all 0.2s ease;
}

.neon-glass-menu {
  background: rgba(15, 22, 32, 0.95) !important;
  border: 1px solid rgba(0, 255, 156, 0.3) !important;
  box-shadow: 0 0 15px rgba(0, 255, 156, 0.3) !important;
  backdrop-filter: blur(10px) !important;
}

.menu-item {
  min-height: 48px; /* Ensure touch-friendly size */
}

/* Responsive tweaks for small screens */
@media (max-width: 400px) {
  .mobile-logo img {
    height: 32px;
  }

  .profile-avatar {
    width: 32px !important;
    height: 32px !important;
  }

  .search-field :deep(.v-field__input) {
    font-size: 13px;
  }
}
</style>