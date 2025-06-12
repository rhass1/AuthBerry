<template>
  <div class="admin-view">
    <div class="back-button-container mb-4">
      <v-btn
        to="/dashboard"
        color="primary"
        variant="outlined"
        prepend-icon="mdi-arrow-left"
        class="btn-cyber-outline terminal-text"
      >
        Back to Dashboard
      </v-btn>
    </div>

    <div class="container">
      <div class="cyber-background">
        <div class="grid"></div>
        <div class="cyber-lines"></div>
        <div class="glow-overlay"></div>
      </div>

      <div class="title-container mb-6">
        <h1 class="cyber-title">Admin Dashboard</h1>
      </div>

      <v-alert
        v-if="!authStore.isAdmin"
        type="error"
        class="mb-6"
        variant="tonal"
        border="start"
      >
        You don't have permission to access this page.
        This page is only accessible to administrators.
      </v-alert>

      <template v-else>
        <v-card class="card-glass mb-6">
          <v-card-title class="cyber-card-title">
            <v-icon color="primary" class="mr-2">mdi-cog</v-icon>
            System Controls
          </v-card-title>

          <v-card-text>
            <v-switch
              v-model="registrationEnabled"
              color="primary"
              hide-details
              class="mb-4"
              @change="toggleRegistration"
              :loading="toggleRegistrationLoading"
            >
              <template v-slot:label>
                <span class="terminal-text">Allow New User Registrations</span>
              </template>
            </v-switch>

            <div class="d-flex align-center justify-space-between">
              <div class="d-flex align-center">
                <v-icon color="primary" class="mr-2">mdi-account-multiple</v-icon>
                <span class="terminal-text">Total Users: {{ users.length || 0 }}</span>
              </div>
              <div class="d-flex align-center">
                <v-icon color="error" class="mr-2">mdi-shield-account</v-icon>
                <span class="terminal-text">Admin Users: {{ adminCount }}</span>
              </div>
            </div>
          </v-card-text>
        </v-card>

        <v-card class="card-glass">
          <v-card-title class="cyber-card-title">
            <div class="d-flex align-center">
              <v-icon color="primary" class="mr-2">mdi-account-cog</v-icon>
              User Management
            </div>
            <v-spacer></v-spacer>

            <v-btn
              color="success"
              variant="flat"
              prepend-icon="mdi-account-plus"
              class="mr-4 terminal-text btn-cyber"
              @click="openCreateUserDialog"
            >
              Create User
            </v-btn>

            <v-text-field
              v-model="userSearch"
              append-icon="mdi-magnify"
              label="Search Users"
              variant="outlined"
              hide-details
              density="compact"
              class="search-field"
              bg-color="rgba(0, 0, 0, 0.2)"
              style="max-width: 300px"
            ></v-text-field>
          </v-card-title>

          <v-divider class="border-opacity-1"></v-divider>

          <div v-if="usersLoading" class="d-flex justify-center py-8">
            <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
          </div>

          <div v-else-if="filteredUsers.length > 0" class="responsive-table-wrapper">
            <v-table class="admin-table">
              <thead>
                <tr>
                  <th class="terminal-text">User</th>
                  <th class="terminal-text">Role</th>
                  <th class="terminal-text d-none d-sm-table-cell">Status</th>
                  <th class="terminal-text text-center">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="user in filteredUsers" :key="user.id" :class="{'current-user': user.id === authStore.userId}">
                  <td>
                    <div class="d-flex align-center">
                      <v-avatar color="primary" class="text-white mr-3 d-none d-sm-flex" size="36">
                        {{ user.username.charAt(0).toUpperCase() }}
                      </v-avatar>
                      <v-avatar color="primary" class="text-white mr-2 d-flex d-sm-none" size="28">
                        {{ user.username.charAt(0).toUpperCase() }}
                      </v-avatar>
                      <div>
                        <div class="font-weight-medium">{{ user.username }}</div>
                        <div class="text-caption text-medium-emphasis d-none d-sm-block">ID: {{ user.id }}</div>
                      </div>
                    </div>
                  </td>
                  <td>
                    <v-chip
                      :color="user.role === 'admin' ? 'error' : 'primary'"
                      size="small"
                    >
                      {{ user.role }}
                    </v-chip>
                  </td>
                  <td class="d-none d-sm-table-cell">
                    <v-chip
                      :color="user.locked ? 'warning' : 'success'"
                      size="small"
                    >
                      {{ user.locked ? 'Locked' : 'Active' }}
                    </v-chip>
                  </td>
                  <td>
                    <div class="d-flex justify-center action-buttons">
                      <v-tooltip :text="user.role === 'admin' ? 'Remove Admin Role' : 'Grant Admin Role'">
                        <template v-slot:activator="{ props }">
                          <v-btn
                            :icon="user.role === 'admin' ? 'mdi-shield-off' : 'mdi-shield'"
                            v-bind="props"
                            variant="text"
                            :color="user.role === 'admin' ? 'error' : 'success'"
                            size="small"
                            class="mx-1 btn-cyber-icon mobile-action-btn"
                            @click="toggleAdminRole(user)"
                            :disabled="user.id === authStore.userId"
                          ></v-btn>
                        </template>
                      </v-tooltip>

                      <v-tooltip :text="user.locked ? 'Unlock User' : 'Lock User'">
                        <template v-slot:activator="{ props }">
                          <v-btn
                            :icon="user.locked ? 'mdi-lock-open' : 'mdi-lock'"
                            v-bind="props"
                            variant="text"
                            :color="user.locked ? 'success' : 'warning'"
                            size="small"
                            class="mx-1 btn-cyber-icon mobile-action-btn"
                            @click="toggleUserLock(user)"
                            :disabled="user.id === authStore.userId"
                          ></v-btn>
                        </template>
                      </v-tooltip>

                      <v-tooltip text="Force Logout">
                        <template v-slot:activator="{ props }">
                          <v-btn
                            icon="mdi-logout"
                            v-bind="props"
                            variant="text"
                            color="info"
                            size="small"
                            class="mx-1 btn-cyber-icon mobile-action-btn"
                            @click="forceUserLogout(user)"
                            :disabled="user.id === authStore.userId"
                          ></v-btn>
                        </template>
                      </v-tooltip>

                      <v-tooltip text="Delete User">
                        <template v-slot:activator="{ props }">
                          <v-btn
                            icon="mdi-delete"
                            v-bind="props"
                            variant="text"
                            color="error"
                            size="small"
                            class="mx-1 btn-cyber-icon mobile-action-btn"
                            @click="confirmDeleteUser(user)"
                            :disabled="user.id === authStore.userId"
                          ></v-btn>
                        </template>
                      </v-tooltip>
                    </div>
                  </td>
                </tr>
              </tbody>
            </v-table>
          </div>

          <v-card-text v-else>
            <p class="text-center terminal-text">No users found.</p>
          </v-card-text>
        </v-card>
      </template>
    </div>

    <v-dialog v-model="deleteUserDialog.show" max-width="400" class="dialog-glass">
      <div class="card card-glass">
        <div class="card-header text-center position-relative cyber-card-header">
          <h1 class="cyber-dialog-title">Delete User</h1>
        </div>
        <div class="card-body">
          <p class="mb-6">
            Are you sure you want to delete the user <span class="terminal-text font-weight-bold">{{ deleteUserDialog.user?.username }}</span>?
          </p>
          <p class="mb-6">
            All data associated with this user will be permanently deleted. This action cannot be undone.
          </p>

          <div class="d-flex justify-end">
            <v-btn
              color="grey-darken-1"
              variant="text"
              class="mr-2 btn-cyber mobile-btn"
              @click="deleteUserDialog.show = false"
            >
              Cancel
            </v-btn>
            <v-btn
              color="error"
              variant="flat"
              class="btn-cyber mobile-btn"
              @click="deleteUser"
              :loading="deleteUserDialog.loading"
            >
              <v-icon start>mdi-delete</v-icon>
              Delete
            </v-btn>
          </div>
        </div>
      </div>
    </v-dialog>

    <v-dialog v-model="logoutUserDialog.show" max-width="400" class="dialog-glass">
      <div class="card card-glass">
        <div class="card-header text-center position-relative cyber-card-header">
          <h1 class="cyber-dialog-title">Force Logout</h1>
        </div>
        <div class="card-body">
          <p class="mb-6">
            Are you sure you want to force <span class="terminal-text font-weight-bold">{{ logoutUserDialog.user?.username }}</span> to log out from all active sessions?
          </p>

          <div class="d-flex justify-end">
            <v-btn
              color="grey-darken-1"
              variant="text"
              class="mr-2 btn-cyber mobile-btn"
              @click="logoutUserDialog.show = false"
            >
              Cancel
            </v-btn>
            <v-btn
              color="primary"
              variant="flat"
              class="btn-cyber mobile-btn"
              @click="confirmForceLogout"
              :loading="logoutUserDialog.loading"
            >
              <v-icon start>mdi-logout</v-icon>
              Force Logout
            </v-btn>
          </div>
        </div>
      </div>
    </v-dialog>

    <v-snackbar
      v-model="statusAlert.show"
      :color="statusAlert.color"
      timeout="3000"
      location="top"
    >
      {{ statusAlert.message }}
    </v-snackbar>

    <v-dialog v-model="createUserDialog.show" max-width="500" class="dialog-glass">
      <div class="card card-glass">
        <div class="card-header text-center position-relative cyber-card-header">
          <h1 class="cyber-dialog-title">Create New User</h1>
          <v-btn
            icon
            size="small"
            class="position-absolute btn-cyber"
            style="top: 5px; right: 5px;"
            @click="createUserDialog.show = false"
          >
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </div>

        <div class="card-body">
          <v-stepper v-model="createUserDialog.step" class="register-stepper">
            <v-stepper-header>
              <v-stepper-item
                value="1"
                complete-icon="mdi-account-key"
                :class="{'active-step': createUserDialog.step === '1', 'completed-step': createUserDialog.step > '1'}"
              >
                <span class="d-none d-sm-flex terminal-text">Account</span>
              </v-stepper-item>

              <v-divider :class="{'active-divider': createUserDialog.step >= '2'}"></v-divider>

              <v-stepper-item
                value="2"
                complete-icon="mdi-camera-account"
                :class="{'active-step': createUserDialog.step === '2'}"
              >
                <span class="d-none d-sm-flex terminal-text">Photo</span>
              </v-stepper-item>
            </v-stepper-header>

            <v-form @submit.prevent="handleCreateUser" ref="createUserForm">
              <div v-if="createUserDialog.step === '1'" class="mt-4">
                <div class="form-group">
                  <v-text-field
                    v-model="createUserDialog.form.username"
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
                    v-model="createUserDialog.form.password"
                    label="Password"
                    prepend-inner-icon="mdi-lock"
                    :append-inner-icon="createUserDialog.showPassword ? 'mdi-eye-off' : 'mdi-eye'"
                    @click:append-inner="createUserDialog.showPassword = !createUserDialog.showPassword"
                    :append-inner-icon-tabindex="-1"
                    :type="createUserDialog.showPassword ? 'text' : 'password'"
                    required
                    variant="outlined"
                    bg-color="transparent"
                    class="glass-input mb-md"
                    :rules="[
                      v => !!v || 'Password is required',
                      v => v.length >= 8 || 'Password must be at least 8 characters'
                    ]"
                    @update:model-value="updateCreatePasswordStrength"
                  ></v-text-field>
                </div>

                <div class="password-strength-container mb-md" v-if="createUserDialog.form.password">
                  <div class="strength-label d-flex justify-space-between">
                    <span class="terminal-text">Strength:</span>
                    <span :class="createUserDialog.passwordStrength.colorClass">{{ createUserDialog.passwordStrength.text }}</span>
                  </div>
                  <div class="strength-meter">
                    <div class="strength-meter-fill" :style="{
                      width: `${createUserDialog.passwordStrength.value}%`,
                      backgroundColor: createUserDialog.passwordStrength.color
                    }"></div>
                  </div>
                </div>

                <div class="form-group">
                  <v-text-field
                    v-model="createUserDialog.form.confirmPassword"
                    label="Confirm Password"
                    prepend-inner-icon="mdi-lock-check"
                    :type="createUserDialog.showPassword ? 'text' : 'password'"
                    required
                    variant="outlined"
                    bg-color="transparent"
                    class="glass-input mb-lg"
                    :rules="[
                      v => !!v || 'Please confirm the password',
                      v => v === createUserDialog.form.password || 'Passwords do not match'
                    ]"
                  ></v-text-field>
                </div>

                <div class="form-group mb-4">
                  <v-switch
                    v-model="createUserDialog.form.isAdmin"
                    color="error"
                    hide-details
                  >
                    <template v-slot:label>
                      <span class="terminal-text">Grant Admin Privileges</span>
                    </template>
                  </v-switch>
                </div>

                <div class="d-flex justify-end">
                  <v-btn
                    color="grey-darken-1"
                    variant="text"
                    class="mr-2 btn-cyber mobile-btn"
                    @click="createUserDialog.show = false"
                  >
                    Cancel
                  </v-btn>
                  <v-btn
                    color="primary"
                    class="btn-cyber mobile-btn"
                    @click="validateCreateUserStep1"
                    :disabled="createUserDialog.loading"
                  >
                    <v-icon end>mdi-arrow-right</v-icon>
                    Continue
                  </v-btn>
                </div>
              </div>

              <div v-if="createUserDialog.step === '2'" class="mt-4">
                <div class="text-center mb-4">
                  <p class="text-body-2 text-medium-emphasis terminal-text">
                    Add a profile photo (optional)
                  </p>
                </div>

                <ProfilePhotoUploader
                  :initial-photo-data="createUserDialog.form.photoData"
                  @update:photo="handleCreateUserPhotoUpdate"
                  class="mb-6"
                  ref="createUserPhotoUploader"
                />

                <div class="d-flex justify-end">
                  <v-btn
                    color="grey-darken-1"
                    variant="text"
                    class="mr-2 btn-cyber mobile-btn"
                    @click="createUserDialog.step = '1'"
                    :disabled="createUserDialog.loading"
                  >
                    <v-icon start>mdi-arrow-left</v-icon>
                    Back
                  </v-btn>
                  <v-btn
                    color="success"
                    type="submit"
                    class="btn-cyber mobile-btn"
                    :loading="createUserDialog.loading"
                  >
                    <v-icon start>mdi-account-plus</v-icon>
                    {{ createUserDialog.form.photo ? 'Create with Photo' : 'Create User' }}
                  </v-btn>
                </div>
              </div>
            </v-form>
          </v-stepper>
        </div>
      </div>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import axios from 'axios'
