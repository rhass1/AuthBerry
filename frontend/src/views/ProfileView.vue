<template>
  <v-container class="profile-container">
    <div class="cyber-background">
      <div class="grid"></div>
      <div class="cyber-lines"></div>
      <div class="glow-overlay"></div>
    </div>

    <v-row justify="center">
      <v-col cols="12" md="10" lg="8">
        <div class="hero-section mb-8">
          <div class="profile-hero-content">
            <div class="profile-photo-wrapper">
              <div class="profile-photo-container">
                <ProfilePhotoUploader
                  :initial-photo-data="authStore.profilePhoto"
                  @update:photo="handlePhotoUpdate"
                  class="profile-uploader"
                />
                <div class="photo-glow"></div>
              </div>
            </div>
            <div class="profile-info">
              <h1 class="cyber-name">{{ authStore.displayName }}</h1>
            </div>
          </div>

          <div class="quick-actions">
            <v-btn
              color="primary"
              variant="outlined"
              class="btn-cyber action-btn security-btn"
              @click="router.push('/dashboard')"
              prepend-icon="mdi-arrow-left"
            >
              Back to Dashboard
            </v-btn>
          </div>
        </div>

        <div class="content-grid">
          <v-card class="cyber-card info-card" elevation="0">
            <div class="card-glow"></div>
            <v-card-title class="d-flex align-center">
              <v-icon color="primary" size="28" class="mr-2">mdi-account-circle</v-icon>
              Account Information
            </v-card-title>
            <v-card-text>
              <div class="info-list">
                <div class="info-item">
                  <div class="info-label">
                    <v-icon color="primary" class="mr-2">mdi-account</v-icon>
                    Username
                  </div>
                  <div class="info-value">{{ authStore.user?.username }}</div>
                </div>

                <div class="info-item">
                  <div class="info-label">
                    <v-icon color="primary" class="mr-2">mdi-shield-account</v-icon>
                    Role
                  </div>
                  <div class="info-value">{{ authStore.user?.role }}</div>
                </div>
              </div>
            </v-card-text>
          </v-card>

          <v-card class="cyber-card security-card" elevation="0">
            <div class="card-glow"></div>
            <v-card-title class="d-flex align-center">
              <v-icon color="info" size="28" class="mr-2">mdi-shield-lock</v-icon>
              Security
            </v-card-title>
            <v-card-text>
              <p class="security-text">Your account is secured with a password. Keep it strong and unique.</p>
              <v-btn
                color="primary"
                variant="outlined"
                class="mt-4 btn-cyber security-btn"
                @click="openPasswordDialog"
              >
                <div class="btn-cyber-glitch"></div>
                <v-icon start>mdi-key</v-icon>
                Update Password
              </v-btn>
            </v-card-text>
          </v-card>

          <v-card class="cyber-card actions-card" elevation="0">
            <div class="card-glow"></div>
            <v-card-title class="d-flex align-center">
              <v-icon color="warning" size="28" class="mr-2">mdi-cog</v-icon>
              Account Actions
            </v-card-title>
            <v-card-text>
              <div class="actions-container">
                <v-btn
                  color="error"
                  variant="outlined"
                  class="btn-cyber action-btn"
                  @click="confirmLogout"
                >
                  <div class="btn-cyber-glitch"></div>
                  <v-icon start>mdi-logout</v-icon>
                  Logout
                </v-btn>

                <v-btn
                  color="error"
                  variant="outlined"
                  class="btn-cyber action-btn"
                  @click="confirmDeleteAccount"
                >
                  <div class="btn-cyber-glitch"></div>
                  <v-icon start>mdi-delete</v-icon>
                  Delete Account
                </v-btn>
              </div>
            </v-card-text>
          </v-card>

          <v-card class="cyber-card stats-card" elevation="0">
            <div class="card-glow"></div>
            <v-card-title class="d-flex align-center">
              <v-icon color="primary" size="28" class="mr-2">mdi-chart-box</v-icon>
              Activity Overview
            </v-card-title>
            <v-card-text>
              <div class="stats-grid">
                <div class="stat-item">
                  <div class="stat-icon">
                    <v-icon size="36" color="primary">mdi-lock</v-icon>
                    <div class="stat-particles"></div>
                  </div>
                  <div class="stat-value">{{ secretsStore.secrets.length }}</div>
                  <div class="stat-label">Secrets Created</div>
                </div>

                <div class="stat-item">
                  <div class="stat-icon">
                    <v-icon size="36" color="info">mdi-share-variant</v-icon>
                    <div class="stat-particles"></div>
                  </div>
                  <div class="stat-value">{{ sharedSecretsCount }}</div>
                  <div class="stat-label">Secrets Shared</div>
                </div>

                <div class="stat-item">
                  <div class="stat-icon">
                    <v-icon size="36" color="success">mdi-calendar-check</v-icon>
                    <div class="stat-particles"></div>
                  </div>
                  <div class="stat-value">{{ daysActive }}</div>
                  <div class="stat-label">Days Active</div>
                </div>
              </div>
            </v-card-text>
          </v-card>
        </div>
      </v-col>
    </v-row>

    <v-dialog v-model="showPasswordDialog" max-width="500px" class="cyber-dialog">
      <v-card class="cyber-card password-dialog">
        <div class="dialog-glow"></div>
        <v-card-title class="text-h5">Update Password</v-card-title>
        <v-card-text>
          <v-form @submit.prevent ref="passwordFormRef">
            <v-alert
              v-if="authStore.error"
              type="error"
              class="mb-4"
              density="compact"
              closable
              @click:close="authStore.error = null"
            >
              {{ authStore.error }}
            </v-alert>

            <v-text-field
              v-model="passwordForm.currentPassword"
              label="Current Password"
              :append-inner-icon="showCurrentPassword ? 'mdi-eye-off' : 'mdi-eye'"
              @click:append-inner="showCurrentPassword = !showCurrentPassword"
              :type="showCurrentPassword ? 'text' : 'password'"
              :rules="passwordRules.currentPassword"
              class="cyber-input mb-4"
              persistent-hint
              tabindex="1"
              autofocus
            ></v-text-field>

            <v-text-field
              v-model="passwordForm.newPassword"
              label="New Password"
              :append-inner-icon="showNewPassword ? 'mdi-eye-off' : 'mdi-eye'"
              @click:append-inner="showNewPassword = !showNewPassword"
              :type="showNewPassword ? 'text' : 'password'"
              :rules="passwordRules.newPassword"
              class="cyber-input mb-4"
              persistent-hint
              tabindex="2"
            ></v-text-field>

            <v-text-field
              v-model="passwordForm.confirmPassword"
              label="Confirm New Password"
              :type="showNewPassword ? 'text' : 'password'"
              :rules="confirmPasswordRules"
              class="cyber-input"
              persistent-hint
              tabindex="3"
            ></v-text-field>
          </v-form>
        </v-card-text>
        <v-card-actions class="dialog-actions">
          <v-spacer></v-spacer>
          <v-btn
            color="grey-darken-1"
            variant="text"
            class="btn-cyber"
            @click="cancelPasswordUpdate"
            tabindex="4"
          >
            Cancel
          </v-btn>
          <v-btn
            color="primary"
            variant="flat"
            class="btn-cyber"
            @click="updatePassword"
            :loading="passwordFormLoading"
            tabindex="5"
          >
            Update
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="showLogoutDialog" max-width="400px" class="cyber-dialog">
      <v-card class="cyber-card logout-dialog">
        <div class="dialog-glow"></div>
        <v-card-title class="text-h5">Confirm Logout</v-card-title>
        <v-card-text>
          Are you sure you want to log out of your account?
        </v-card-text>
        <v-card-actions class="dialog-actions">
          <v-spacer></v-spacer>
          <v-btn
            color="grey-darken-1"
            variant="text"
            class="btn-cyber"
            @click="showLogoutDialog = false"
          >
            Cancel
          </v-btn>
          <v-btn
            color="error"
            variant="flat"
            class="btn-cyber"
            @click="logout"
          >
            Logout
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="showDeleteDialog" max-width="500px" class="cyber-dialog">
      <v-card class="cyber-card delete-dialog">
        <div class="dialog-glow"></div>
        <v-card-title class="text-h5 text-error">Delete Account</v-card-title>
        <v-card-text>
          <p class="mb-4">This action will permanently delete your account and all associated data. This cannot be undone.</p>
          <v-form @submit.prevent="deleteAccount" ref="deleteForm">
            <v-text-field
              v-model="deleteForm.password"
              label="Current Password"
              :append-inner-icon="showDeletePassword ? 'mdi-eye-off' : 'mdi-eye'"
              @click:append-inner="showDeletePassword = !showDeletePassword"
              :type="showDeletePassword ? 'text' : 'password'"
              required
              :rules="[v => !!v || 'Password is required']"
              class="cyber-input mb-4"
            ></v-text-field>

            <v-text-field
              v-model="deleteForm.confirmation"
              label="Type DELETE to confirm"
              required
              :rules="[
                v => !!v || 'Confirmation is required',
                v => v === 'DELETE' || 'Please type DELETE exactly'
              ]"
              class="cyber-input"
            ></v-text-field>
          </v-form>
        </v-card-text>
        <v-card-actions class="dialog-actions">
          <v-spacer></v-spacer>
          <v-btn
            color="grey-darken-1"
            variant="text"
            class="btn-cyber"
            @click="showDeleteDialog = false"
          >
            Cancel
          </v-btn>
          <v-btn
            color="error"
            variant="flat"
            class="btn-cyber"
            @click="deleteAccount"
            :loading="deleteFormLoading"
            :disabled="!canDelete"
          >
            Delete Account
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<style scoped>
.profile-container {
  position: relative;
  min-height: 100vh;
  padding-top: 2rem;
  z-index: 1;
  overflow-y: auto;
}

