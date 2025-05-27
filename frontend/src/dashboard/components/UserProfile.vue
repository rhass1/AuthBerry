<template>
  <div class="panel-header" @click.stop>
    <div class="logo-mini" @click.stop>
      <img src="/logo.svg" alt="AuthBerry" height="150" />
    </div>

    <div class="user-profile-section" @click.stop>
      <div class="profile-container" @click.stop>
        <v-menu offset-y>
          <template v-slot:activator="{ props }">
            <v-avatar
              v-bind="props"
              size="80"
              class="profile-avatar"
              @click.stop
            >
              <v-img
                v-if="authStore.profilePhoto && !profilePhotoLoadError"
                :src="authStore.profilePhoto"
                alt="Profile Photo"
                @error="handleProfilePhotoError"
                @load="() => {}"
                cover
              ></v-img>
              <v-icon
                v-else
                size="50"
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
        <div class="cyber-user-info" @click.stop>
          <div class="cyber-user-name">{{ authStore.displayName }}</div>
          <div class="user-last-login" v-if="authStore.user?.last_modified">
            Last seen: {{ formatTimeAgo(authStore.user.last_modified) }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useSplashStore } from '@/stores/splash'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const splashStore = useSplashStore()
const router = useRouter()
const profilePhotoLoadError = ref(false)

// Navigation methods
function goToProfile(event) {
  if (event) {
    event.stopPropagation()
  }
  router.push({ name: 'profile' })
}

function goToAdmin(event) {
  if (event) {
    event.stopPropagation()
  }
  router.push({ name: 'admin' })
}

async function handleLogout(event) {
  if (event) {
    event.stopPropagation()
  }

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

// Format the timestamp to a human-readable "time ago" format
function formatTimeAgo(dateString) {
  const date = new Date(dateString)
  const now = new Date()
  const diffInSeconds = Math.floor((now - date) / 1000)

  if (diffInSeconds < 60) {
    return 'just now'
  }

  const diffInMinutes = Math.floor(diffInSeconds / 60)
  if (diffInMinutes < 60) {
    return `${diffInMinutes} minute${diffInMinutes > 1 ? 's' : ''} ago`
  }

  const diffInHours = Math.floor(diffInMinutes / 60)
  if (diffInHours < 24) {
    return `${diffInHours} hour${diffInHours > 1 ? 's' : ''} ago`
  }

  const diffInDays = Math.floor(diffInHours / 24)
  if (diffInDays < 30) {
    return `${diffInDays} day${diffInDays > 1 ? 's' : ''} ago`
  }

  const diffInMonths = Math.floor(diffInDays / 30)
  if (diffInMonths < 12) {
    return `${diffInMonths} month${diffInMonths > 1 ? 's' : ''} ago`
  }

  const diffInYears = Math.floor(diffInMonths / 12)
  return `${diffInYears} year${diffInYears > 1 ? 's' : ''} ago`
}

// Function to handle profile photo errors
function handleProfilePhotoError(event) {
  // Mark the photo as failed to load so we don't try to display it again
  profilePhotoLoadError.value = true

  // Try to refresh user data to get a fresh profile URL
  authStore.refreshUserData().then(() => {
    // If we have a profile photo and it's a data URI (base64), we can try again
    if (authStore.profilePhoto && authStore.profilePhoto.startsWith('data:image')) {
      // Reset error state to allow the image to display
      profilePhotoLoadError.value = false
    }
  }).catch(error => {
    // Error refreshing user data (console.error removed)
  })
}
</script>

<style scoped>
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(0, 255, 156, 0.2);
  background: rgba(15, 22, 32, 0.8);
  position: relative;
}

.logo-mini {
  display: flex;
  align-items: center;
  position: relative;
  overflow: hidden;
  margin-right: 20px;
  width: 150px;
  height: 150px;
}

.logo-mini img {
  position: relative;
  z-index: 2;
  width: 100%;
  height: 100%;
  object-fit: contain;
}

/* Electric circuit animation - contained within logo boundaries */
@keyframes spark-effect {
  0%, 100% { opacity: 0; }
  5%, 8% { opacity: 0.8; }
  9%, 15% { opacity: 0.5; }
  20% { opacity: 0; }
  50%, 52% { opacity: 0.7; }
  54% { opacity: 0; }
  80%, 82% { opacity: 0.6; }
  84% { opacity: 0; }
}

/* More visible spark points - contained */
.logo-mini::before {
  content: '';
  position: absolute;
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
  background-image:
    radial-gradient(circle at 30% 30%, rgba(0, 255, 156, 0.7) 0%, transparent 15%),
    radial-gradient(circle at 70% 40%, rgba(0, 136, 255, 0.7) 0%, transparent 15%),
    radial-gradient(circle at 20% 80%, rgba(140, 82, 255, 0.7) 0%, transparent 15%),
    radial-gradient(circle at 80% 20%, rgba(0, 230, 204, 0.7) 0%, transparent 15%);
  z-index: 1;
  mix-blend-mode: screen;
  animation: spark-effect 8s infinite ease-out;
  pointer-events: none;
}