import ProfilePhotoUploader from '@/components/ProfilePhotoUploader.vue'

const authStore = useAuthStore()

// Data
const users = ref([])
const usersLoading = ref(false)
const userSearch = ref('')
const registrationEnabled = ref(true)
const toggleRegistrationLoading = ref(false)

// Status alert
const statusAlert = reactive({
  show: false,
  message: '',
  color: 'success'
})

// Dialogs
const deleteUserDialog = reactive({
  show: false,
  loading: false,
  user: null
})

const logoutUserDialog = reactive({
  show: false,
  loading: false,
  user: null
})

// Create User Dialog
const createUserDialog = reactive({
  show: false,
  loading: false,
  step: '1',
  showPassword: false,
  passwordStrength: {
    value: 0,
    text: '',
    color: '',
    colorClass: ''
  },
  form: {
    username: '',
    password: '',
    confirmPassword: '',
    isAdmin: false,
    photo: null,
    photoData: null
  }
})

// Form refs
const createUserForm = ref(null)
const createUserPhotoUploader = ref(null)

// Fetch data
onMounted(async () => {
  // Wait a moment for authentication to fully establish
  setTimeout(async () => {
    try {
      // Verify admin status directly
      try {
        const adminCheck = await axios.get('/api/users/check-admin')
        if (!adminCheck.data.is_admin) {
          showStatusAlert('You do not have admin privileges', 'error')
        } else {
          // If admin check worked but fetchUser might not have, update the user data immediately
          authStore.user = adminCheck.data.user
          // Now try to fetch users
          await fetchUsers()
          // Fetch registration status
          await fetchRegistrationStatus()
        }
      } catch (adminErr) {
        showStatusAlert('Failed to verify admin status', 'error')
      }
    } catch (error) {
      showStatusAlert('Error initializing admin view', 'error')
    }
  }, 500); // Give auth cookies time to be fully processed
})