/* Animated Background */
.cyber-background {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, #0f1620 0%, #1a2635 100%);
  z-index: -1;
  overflow: hidden;
}

.grid {
  position: absolute;
  width: 200%;
  height: 200%;
  background-image: linear-gradient(rgba(0, 255, 156, 0.1) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(0, 255, 156, 0.1) 1px, transparent 1px);
  background-size: 50px 50px;
  transform: rotate(45deg);
  animation: gridMove 20s linear infinite;
}

.cyber-lines {
  position: absolute;
  width: 100%;
  height: 100%;
  background: repeating-linear-gradient(
    90deg,
    rgba(0, 255, 156, 0.05),
    rgba(0, 255, 156, 0.05) 1px,
    transparent 1px,
    transparent 30px
  );
  opacity: 0.5;
}

.glow-overlay {
  position: absolute;
  width: 100%;
  height: 100%;
  background: radial-gradient(circle at 50% 50%,
    rgba(0, 255, 156, 0.1) 0%,
    rgba(0, 136, 255, 0.1) 50%,
    transparent 100%
  );
  animation: glowPulse 4s ease-in-out infinite;
}

/* Hero Section */
.hero-section {
  position: relative;
  padding: 2rem;
  border-radius: 16px;
  background: rgba(15, 22, 32, 0.7);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 255, 156, 0.3);
  overflow: hidden;
}

