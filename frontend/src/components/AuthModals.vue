<template>
  <div class="auth-modals">
    <v-dialog 
      v-model="showLoginModal" 
      max-width="500px" 
      @click:outside="closeLoginModal"
      @keydown.esc="closeLoginModal"
      @update:model-value="val => !val && closeLoginModal()"
      retain-focus
      persistent
    >
      <div class="card card-glass">
        <div class="card-header text-center position-relative">
          <v-btn
            icon
            size="small"
            class="position-absolute"
            style="top: 5px; right: 5px;"
            @click="closeLoginModal"
          >
            <v-icon>mdi-close</v-icon>
          </v-btn>
          <h1 class="card-title terminal-text">Login</h1>
        </div>
        
        <div class="card-body">
          <div
            v-if="authStore.error"
            class="alert alert-cyber alert-error mb-lg"
          >
            {{ authStore.error }}
          </div>
          
          <div
            v-if="loginSuccess"
            class="alert alert-cyber alert-success mb-lg"
          >
            Login successful! Redirecting...
          </div>
          
          <v-form @submit.prevent="handleLogin" ref="loginForm">
            <div class="form-group">
              <v-text-field
                v-model="loginUsername"
                label="Username"
                prepend-inner-icon="mdi-account"
                required
                variant="outlined"
                bg-color="transparent"
                class="glass-input mb-md"
                :rules="[v => !!v || 'Username is required']"
              ></v-text-field>
            </div>
            
            <div class="form-group">
              <v-text-field
                v-model="loginPassword"
                label="Password"
                prepend-inner-icon="mdi-lock"
                :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
                @click:append-inner="showPassword = !showPassword"
                :append-inner-icon-tabindex="-1"
                :type="showPassword ? 'text' : 'password'"
                required
                variant="outlined"
                bg-color="transparent"
                class="glass-input mb-lg"
                :rules="[v => !!v || 'Password is required']"
              ></v-text-field>
            </div>
            
            <div class="d-flex flex-column align-center">
              <v-btn
                color="primary"
                type="submit"
                class="btn-cyber btn-login mb-md"
                :loading="authStore.loading"
                height="50"
                min-width="150px"
              >
                <div class="btn-cyber-glitch"></div>
                <v-icon start>mdi-login</v-icon>
                Login
              </v-btn>
              
              <div class="d-flex justify-center align-center mt-md">
                <span class="text-body-2">Don't have an account?</span>
                <v-btn
                  variant="text"
                  color="primary"
                  class="ml-2 terminal-link"
                  @click="showRegisterInstead"
                  :disabled="authStore.loading"
                >
                  Register
                </v-btn>
              </div>
            </div>
          </v-form>
        </div>
      </div>
    </v-dialog>

    <v-dialog 
      v-model="showRegisterModal" 
      max-width="500px" 
      @click:outside="closeRegisterModal"
      @keydown.esc="closeRegisterModal"
      @update:model-value="val => !val && closeRegisterModal()"
      retain-focus
      persistent
    >
      <div class="card card-glass">
        <div class="card-header text-center position-relative">
          <v-btn
            icon
            size="small"
            class="position-absolute"
            style="top: 5px; right: 5px;"
            @click="closeRegisterModal"
          >
            <v-icon>mdi-close</v-icon>
          </v-btn>
          <h1 class="card-title terminal-text">Register</h1>
        </div>
        
        <div class="card-body">
          <v-alert
            v-if="authStore.error"
            type="error"
            variant="tonal"
            closable
            class="mb-4"
          >
            {{ authStore.error }}
          </v-alert>
          
          <v-form @submit.prevent="handleRegister" ref="registerForm">
            <v-stepper v-model="registerStep" class="mb-4 register-stepper">
              <v-stepper-header>
                <v-stepper-item 
                  value="1" 
                  complete-icon="mdi-account-key"
                  :class="{'active-step': registerStep === '1', 'completed-step': registerStep > '1'}"
                >
                  <span class="d-none d-sm-flex">Account</span>
                </v-stepper-item>
                
                <v-divider :class="{'active-divider': registerStep >= '2'}"></v-divider>
                
                <v-stepper-item 
                  value="2" 
                  complete-icon="mdi-camera-account"
                  :class="{'active-step': registerStep === '2'}"
                >
                  <span class="d-none d-sm-flex">Photo</span>
                </v-stepper-item>
              </v-stepper-header>
            </v-stepper>

            <div v-if="registerStep === '1'">
              <div class="form-group">
                <v-text-field
                  v-model="registerUsername"
                  label="Username"
                  prepend-inner-icon="mdi-account"
                  required
                  variant="outlined"
                  bg-color="transparent"
                  class="glass-input mb-md"
                  :rules="[v => !!v || 'Username is required', v => v.length >= 3 || 'Username must be at least 3 characters']"
                ></v-text-field>
              </div>
              
              <div class="form-group">
                <v-text-field
                  v-model="registerPassword"
                  label="Password"
                  prepend-inner-icon="mdi-lock"
                  :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
                  @click:append-inner="showPassword = !showPassword"
                  :append-inner-icon-tabindex="-1"
                  :type="showPassword ? 'text' : 'password'"
                  required
                  variant="outlined"
                  bg-color="transparent"
                  class="glass-input mb-sm"
                  :rules="[
                    v => !!v || 'Password is required',
                    v => v.length >= 8 || 'Password must be at least 8 characters'
                  ]"
                  @update:model-value="updatePasswordStrength"
                ></v-text-field>
              </div>
              
              <div class="password-strength-container mb-md" v-if="registerPassword">
                <div class="strength-label d-flex justify-space-between">
                  <span>Strength:</span>
                  <span :class="strengthColorClass">{{ strengthText }}</span>
                </div>
                <div class="strength-meter">
                  <div class="strength-meter-fill" :style="{ width: `${passwordStrength}%`, backgroundColor: strengthColor }"></div>
                </div>
              </div>
              
              <div class="form-group">
                <v-text-field
                  v-model="confirmPassword"
                  label="Confirm Password"
                  prepend-inner-icon="mdi-lock-check"
                  :type="showPassword ? 'text' : 'password'"
                  required
                  variant="outlined"
                  bg-color="transparent"
                  class="glass-input mb-lg"
                  :rules="[
                    v => !!v || 'Please confirm your password',
                    v => v === registerPassword || 'Passwords do not match'
                  ]"
                ></v-text-field>
              </div>
              
              <div class="d-flex justify-center mb-4">
                <v-btn
                  color="primary"
                  @click="validateRegisterStep1"
                  class="mr-2"
                  :disabled="authStore.loading"
                >
                  <v-icon end>mdi-arrow-right</v-icon>
                  Continue
                </v-btn>
              </div>
            </div>

            <div v-if="registerStep === '2'">
              <div class="text-center mb-4">
                <p class="text-body-2 text-medium-emphasis">
                  Add a profile photo (optional)
                </p>
              </div>
              
              <ProfilePhotoUploader
                :initial-photo-data="profilePhotoData"
                @update:photo="handlePhotoUpdate"
                class="mb-6"
                ref="photoUploader"
              />
              
              <div class="d-flex justify-center">
                <v-btn
                  color="secondary"
                  type="submit"
                  class="mt-4 btn-register"
                  :loading="authStore.loading"
                  min-width="150px"
                >
                  <v-icon start>mdi-account-plus</v-icon>
                  {{ profilePhoto ? 'Register with Photo' : 'Register' }}
                </v-btn>
                
                <v-btn
                  variant="text"
                  color="primary"
                  class="mt-4 ml-2"
                  @click="registerStep = '1'"
                  :disabled="authStore.loading"
                >
                  <v-icon start>mdi-arrow-left</v-icon>
                  Back
                </v-btn>
              </div>
            </div>
            
            <div class="d-flex justify-center align-center mt-4">
              <span class="text-body-2">Already have an account?</span>
              <v-btn
                variant="text"
                color="primary"
                class="ml-2 terminal-link"
                @click="showLoginInstead"
                :disabled="authStore.loading"
              >
                Login
              </v-btn>
            </div>
          </v-form>
        </div>
      </div>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, defineEmits, watch, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'