async function fetchUsers() {
  usersLoading.value = true
  try {
    const response = await axios.get('/api/users/')
    // Add locked status to each user (we'll implement this in the backend later)
    users.value = (response.data.users || []).map(user => ({
      ...user,
      locked: user.locked || false
    }))
  } catch (error) {
    showStatusAlert('Failed to fetch users', 'error')
  } finally {
    usersLoading.value = false
  }
}

async function fetchRegistrationStatus() {
  try {
    const response = await axios.get('/api/auth/registration-status')
    registrationEnabled.value = response.data.enabled
  } catch (error) {
    // Default to enabled if there's an error
    registrationEnabled.value = true
  }
}

// Users filtering
const filteredUsers = computed(() => {
  if (!userSearch.value) return users.value

  const search = userSearch.value.toLowerCase()
  return users.value.filter(user =>
    user.username.toLowerCase().includes(search) ||
    user.role.toLowerCase().includes(search) ||
    user.id.toString().includes(search)
  )
})

// System statistics
const adminCount = computed(() => {
  return users.value.filter(user => user.role === 'admin').length
})

// Actions
async function toggleRegistration() {
  toggleRegistrationLoading.value = true
  try {
    const response = await axios.post('/api/auth/toggle-registration', {
      enabled: registrationEnabled.value
    })
    showStatusAlert(
      `User registration ${registrationEnabled.value ? 'enabled' : 'disabled'}`,
      'success'
    )
  } catch (error) {
    showStatusAlert('Failed to update registration settings', 'error')
    // Revert the toggle on error
    registrationEnabled.value = !registrationEnabled.value
  } finally {
    toggleRegistrationLoading.value = false
  }
}