.profile-hero-content {
  display: flex;
  align-items: center;
  gap: 2rem;
  margin-bottom: 2rem;
}

.profile-photo-wrapper {
  position: relative;
  width: 160px;
  height: 160px;
}

.profile-photo-container {
  position: relative;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  overflow: hidden;
  transition: all 0.3s ease;
  border: 2px solid rgba(0, 255, 156, 0.3);
  box-shadow: 0 0 20px rgba(0, 255, 156, 0.2);
  cursor: pointer;
}

.profile-photo-container:hover {
  border-color: rgba(0, 255, 156, 0.7);
  box-shadow: 0 0 30px rgba(0, 255, 156, 0.4);
  transform: scale(1.02);
}

.profile-photo-container:hover .photo-glow {
  opacity: 1;
}

.photo-glow {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: radial-gradient(circle at center,
    rgba(0, 255, 156, 0.3),
    transparent 70%
  );
  pointer-events: none;
  z-index: 2;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.profile-info {
  flex: 1;
}

.cyber-name {
  font-size: 3rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  background: linear-gradient(
    90deg,
    rgba(0, 255, 156, 0.9),
    rgba(0, 136, 255, 0.9)
  );
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow: 0 0 20px rgba(0, 255, 156, 0.3);
  position: relative;
}

.cyber-name::after {
  content: '';
  position: absolute;
  bottom: -4px;
  left: 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(0, 255, 156, 0.7),
    rgba(0, 136, 255, 0.7),
    transparent
  );
}

/* Content Grid */
.content-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
  margin-top: 2rem;
}

.cyber-card {
  position: relative;
  background: rgba(15, 22, 32, 0.7) !important;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 255, 156, 0.2) !important;
  overflow: hidden;
  transition: all 0.3s ease;
}

.cyber-card:hover {
  border-color: rgba(0, 255, 156, 0.4) !important;
  transform: translateY(-2px);
}

.cyber-card:hover .card-glow {
  opacity: 1;
}

