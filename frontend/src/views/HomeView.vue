<template>
  <div class="home-view" :class="{ 'blur-background': showingAuthModal }">
    <div class="tpm-background" :class="{'tpm-mobile': $vuetify.display.xs || $vuetify.display.sm}">
      <div class="tpm-circuit"></div>
      <div class="tpm-data-paths"></div>
      <div class="tpm-gates"></div>
      <div class="tpm-encryption"></div>
      <div class="tpm-transistors"></div>
      <div class="tpm-data-flow"></div>
    </div>

    <v-container fluid class="fill-height pa-0">
      <v-row no-gutters class="fill-height align-center justify-center" :class="{'align-sm-start mt-sm-8': $vuetify.display.xs || $vuetify.display.sm}">
        <v-col cols="12" sm="10" md="8" lg="6" class="d-flex flex-column align-center justify-center">
          <div class="logo-container" :class="{'mt-2 mb-2': $vuetify.display.xs || $vuetify.display.sm, 'mb-6': !$vuetify.display.xs && !$vuetify.display.sm}">
            <div class="logo-wrapper" :class="{'logo-wrapper-desktop': !$vuetify.display.xs && !$vuetify.display.sm}">
              <img src="/logo.svg" alt="AuthBerry Logo" class="logo animated-logo" />
              <div class="logo-particles"></div>
            </div>
          </div>

          <div v-if="!authStore.isAuthenticated" class="auth-buttons d-flex flex-row flex-xs-column justify-center" :class="{'my-2': $vuetify.display.xs || $vuetify.display.sm, 'my-4': !$vuetify.display.xs && !$vuetify.display.sm}">
            <v-btn
              @click="openLoginModal"
              color="primary"
              class="btn-cyber btn-login ma-1"
              :size="$vuetify.display.xs ? 'default' : 'large'"
              elevation="4"
              :min-width="$vuetify.display.xs ? 120 : 150"
            >
              <div class="btn-cyber-glitch"></div>
              <v-icon start>mdi-login</v-icon>
              Login
            </v-btn>

            <v-btn
              v-if="registrationEnabled"
              @click="router.push('/register')"
              color="secondary"
              class="btn-cyber btn-register ma-1"
              :size="$vuetify.display.xs ? 'default' : 'large'"
              variant="outlined"
              :min-width="$vuetify.display.xs ? 120 : 150"
            >
              <div class="btn-cyber-glitch"></div>
              <v-icon start>mdi-account-plus</v-icon>
              Register
            </v-btn>
          </div>

          <div v-else class="auth-buttons" :class="{'my-2': $vuetify.display.xs || $vuetify.display.sm, 'my-4': !$vuetify.display.xs && !$vuetify.display.sm}">
            <v-btn
              @click="goToDashboard"
              color="accent"
              class="btn-cyber"
              size="large"
            >
              <div class="btn-cyber-glitch"></div>
              <v-icon start>mdi-view-dashboard</v-icon>
              Go to Dashboard
            </v-btn>
          </div>

          <div class="features-container" :class="{'mt-2': $vuetify.display.xs || $vuetify.display.sm, 'mt-4': !$vuetify.display.xs && !$vuetify.display.sm}">
            <KeyFeatures :features="features" />
          </div>
        </v-col>
      </v-row>

      <AuthModals
        ref="authModals"
        @modal-opened="handleModalOpened"
        @modal-closed="handleModalClosed"
      />
    </v-container>
  </div>
</template>

<script setup>
import { computed, onMounted, onUpdated, ref, watch, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRoute, useRouter } from 'vue-router'
import KeyFeatures from '@/components/KeyFeatures.vue'
import AuthModals from '@/components/AuthModals.vue'
import axios from 'axios'

const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()
const authModals = ref(null)
const showingAuthModal = ref(false)
const registrationEnabled = ref(true)

// Fetch registration status
async function fetchRegistrationStatus() {
  try {
    const response = await axios.get('/api/auth/registration-status')
    registrationEnabled.value = response.data.enabled
  } catch (error) {
    // Default to enabled if there's an error
    registrationEnabled.value = true
  }
}

