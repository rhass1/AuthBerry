<template>
  <div class="register-view">
    <div class="tpm-background" :class="{'tpm-mobile': $vuetify.display.xs || $vuetify.display.sm}">
      <div class="tpm-circuit"></div>
      <div class="tpm-data-paths"></div>
      <div class="tpm-gates"></div>
      <div class="tpm-encryption"></div>
      <div class="tpm-transistors"></div>
      <div class="tpm-data-flow"></div>
    </div>

    <v-container class="d-flex flex-column justify-center align-center py-4 py-sm-6" style="min-height: 100vh;">
      <v-row justify="center" align="center" class="w-100">
        <v-col cols="12" sm="10" md="8" lg="6" xl="5">
          <v-card class="px-3 px-sm-4 py-4 pa-md-6 register-card">
            <div class="text-center mb-4 d-flex justify-center">
              <img src="/logo.svg" alt="AuthBerry Logo" class="logo animated-logo" />
            </div>

            <h1 class="text-h5 text-sm-h4 text-center mb-4 cyber-title">
              Create Your Account
            </h1>

            <v-alert
              v-if="errorMessage"
              type="error"
              variant="tonal"
              closable
              class="mb-4"
              @click:close="errorMessage = null"
              density="compact"
            >
              {{ errorMessage }}
            </v-alert>

            <v-alert
              v-if="connectionError"
              type="error"
              variant="tonal"
              class="mb-4"
              density="compact"
            >
              <div class="d-flex flex-column">
                <div class="font-weight-bold mb-1">Connection Error</div>
                <p class="mb-0">Unable to connect to the backend. Please check that the server is running.</p>
              </div>
            </v-alert>

            <v-alert
              v-if="authStore.error && !connectionError"
              type="error"
              variant="tonal"
              closable
              class="mb-4"
              density="compact"
            >
              {{ authStore.error }}
            </v-alert>

            <v-stepper v-model="currentStep" class="mb-4 mb-sm-6 register-stepper">
              <v-stepper-header>
                <v-stepper-item
                  value="1"
                  complete-icon="mdi-account-key"
                  :class="{'active-step': currentStep === '1', 'completed-step': currentStep > '1'}"
                >
                  <span class="d-none d-sm-flex">Account</span>
                </v-stepper-item>

                <v-divider :class="{'active-divider': currentStep >= '2'}"></v-divider>

                <v-stepper-item
                  value="2"
                  complete-icon="mdi-account-details"
                  :class="{'active-step': currentStep === '2', 'completed-step': currentStep > '2'}"
                >
                  <span class="d-none d-sm-flex">Profile</span>
                </v-stepper-item>

                <v-divider :class="{'active-divider': currentStep >= '3'}"></v-divider>

                <v-stepper-item
                  value="3"
                  complete-icon="mdi-camera-account"
                  :class="{'active-step': currentStep === '3'}"
                >
                  <span class="d-none d-sm-flex">Photo</span>
                </v-stepper-item>
              </v-stepper-header>
            </v-stepper>

            <v-form
              v-if="currentStep === '1'"
              @submit.prevent="validateStep1"
              ref="accountForm"
              v-model="forms.account.valid"
            >
              <v-text-field
                v-model="username"
                label="Username"
                prepend-icon="mdi-account-circle"
                required
                :rules="[
                  v => !!v || 'Username is required',
                  v => v.length >= 3 || 'Username must be at least 3 characters'
                ]"
                class="mb-4"
                tabindex="1"
                ref="usernameInput"
                :error-messages="usernameError"
                :loading="checkingUsername"
                @blur="checkUsernameExists"
              ></v-text-field>

              <v-text-field
                v-model="password"
                label="Password"
                prepend-icon="mdi-lock"
                :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
                @click:append-inner="showPassword = !showPassword"
                :append-inner-icon-tabindex="-1"
                :type="showPassword ? 'text' : 'password'"
                required
                :rules="[
                  v => !!v || 'Password is required',
                  v => v.length >= 8 || 'Password must be at least 8 characters',
                  v => /[A-Z]/.test(v) || 'Password must contain at least one uppercase letter',
                  v => /[0-9]/.test(v) || 'Password must contain at least one number'
                ]"
                class="mb-2"
                tabindex="2"
              ></v-text-field>

              <div class="strength-meter-wrapper">
                <PasswordStrengthMeter
                  :password="password"
                  @update:strength="passwordStrength = $event"
                  class="mb-4"
                  v-if="password"
                />
              </div>

              <v-text-field
                v-model="confirmPassword"
                label="Confirm Password"
                prepend-icon="mdi-lock-check"
                :type="showPassword ? 'text' : 'password'"
                required
                :rules="[
                  v => !!v || 'Please confirm your password',
                  v => v === password || 'Passwords do not match'
                ]"
                class="mb-6"
                tabindex="3"
              ></v-text-field>

              <div class="d-flex justify-center align-center flex-wrap">
                <v-btn
                  color="primary"
                  type="submit"
                  size="large"
                  :disabled="connectionError || checkingUsername || usernameExists"
                  class="btn-cyber px-6 ma-2"
                  width="auto"
                  tabindex="4"
                >
                  <div class="btn-cyber-glitch"></div>
                  <v-icon start>mdi-arrow-right</v-icon>
                  Continue to Profile
                </v-btn>

                <v-btn
                  color="secondary"
                  variant="outlined"
                  class="ma-2"
                  @click="goToLogin"
                  tabindex="5"
                >
                  <v-icon start>mdi-login</v-icon>
                  Back to Login
                </v-btn>
              </div>
            </v-form>

            <v-form
              v-if="currentStep === '2'"
              @submit.prevent="validateStep2"
              ref="profileForm"
              v-model="forms.profile.valid"
            >
              <v-text-field
                v-model="firstName"
                label="First Name"
                prepend-icon="mdi-account"
                required
                :rules="[v => !!v || 'First name is required']"
                class="mb-4"
                tabindex="1"
                ref="firstNameInput"
              ></v-text-field>

              <v-text-field
                v-model="lastName"
                label="Last Name"
                prepend-icon="mdi-account"
                required
                :rules="[v => !!v || 'Last name is required']"
                class="mb-6"
                tabindex="2"
              ></v-text-field>

              <div class="d-flex justify-center align-center flex-wrap">
                <v-btn
                  color="primary"
                  type="submit"
                  size="large"
                  class="btn-cyber px-6 ma-2"
                  width="auto"
                  tabindex="3"
                >
                  <div class="btn-cyber-glitch"></div>
                  <v-icon start>mdi-arrow-right</v-icon>
                  Continue to Photo
                </v-btn>

                <v-btn
                  color="secondary"
                  variant="outlined"
                  class="ma-2"
                  @click="currentStep = '1'"
                  width="auto"
                  tabindex="4"
                >
                  <v-icon start>mdi-arrow-left</v-icon>
                  Back
                </v-btn>
              </div>
            </v-form>

            <div v-if="currentStep === '3'" class="pb-2">
              <div class="text-center mb-4">
                <h3 class="text-h6">Add Your Profile Photo</h3>
                <p class="text-body-2 text-medium-emphasis">
                  This will be displayed throughout the app. You can skip this step if you prefer.
                </p>
              </div>

              <ProfilePhotoUploader
                :initial-photo-data="profilePhotoData"
                @update:photo="handlePhotoUpdate"
                class="mb-6"
                ref="photoUploader"
              />

              <div class="d-flex justify-center align-center flex-wrap">
                <v-btn
                  color="primary"
                  size="large"
                  class="btn-cyber px-6 ma-2"
                  :loading="isSubmitting"
                  @click="completeRegistration"
                  width="auto"
                  tabindex="1"
                >
                  <div class="btn-cyber-glitch"></div>
                  <v-icon start>mdi-check</v-icon>
                  {{ profilePhoto ? 'Complete Registration with Photo' : 'Complete Registration' }}
                </v-btn>

                <v-btn
                  color="secondary"
                  variant="outlined"
                  class="ma-2"
                  @click="currentStep = '2'"
                  :disabled="isSubmitting"
                  width="auto"
                  tabindex="2"
                >
                  <v-icon start>mdi-arrow-left</v-icon>
                  Back
                </v-btn>
              </div>
            </div>

          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, computed, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useSplashStore } from '@/stores/splash'