import ProfilePhotoUploader from '@/components/ProfilePhotoUploader.vue'
import { useSplashStore } from '@/stores/splash'

const emit = defineEmits(['modal-opened', 'modal-closed'])
const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const splashStore = useSplashStore()

const showLoginModal = ref(false)
const showRegisterModal = ref(false)

const loginForm = ref(null)
const registerForm = ref(null)
const photoUploader = ref(null)

const registerStep = ref('1')

const loginUsername = ref('')
const loginPassword = ref('')
const registerUsername = ref('')
const registerPassword = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)

const profilePhoto = ref(null)
const profilePhotoData = ref(null)

const passwordStrength = ref(0)
const strengthText = ref('')
const strengthColor = ref('')
const strengthColorClass = ref('')

const loginSuccess = ref(false)

const updatePasswordStrength = () => {
  const password = registerPassword.value
  
  if (!password) {
    passwordStrength.value = 0
    strengthText.value = ''
    strengthColor.value = ''
    strengthColorClass.value = ''
    return
  }
  
  let strength = 0
  
  if (password.length >= 12) {
    strength += 25
  } else if (password.length >= 8) {
    strength += 15
  } else {
    strength += 5
  }
  
  if (/[A-Z]/.test(password)) strength += 15
  if (/[a-z]/.test(password)) strength += 10
  if (/[0-9]/.test(password)) strength += 15
  if (/[^A-Za-z0-9]/.test(password)) strength += 20
  
  if (/(.)\1\1/.test(password)) strength -= 10
  if (/^[A-Za-z]+$/.test(password) || /^[0-9]+$/.test(password)) strength -= 5
  
  const sequences = ['abcdefghijklmnopqrstuvwxyz', '01234567890', 'qwertyuiop', 'asdfghjkl', 'zxcvbnm']
  for (const seq of sequences) {
    for (let i = 0; i < seq.length - 2; i++) {
      const fragment = seq.substring(i, i + 3)
      if (password.toLowerCase().includes(fragment)) {
        strength -= 10
        break
      }
    }
  }
  
  passwordStrength.value = Math.max(0, Math.min(100, strength))
  
  if (passwordStrength.value >= 80) {
    strengthText.value = 'Strong'
    strengthColor.value = '#00ff9c'
    strengthColorClass.value = 'text-success'
  } else if (passwordStrength.value >= 50) {
    strengthText.value = 'Medium'
    strengthColor.value = '#eacc13'
    strengthColorClass.value = 'text-warning'
  } else {
    strengthText.value = 'Weak'
    strengthColor.value = '#ff5252'
    strengthColorClass.value = 'text-error'
  }
}