async function toggleAdminRole(user) {
  if (user.id === authStore.userId) {
    showStatusAlert('Cannot change your own admin role', 'warning')
    return
  }

  const newRole = user.role === 'admin' ? 'user' : 'admin'
  const actionText = newRole === 'admin' ? 'granted to' : 'removed from'

  try {
    // Make API call to update user role
    await axios.put(`/api/users/${user.id}`, {
      role: newRole
    })

    // Update local state
    const index = users.value.findIndex(u => u.id === user.id)
    if (index !== -1) {
      users.value[index].role = newRole
    }

    showStatusAlert(`Admin role ${actionText} ${user.username}`, 'success')
  } catch (error) {
    showStatusAlert(`Failed to update role for ${user.username}`, 'error')
  }
}

async function toggleUserLock(user) {
  if (user.id === authStore.userId) {
    showStatusAlert('Cannot lock your own account', 'warning')
    return
  }

  const newLockedStatus = !user.locked
  const actionText = newLockedStatus ? 'locked' : 'unlocked'

  try {
    // Placeholder - will implement actual API endpoint
    // await axios.put(`/api/users/${user.id}/lock`, {
    //   locked: newLockedStatus
    // })

    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 500))

    // Update local state
    const index = users.value.findIndex(u => u.id === user.id)
    if (index !== -1) {
      users.value[index].locked = newLockedStatus
    }

    showStatusAlert(`User ${user.username} has been ${actionText}`, 'success')
  } catch (error) {
    showStatusAlert(`Failed to ${actionText} ${user.username}`, 'error')
  }
}