import axios from 'axios'
import ProfilePhotoUploader from '@/components/ProfilePhotoUploader.vue'
import PasswordStrengthMeter from '@/components/PasswordStrengthMeter.vue'

const router = useRouter()
const authStore = useAuthStore()
const splashStore = useSplashStore()
const accountForm = ref(null)
const profileForm = ref(null)
const usernameInput = ref(null)
const firstNameInput = ref(null)
const photoUploader = ref(null)

// Form data
const currentStep = ref('1')
const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const firstName = ref('')
const lastName = ref('')
const profilePhoto = ref(null)
const profilePhotoData = ref(null)
const showPassword = ref(false)
const connectionError = ref(false)
const checkingConnection = ref(false)
const isSubmitting = ref(false)
const errorMessage = ref(null)

// Username validation
const usernameError = ref('')
const checkingUsername = ref(false)
const usernameExists = ref(false)

// Password strength variable from component
const passwordStrength = ref(0)

// Watch for step changes to set focus on the first field
watch(currentStep, (newStep) => {
  nextTick(() => {
    if (newStep === '1' && usernameInput.value) {
      usernameInput.value.focus()
    } else if (newStep === '2' && firstNameInput.value) {
      firstNameInput.value.focus()
    } else if (newStep === '3' && photoUploader.value) {
      // Focus on the photo uploader if possible
      const btn = document.querySelector('.profile-photo-uploader .v-btn')
      if (btn) btn.focus()
    }
  })
})

