<template>
  <div class="setup-view">
    <div class="tpm-background">
      <div class="tpm-circuit"></div>
      <div class="tpm-data-paths"></div>
      <div class="tpm-gates"></div>
      <div class="tpm-encryption"></div>
      <div class="tpm-transistors"></div>
      <div class="tpm-data-flow"></div>
    </div>

    <v-container class="d-flex flex-column justify-center align-center py-4 py-sm-6">
      <v-card max-width="600" width="100%" class="pa-4 pa-sm-6 my-4 setup-card">
        <div class="text-center mb-4 d-flex justify-center">
          <img src="/logo.svg" alt="AuthBerry Logo" class="logo animated-logo" />
        </div>

        <h1 class="text-h4 text-center mb-4 cyber-title">
          Admin Setup
        </h1>

        <v-alert
          v-if="errorMessage"
          type="error"
          variant="tonal"
          closable
          class="mb-4"
          @click:close="errorMessage = null"
        >
          {{ errorMessage }}
        </v-alert>

        <v-alert
          v-if="connectionError"
          type="error"
          variant="tonal"
          class="mb-4"
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
        >
          {{ authStore.error }}
        </v-alert>

        <v-stepper v-model="currentStep" class="mb-6 setup-stepper">
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
            label="Admin Username"
            prepend-icon="mdi-account-circle"
            required
            :rules="[
              v => !!v || 'Username is required',
              v => v.length >= 3 || 'Username must be at least 3 characters'
            ]"
            class="mb-4"
            tabindex="1"
            ref="usernameInput"
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
            @update:model-value="updatePasswordStrength"
          ></v-text-field>

          <div class="password-strength-container mb-4" v-if="password">
            <div class="strength-label d-flex justify-space-between">
              <span>Strength:</span>
              <span :class="strengthColorClass">{{ strengthText }}</span>
            </div>
            <div class="strength-meter">
              <div class="strength-meter-fill" :style="{ width: `${passwordStrength}%`, backgroundColor: strengthColor }"></div>
            </div>
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

          <v-alert
            type="info"
            variant="tonal"
            class="mb-6"
          >
            <p class="mb-0">
              This will create your administrator account with full access to manage users and secrets.
            </p>
          </v-alert>

          <div class="d-flex flex-column flex-sm-row justify-center align-center">
            <v-btn
              color="primary"
              type="submit"
              size="large"
              :disabled="connectionError"
              class="btn-cyber px-6 mb-3 mb-sm-0"
              width="auto"
              tabindex="4"
            >
              <div class="btn-cyber-glitch"></div>
              <v-icon start>mdi-arrow-right</v-icon>
              Continue to Profile
            </v-btn>

            <v-btn
              v-if="connectionError"
              color="secondary"
              variant="outlined"
              class="ml-sm-3"
              @click="retryConnection"
              :loading="checkingConnection"
              tabindex="5"
            >
              <v-icon start>mdi-refresh</v-icon>
              Retry Connection
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

          <div class="d-flex flex-column flex-sm-row justify-center align-center">
            <v-btn
              color="primary"
              type="submit"
              size="large"
              class="btn-cyber px-6 mb-3 mb-sm-0"
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
              class="ml-sm-3"
              @click="currentStep = '1'"
              width="auto"
              tabindex="4"
            >
              <v-icon start>mdi-arrow-left</v-icon>
              Back
            </v-btn>
          </div>
        </v-form>

        <div v-if="currentStep === '3'">
          <div class="text-center mb-4">
            <h3 class="text-h6">Add Your Profile Photo</h3>
            <p class="text-body-2 text-medium-emphasis">
              This will be displayed throughout the app. You can skip this step if you prefer.
            </p>
          </div>

          <div class="profile-photo-container mb-6">
            <ProfilePhotoUploader
              :initial-photo-data="profilePhotoData"
              @update:photo="handlePhotoUpdate"
              ref="photoUploader"
            />
          </div>

          <div class="d-flex flex-column flex-sm-row justify-center align-center">
            <v-btn
              color="primary"
              size="large"
              class="btn-cyber px-6 mb-3 mb-sm-0"
              :loading="isSubmitting"
              @click="completeSetup"
              width="auto"
              tabindex="1"
            >
              <div class="btn-cyber-glitch"></div>
              <v-icon start>mdi-check</v-icon>
              {{ profilePhoto ? 'Complete Setup with Photo' : 'Complete Setup' }}
            </v-btn>

            <v-btn
              color="secondary"
              variant="outlined"
              class="ml-sm-3"
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

