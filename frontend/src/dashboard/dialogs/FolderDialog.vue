<template>
  <v-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    max-width="600px"
    :fullscreen="isMobile"
    :scrim="true"
    :content-class="isMobile ? 'mobile-dialog' : ''"
  >
    <v-card class="dialog-card">
      <v-toolbar v-if="isMobile" density="compact" color="#0F1620" class="mobile-toolbar">
        <v-btn icon variant="text" @click="cancel">
          <v-icon>mdi-close</v-icon>
        </v-btn>
        <v-toolbar-title>{{ isEdit ? 'Edit Folder' : 'Create New Folder' }}</v-toolbar-title>
        <v-spacer></v-spacer>
        <v-btn color="primary" @click="save" :loading="loading" variant="text">
          Save
        </v-btn>
      </v-toolbar>

      <v-card-title v-if="!isMobile" class="dialog-title">
        {{ isEdit ? 'Edit Folder' : 'Create New Folder' }}
      </v-card-title>

      <v-card-text :class="{'mobile-content': isMobile}">
        <v-form @submit.prevent="save" ref="form">
          <div class="form-row">
            <v-text-field
              v-model="formData.name"
              label="Folder Name"
              required
              variant="outlined"
              class="form-field"
              :rules="[v => !!v || 'Name is required']"
              bg-color="rgba(15, 22, 32, 0.3)"
            ></v-text-field>
          </div>

          <div class="form-row">
            <v-textarea
              v-model="formData.description"
              label="Description (Optional)"
              variant="outlined"
              class="form-field"
              :auto-grow="true"
              rows="3"
              bg-color="rgba(15, 22, 32, 0.3)"
            ></v-textarea>
          </div>

          <div class="form-row folder-type-row">
            <div class="folder-type-toggle">
              <div class="toggle-label">Private or Shared</div>
              <v-switch
                v-model="isSharedFolder"
                color="success"
                :label="`${isSharedFolder ? 'Shared' : 'Private'} Folder`"
                hide-details
                inset
              >
                <template v-slot:prepend>
                  <v-icon :color="isSharedFolder ? 'success' : 'primary'">
                    {{ isSharedFolder ? 'mdi-folder-multiple' : 'mdi-folder-lock' }}
                  </v-icon>
                </template>
              </v-switch>
            </div>

            <div class="folder-type-hint" v-if="true">
              <div class="hint-content" :class="isSharedFolder ? 'shared-hint' : 'private-hint'">
                <v-icon size="small" :color="isSharedFolder ? 'success' : 'primary'" class="mr-2">
                  mdi-information-outline
                </v-icon>
                <span class="hint-text">
                  {{ isSharedFolder ? 'Secrets in a shared folder will inherit permissions' : 'Private folder for personal organization' }}
                </span>
              </div>
            </div>
          </div>

          <div v-if="isSharedFolder" class="sharing-section">
            <div v-if="fetchingUsers" class="text-center py-4">
              <v-progress-circular indeterminate color="info"></v-progress-circular>
              <div class="mt-2">Loading users...</div>
            </div>

            <div v-else-if="sharingError" class="error-message">
              {{ sharingError }}
            </div>

            <div v-else-if="availableUsers.length === 0" class="text-center py-4">
              <v-icon color="warning" size="large" class="mb-2">mdi-account-off</v-icon>
              <div>No other users available to share with.</div>
              <div class="text-caption">You need to create additional user accounts first.</div>
            </div>

            <template v-else>
              <v-select
                v-model="sharedUsers"
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

              <v-select
                v-model="sharePermissions"
                label="Permissions"
                :items="permissionOptions"
                required
                variant="outlined"
                class="form-field"
                :rules="[v => !!v || 'Permissions are required']"
              ></v-select>
            </template>
          </div>

          <v-combobox
            v-model="formData.tags"
            label="Tags (Optional)"
            variant="outlined"
            class="form-field"
            multiple
            chips
            small-chips
            :items="suggestedTags"
          ></v-combobox>

          <v-btn
            v-if="isMobile && isEdit"
            color="error"
            variant="outlined"
            block
            class="mt-4 mb-4"
            prepend-icon="mdi-delete"
            @click="confirmDelete"
          >
            Delete This Folder
          </v-btn>
        </v-form>
      </v-card-text>

      <v-card-actions v-if="!isMobile" class="dialog-actions">
        <v-menu v-if="isEdit" offset-y>
          <template v-slot:activator="{ props }">
            <v-btn
              color="error"
              variant="text"
              v-bind="props"
              class="delete-menu-btn"
            >
              Delete
              <v-icon end>mdi-chevron-down</v-icon>
            </v-btn>
          </template>
          <v-list class="delete-menu">
            <v-list-item @click="confirmDelete">
              <template v-slot:prepend>
                <v-icon color="error">mdi-delete</v-icon>
              </template>
              <v-list-item-title class="delete-confirmation">
                Confirm Deletion
              </v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>

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
          @click="save"
          :loading="loading"
          class="save-btn"
        >
          Save
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, reactive, watch, onMounted, onBeforeUnmount } from 'vue'
import { useAuthStore } from '@/stores/auth'
import axios from 'axios'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  isEdit: {
    type: Boolean,
    default: false
  },
  folder: {
    type: Object,
    default: () => ({
      id: null,
      name: '',
      description: '',
      tags: [],
      folder_type: 'regular'
    })
  },
  suggestedTags: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'save', 'delete', 'share'])