.card-glow {
  position: absolute;
  inset: 0;
  background: radial-gradient(
    circle at var(--mouse-x, 50%) var(--mouse-y, 50%),
    rgba(0, 255, 156, 0.15),
    transparent 50%
  );
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  padding: 0.5rem;
}

.stat-item {
  position: relative;
  text-align: center;
  padding: 1rem;
  background: rgba(15, 22, 32, 0.5);
  border-radius: 12px;
  border: 1px solid rgba(0, 255, 156, 0.2);
}

.stat-item:hover {
  transform: none;
  border-color: rgba(0, 255, 156, 0.2);
}

.stat-icon {
  position: relative;
  margin-bottom: 0.5rem;
}

.stat-particles {
  position: absolute;
  inset: -10px;
  background: radial-gradient(
    circle at center,
    rgba(0, 255, 156, 0.2),
    transparent 70%
  );
  opacity: 0.3;
  pointer-events: none;
}

.stat-item:hover .stat-particles {
  opacity: 0.3;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: rgba(0, 255, 156, 0.9);
  text-shadow: 0 0 10px rgba(0, 255, 156, 0.3);
  margin-bottom: 0.25rem;
  line-height: 1;
}

.stat-label {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.7);
  text-transform: uppercase;
  letter-spacing: 1px;
  line-height: 1.2;
}

/* Buttons */
.btn-cyber {
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
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
}

.btn-cyber::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.2),
    transparent
  );
  transition: 0.5s;
}

.btn-cyber:hover::before {
  left: 100%;
}

.security-btn {
  min-width: 200px;
  color: rgb(0, 255, 156) !important;
}

.security-btn:hover {
  color: rgb(255, 255, 255) !important;
  background: rgba(0, 255, 156, 0.2) !important;
}

.logout-btn {
  width: 100%;
}

.actions-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.action-btn {
  width: 200px;
}

.info-list {
  padding: 0.5rem 0;
}

.info-item {
  padding: 1rem 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.info-item:last-child {
  border-bottom: none;
}

.info-label {
  display: flex;
  align-items: center;
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 0.5rem;
}

.info-value {
  font-size: 1.1rem;
  color: rgba(255, 255, 255, 0.9);
  padding-left: 1.8rem;
}

.delete-dialog {
  border-color: rgba(244, 67, 54, 0.3) !important;
}

.delete-dialog:hover {
  border-color: rgba(244, 67, 54, 0.5) !important;
}

/* Animations */
@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes glowPulse {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 0.8; }
}

@keyframes gridMove {
  0% { transform: rotate(45deg) translateY(0); }
  100% { transform: rotate(45deg) translateY(-50%); }
}

/* Responsive Design */
@media (max-width: 960px) {
  .content-grid {
    grid-template-columns: 1fr;
  }

  .stats-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 0.75rem;
  }

  .stat-item {
    padding: 0.75rem;
  }

  .stat-icon {
    margin-bottom: 0.25rem;
  }

  .stat-value {
    font-size: 1.75rem;
  }
}

@media (max-width: 600px) {
  .profile-hero-content {
    flex-direction: column;
    text-align: center;
  }

  .profile-photo-wrapper {
    width: 120px;
    height: 120px;
  }

  .cyber-name {
    font-size: 2rem;
  }

  .actions-container {
    align-items: center;
  }

  .stats-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: 0.5rem;
  }

  .stat-item {
    padding: 0.5rem;
  }

  .stat-icon :deep(i) {
    font-size: 24px !important;
  }

  .stat-value {
    font-size: 1.5rem;
  }

  .stat-label {
    font-size: 0.7rem;
  }
}

@media (max-width: 400px) {
  .stats-grid {
    grid-template-columns: 1fr;
    gap: 0.75rem;
  }

  .stat-item {
    padding: 0.75rem;
  }

  .stat-icon :deep(i) {
    font-size: 28px !important;
  }

  .stat-value {
    font-size: 1.75rem;
  }

  .stat-label {
    font-size: 0.8rem;
  }

  .action-btn {
    width: 100%;
  }
}
</style>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useSecretsStore } from '@/stores/secrets'
import ProfilePhotoUploader from '@/components/ProfilePhotoUploader.vue'

const router = useRouter()
const authStore = useAuthStore()
const secretsStore = useSecretsStore()