// Password strength variables
const passwordStrength = ref(0)
const strengthText = ref('')
const strengthColor = ref('')
const strengthColorClass = ref('')

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

// Password strength evaluation function
const updatePasswordStrength = () => {
  const pwd = password.value

  if (!pwd) {
    passwordStrength.value = 0
    strengthText.value = ''
    strengthColor.value = ''
    strengthColorClass.value = ''
    return
  }

  // Calculate password strength based on various factors
  let strength = 0

  // Length
  if (pwd.length >= 12) {
    strength += 25
  } else if (pwd.length >= 8) {
    strength += 15
  } else {
    strength += 5
  }

  // Complexity - characters
  if (/[A-Z]/.test(pwd)) strength += 15 // Uppercase
  if (/[a-z]/.test(pwd)) strength += 10 // Lowercase
  if (/[0-9]/.test(pwd)) strength += 15 // Numbers
  if (/[^A-Za-z0-9]/.test(pwd)) strength += 20 // Special characters

  // Complexity - patterns
  if (/(.)\1\1/.test(pwd)) strength -= 10 // Repeating characters (3+)
  if (/^[A-Za-z]+$/.test(pwd) || /^[0-9]+$/.test(pwd)) strength -= 5 // Only letters or only numbers

  // Sequential characters check
  const sequences = ['abcdefghijklmnopqrstuvwxyz', '01234567890', 'qwertyuiop', 'asdfghjkl', 'zxcvbnm']
  for (const seq of sequences) {
    for (let i = 0; i < seq.length - 2; i++) {
      const fragment = seq.substring(i, i + 3)
      if (pwd.toLowerCase().includes(fragment)) {
        strength -= 10
        break
      }
    }
  }

  // Ensure the percentage is between 0 and 100
  passwordStrength.value = Math.max(0, Math.min(100, strength))

  // Set text and color based on strength
  if (passwordStrength.value >= 80) {
    strengthText.value = 'Strong'
    strengthColor.value = '#00ff9c' // Green
    strengthColorClass.value = 'text-success'
  } else if (passwordStrength.value >= 50) {
    strengthText.value = 'Medium'
    strengthColor.value = '#eacc13' // Yellow
    strengthColorClass.value = 'text-warning'
  } else {
    strengthText.value = 'Weak'
    strengthColor.value = '#ff5252' // Red
    strengthColorClass.value = 'text-error'
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
  try {
    await checkConnection()

    // Set focus on the first field
    nextTick(() => {
      if (usernameInput.value) {
        usernameInput.value.focus()
      }
    })
  } catch (error) {
    // Set connection error flag to allow UI to render properly with retry option
    connectionError.value = true
    checkingConnection.value = false
  }
})