// Username availability check
async function checkUsernameExists() {
  if (!username.value || username.value.length < 3) {
    usernameError.value = ''
    usernameExists.value = false
    return
  }

  try {
    checkingUsername.value = true
    usernameError.value = ''

    const response = await axios.get(`/api/auth/check-username-exists?username=${encodeURIComponent(username.value)}`)

    if (response.data.exists) {
      usernameError.value = 'This username is already taken'
      usernameExists.value = true
    } else {
      usernameError.value = ''
      usernameExists.value = false
    }
  } catch (error) {
    usernameError.value = 'Error checking username'
  } finally {
    checkingUsername.value = false
  }
}

// Form validation state
const forms = reactive({
  account: {
    valid: false
  },
  profile: {
    valid: false
  }
})

// Check database connection when component mounts
onMounted(async () => {
  await checkConnection()

  // Check if registration is enabled
  await checkRegistrationEnabled()

  // Set focus on the first field
  nextTick(() => {
    if (usernameInput.value) {
      usernameInput.value.focus()
    }
  })
})

// Check if the database is available
async function checkConnection() {
  checkingConnection.value = true

  try {
    await axios.get('/api/auth/check-users-exist')
    connectionError.value = false
  } catch (err) {
    if (err.response?.status === 500) {
      connectionError.value = true
    }
  } finally {
    checkingConnection.value = false
  }

  // Clear auth store error if we have a connection error
  if (connectionError.value && authStore.error) {
    authStore.error = null
  }
}

// Check if user registration is enabled
async function checkRegistrationEnabled() {
  try {
    const response = await axios.get('/api/auth/registration-status')
    const enabled = response.data.enabled

    if (!enabled) {
      // Registration is disabled, redirect to home
      errorMessage.value = "User registration is currently disabled"

      // Wait 2 seconds before redirecting
      setTimeout(() => {
        router.push({
          path: '/',
          query: { showModal: 'login' },
          params: { message: 'Registration is disabled. Please contact the administrator.' }
        })
      }, 2000)
    }
  } catch (error) {
    // Error checking registration status (console.error removed)
  }
}

// Navigate back to login
function goToLogin() {
  router.push({ path: '/', query: { showModal: 'login' } })
}

// Step 1 validation
async function validateStep1() {
  // First check if the username exists
  await checkUsernameExists()

  // If username exists, don't proceed
  if (usernameExists.value) {
    return
  }

  const isValid = await accountForm.value.validate()
  if (isValid.valid) {
    currentStep.value = '2'
  }
}

// Step 2 validation
async function validateStep2() {
  const isValid = await profileForm.value.validate()
  if (isValid.valid) {
    currentStep.value = '3'
  }
}

// Handle profile photo update from uploader component
function handlePhotoUpdate(photo) {
  profilePhoto.value = photo
}

// Complete registration process
async function completeRegistration() {
  if (!forms.profile.valid) { // This check seems out of place if currentStep is '3'
    errorMessage.value = "Please fill in required fields" // Consider re-validating or removing this check
    return
  }

  isSubmitting.value = true
  errorMessage.value = null

  try {
    // 1. First, create the user
    const userData = {
      username: username.value,
      password: password.value,
      first_name: firstName.value,
      last_name: lastName.value,
      role: 'user' // Regular user role
    }

    const registrationResult = await authStore.register(userData)

    if (!registrationResult) {
      throw new Error(authStore.error || "Failed to create user account")
    }

    // 2. If we have a profile photo, upload it
    if (profilePhoto.value) {
      await uploadProfilePhoto()
    }

    // 3. Make sure splash screen state is reset
    splashStore.resetSplashState()

    // 4. Navigate to splash screen instead of dashboard
    router.push('/splash')
  } catch (error) {
    errorMessage.value = error.message || "An error occurred during registration"
  } finally {
    isSubmitting.value = false
  }
}