function forceUserLogout(user) {
  if (user.id === authStore.userId) {
    showStatusAlert('Cannot force logout on yourself', 'warning')
    return
  }

  logoutUserDialog.user = user
  logoutUserDialog.show = true
}

async function confirmForceLogout() {
  logoutUserDialog.loading = true

  try {
    // Placeholder - will implement actual API endpoint
    // await axios.post(`/api/users/${logoutUserDialog.user.id}/force-logout`)

    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 500))

    showStatusAlert(`${logoutUserDialog.user.username} has been logged out from all sessions`, 'success')
    logoutUserDialog.show = false
  } catch (error) {
    showStatusAlert(`Failed to force logout for ${logoutUserDialog.user.username}`, 'error')
  } finally {
    logoutUserDialog.loading = false
  }
}

function confirmDeleteUser(user) {
  if (user.id === authStore.userId) {
    showStatusAlert('Cannot delete your own account', 'warning')
    return
  }

  deleteUserDialog.user = user
  deleteUserDialog.show = true
}

async function deleteUser() {
  deleteUserDialog.loading = true

  try {
    // Make API call to delete user
    await axios.delete(`/api/users/${deleteUserDialog.user.id}`)

    // Update local users list
    users.value = users.value.filter(u => u.id !== deleteUserDialog.user.id)

    showStatusAlert(`User ${deleteUserDialog.user.username} has been deleted`, 'success')
    deleteUserDialog.show = false
  } catch (error) {
    showStatusAlert(`Failed to delete ${deleteUserDialog.user.username}`, 'error')
  } finally {
    deleteUserDialog.loading = false
  }
}