// Check if the database is available
async function checkConnection() {
  checkingConnection.value = true

  try {
    const response = await axios.get('/api/auth/check-users-exist')
    connectionError.value = false
  } catch (err) {
    if (err.response) {
      // Any server response means the server is running but might have an error
      connectionError.value = err.response.status === 500
    } else if (err.request) {
      // Request was made but no response received - network error
      connectionError.value = true
    } else {
      // Other errors
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

// Retry database connection
async function retryConnection() {
  await checkConnection()
  // Also check if users exist (updates the authStore.anyUsersExist value)
  if (!connectionError.value) {
    await authStore.checkIfUsersExist()
  }
}

// Step 1 validation
async function validateStep1() {
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

// Complete setup process
async function completeSetup() {
  if (!forms.profile.valid) { // This check seems out of place for step 3
    errorMessage.value = "Please fill in required fields"
    return
  }

  isSubmitting.value = true
  errorMessage.value = null

  try {
    // 1. First, create the admin user
    const userData = {
      username: username.value,
      password: password.value,
      first_name: firstName.value,
      last_name: lastName.value,
      role: 'admin' // Explicitly set admin role
    }

    const setupResult = await authStore.setupAdmin(userData)

    if (!setupResult) {
      throw new Error(authStore.error || "Failed to create admin user")
    }

    // 2. Upload profile photo if one has been selected
    if (profilePhoto.value) {
      const photoResult = await uploadProfilePhoto()
      if (!photoResult) {
        // Photo upload failed, but continuing with setup (console.warn removed)
      }
    }

    // 3. Reset splash state so it will show after setup
    splashStore.resetSplashState()

    // 4. Navigate to dashboard (router guard will handle splash screen)
    router.push('/dashboard')
  } catch (error) {
    errorMessage.value = error.message || "An error occurred during setup"
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
    const token = localStorage.getItem('authToken')

    if (!token) {
      return false
    }

    const formData = new FormData()
    formData.append('photo', profilePhoto.value)

    try {
      const response = await fetch('/api/users/profile-photo', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      })

      const result = await response.json()

      if (response.ok && result.user && result.user.profile_photo_url) {
        profilePhotoData.value = result.user.profile_photo_url
        return true
      }
    } catch (fetchError) {
      
    }

    try {
      const response = await axios.post('/api/users/profile-photo', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.data.user && response.data.user.profile_photo_url) {
        profilePhotoData.value = response.data.user.profile_photo_url
        return true
      }
    } catch (axiosError) {
      
    }

    return false
  } catch (error) {
    return false
  }
}
</script>

<style scoped>
.setup-view {
  min-height: 100vh;
  width: 100%;
  position: relative;
}

/* Modified global styles to allow scrolling when needed */
:global(html),
:global(body) {
  margin: 0;
  padding: 0;
  min-height: 100vh;
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
}

.tpm-circuit {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: linear-gradient(rgba(0, 255, 240, 0.03) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(0, 255, 240, 0.03) 1px, transparent 1px);
  background-size: 40px 40px;
  background-position: center center;
  opacity: 0.3;
}

.setup-card {
  background-color: rgba(15, 23, 42, 0.7) !important;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 0 30px rgba(0, 0, 0, 0.5) !important;
}

.setup-stepper {
  background-color: transparent !important;
}

/* Logo styling - fix to remove box */
.logo {
  width: 100px;
  height: auto;
  filter: drop-shadow(0 0 10px rgba(138, 43, 226, 0.7));
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

.setup-stepper :deep(.v-stepper-item) {
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

/* Password Strength Meter Styles */
.password-strength-container {
  padding: 0.5rem 0;
}

.strength-label {
  font-size: 0.9rem;
  margin-bottom: 0.25rem;
  font-family: var(--font-heading);
  letter-spacing: 0.5px;
}

.text-success {
  color: #00ff9c;
  text-shadow: 0 0 8px rgba(0, 255, 156, 0.7);
}

.text-warning {
  color: #eacc13;
  text-shadow: 0 0 8px rgba(234, 204, 19, 0.7);
}

.text-error {
  color: #ff5252;
  text-shadow: 0 0 8px rgba(255, 82, 82, 0.7);
}

.strength-meter {
  height: 6px;
  background-color: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  position: relative;
  overflow: hidden;
  box-shadow: inset 0 0 5px rgba(0, 0, 0, 0.5);
}

.strength-meter-fill {
  height: 100%;
  transition: width 0.3s ease, background-color 0.3s ease;
  position: relative;
  border-radius: 2px;
  box-shadow: 0 0 10px currentColor;
}

.strength-meter-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.2) 50%,
    transparent 100%);
  animation: glitch 1.5s cubic-bezier(.25, .46, .45, .94) infinite;
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

/* Profile photo container styling */
.profile-photo-container {
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 0 auto;
  width: 100%;
  max-width: 200px;
  max-height: 200px;
}

/* Added responsive margins for smaller screens */
@media (max-width: 600px) {
  .setup-card {
    margin-top: 1rem;
    margin-bottom: 1rem;
  }
  
  .footer-text {
    margin-bottom: 1rem;
  }
}
</style>