// Upload profile photo if provided
async function uploadProfilePhoto() {
  if (!profilePhoto.value) {
    return true
  }

  try {
    const formData = new FormData()
    formData.append('photo', profilePhoto.value)

    const result = await authStore.updateProfilePhoto(profilePhoto.value)

    if (result) {
      return true
    } else {
      return false
    }
  } catch (error) {
    return false
  }
}
</script>

<style scoped>
.register-view {
  min-height: 100vh;
  width: 100%;
  position: relative;
  overflow-x: hidden;
  overflow-y: auto;
}

/* Add a global style to eliminate any possible scrolling */
:global(html),
:global(body) {
  margin: 0;
  padding: 0;
  min-height: 100vh;
  overflow-x: hidden;
}

/* TPM Background styling (matching HomeView) */
.tpm-background {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: -1;
  background-color: #030b14;
  background-image:
    radial-gradient(circle at 20% 35%, rgba(0, 56, 101, 0.15) 0%, transparent 50%),
    radial-gradient(circle at 75% 44%, rgba(6, 125, 76, 0.1) 0%, transparent 50%);
  overflow: hidden;
}

.tpm-mobile {
  /* Adjust background for mobile devices */
  background-image:
    radial-gradient(circle at 50% 30%, rgba(0, 56, 101, 0.15) 0%, transparent 60%),
    radial-gradient(circle at 50% 70%, rgba(6, 125, 76, 0.1) 0%, transparent 60%);
}

.register-card {
  background-color: rgba(15, 23, 42, 0.7) !important;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 0 30px rgba(0, 0, 0, 0.5) !important;
}

.register-stepper {
  background-color: transparent !important;
}

/* Logo styling - fix to remove box */
.logo {
  width: 80px;
  height: auto;
  filter: drop-shadow(0 0 10px rgba(138, 43, 226, 0.7));
}

@media (min-width: 600px) {
  .logo {
    width: 100px;
  }
}

.animated-logo {
  animation: pulse 3s infinite alternate, color-shift 10s infinite alternate;
}

/* Improved Stepper Styling */
.active-step {
  color: #00ff9c !important;
  font-weight: bold;
}

.active-step :deep(.v-stepper-item__avatar) {
  background-color: #00ff9c !important;
  box-shadow: 0 0 15px rgba(0, 255, 156, 0.7);
}

.completed-step :deep(.v-stepper-item__avatar) {
  background-color: #00ff9c !important;
  opacity: 0.8;
}

.register-stepper :deep(.v-stepper-item) {
  transition: all 0.3s ease;
}

.active-divider {
  border-color: #00ff9c !important;
  position: relative;
  overflow: hidden;
}

.active-divider::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(0, 255, 156, 0.7), transparent);
  animation: pulse-divider 2s ease-in-out infinite;
}

@keyframes pulse-divider {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

/* Cyberpunk button styles */
.btn-cyber {
  position: relative;
  overflow: hidden;
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
}

/* Wrapper for strength meter to ensure visibility */
.strength-meter-wrapper {
  width: 100%;
  display: block;
  margin-bottom: 1rem;
}

/* Cyber title styling */
.cyber-title {
  font-family: var(--font-heading);
  color: #00ff9c;
  text-shadow: 0 0 10px rgba(0, 255, 156, 0.7);
  letter-spacing: 1px;
  text-transform: uppercase;
  position: relative;
  font-weight: 600;
}

.cyber-title::after {
  content: '';
  position: absolute;
  bottom: -8px;
  left: 50%;
  transform: translateX(-50%);
  width: 100px;
  height: 2px;
  background: linear-gradient(90deg,
    transparent,
    rgba(0, 255, 156, 0.7),
    transparent);
}

/* Animations */
@keyframes pulse {
  0% { transform: scale(1); filter: brightness(1); }
  100% { transform: scale(1.05); filter: brightness(1.2); }
}

@keyframes color-shift {
  0% { filter: drop-shadow(0 0 8px rgba(0, 255, 156, 0.7)); }
  33% { filter: drop-shadow(0 0 8px rgba(0, 136, 255, 0.7)); }
  66% { filter: drop-shadow(0 0 8px rgba(140, 82, 255, 0.7)); }
  100% { filter: drop-shadow(0 0 8px rgba(0, 255, 156, 0.7)); }
}

@keyframes glitch {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

/* Footer styling */
.footer-text {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.6);
  width: 100%;
}

.version-text {
  color: #00ff9c;
  font-family: var(--font-heading);
  letter-spacing: 1px;
  margin-right: 5px;
}
</style>