function handlePhotoUpdate(photo) {
  profilePhoto.value = photo
}

async function validateRegisterStep1() {
  const { valid } = await registerForm.value.validate()
  if (valid) {
    registerStep.value = '2'
  }
}

const getRedirectUrl = () => {
  return route.query.redirect || '/'
}

const openLoginModal = () => {
  showLoginModal.value = true
  showRegisterModal.value = false
  emit('modal-opened')
}

const openRegisterModal = () => {
  showRegisterModal.value = true
  showLoginModal.value = false
  registerStep.value = '1'
  emit('modal-opened')
}

const closeLoginModal = () => {
  showLoginModal.value = false
  authStore.error = null
  emit('modal-closed')
}

const closeRegisterModal = () => {
  showRegisterModal.value = false
  authStore.error = null
  registerStep.value = '1'
  profilePhoto.value = null
  emit('modal-closed')
}

const showLoginInstead = () => {
  closeRegisterModal()
  openLoginModal()
}

const showRegisterInstead = async () => {
  try {
    const response = await axios.get('/api/auth/registration-status')
    if (!response.data.enabled) {
      authStore.error = "Registration is currently disabled"
      return
    }
    
    closeLoginModal()
    openRegisterModal()
  } catch (error) {
    closeLoginModal()
    openRegisterModal()
  }
}

