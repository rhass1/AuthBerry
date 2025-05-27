<template>
  <v-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" max-width="600px">
    <v-card class="dialog-card">
      <v-card-title class="dialog-title">
        <v-icon color="info" class="mr-2">mdi-share-variant</v-icon>
        Share {{ itemType === 'folder' ? 'Folder' : 'Secret' }}
      </v-card-title>

      <v-card-text class="dialog-content">
        <div v-if="loading" class="text-center py-4">
          <v-progress-circular indeterminate color="info"></v-progress-circular>
          <div class="mt-2">Loading users...</div>
        </div>

        <div v-else-if="error" class="error-message">
          {{ error }}
        </div>

        <div v-else-if="availableUsers.length === 0" class="text-center py-4">
          <v-icon color="warning" size="large" class="mb-2">mdi-account-off</v-icon>
          <div>No other users available to share with.</div>
          <div class="text-caption">You need to create additional user accounts first.</div>
        </div>

        <v-form v-else ref="form" class="sharing-section">
          <div class="form-row">
            <v-select
              v-model="selectedUsers"
              label="Select Users"
              :items="availableUsers"
              item-title="username"
              item-value="id"
              multiple
              chips
              variant="outlined"
              class="form-field"
              :rules="[v => v.length > 0 || 'At least one user must be selected']"
              return-object
              bg-color="rgba(15, 22, 32, 0.3)"
            >
              <template v-slot:chip="{ props, item }">
                <v-chip
                  v-bind="props"
                  :prepend-avatar="getUserAvatar(item.raw)"
                  :text="getDisplayName(item.raw)"
                  class="user-chip"
                ></v-chip>
              </template>

              <template v-slot:item="{ item, props }">
                <v-list-item
                  v-bind="props"
                  :prepend-avatar="getUserAvatar(item.raw)"
                  :title="getDisplayName(item.raw)"
                  :subtitle="item.raw.username"
                  class="user-list-item"
                ></v-list-item>
              </template>
            </v-select>
          </div>

          <div class="form-row">
            <v-select
              v-model="permissions"
              label="Permissions"
              :items="permissionOptions"
              required
              variant="outlined"
              class="form-field"
              :rules="[v => !!v || 'Permissions are required']"
              bg-color="rgba(15, 22, 32, 0.3)"
            ></v-select>
          </div>

          <div class="permissions-hint">
            <div class="hint-content info-hint">
              <v-icon size="small" color="info" class="mr-2">
                mdi-information-outline
              </v-icon>
              <span class="hint-text">
                {{
                  permissions === 'read' ? 'Users will be able to view but not modify the shared content' :
                  permissions === 'write' ? 'Users will be able to view and modify the shared content' :
                  'Users will have full control over the shared content'
                }}
              </span>
            </div>
          </div>
        </v-form>
      </v-card-text>

      <v-card-actions class="dialog-actions">
        <v-spacer></v-spacer>
        <v-btn
          variant="text"
          @click="cancel"
          class="cancel-btn"
        >
          Cancel
        </v-btn>
        <v-btn
          color="primary"
          @click="share"
          :disabled="availableUsers.length === 0 || loading"
          :loading="submitting"
          class="share-btn"
        >
          Share
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import axios from 'axios'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  itemType: {
    type: String,
    required: true,
    validator: value => ['secret', 'folder'].includes(value)
  },
  loading: {
    type: Boolean,
    default: false // This prop seems unused locally as there's a local 'loading' ref
  }
})

const emit = defineEmits(['update:modelValue', 'share'])
const authStore = useAuthStore()

const form = ref(null)
const selectedUsers = ref([])
const permissions = ref('read')
const availableUsers = ref([])
const loading = ref(false) // Local loading state for fetching users
const submitting = ref(false)
const error = ref(null)

// Permission options for sharing
const permissionOptions = [
  { title: 'Read Only', value: 'read' },
  { title: 'Read & Write', value: 'write' },
  { title: 'Full Access', value: 'full' }
]

// Load list of users to share with when the component is mounted
onMounted(async () => {
  if (props.modelValue) {
    await fetchUsers()
  }
})

// Also fetch users when dialog becomes visible
watch(() => props.modelValue, async (newValue) => {
  if (newValue) {
    await fetchUsers()
  }
}, { immediate: true })

// Fetch users from the API
async function fetchUsers() {
  loading.value = true
  error.value = null
  availableUsers.value = []
  selectedUsers.value = []

  try {
    // Get all users from the API
    const response = await axios.get('/api/users/')

    if (!response.data || !response.data.users) {
      throw new Error('Invalid response format from server')
    }

    // Filter out the current user
    const currentUserId = authStore.userId
    availableUsers.value = response.data.users.filter(user =>
      user.id !== currentUserId
    )

  } catch (err) {
    error.value = 'Failed to load users. Please try again later.'

    // If access is denied due to permissions, show specific message
    if (err.response?.status === 403) {
      error.value = 'You do not have permission to view other users.'
    }
  } finally {
    loading.value = false
  }
}

// Get the display name for a user (first name + last name, or username)
function getDisplayName(user) {
  if (user.first_name && user.last_name) {
    return `${user.first_name} ${user.last_name}`
  } else if (user.display_name) {
    return user.display_name
  }
  return user.username
}