function showStatusAlert(message, color = 'success') {
  statusAlert.message = message
  statusAlert.color = color
  statusAlert.show = true
}

// Create User Dialog
function openCreateUserDialog() {
  // Reset the form
  createUserDialog.step = '1'
  createUserDialog.form = {
    username: '',
    password: '',
    confirmPassword: '',
    isAdmin: false,
    photo: null,
    photoData: null
  }
  createUserDialog.passwordStrength = {
    value: 0,
    text: '',
    color: '',
    colorClass: ''
  }
  createUserDialog.showPassword = false
  createUserDialog.show = true
}

async function validateCreateUserStep1() {
  if (!createUserForm.value) return

  const { valid } = await createUserForm.value.validate()
  if (valid) {
    createUserDialog.step = '2'
  }
}

function updateCreatePasswordStrength() {
  const password = createUserDialog.form.password

  if (!password) {
    createUserDialog.passwordStrength = {
      value: 0,
      text: '',
      color: '',
      colorClass: ''
    }
    return
  }

  // Calculate password strength based on various factors
  let strength = 0

  // Length
  if (password.length >= 12) {
    strength += 25
  } else if (password.length >= 8) {
    strength += 15
  } else {
    strength += 5
  }

  // Complexity - characters
  if (/[A-Z]/.test(password)) strength += 15 // Uppercase
  if (/[a-z]/.test(password)) strength += 10 // Lowercase
  if (/[0-9]/.test(password)) strength += 15 // Numbers
  if (/[^A-Za-z0-9]/.test(password)) strength += 20 // Special characters

  // Complexity - patterns
  if (/(.)\1\1/.test(password)) strength -= 10 // Repeating characters (3+)
  if (/^[A-Za-z]+$/.test(password) || /^[0-9]+$/.test(password)) strength -= 5 // Only letters or only numbers

  // Sequential characters check
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

  // Ensure the percentage is between 0 and 100
  strength = Math.max(0, Math.min(100, strength))

  // Set text and color based on strength
  let text, color, colorClass

  if (strength >= 80) {
    text = 'Strong'
    color = '#00ff9c' // Green
    colorClass = 'text-success'
  } else if (strength >= 50) {
    text = 'Medium'
    color = '#eacc13' // Yellow
    colorClass = 'text-warning'
  } else {
    text = 'Weak'
    color = '#ff5252' // Red
    colorClass = 'text-error'
  }

  createUserDialog.passwordStrength = {
    value: strength,
    text,
    color,
    colorClass
  }
}

function handleCreateUserPhotoUpdate(photo) {
  createUserDialog.form.photo = photo
}

async function handleCreateUser() {
  if (!createUserForm.value) return

  const { valid } = await createUserForm.value.validate()
  if (!valid) return

  createUserDialog.loading = true

  try {
    // Prepare user data
    const userData = {
      username: createUserDialog.form.username,
      password: createUserDialog.form.password,
      role: createUserDialog.form.isAdmin ? 'admin' : 'user'
    }

    // Register the user
    const response = await axios.post('/api/auth/register', userData)

    if (response.data && response.data.user) {
      // If we have a profile photo, upload it for the new user
      if (createUserDialog.form.photo) {
        const formData = new FormData()
        formData.append('photo', createUserDialog.form.photo)

        await axios.post('/api/users/profile-photo', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
            'Authorization': `Bearer ${authStore.token}`
          }
        })
      }

      // Add user to the list
      const newUser = {
        ...response.data.user,
        locked: false // Default to unlocked
      }
      users.value.push(newUser)

      // Show success message
      showStatusAlert(`User ${newUser.username} created successfully`, 'success')

      // Close the dialog
      createUserDialog.show = false
    }
  } catch (error) {
    showStatusAlert(error.response?.data?.msg || 'Failed to create user', 'error')
  } finally {
    createUserDialog.loading = false
  }
}
</script>