async function uploadProfilePhoto(userId) {
  if (!profilePhoto.value) {
    return true
  }
  
  try {
    const token = authStore.token
    if (!token) {
      return false
    }
    
    const formData = new FormData()
    formData.append('photo', profilePhoto.value)
    
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
    
    return false
  } catch (error) {
    return false
  }
}

const handleLogin = async () => {
  const { valid } = await loginForm.value.validate()
  
  if (valid) {
    loginSuccess.value = false
    
    const result = await authStore.login(loginUsername.value, loginPassword.value)
    
    if (result) {
      if (authStore.token) {
        axios.defaults.headers.common['Authorization'] = `Bearer ${authStore.token}`
      }
      
      loginSuccess.value = true
      
      splashStore.resetSplashState()
      
      setTimeout(() => {
        closeLoginModal()
        
        setTimeout(() => {
          const redirectPath = route.query.redirect
          
          if (redirectPath) {
            router.push(redirectPath)
          } else {
            router.push('/splash').catch(error => {
              console.error('Navigation error:', error)
              router.push('/dashboard')
            })
          }
        }, 100)
      }, 500)
    }
  }
}

const handleRegister = async () => {
  const { valid } = await registerForm.value.validate()
  
  if (valid) {
    const result = await authStore.register({
      username: registerUsername.value,
      password: registerPassword.value
    })
    
    if (result) {
      if (profilePhoto.value) {
        const photoResult = await uploadProfilePhoto()
      }
      
      splashStore.resetSplashState()
      
      closeRegisterModal()
      
      router.push('/splash')
    }
  }
}

watch([showLoginModal, showRegisterModal], ([loginVisible, registerVisible], [prevLoginVisible, prevRegisterVisible]) => {
  if ((!prevLoginVisible && !prevRegisterVisible) && (loginVisible || registerVisible)) {
    emit('modal-opened')
  } 
  else if ((prevLoginVisible || prevRegisterVisible) && !loginVisible && !registerVisible) {
    emit('modal-closed')
  }
}, { immediate: true })

onUnmounted(() => {
  if (showLoginModal.value || showRegisterModal.value) {
    emit('modal-closed')
  }
})

defineExpose({
  openLoginModal,
  openRegisterModal,
  closeLoginModal,
  closeRegisterModal
})
</script>

<style scoped>
.terminal-link {
  position: relative;
  font-family: var(--font-heading);
  letter-spacing: 1px;
}

.terminal-link::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 1px;
  background-color: currentColor;
  transform: scaleX(0);
  transform-origin: right;
  transition: transform 0.25s ease;
}

.terminal-link:hover::after {
  transform: scaleX(1);
  transform-origin: left;
}

:deep(.v-overlay__scrim) {
  backdrop-filter: blur(5px);
  -webkit-backdrop-filter: blur(5px);
  background-color: rgba(10, 14, 20, 0.7) !important;
}

:deep(.v-dialog) {
  box-shadow: 0 0 20px rgba(0, 255, 156, 0.2);
  overflow: hidden;
}

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

:deep(.v-field__input),
:deep(.v-field),
:deep(.v-field__field),
:deep(.v-field--focused),
:deep(.v-field--active),
:deep(.v-field__overlay) {
  background-color: transparent !important;
}

:deep(.v-field--variant-outlined),
:deep(.v-field--variant-filled),
:deep(.v-field--variant-plain) {
  background-color: transparent !important;
}

:deep(.v-field__overlay) {
  opacity: 0 !important;
}
</style>