async function share() {
  if (availableUsers.value.length === 0) return

  if (form.value) {
    const { valid } = await form.value.validate()
    if (!valid) return
  }

  submitting.value = true

  try {
    // Share with each selected user
    for (const user of selectedUsers.value) {
      // Handle user being either an object (with return-object) or just an ID
      const userId = typeof user === 'object' ? user.id : user;
      const username = typeof user === 'object' ? user.username : availableUsers.value.find(u => u.id === user)?.username;

      if (userId) {
        emit('share', {
          userId,
          userName: username,
          permissions: permissions.value
        })
      }
    }

    // Reset form after submitting
    selectedUsers.value = []
    permissions.value = 'read'
    emit('update:modelValue', false) // Close dialog after sharing
  } catch (err) {
    error.value = 'Failed to share. Please try again later.'
  } finally {
    submitting.value = false
  }
}

function cancel() {
  emit('update:modelValue', false)

  // Reset form when canceling
  selectedUsers.value = []
  permissions.value = 'read'
  error.value = null
}

function getUserAvatar(user) {
  // Return default avatar if no user or no profile photo
  if (!user || !user.profile_photo) {
    return null;
  }

  // If it's already a data URL, return it
  if (user.profile_photo.startsWith('data:image/')) {
    return user.profile_photo;
  }

  // Otherwise, add data:image prefix
  return `data:image/jpeg;base64,${user.profile_photo}`;
}
</script>

<style scoped>
/* Dialog styling */
.dialog-card {
  background: linear-gradient(to bottom right, rgba(15, 22, 32, 0.95), rgba(25, 35, 48, 0.95)) !important;
  border: 1px solid rgba(0, 255, 156, 0.2) !important;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3) !important;
  overflow: hidden;
}

.dialog-title {
  background: linear-gradient(to right, rgba(0, 255, 156, 0.1), transparent);
  color: rgba(255, 255, 255, 0.9);
  font-weight: 600;
  font-size: 1.5rem !important;
  letter-spacing: 0.5px;
  border-bottom: 1px solid rgba(0, 255, 156, 0.1);
  padding: 16px 24px !important;
}

.dialog-content {
  padding: 20px 24px;
}

.form-row {
  margin-bottom: 20px;
  max-width: 500px;
  margin-left: auto;
  margin-right: auto;
}

.form-field {
  margin-bottom: 16px;
  background: transparent !important;
}

.sharing-section {
  background: rgba(0, 255, 156, 0.05);
  border: 1px solid rgba(0, 255, 156, 0.1);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.permissions-hint {
  margin-top: 8px;
  font-size: 0.9rem;
  padding-left: 12px;
}

.hint-content {
  display: flex;
  align-items: flex-start;
  padding: 10px 14px;
  border-radius: 6px;
}

.hint-text {
  line-height: 1.4;
}

.info-hint {
  background-color: rgba(33, 150, 243, 0.1);
  border-left: 3px solid rgba(33, 150, 243, 0.4);
  color: rgba(255, 255, 255, 0.9);
}

.dialog-actions {
  border-top: 1px solid rgba(0, 255, 156, 0.1);
  padding: 16px 24px !important;
  background: rgba(15, 22, 32, 0.5);
}

.share-btn {
  min-width: 120px;
  background: linear-gradient(to right, rgba(0, 255, 156, 0.8), rgba(0, 200, 156, 0.8)) !important;
  box-shadow: 0 4px 12px rgba(0, 255, 156, 0.3) !important;
  text-transform: uppercase;
  letter-spacing: 1px;
  font-weight: 700;
  color: rgba(0, 55, 36, 1) !important;
}

.share-btn:hover {
  background: linear-gradient(to right, rgba(0, 255, 156, 0.9), rgba(0, 200, 156, 0.9)) !important;
  box-shadow: 0 4px 15px rgba(0, 255, 156, 0.4) !important;
  color: rgba(0, 35, 23, 1) !important;
}

.cancel-btn {
  color: rgba(255, 255, 255, 0.7);
  margin-right: 12px;
}

.error-message {
  color: #ff5252;
  background: rgba(255, 82, 82, 0.1);
  padding: 12px;
  border-radius: 4px;
  margin-bottom: 16px;
  text-align: center;
}

.user-chip {
  background: rgba(0, 255, 156, 0.1) !important;
  border: 1px solid rgba(0, 255, 156, 0.2) !important;
}

.user-list-item {
  border-radius: 4px;
  margin: 4px;
}

.user-list-item:hover {
  background: rgba(0, 255, 156, 0.05) !important;
}

/* Make all Vuetify input components completely transparent */
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

.v-field__input {
  background-color: transparent !important;
}

.v-field__outline {
  --v-field-border-opacity: 0.1;
}

.v-text-field {
  background-color: transparent !important;
}

/* Additional overrides */
.v-field {
  background-color: transparent !important;
}

.v-field__overlay {
  background-color: transparent !important;
  opacity: 0 !important;
}

.v-field__field {
  background-color: transparent !important;
}

.v-field--focused {
  background-color: transparent !important;
}

.form-field :deep(.v-field--variant-outlined),
.form-field :deep(.v-field--active),
.form-field :deep(.v-field__overlay) {
  background-color: transparent !important;
}
</style>