// Watch for modal state in the child component
const openLoginModal = () => {
  if (authModals.value) {
    authModals.value.openLoginModal()
  }
}

const openRegisterModal = () => {
  if (authModals.value && registrationEnabled.value) {
    authModals.value.openRegisterModal()
  } else if (!registrationEnabled.value) {
    // Cannot open register modal: Registration is disabled (console.warn removed)
  }
}

// Set up watchers to track modal state
onMounted(async () => {
  // Get registration status
  await fetchRegistrationStatus()

  // Check if the user is authenticated and preserve state more aggressively
  if (authStore.isAuthenticated || authStore.token) {
    // Make sure axios headers are set correctly
    axios.defaults.headers.common['Authorization'] = `Bearer ${authStore.token}`;
    
    // Refresh user data to ensure we have the latest
    await authStore.refreshUserData();
    
    // Only redirect if still authenticated after refresh
    if (authStore.isAuthenticated) {
      router.push('/dashboard');
      return;
    }
  }

  // If auth store is empty, try to initialize from localStorage
  if (!authStore.isAuthenticated && !authStore.user) {
    await authStore.init();

    // Check again after initialization
    if (authStore.isAuthenticated) {
      router.push('/dashboard');
      return;
    }
  }

  // Check for query parameters to show modals
  if (route.query.showModal) {
    if (route.query.showModal === 'login') {
      openLoginModal();
    } else if (route.query.showModal === 'register' && registrationEnabled.value) {
      openRegisterModal();
    }
  }
})

// Also watch for auth state changes (e.g. when login completes from modal)
watch(() => authStore.isAuthenticated, (isAuthenticated) => {
  if (isAuthenticated) {
    router.push('/dashboard');
  }
})

// Make sure the modal state is properly cleared when the component is unmounted
onUnmounted(() => {
  showingAuthModal.value = false
})

// Create a more reliable function to handle the blur state
const handleModalOpened = () => {
  showingAuthModal.value = true
}

const handleModalClosed = () => {
  showingAuthModal.value = false
}

// Features showcase
const features = [
  {
    title: 'Security First',
    description: 'Hardware-based encryption using the TPM chip. Your secrets are never stored as plaintext.',
    icon: 'mdi-shield-lock',
    color: 'success'
  },
  {
    title: 'Easy Sharing',
    description: 'Share your secrets seamlessly and securely with other users on the platform.',
    icon: 'mdi-share-variant',
    color: 'info'
  },
  {
    title: 'Access Controls',
    description: 'Fine-grained permissions to control who can read, write, or delete your secrets.',
    icon: 'mdi-key',
    color: 'warning'
  }
]

const goToDashboard = () => {
  if (authStore.token) {
    // Ensure the Authorization header is set
    axios.defaults.headers.common['Authorization'] = `Bearer ${authStore.token}`;

    // Now navigate to dashboard
    router.push('/dashboard');
  } else {
    // Force re-authentication
    router.push({ path: '/', query: { showModal: 'login', redirect: '/dashboard' } });
  }
}
</script>

<style scoped>
.home-view {
  height: 100vh;
  position: relative;
  transition: filter 0.3s ease;
  overflow: auto;
}

.blur-background {
  filter: blur(3px);
  pointer-events: none;
}

.logo-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  position: relative;
  z-index: 2;
}

.logo-wrapper {
  position: relative;
  width: 100px;
  height: 100px;
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 0.5rem;
}

.logo-wrapper-desktop {
  width: 140px;
  height: 140px;
}

.logo-particles {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: radial-gradient(circle at center, transparent 50%, rgba(0, 255, 156, 0.1) 70%, transparent 100%);
  border-radius: 50%;
  animation: particle-pulse 5s ease-in-out infinite alternate, rotate 15s linear infinite;
}