const authStore = useAuthStore()

// Track if we're on mobile
const isMobile = ref(false)

// Folder sharing state - replaces folder_type selection
const isSharedFolder = ref(false)

// Available folder types
const folderTypes = [
  { text: 'Private Folder', value: 'regular', icon: 'mdi-folder-lock' },
  { text: 'Shared Folder', value: 'shared', icon: 'mdi-folder-multiple' }
]

// User sharing data
const sharedUsers = ref([])
const sharePermissions = ref('read')
const availableUsers = ref([])
const fetchingUsers = ref(false)
const sharingError = ref(null)

// Permission options for sharing
const permissionOptions = [
  { title: 'Read Only', value: 'read' },
  { title: 'Read & Write', value: 'write' },
  { title: 'Full Access', value: 'full' }
]

// Check for mobile screen size
function checkMobile() {
  isMobile.value = window.innerWidth < 768
}

// Setup mobile detection
onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', checkMobile)
})

const form = ref(null)

// Form data
const formData = reactive({...props.folder})

// Reset form data when dialog closes
watch(() => props.modelValue, (visible) => {
  if (visible) {
    if (props.isEdit) {
      // For editing, load the folder data
      Object.assign(formData, {
        ...props.folder
      });

      // Set isSharedFolder based on folder_type
      isSharedFolder.value = props.folder.folder_type === 'shared';
    } else {
      // For new folders, reset to defaults
      Object.assign(formData, {
        id: null,
        name: '',
        description: '',
        tags: [],
        folder_type: 'regular'
      });

      // Default to private folder
      isSharedFolder.value = false;
    }

    // Reset sharing data for new folders
    if (!props.isEdit) {
      sharedUsers.value = []
      sharePermissions.value = 'read'
    }

    // If it's a shared folder, fetch available users
    if (isSharedFolder.value) {
      fetchUsers()
    }
  }
})

// Watch for folder type changes to fetch users when shared is selected
watch(() => isSharedFolder.value, (isShared) => {
  if (isShared) {
    fetchUsers()
  }
})

// Watch for dialog visibility to fetch users if needed
watch(() => props.modelValue, (visible) => {
  if (visible && isSharedFolder.value) {
    fetchUsers()
  }
})

// Functions
async function save() {
  const { valid } = await form.value.validate()

  if (!valid) return

  // Create a clean copy of the folder data without the sharing info
  const folderData = {
    ...formData,
    folder_type: isSharedFolder.value ? 'shared' : 'regular'
  }
  delete folderData.sharedWith

  // Save the folder first - emit save and capture the response
  const saveResponse = await new Promise(resolve => {
    let hasResolved = false;

    // Set a timeout as a safeguard
    const timeoutId = setTimeout(() => {
      if (!hasResolved) {
        hasResolved = true;
        resolve(formData.id); // Fallback to the current ID if we have one
      }
    }, 2000);

    // Emit save and listen for callback
    emit('save', folderData, (savedFolderId) => {
      clearTimeout(timeoutId);
      if (!hasResolved) {
        hasResolved = true;
        resolve(savedFolderId);
      }
    });
  })

  // If it's a shared folder with users selected, emit additional share events
  // The parent component will handle these after the folder is created
  if (isSharedFolder.value && sharedUsers.value.length > 0) {
    const sharingInfo = {
      folderId: saveResponse, // Include the newly created folder ID
      users: sharedUsers.value.map(user => ({
        userId: typeof user === 'object' ? user.id : user,
        userName: typeof user === 'object' ? user.username : availableUsers.value.find(u => u.id === user)?.username,
      })),
      permissions: sharePermissions.value
    }

    // Emit a separate event for sharing the folder
    emit('share', sharingInfo)
  }
}

function cancel() {
  emit('update:modelValue', false)

  // Reset the form data when canceling
  if (!props.isEdit) {
    // Reset to defaults with empty folder_type for new folders
    Object.assign(formData, {
      id: null,
      name: '',
      description: '',
      tags: [],
      folder_type: null
    })

    // Reset sharing data
    sharedUsers.value = []
    sharePermissions.value = 'read'
  }
}

function confirmDelete() {
  // Only allow deletion if in edit mode and we have an ID
  if (props.isEdit && formData.id) {
    emit('delete')
    emit('update:modelValue', false)
  }
}