<style scoped>
.admin-view {
  min-height: 100vh;
  position: relative;
  padding-top: 1rem;
  z-index: 1;
  background-color: transparent;
  background-image: none;
}

.back-button-container {
  padding: 16px;
}

.container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 16px;
  position: relative;
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

/* Title */
.title-container {
  text-align: center;
}

.cyber-title {
  font-size: 2.5rem;
  font-weight: 700;
  background: linear-gradient(
    90deg,
    rgba(0, 255, 156, 0.9),
    rgba(0, 136, 255, 0.9)
  );
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow: 0 0 20px rgba(0, 255, 156, 0.3);
  position: relative;
  margin-bottom: 1rem;
  text-align: center;
}

.cyber-title::after {
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

.terminal-text {
  font-family: 'Courier New', monospace;
  letter-spacing: 0.5px;
  color: #ffffff;
}

/* Cards */
.card-glass {
  background: rgba(15, 22, 32, 0.7) !important;
  border: 1px solid rgba(0, 255, 156, 0.2) !important;
  backdrop-filter: blur(10px);
  border-radius: 8px;
  box-shadow: 0 4px 24px rgba(0, 255, 156, 0.15);
  overflow: hidden;
  transition: all 0.3s ease;
}

.card-glass:hover {
  border-color: rgba(0, 255, 156, 0.4) !important;
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(0, 255, 156, 0.2);
}

/* Table */
.admin-table {
  background: transparent;
  width: 100%;
  overflow-x: auto;
}

.admin-table th {
  font-family: 'Courier New', monospace;
  text-transform: uppercase;
  letter-spacing: 1px;
  font-weight: bold;
  color: #00ff9c !important;
  background-color: rgba(0, 0, 0, 0.3);
  white-space: nowrap;
  vertical-align: middle;
  text-align: center;
}

.admin-table tr {
  border-bottom: 1px solid rgba(0, 255, 156, 0.1);
}

.admin-table tr:hover {
  background-color: rgba(0, 255, 156, 0.05);
}

.current-user {
  background-color: rgba(0, 255, 156, 0.1);
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
  z-index: 1;
}

.btn-cyber:hover::before {
  left: 100%;
}

/* Special style for outlined buttons like Back to Dashboard */
.btn-cyber-outline {
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

.btn-cyber-outline:hover {
  background-color: rgba(0, 255, 156, 0.1) !important;
  border-color: rgba(0, 255, 156, 0.7) !important;
  box-shadow: 0 0 15px rgba(0, 255, 156, 0.3);
}

.btn-cyber-outline .v-btn__content {
  color: rgba(0, 255, 156, 0.9) !important;
}

/* Dialogs */
.dialog-glass :deep(.v-overlay__content) {
  box-shadow: 0 0 30px rgba(0, 255, 156, 0.3);
  width: 95%;
  max-width: 500px;
  margin: 0 auto;
}

/* Animations */
@keyframes glowPulse {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 0.8; }
}

@keyframes gridMove {
  0% { transform: rotate(45deg) translateY(0); }
  100% { transform: rotate(45deg) translateY(-50%); }
}

/* Responsive Table Design */
@media (max-width: 768px) {
  .admin-table td {
    white-space: nowrap;
  }

  .admin-table .d-flex.align-center {
    flex-wrap: nowrap;
  }
}

/* Mobile-first design with responsive breakpoints */
@media (max-width: 960px) {
  .cyber-title {
    font-size: 2rem;
  }

  .back-button-container {
    padding: 12px;
  }

  .container {
    padding: 0 12px;
  }

  /* Stack header elements on mobile */
  .cyber-card-title {
    flex-direction: column;
    align-items: flex-start;
  }

  /* Responsive card header with search and action buttons */
  .cyber-card-title :deep(.v-spacer) {
    display: none;
  }

  /* Create smaller action buttons on mobile */
  .cyber-card-title .v-btn {
    margin-top: 8px;
    margin-bottom: 8px;
  }

  /* Make search box full width on mobile */
  .cyber-card-title .search-field {
    width: 100%;
    max-width: 100%;
    margin-top: 8px;
  }
}

@media (max-width: 600px) {
  .cyber-title {
    font-size: 1.75rem;
  }

  /* Smaller padding for mobile */
  .back-button-container,
  .container {
    padding: 8px;
  }

  /* Optimize dialogs for mobile */
  .dialog-glass :deep(.v-overlay__content) {
    width: 92%;
  }

  /* Stack buttons in create user dialog on mobile */
  .d-flex.justify-end {
    flex-direction: column-reverse;
  }

  .d-flex.justify-end .v-btn {
    margin: 4px 0;
    width: 100%;
  }

  /* Hide avatar for very small screens in user table */
  .admin-table .v-avatar {
    display: none;
  }
}

/* Icon Buttons */
.btn-cyber-icon {
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
  border-radius: 4px;
}

.btn-cyber-icon::after {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at center, rgba(255, 255, 255, 0.2), transparent 70%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.btn-cyber-icon:hover::after {
  opacity: 1;
}

.search-field {
  border-color: rgba(0, 255, 156, 0.3);
}

/* Card Title */
.cyber-card-title {
  font-family: 'Courier New', monospace;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  font-weight: bold;
  color: rgba(0, 255, 156, 0.9) !important;
  text-shadow: 0 0 10px rgba(0, 255, 156, 0.3);
  padding: 16px;
  border-bottom: 1px solid rgba(0, 255, 156, 0.2);
  background-color: rgba(0, 0, 0, 0.2);
  display: flex;
  flex-wrap: wrap;
  align-items: center;
}

.card-header {
  padding: 16px 20px;
  background-color: rgba(0, 0, 0, 0.4);
  border-bottom: 1px solid rgba(0, 255, 156, 0.2);
}

.cyber-card-header {
  padding: 16px 20px;
  background-color: rgba(0, 0, 0, 0.4);
  border-bottom: 1px solid rgba(0, 255, 156, 0.2);
  position: relative;
  overflow: hidden;
}

.cyber-card-header::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(0, 255, 156, 0.7),
    rgba(0, 136, 255, 0.7),
    transparent
  );
}