// Check if user data needs to be loaded
onMounted(async () => {
  if (!authStore.user) {
    await authStore.fetchUser()
  }

  // Get user's secrets for the stats
  if (secretsStore.secrets.length === 0) {
    await secretsStore.fetchSecrets()
  }
})

// Password update dialog
const showPasswordDialog = ref(false)
const showCurrentPassword = ref(false)
const showNewPassword = ref(false)
const passwordForm = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})
const passwordFormRef = ref(null)
const passwordFormLoading = ref(false)

// Create validation rules as computed properties to ensure they always have access to the latest form values
const passwordRules = computed(() => ({
  currentPassword: [v => !!v || 'Current password is required'],
  newPassword: [
    v => !!v || 'New password is required',
    v => v.length >= 8 || 'Password must be at least 8 characters'
  ]
}))

// Create a computed property for the confirm password rule
const confirmPasswordRules = computed(() => [
  v => !!v || 'Please confirm your password',
  v => v === passwordForm.value.newPassword || 'Passwords do not match'
])

// Logout dialog
const showLogoutDialog = ref(false)

// Delete account dialog and form
const showDeleteDialog = ref(false)
const showDeletePassword = ref(false)
const deleteForm = ref({
  password: '',
  confirmation: ''
})
const deleteFormRef = ref(null)
const deleteFormLoading = ref(false)

// Stats calculations
const sharedSecretsCount = computed(() => {
  return secretsStore.secrets.filter(secret => secret.shared_with?.length > 0).length
})

const daysActive = computed(() => {
  if (!authStore.user?.created_time) return 0

  // Parse the UTC date string
  const createdDate = new Date(authStore.user.created_time)
  const now = new Date()

  // Get time difference in milliseconds
  const diffTime = Math.abs(now - createdDate)

  // Convert to days and round up to include partial days
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24))
})

const canDelete = computed(() => {
  return deleteForm.value.password && deleteForm.value.confirmation === 'DELETE'
})

// Methods
async function handlePhotoUpdate(photo) {
  try {
    const result = await authStore.updateProfilePhoto(photo)
    if (!result) {
      throw new Error('Failed to update profile photo')
    }
  } catch (error) {
    // Error updating profile photo (console.error removed)
  }
}

async function updatePassword() {
  // Clear any previous error
  authStore.error = null

  try {
    if (!passwordFormRef.value) {
      return
    }

    // Validate form first
    const { valid } = await passwordFormRef.value.validate()

    if (!valid) {
      return
    }

    // If validation passed, proceed with updating password
    passwordFormLoading.value = true

    const result = await authStore.updatePassword({
      currentPassword: passwordForm.value.currentPassword,
      newPassword: passwordForm.value.newPassword
    })

    if (result) {
      // Success! Close the dialog
      showPasswordDialog.value = false
    }
  } catch (error) {
    // Failed to update password (console.error removed)
  } finally {
    passwordFormLoading.value = false
  }
}

// Add new initialization for when the dialog is opened
function openPasswordDialog() {
  // Reset the form and errors before showing the dialog
  passwordForm.value = {
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  }
  authStore.error = null
  showPasswordDialog.value = true

  // Use nextTick to ensure the dialog is rendered before trying to focus
  nextTick(() => {
    // Find the current password input element and focus it
    const firstInput = document.querySelector('.password-dialog .v-text-field input');
    if (firstInput) {
      firstInput.focus();
    }
  });
}

function confirmLogout() {
  showLogoutDialog.value = true
}

async function logout() {
  try {
    await authStore.logout()
    router.push('/')
  } catch (error) {
    // Logout error (console.error removed)
  } finally {
    showLogoutDialog.value = false
  }
}

function confirmDeleteAccount() {
  showDeleteDialog.value = true
}

async function deleteAccount() {
  if (!deleteFormRef.value) return

  const { valid } = await deleteFormRef.value.validate()
  if (!valid) return

  deleteFormLoading.value = true

  try {
    const result = await authStore.deleteAccount(deleteForm.value.password)
    if (result) {
      await router.push('/')
    }
  } catch (error) {
    // Failed to delete account (console.error removed)
  } finally {
    deleteFormLoading.value = false
  }
}

// Watch for dialog close to reset form state
watch(showPasswordDialog, (newVal, oldVal) => {
  if (!newVal && oldVal) {
    // Only reset form when dialog is closed, not during interaction
    setTimeout(() => {
      authStore.error = null
    }, 300)
  }
})

function cancelPasswordUpdate() {
  showPasswordDialog.value = false
}
</script>