/* Circuit line pattern - contained */
.logo-mini::after {
  content: '';
  position: absolute;
  /* Reduce size to prevent edge artifacts */
  width: 90%;
  height: 90%;
  top: 5%;
  left: 5%;
  background-image:
    /* Horizontal circuit lines - make less prominent */
    repeating-linear-gradient(90deg, transparent, transparent 8px, rgba(0, 255, 156, 0.15) 9px, transparent 10px),
    /* Vertical circuit lines - make less prominent */
    repeating-linear-gradient(0deg, transparent, transparent 8px, rgba(0, 136, 255, 0.15) 9px, transparent 10px),
    /* Diagonal circuit paths */
    linear-gradient(45deg, transparent 97.5%, rgba(0, 255, 156, 0.7) 97.5%, transparent 99%),
    linear-gradient(-45deg, transparent 97.5%, rgba(0, 136, 255, 0.7) 97.5%, transparent 99%),
    /* Extra diagonal sparks */
    linear-gradient(135deg, transparent 98.5%, rgba(140, 82, 255, 0.7) 98.5%, transparent 99.5%);
  /* Reduce opacity to make grid less visible */
  opacity: 0.4;
  mix-blend-mode: lighten;
  pointer-events: none;
  animation: circuit-pulse 6s infinite linear;
  z-index: 0;
  border-radius: 10%; /* Add border radius to soften edges */
}

/* More dynamic circuit animation */
@keyframes circuit-pulse {
  0% {
    background-position: 0 0, 0 0, 0 0, 0 0, 0 0;
    opacity: 0.3;
  }
  25% {
    background-position: 10px 0, 0 10px, 5px 3px, -3px -5px, 4px -4px;
    opacity: 0.5;
  }
  50% {
    background-position: 20px 0, 0 20px, 10px 5px, -5px -10px, 8px -8px;
    opacity: 0.3;
  }
  75% {
    background-position: 30px 0, 0 30px, 15px 8px, -8px -15px, 12px -12px;
    opacity: 0.5;
  }
  100% {
    background-position: 40px 0, 0 40px, 20px 10px, -10px -20px, 16px -16px;
    opacity: 0.3;
  }
}

.user-profile-section {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.profile-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  padding: 4px;
}

.cyber-user-info {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  text-align: center;
}

.cyber-user-name {
  font-size: 1.2rem;
  font-weight: 600;
  color: #fff;
  text-shadow:
    0 0 5px rgba(0, 255, 156, 0.7),
    0 0 10px rgba(0, 255, 156, 0.5);
  background: linear-gradient(90deg, rgba(0, 255, 156, 0.8), rgba(0, 136, 255, 0.8));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 4px;
  position: relative;
  letter-spacing: 1px;
}

.cyber-user-name::after {
  content: '';
  position: absolute;
  width: 100%;
  height: 1px;
  bottom: -2px;
  left: 0;
  background: linear-gradient(90deg, transparent, rgba(0, 255, 156, 0.7), rgba(0, 136, 255, 0.7), transparent);
}

.user-last-login {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.6);
  white-space: nowrap;
}

.profile-avatar {
  position: relative;
  cursor: pointer;
  border: none;
  border-radius: 50%;
  transition: transform 0.3s ease;
  background: transparent;
  overflow: hidden;
  box-shadow:
    0 0 10px rgba(0, 255, 156, 0.4),
    0 0 20px rgba(0, 163, 255, 0.2);
}

.profile-avatar::before {
  content: '';
  position: absolute;
  top: -3px;
  left: -3px;
  right: -3px;
  bottom: -3px;
  background: transparent;
  border-radius: 50%;
  z-index: -1;
}

.profile-avatar::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(0, 255, 156, 0.15), transparent 70%);
  border-radius: 50%;
  z-index: 2;
  pointer-events: none;
}

@keyframes moveGradient {
  /* Empty animation definition - not used */
}

.profile-avatar:hover::before {
  /* No background changes on hover */
}

.profile-avatar:hover {
  transform: scale(1.05);
}

.neon-glass-menu {
  background: rgba(15, 22, 32, 0.95) !important;
  border: 1px solid rgba(0, 255, 156, 0.3) !important;
  box-shadow: 0 0 15px rgba(0, 255, 156, 0.3) !important;
  backdrop-filter: blur(10px) !important;
}

/* Responsive design */
@media (max-width: 960px) {
  /* Updated user profile responsive styles */
  .panel-header {
    flex-wrap: wrap;
    justify-content: center;
  }

  .logo-mini {
    width: 120px;
    height: 120px;
    margin-right: 0;
    margin-bottom: 10px;
  }

  .user-profile-section {
    margin-top: 8px;
  }

  .profile-avatar {
    width: 70px !important;
    height: 70px !important;
  }
}

@media (max-width: 600px) {
  .logo-mini {
    width: 100px;
    height: 100px;
  }

  .profile-avatar {
    width: 60px !important;
    height: 60px !important;
  }

  .cyber-user-name {
    font-size: 1rem;
  }
}

@media (max-width: 480px) {
  .profile-avatar {
    width: 50px !important;
    height: 50px !important;
  }

  .cyber-user-name {
    font-size: 0.9rem;
  }

  .user-last-login {
    font-size: 0.65rem;
  }
}
</style>