.cyber-dialog-title {
  font-size: 1.5rem;
  margin: 0;
  font-family: 'Courier New', monospace;
  background: linear-gradient(
    90deg,
    rgba(0, 255, 156, 0.9),
    rgba(0, 136, 255, 0.9)
  );
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow: 0 0 10px rgba(0, 255, 156, 0.3);
}

/* Responsive form controls */
.glass-input {
  width: 100%;
}

.password-strength-container {
  width: 100%;
}

.strength-meter {
  width: 100%;
  height: 4px;
  background-color: rgba(0, 0, 0, 0.2);
  border-radius: 2px;
  overflow: hidden;
}

.strength-meter-fill {
  height: 100%;
  transition: width 0.3s ease, background-color 0.3s ease;
}

/* Mobile-first layout adjustments */
.mb-md {
  margin-bottom: 16px;
}

.mb-lg {
  margin-bottom: 24px;
}

.mobile-btn {
  min-width: 100px;
}

@media (max-width: 600px) {
  .mobile-btn {
    width: 100%;
    margin-left: 0 !important;
    margin-right: 0 !important;
    margin-bottom: 8px;
  }
}

/* Making the user management card and table more responsive */
.responsive-table-wrapper {
  width: 100%;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

:deep(.v-table__wrapper) {
  overflow-x: auto;
}

.action-buttons {
  display: flex;
  flex-wrap: nowrap;
  justify-content: center;
}

.mobile-action-btn {
  margin: 0 2px;
}

@media (max-width: 480px) {
  /* Adjust table for very small screens */
  .admin-table td,
  .admin-table th {
    padding: 8px 4px;
    font-size: 0.8rem;
  }

  .mobile-action-btn {
    height: 36px !important;
    width: 36px !important;
    margin: 0 1px;
  }

  .action-buttons {
    flex-wrap: wrap;
  }
}

.admin-table td {
  vertical-align: middle;
  padding: 12px 8px;
}
</style>