// Fetch users from the API
async function fetchUsers() {
  fetchingUsers.value = true
  sharingError.value = null
  availableUsers.value = []

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
    sharingError.value = 'Failed to load users. Please try again later.'

    // If access is denied due to permissions, show specific message
    if (err.response?.status === 403) {
      sharingError.value = 'You do not have permission to view other users.'
    }
  } finally {
    fetchingUsers.value = false
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

function getUserAvatar(user) {
  if (!user || !user.profile_photo_url) {
    return null
  }

  if (user.profile_photo_url.startsWith('http')) {
    return user.profile_photo_url
  }

  return `${window.location.origin}${user.profile_photo_url}`
}
</script>

<style scoped>
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

.form-row {
  margin-bottom: 20px;
  max-width: 500px;
  margin-left: auto;
  margin-right: auto;
}

.folder-type-row {
  display: flex;
  flex-direction: column;
}

.folder-type-toggle {
  display: flex;
  flex-direction: column;
  padding: 12px 16px;
  background: rgba(15, 22, 32, 0.3);
  border-radius: 8px;
  border: 1px solid rgba(0, 255, 156, 0.1);
}

.toggle-label {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 8px;
  font-weight: 500;
}

.folder-type-hint {
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

.private-hint {
  background-color: rgba(0, 176, 255, 0.1);
  border-left: 3px solid rgba(0, 176, 255, 0.4);
  color: rgba(255, 255, 255, 0.9);
}

.shared-hint {
  background-color: rgba(76, 175, 80, 0.1);
  border-left: 3px solid rgba(76, 175, 80, 0.4);
  color: rgba(255, 255, 255, 0.9);
}

.mobile-toolbar {
  background: linear-gradient(to right, rgba(15, 22, 32, 1), rgba(25, 35, 48, 1)) !important;
  border-bottom: 1px solid rgba(0, 255, 156, 0.2);
}

.mobile-content {
  padding-top: 16px;
}

.dialog-actions {
  border-top: 1px solid rgba(0, 255, 156, 0.1);
  padding: 16px 24px !important;
  background: rgba(15, 22, 32, 0.5);
}

.save-btn {
  min-width: 120px;
  background: linear-gradient(to right, rgba(0, 255, 156, 0.8), rgba(0, 200, 156, 0.8)) !important;
  box-shadow: 0 4px 12px rgba(0, 255, 156, 0.3) !important;
  text-transform: uppercase;
  letter-spacing: 1px;
  font-weight: 700;
  color: rgba(0, 55, 36, 1) !important;
}

.save-btn:hover {
  background: linear-gradient(to right, rgba(0, 255, 156, 0.9), rgba(0, 200, 156, 0.9)) !important;
  box-shadow: 0 4px 15px rgba(0, 255, 156, 0.4) !important;
  color: rgba(0, 35, 23, 1) !important;
}

.cancel-btn {
  color: rgba(255, 255, 255, 0.7);
  margin-right: 12px;
}

/* Mobile responsiveness */
@media (max-width: 600px) {
  .form-row {
    max-width: 100%;
  }

  .folder-type-hint {
    padding-left: 0;
  }
}

/* Dialog styling */
.form-field {
  margin-bottom: 16px;
  background: transparent !important;
}

.form-field:focus-within {
  background: transparent !important;
}

/* Sharing section styles */
.sharing-section {
  background: rgba(0, 255, 156, 0.05);
  border: 1px solid rgba(0, 255, 156, 0.1);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
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

.delete-menu-btn {
  margin-right: auto;
  color: #ff5252;
}

.delete-menu {
  background: #0F1620 !important;
  border: 1px solid rgba(255, 82, 82, 0.3) !important;
  box-shadow: 0 0 15px rgba(255, 82, 82, 0.3) !important;
  border-radius: 4px !important;
}

.delete-confirmation {
  color: #ff5252;
  font-weight: 500;
}

/* Mobile styles */
.mobile-dialog {
  margin: 0 !important;
  height: 100% !important;
  overflow: hidden !important;
}

.mobile-toolbar :deep(.v-toolbar-title) {
  font-size: 1.1rem !important;
  font-weight: 600 !important;
  color: #fff !important;
  text-align: center !important;
}

.mobile-content {
  padding-top: 8px !important;
  padding-bottom: 16px !important;
  height: calc(100vh - 56px) !important;
  overflow-y: auto !important;
  -webkit-overflow-scrolling: touch !important;
}

/* Ensure dialog fits well on mobile */
@media (max-width: 767px) {
  :deep(.v-dialog) {
    margin: 0 !important;
    position: fixed !important;
    top: 0 !important;
    left: 0 !important;
    width: 100% !important;
    height: 100% !important;
    max-height: 100% !important;
    border-radius: 0 !important;
    overflow: hidden !important;
  }

  :deep(.v-dialog--fullscreen) {
    width: 100% !important;
    height: 100% !important;
  }

  :deep(.v-card) {
    border-radius: 0 !important;
    height: 100% !important;
    max-height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
  }

  :deep(.v-card-text) {
    flex: 1 !important;
    overflow-y: auto !important;
  }

  .form-field {
    margin-bottom: 20px;
  }

  /* Add some bottom padding to ensure form fields don't get hidden by mobile keyboards */
  .mobile-content form {
    padding-bottom: 32px !important;
  }
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