.logo-wrapper::before {
  content: '';
  position: absolute;
  top: -5px;
  left: -5px;
  right: -5px;
  bottom: -5px;
  border-radius: 50%;
  background: conic-gradient(
    rgba(0, 255, 156, 0.2),
    rgba(0, 136, 255, 0.2),
    rgba(140, 82, 255, 0.2),
    rgba(0, 255, 156, 0.2)
  );
  animation: rotate 4s linear infinite;
  z-index: -1;
}

.app-subtitle {
  font-family: 'Caudex', serif;
  color: rgba(255, 255, 255, 0.8);
  font-size: 1.1rem;
  max-width: 600px;
  line-height: 1.3;
}

.logo {
  width: 80%;
  height: auto;
  position: relative;
  z-index: 2;
}

.animated-logo {
  animation: pulse 3s infinite alternate, color-shift 10s infinite alternate;
  filter: drop-shadow(0 0 10px rgba(138, 43, 226, 0.7));
}

.auth-buttons {
  width: 100%;
  max-width: 500px;
  z-index: 2;
  display: flex;
  justify-content: center;
  align-items: center;
}

.btn-cyber {
  position: relative;
  border: 1px solid;
  clip-path: polygon(
    5px 0,
    calc(100% - 5px) 0,
    100% 5px,
    100% calc(100% - 5px),
    calc(100% - 5px) 100%,
    5px 100%,
    0 calc(100% - 5px),
    0 5px
  );
  transition: all 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.btn-cyber::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: radial-gradient(circle at center, transparent 30%, rgba(0, 0, 0, 0.5) 100%);
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.btn-cyber:hover::after {
  opacity: 1;
}

.btn-cyber:active {
  transform: translateY(2px);
}

.btn-cyber-glitch {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: none;
  opacity: 0;
  pointer-events: none;
  z-index: 0;
}

.btn-login:hover {
  box-shadow: 0 0 20px rgba(138, 43, 226, 0.9), inset 0 0 15px rgba(138, 43, 226, 0.5) !important;
  border: 2px solid rgba(255, 255, 255, 0.8) !important;
  transform: scale(1.03);
}

.btn-login:hover .btn-cyber-glitch {
  animation: glitch 0.3s cubic-bezier(.25, .46, .45, .94) both infinite;
  background: linear-gradient(90deg,
    rgba(138, 43, 226, 0) 0%,
    rgba(138, 43, 226, 0.3) 50%,
    rgba(138, 43, 226, 0) 100%);
}

.btn-register:hover {
  transform: scale(1.05);
  border: 2px solid rgba(0, 255, 156, 0.9) !important;
  box-shadow: 0 0 15px rgba(0, 255, 156, 0.7), inset 0 0 10px rgba(0, 255, 156, 0.3) !important;
}

.btn-register:hover .btn-cyber-glitch {
  animation: glitch 0.5s cubic-bezier(.25, .46, .45, .94) both infinite;
  background: linear-gradient(90deg,
    rgba(0, 255, 156, 0) 0%,
    rgba(0, 255, 156, 0.2) 50%,
    rgba(0, 255, 156, 0) 100%);
}

@keyframes glitch {
  0% {
    transform: translateX(-100%);
    opacity: 0.5;
  }

  100% {
    transform: translateX(100%);
    opacity: 0;
  }
}

.features-container {
  width: 100%;
  max-width: 1200px;
  position: relative;
  z-index: 2;
}

@keyframes pulse {
  0% {
    transform: scale(1);
  }
  100% {
    transform: scale(1.05);
    filter: drop-shadow(0 0 15px rgba(138, 43, 226, 0.9));
  }
}

@keyframes color-shift {
  0% {
    filter: drop-shadow(0 0 15px rgba(138, 43, 226, 0.9));
  }
  33% {
    filter: drop-shadow(0 0 15px rgba(0, 255, 156, 0.9));
  }
  66% {
    filter: drop-shadow(0 0 15px rgba(0, 136, 255, 0.9));
  }
  100% {
    filter: drop-shadow(0 0 15px rgba(138, 43, 226, 0.9));
  }
}

@keyframes particle-pulse {
  0% {
    opacity: 0.3;
    transform: scale(0.8);
  }
  100% {
    opacity: 0.8;
    transform: scale(1.2);
  }
}

@keyframes rotate {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

/* TPM Chip Background Styles */
.tpm-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  pointer-events: none;
  overflow: hidden;
  z-index: 0;
  opacity: 0.35;
}

/* Mobile optimized background */
.tpm-mobile {
  opacity: 0.2;
}

.tpm-mobile .tpm-circuit {
  background-size: 20px 20px;
}

.tpm-mobile .tpm-gates {
  background-size: 25px 25px;
  opacity: 0.5;
  animation: none;
}

.tpm-mobile .tpm-transistors {
  background-size: 60px 60px;
  opacity: 0.3;
}

.tpm-mobile .tpm-encryption::before {
  opacity: 0.4;
  animation: none;
}

.tpm-mobile .tpm-data-flow::before,
.tpm-mobile .tpm-data-flow::after {
  display: none;
}

.tpm-mobile .tpm-background::after,
.tpm-mobile .tpm-background::before,
.tpm-mobile .tpm-encryption::after {
  display: none;
}

.tpm-circuit {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image:
    linear-gradient(90deg, transparent 99%, rgba(0, 255, 156, 0.7) 99%, transparent 100%),
    linear-gradient(0deg, transparent 99%, rgba(0, 136, 255, 0.7) 99%, transparent 100%);
  background-size: 30px 30px;
  opacity: 0.9;
}

.tpm-data-paths {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background:
    radial-gradient(circle at 15% 15%, rgba(0, 255, 156, 0.25) 0%, transparent 25%),
    radial-gradient(circle at 85% 85%, rgba(0, 136, 255, 0.25) 0%, transparent 25%),
    radial-gradient(circle at 85% 15%, rgba(140, 82, 255, 0.25) 0%, transparent 25%),
    radial-gradient(circle at 15% 85%, rgba(0, 230, 204, 0.25) 0%, transparent 25%);
}

.tpm-gates {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image:
    linear-gradient(45deg, transparent 94%, rgba(0, 255, 156, 0.7) 94%, transparent 96%),
    linear-gradient(-45deg, transparent 94%, rgba(0, 136, 255, 0.7) 94%, transparent 96%);
  background-size: 40px 40px;
  animation: moveGates 20s linear infinite;
}

.tpm-encryption {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.tpm-encryption::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background-image:
    repeating-conic-gradient(
      transparent 0deg 5deg,
      rgba(0, 136, 255, 0.05) 5deg 6deg,
      transparent 6deg 45deg,
      rgba(0, 255, 156, 0.05) 45deg 46deg
    );
  animation: rotateEncryption 60s linear infinite;
}

.tpm-transistors {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image:
    linear-gradient(to right, transparent 49.5%, rgba(0, 255, 156, 0.4) 49.5%, rgba(0, 255, 156, 0.4) 50.5%, transparent 50.5%),
    linear-gradient(to bottom, transparent 49.5%, rgba(0, 136, 255, 0.4) 49.5%, rgba(0, 136, 255, 0.4) 50.5%, transparent 50.5%);
  background-size: 120px 120px;
  opacity: 0.5;
}

@keyframes moveGates {
  0% {
    background-position: 0 0;
  }
  100% {
    background-position: 40px 40px;
  }
}

@keyframes rotateEncryption {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.tpm-data-flow {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

@media (max-width: 600px) {
  .home-view {
    height: 100vh;
    overflow: auto;
  }

  .features-container {
    margin-bottom: 2rem;
  }
}

@media (max-height: 750px) and (max-width: 600px) {
  .logo-wrapper {
    width: 80px;
    height: 80px;
  }

  .v-col {
    padding-top: 0.5rem !important;
  }
}

/* Only stack buttons on very narrow screens */
@media (max-width: 340px) {
  .auth-buttons {
    flex-direction: column !important;
  }

  .auth-buttons .v-btn {
    width: 100%;
  }
}
</style>