<template>
  <DashboardLayout
    @click="handleOutsideClick"
    :hasSelectedItem="!!selectedItemId"
    @mobile-state-changed="handleMobileStateChange"
  >
    <template v-slot:mobile-top>
      <MobileTopBar
        v-model:search="search"
        @create-secret="openCreateSecretDialog"
        @create-folder="openCreateFolderDialog"
        :can-add-to-current-folder="canAddToCurrentFolder"
      />
    </template>

    <template v-slot:left-pane>
      <UserProfile v-if="!isMobile" />

      <SearchBar
        v-if="!isMobile"
        v-model:search="search"
        @create-secret="openCreateSecretDialog"
        @create-folder="openCreateFolderDialog"
      />

      <ItemsList
        ref="itemsListRef"
        :folders="filteredFolders"
        :secrets="filteredSecrets"
        :loading="secretsStore.loading"
        :error="secretsStore.error"
        :selected-item-id="selectedItemId"
        :selected-item-type="selectedItemType"
        :is-admin="authStore.isAdmin"
        :userId="authStore.userId"
        :search-query="search"
        :search-matching-items="matchingItemIds"
        :search-expanded-folders="expandedFolderIds"
        :is-mobile="isMobile"
        @select-secret="selectSecret"
        @select-folder="selectFolder"
        @create-secret="openCreateSecretDialog"
        @create-folder="openCreateFolderDialog"
        @add-secret-to-folder="openCreateSecretInFolderDialog"
        @move-secret="moveSecret"
        @select-all-secrets-folder="selectAllSecretsFolder"
        @remove-from-folder="removeSecretFromFolder"
      />
    </template>

    <template v-slot:right-pane>
      <WelcomePanel
        v-if="!selectedItemId && selectedItemType !== 'all-secrets-folder'"
        :loading="secretsStore.loading"
        :isEmpty="secretsStore.secrets.length === 0 && (!secretsStore.folders || secretsStore.folders.length === 0)"
        :is-mobile="isMobile"
        :is-admin="authStore.isAdmin"
        @create-secret="openCreateSecretDialog"
        @create-folder="openCreateFolderDialog"
      />

      <SecretDetails
        v-else-if="selectedItemType === 'secret' && currentSecret"
        ref="secretDetailsRef"
        :secret="currentSecret"
        :is-mobile="isMobile"
        :is-admin="authStore.isAdmin"
        @edit="editSecret"
        @delete="confirmDeleteSecret"
        @share="openShareDialog"
        @navigate-to-folder="navigateToFolder"
        @back="clearSelection"
      />

      <FolderDetails
        v-else-if="selectedItemType === 'folder' && currentFolder"
        ref="folderDetailsRef"
        :folder="currentFolder"
        :folder-contents="folderContents"
        :is-mobile="isMobile"
        :is-admin="authStore.isAdmin"
        @edit="editFolder"
        @delete="confirmDeleteFolder"
        @share="openShareFolderDialog"
        @add-secret="openCreateSecretInFolderDialog"
        @select-secret="selectSecret"
        @back="clearSelection"
      />
      
      <AllSecretsView
        v-else-if="selectedItemType === 'all-secrets-folder'"
        :secrets="secretsStore.secrets"
        :loading="secretsStore.loading"
        :is-mobile="isMobile"
        :is-admin="authStore.isAdmin"
        @create-secret="openCreateSecretDialog"
        @select-secret="selectSecret"
        @back="clearSelection"
      />
    </template>

    <template v-slot:dialogs>
      <SecretDialog
        v-model="secretDialog.show"
        :is-edit="secretDialog.isEdit"
        :secret="secretDialog.form"
        :in-folder="secretDialog.inFolder"
        :folder-id="secretDialog.form.folder_id"
        :folder-options="folderOptions"
        :suggested-tags="suggestedTags"
        :loading="secretsStore.loading"
        @save="saveSecret"
        @delete="deleteItem('secret', secretDialog.form)"
      />

      <FolderDialog
        v-model="folderDialog.show"
        :is-edit="folderDialog.isEdit"
        :folder="folderDialog.form"
        :suggested-tags="suggestedTags"
        :loading="secretsStore.loading"
        @save="saveFolder"
        @delete="deleteItem('folder', folderDialog.form)"
        @share="handleSharedFolderCreation"
      />

      <DeleteDialog
        v-model="deleteDialog.show"
        :item-type="deleteDialog.itemType"
        :loading="secretsStore.loading"
        @confirm="deleteItem(deleteDialog.itemType, deleteDialog.item)"
      />

      <ShareDialog
        v-model="shareDialog.show"
        :item-type="shareDialog.itemType"
        :loading="secretsStore.loading"
        @share="shareWithUser"
      />
    </template>
  </DashboardLayout>
</template>

<script setup>
import { ref, computed, onMounted, reactive, watch, inject, nextTick } from 'vue'
import { useSecretsStore } from '@/stores/secrets'
import { useNotificationsStore } from '@/stores/notifications'
import { useAuthStore } from '@/stores/auth'
import { useSplashStore } from '@/stores/splash'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

// Import layout components - updated for Vue 3 compatibility
import DashboardLayout from '@/dashboard/layout/DashboardLayout.vue'
import UserProfile from '@/dashboard/components/UserProfile.vue'
import SearchBar from '@/dashboard/components/SearchBar.vue'
import ItemsList from '@/dashboard/components/ItemsList.vue'
import WelcomePanel from '@/dashboard/components/WelcomePanel.vue'
import SecretDetails from '@/dashboard/components/SecretDetails.vue'
import FolderDetails from '@/dashboard/components/FolderDetails.vue'
import MobileTopBar from '@/dashboard/components/MobileTopBar.vue'
import AllSecretsView from '@/dashboard/components/AllSecretsView.vue'

// Import dialog components - fixed v-model binding issues
import SecretDialog from '@/dashboard/dialogs/SecretDialog.vue'
import FolderDialog from '@/dashboard/dialogs/FolderDialog.vue'
import DeleteDialog from '@/dashboard/dialogs/DeleteDialog.vue'
import ShareDialog from '@/dashboard/dialogs/ShareDialog.vue'

// Stores
const secretsStore = useSecretsStore()
const authStore = useAuthStore()
const splashStore = useSplashStore()
const route = useRoute()
const router = useRouter()
const notificationsStore = useNotificationsStore()

// State
const selectedItemId = ref(null)
const selectedItemType = ref(null)
const search = ref('')
const shareableLink = ref(null)
// Track which folders should be expanded due to search matches
const expandedFolderIds = ref({})
// Track which items match the search query (for highlighting)
const matchingItemIds = ref({
  secrets: {},
  folders: {}
})
// Track mobile state
const isMobile = ref(false)

// Add the notifications injection
const notifications = inject('notifications', notificationsStore)

// Handle mobile state change from layout
function handleMobileStateChange(mobile) {
  isMobile.value = mobile
}

// Clear selection (used for mobile back button)
function clearSelection() {
  selectedItemId.value = null
  selectedItemType.value = null
}

// Dialog states
const secretDialog = reactive({
  show: false,
  isEdit: false,
  inFolder: false,
  form: {
    id: null,
    name: '',
    type: 'plaintext',
    value: '',
    description: '',
    folder_id: null,
    tags: []
  }
})

const folderDialog = reactive({
  show: false,
  isEdit: false,
  form: {
    id: null,
    name: '',
    description: '',
    tags: []
  }
})

const deleteDialog = reactive({
  show: false,
  itemType: null,
  item: null
})

const shareDialog = reactive({
  show: false,
  itemType: null
})

// Current secret computed property
const currentSecret = computed(() => {
  if (!selectedItemId.value || selectedItemType.value !== 'secret') return null;

  // First check if currentSecret exists in the store
  if (secretsStore.currentSecret) {
    const storedSecret = secretsStore.currentSecret;

    // Make sure permissions are properly set for owned secrets
    if (storedSecret.owner_id && storedSecret.owner_id == authStore.userId) { // intentional loose equality for type coercion
      if (!storedSecret.permissions) {
        // Inject permissions if missing
        storedSecret.permissions = {
          can_read: true,
          can_write: true,
          can_delete: true,
          is_owner: true,
          has_direct_access: true
        };
      }
    }
    return storedSecret;
  }

  // Fallback: try to find the secret in the secrets array
  const id = parseInt(selectedItemId.value);
  const foundSecret = secretsStore.secrets.find(s => s.id === id);
  if (foundSecret) {
    // Make sure permissions are properly set for owned secrets
    if (foundSecret.owner_id && foundSecret.owner_id == authStore.userId) { // intentional loose equality for type coercion
      if (!foundSecret.permissions) {
        // Inject permissions if missing
        foundSecret.permissions = {
          can_read: true,
          can_write: true,
          can_delete: true,
          is_owner: true,
          has_direct_access: true
        };
      }
    }
    // Schedule a fetch to ensure we get full details
    secretsStore.fetchSecret(id).catch(err => {
      // Error loading secret details (console.error removed)
    });
    return foundSecret;
  }
  return null;
})

// Current folder computed property
const currentFolder = computed(() => {
  if (!selectedItemId.value || selectedItemType.value !== 'folder') return null;

  // First check if currentFolder exists in the store
  if (secretsStore.currentFolder) {
    return secretsStore.currentFolder;
  }

  // Fallback: try to find the folder in the folders array
  const id = parseInt(selectedItemId.value);
  const foundFolder = secretsStore.folders.find(f => f.id === id);
  if (foundFolder) {
    // Schedule a fetch to ensure we get full details
    secretsStore.fetchFolder(id).catch(err => {
      // Error loading folder details (console.error removed)
    });
    return foundFolder;
  }
  return null;
})

// Folder options for select
const folderOptions = computed(() => {
  if (!secretsStore.folders || !Array.isArray(secretsStore.folders)) return []
  return secretsStore.folders.map(folder => ({
    title: folder.name,
    value: folder.id,
    is_shared: folder.is_shared_folder // Added for styling in dropdown
  }))
})

// Folder contents (secrets inside selected folder)
const folderContents = computed(() => {
  if (!selectedItemId.value || selectedItemType.value !== 'folder') return []
  const folderId = parseInt(selectedItemId.value)
  // Use the secretsByFolderId getter from the store
  return secretsStore.secretsByFolderId(folderId)
})

// Suggested tags for autocomplete
const suggestedTags = computed(() => {
  const allTags = new Set()
  // Collect tags from secrets
  if (secretsStore.secrets && Array.isArray(secretsStore.secrets)) {
    secretsStore.secrets.forEach(secret => {
      if (secret.tags && Array.isArray(secret.tags)) {
        secret.tags.forEach(tag => allTags.add(tag))
      }
    })
  }
  // Collect tags from folders
  if (secretsStore.folders && Array.isArray(secretsStore.folders)) {
    secretsStore.folders.forEach(folder => {
      if (folder.tags && Array.isArray(folder.tags)) {
        folder.tags.forEach(tag => allTags.add(tag))
      }
    })
  }
  return Array.from(allTags)
})

// Helper function to normalize string for search comparison
function normalizeForSearch(str) {
  return str ? str.toLowerCase().trim() : ''
}

// Computed: Get folders that should be expanded based on search results
const foldersToExpand = computed(() => {
  if (!search.value) return {}
  const result = {}
  const normalizedSearch = normalizeForSearch(search.value)
  // If not searching, don't expand any folders
  if (!normalizedSearch) return result
  // First identify which secrets match the search
  const matchingSecrets = secretsStore.secrets.filter(secret => {
    const nameMatches = normalizeForSearch(secret.name).includes(normalizedSearch)
    const tagMatches = secret.tags && secret.tags.some(tag =>
      normalizeForSearch(tag).includes(normalizedSearch)
    )
    // Track matching secrets for highlighting
    matchingItemIds.value.secrets[secret.id] = nameMatches || tagMatches
    return nameMatches || tagMatches
  })
  // Include parent folders of matching secrets
  matchingSecrets.forEach(secret => {
    if (secret.folder_id) {
      result[secret.folder_id] = true
    }
  })
  // Also track which folders directly match the search
  secretsStore.folders.forEach(folder => {
    const nameMatches = normalizeForSearch(folder.name).includes(normalizedSearch)
    const tagMatches = folder.tags && folder.tags.some(tag =>
      normalizeForSearch(tag).includes(normalizedSearch)
    )
    // Track matching folders for highlighting
    matchingItemIds.value.folders[folder.id] = nameMatches || tagMatches
    // If the folder itself matches, it should be expanded
    if (nameMatches || tagMatches) {
      result[folder.id] = true
    }
  })
  return result
})

// Computed filtered secrets
const filteredSecrets = computed(() => {
  if (!secretsStore.secrets || !Array.isArray(secretsStore.secrets)) return []
  // If not searching, return all secrets
  if (!search.value) {
    // Clear matching items tracking
    matchingItemIds.value = { secrets: {}, folders: {} }
    return secretsStore.secrets
  }
  const normalizedSearch = normalizeForSearch(search.value)
  let filtered = secretsStore.secrets
  // Filter by search term
  if (normalizedSearch) {
    filtered = filtered.filter(secret => {
      const nameMatches = normalizeForSearch(secret.name).includes(normalizedSearch)
      const tagMatches = secret.tags && secret.tags.some(tag =>
        normalizeForSearch(tag).includes(normalizedSearch)
      )
      return nameMatches || tagMatches
    })
  }
  return filtered
})

// Computed filtered folders
const filteredFolders = computed(() => {
  if (!secretsStore.folders || !Array.isArray(secretsStore.folders)) return []
  // Deduplicate folders by ID first
  const uniqueFolders = [];
  const seenIds = new Set();
  for (const folder of secretsStore.folders) {
    if (folder && folder.id && !seenIds.has(folder.id)) {
      seenIds.add(folder.id);
      uniqueFolders.push(folder);
    }
  }
  // If not searching, return all unique folders
  if (!search.value) {
    return uniqueFolders;
  }
  const normalizedSearch = normalizeForSearch(search.value)
  const foldersToShow = { ...foldersToExpand.value }
  // Include folders that directly match the search criteria
  uniqueFolders.forEach(folder => {
    const nameMatches = normalizeForSearch(folder.name).includes(normalizedSearch)
    const tagMatches = folder.tags && folder.tags.some(tag =>
      normalizeForSearch(tag).includes(normalizedSearch)
    )
    if (nameMatches || tagMatches) {
      foldersToShow[folder.id] = true
    }
  })
  // Filter to show only matching folders or parents of matching secrets
  return uniqueFolders.filter(folder =>
    foldersToShow[folder.id]
  )
})

// Watch search input to update expanded folders
watch(search, (newValue) => {
  if (!newValue) {
    // When search is cleared, reset expanded state to default
    expandedFolderIds.value = {}
    matchingItemIds.value = { secrets: {}, folders: {} }
  } else {
    // Update expanded folders based on search matches
    expandedFolderIds.value = { ...foldersToExpand.value }
  }
})

// Ensure authentication is properly set up on mount
onMounted(async () => {
  // Initialize auth from localStorage if needed
  if (!authStore.token) {
    authStore.init()
  }
  // If still not authenticated, redirect to home
  if (!authStore.isAuthenticated) {
    router.push('/')
    return
  }
  // Try to refresh user data to ensure we have latest profile info
  try {
    await authStore.refreshUserData()
  } catch (error) {
    // Error refreshing user data (console.error removed)
  }
  // Initialize page data (load secrets, etc)
  await loadSecrets()
  // Additional check to validate selected item exists after initial data load
  validateSelectedItem()
})

// Load secrets from the server
async function loadSecrets() {
  try {
    // Set loading state to provide user feedback
    secretsStore.loading = true
    // Load both secrets and folders in parallel for efficiency
    await Promise.all([
      secretsStore.fetchSecrets(),
      secretsStore.fetchFolders()
    ])
    // After loading data, validate that the selected item still exists
    validateSelectedItem()
    // If we have a selected folder, refresh its contents
    if (selectedItemType.value === 'folder' && selectedItemId.value) {
      await secretsStore.fetchFolder(selectedItemId.value)
    }
    // If we have a selected secret, refresh it
    if (selectedItemType.value === 'secret' && selectedItemId.value) {
      await secretsStore.fetchSecret(selectedItemId.value)
    }
  } catch (error) {
    // Error loading data (console.error removed)
  } finally {
    secretsStore.loading = false
  }
}

// Validate that the currently selected item exists in our data
function validateSelectedItem() {
  if (!selectedItemId.value) return
  const id = parseInt(selectedItemId.value)
  if (selectedItemType.value === 'secret') {
    // Check if this secret still exists in our data
    const secretExists = secretsStore.secrets.some(s => s.id === id)
    if (!secretExists) {
      selectedItemId.value = null
      selectedItemType.value = null
    }
  } else if (selectedItemType.value === 'folder') {
    // Check if this folder still exists in our data
    const folderExists = secretsStore.folders.some(f => f.id === id)
    if (!folderExists) {
      selectedItemId.value = null
      selectedItemType.value = null
    }
  }
}

// Watch for changes in selected item ID
watch(selectedItemId, async (newId) => {
  if (newId) {
    try {
      if (selectedItemType.value === 'secret') {
        await secretsStore.fetchSecret(newId)
      } else if (selectedItemType.value === 'folder') {
        const result = await secretsStore.fetchFolder(newId)
        // If we couldn't fetch the folder data and there's no local data either
        if (!result && !secretsStore.currentFolder) {
          // Reset the selection to avoid showing an empty/error state
          selectedItemId.value = null
          selectedItemType.value = null
        }
      }
    } catch (error) {
      // Reset selection on critical errors
      selectedItemId.value = null
      selectedItemType.value = null
    }
  }
})

// Actions
function selectSecret(id) {
  // Check if the secret exists in our store's secrets array
  const secretExists = secretsStore.secrets.some(s => s.id === parseInt(id))
  if (secretExists) {
    selectedItemId.value = id
    selectedItemType.value = 'secret'
  } else {
    // Attempted to select non-existent secret
  }
}

function selectFolder(id) {
  // First check if the folder exists in our store's folder array
  const folderExists = secretsStore.folders.some(f => f.id === parseInt(id))
  if (folderExists) {
    selectedItemId.value = id
    selectedItemType.value = 'folder'
    // Close mobile menu when an item is selected
    const dashboard = document.querySelector('.dashboard-container')
    if (dashboard && window.innerWidth < 768) {
      const mobileNav = document.querySelector('.left-pane')
      if (mobileNav && mobileNav.classList.contains('mobile-open')) {
        // Delay closing the menu slightly to allow the selection to register
        setTimeout(() => {
          mobileNav.classList.remove('mobile-open')
          document.body.classList.remove('mobile-nav-open')
          document.body.style.overflow = ''
        }, 150)
      }
    }
    // Track that we're attempting to load this folder
    const loadingFolderId = id
    // Fetch folder details asynchronously
    secretsStore.fetchFolder(id).then(folderData => {
      if (!folderData) {
        if (secretsStore.error && secretsStore.error.includes('Permission denied')) {
          // Reload folders list to make sure our data is up to date
          secretsStore.fetchFolders().then(() => {
            // Check if folder still exists after reload
            const stillExists = secretsStore.folders.some(f => f.id === parseInt(id))
            if (!stillExists) {
              // Reset selection if folder no longer exists
              if (selectedItemId.value === loadingFolderId) {
                selectedItemId.value = null
                selectedItemType.value = null
              }
            }
          }).catch(err => {
            // Error reloading folders
          })
        }
      }
    }).catch(err => {
      // Error in folder selection
    })
  } else {
    // Attempted to select non-existent folder
  }
}

function selectAllSecretsFolder() {
  selectedItemId.value = null
  selectedItemType.value = 'all-secrets-folder'
  
  // Close mobile menu when selecting All Secrets folder
  if (window.innerWidth < 768) {
    const mobileNav = document.querySelector('.left-pane')
    if (mobileNav && mobileNav.classList.contains('mobile-open')) {
      setTimeout(() => {
        mobileNav.classList.remove('mobile-open')
        document.body.classList.remove('mobile-nav-open')
        document.body.style.overflow = ''
      }, 150)
    }
  }
}

function openCreateSecretDialog() {
  secretDialog.isEdit = false
  secretDialog.inFolder = false
  secretDialog.form = {
    id: null,
    name: '',
    type: 'plaintext',
    value: '',
    description: '',
    folder_id: null,
    tags: []
  }
  secretDialog.show = true
}

function openCreateFolderDialog() {
  folderDialog.isEdit = false
  folderDialog.form = {
    id: null,
    name: '',
    description: '',
    tags: []
  }
  folderDialog.show = true
}

function openCreateSecretInFolderDialog(folderId) {
  if (!folderId && !currentFolder.value) return
  const targetFolderId = folderId || currentFolder.value.id
  secretDialog.isEdit = false
  secretDialog.inFolder = true
  secretDialog.form = {
    id: null,
    name: '',
    type: 'plaintext',
    value: '',
    description: '',
    folder_id: targetFolderId,
    tags: []
  }
  secretDialog.show = true
}

function editSecret() {
  if (!currentSecret.value) return
  // Create a copy of the current secret to avoid any reference issues
  const secretToEdit = {
    id: currentSecret.value.id,
    name: currentSecret.value.name || '',
    type: currentSecret.value.type || 'plaintext',
    value: currentSecret.value.value || '',
    description: currentSecret.value.description || '',
    folder_id: currentSecret.value.folder_id, // Preserve folder_id
    tags: Array.isArray(currentSecret.value.tags) ? [...currentSecret.value.tags] : []
  }
  secretDialog.isEdit = true
  secretDialog.form = secretToEdit
  secretDialog.show = true
}

function editFolder() {
  if (!currentFolder.value) return
  folderDialog.isEdit = true
  folderDialog.form = {
    id: currentFolder.value.id,
    name: currentFolder.value.name,
    description: currentFolder.value.description || '',
    tags: currentFolder.value.tags || []
  }
  folderDialog.show = true
}

function confirmDeleteFolder() {
  if (!currentFolder.value) return
  // Check if user has permission to delete this folder
  const canDelete = currentFolder.value.is_owner || // Owner can delete
                    (currentFolder.value.permissions && currentFolder.value.permissions.can_delete); // User with explicit delete permission
  if (!canDelete) {
    // If they don't have permission, show a notification instead
    notificationsStore.showNotification({
      type: 'error',
      message: 'You don\'t have permission to delete this folder'
    });
    return;
  }
  // Show the delete confirmation dialog
  deleteDialog.show = true
  deleteDialog.itemType = 'folder'
  deleteDialog.item = { ...currentFolder.value }
}

function confirmDeleteSecret() {
  if (!currentSecret.value) return
  // Check if user has permission to delete this secret
  const canDelete = currentSecret.value.owner_id === authStore.userId || // Owner can delete
                    (currentSecret.value.permissions && currentSecret.value.permissions.can_delete); // User with explicit delete permission
  if (!canDelete) {
    // If they don't have permission, show a notification instead
    notificationsStore.showNotification({
      type: 'error',
      message: 'You don\'t have permission to delete this secret'
    });
    return;
  }
  // Show the delete confirmation dialog
  deleteDialog.show = true
  deleteDialog.itemType = 'secret'
  deleteDialog.item = { ...currentSecret.value }
}

async function saveSecret(formData) {
  try {
    const secretId = formData.id
    const secretsStore = useSecretsStore()
    const notificationStore = notificationsStore // Use the store from above
    let newSecret = null
    // Handle different save scenarios
    if (secretId) {
      // Update existing secret
      if (formData.type === 'image' || formData.type === 'file') {
        // For file updates, use the file update endpoint
        if (formData.file) {
          newSecret = await secretsStore.updateSecretFile(secretId, formData)
        } else {
          // Just update metadata without changing the file
          newSecret = await secretsStore.updateSecret(secretId, formData)
        }
      } else {
        // For text secrets, use the standard update endpoint
        newSecret = await secretsStore.updateSecret(secretId, formData)
      }
    } else {
      // Create new secret
      if (formData.type === 'image' || formData.type === 'file') {
        // For file secrets, use the file creation endpoint
        newSecret = await secretsStore.createSecretFile(formData)
      } else {
        // For text secrets, use the standard creation endpoint
        newSecret = await secretsStore.createSecret(formData)
      }
    }
    // Close modal and reload data
    secretDialog.show = false
    await loadSecrets()
    // Show success notification
    if (notificationsStore) { // Check if notification store exists
      notificationsStore.showNotification({
        type: 'success',
        message: secretId ? 'Secret updated successfully' : 'Secret created successfully'
      })
    }
    return newSecret
  } catch (error) {
    // Show error notification
    if (notificationsStore) { // Check if notification store exists
      notificationsStore.showNotification({
        type: 'error',
        message: `Failed to save secret: ${error.message || 'Unknown error'}`
      })
    }
    throw error
  }
}

async function saveFolder(folderData, callback) {
  try {
    let folderId;
    if (folderDialog.isEdit) {
      await secretsStore.updateFolder(folderData.id, folderData)
      folderId = folderData.id
    } else {
      const newFolder = await secretsStore.createFolder(folderData)
      if (newFolder) {
        // Close any open menus
        closeActiveMenus()
        folderId = newFolder.id
        selectedItemId.value = folderId.toString()
        selectedItemType.value = 'folder'
      }
    }
    folderDialog.show = false
    // Call the callback with the folder ID if provided
    if (typeof callback === 'function') {
      callback(folderId)
    }
    // Return the folder ID in case we need it
    return folderId
  } catch (error) {
    notificationsStore.showNotification({
      type: 'error',
      message: `Error saving folder: ${error.response?.data?.error || error.message || 'Unknown error'}`
    })
    // Call the callback with null to indicate failure if provided
    if (typeof callback === 'function') {
      callback(null)
    }
    return null
  }
}

// Function to close any active menus (like the + menu)
function closeActiveMenus() {
  // Find any active menus and programmatically close them
  const menus = document.querySelectorAll('.v-overlay--active')
  menus.forEach(menu => {
    const closeButton = menu.querySelector('.v-overlay__close-button')
    if (closeButton) {
      closeButton.click()
    }
  })
}

async function deleteItem(type, item) {
  if (!item || !item.id) return
  try {
    let success = false
    if (type === 'secret') {
      success = await secretsStore.deleteSecret(item.id)
    } else if (type === 'folder') {
      success = await secretsStore.deleteFolder(item.id)
    }
    if (success) {
      // Close all relevant dialogs
      deleteDialog.show = false
      // Also close the secret or folder edit dialog
      if (type === 'secret') {
        secretDialog.show = false
      } else if (type === 'folder') {
        folderDialog.show = false
      }
      // Always reset selection when something is deleted to prevent "not found" errors
      selectedItemId.value = null
      selectedItemType.value = null
      // Show success notification
      notificationsStore.showNotification({
        type: 'success',
        message: `${type === 'secret' ? 'Secret' : 'Folder'} deleted successfully`
      })
      // Reload data to ensure view is up to date
      await loadSecrets()
      // Slight delay to ensure UI updates properly
      setTimeout(() => {
        // Double-check that no remnants of the deleted item remain
        if (type === 'secret') {
          // Verify the secret is no longer in the store
          const stillExists = secretsStore.secretById(item.id)
          if (stillExists) {
            // Force remove from local array if it somehow still exists
            secretsStore.secrets = secretsStore.secrets.filter(s => s.id !== parseInt(item.id))
          }
        } else if (type === 'folder') {
          // Verify the folder is no longer in the store
          const stillExists = secretsStore.folderById(item.id)
          if (stillExists) {
            // Force remove from local array if it somehow still exists
            secretsStore.folders = secretsStore.folders.filter(f => f.id !== parseInt(item.id))
          }
        }
      }, 100)
    }
  } catch (error) {
    // Error deleting (console.error removed)
  }
}

function openShareDialog() {
  shareDialog.itemType = 'secret'
  shareDialog.show = true
}

function openShareFolderDialog() {
  shareDialog.itemType = 'folder'
  shareDialog.show = true
}

async function shareWithUser(shareData) {
  if (!selectedItemId.value) return
  try {
    let result = null
    // Convert UI permission value to API permission format
    const permissionObj = { can_read: false, can_write: false, can_delete: false }
    if (shareData.permissions === 'read') {
      permissionObj.can_read = true
    } else if (shareData.permissions === 'write') {
      permissionObj.can_read = true
      permissionObj.can_write = true
    } else if (shareData.permissions === 'full') {
      permissionObj.can_read = true
      permissionObj.can_write = true
      permissionObj.can_delete = true
    }
    if (shareDialog.itemType === 'secret') {
      result = await secretsStore.shareSecret(
        selectedItemId.value,
        shareData.userId,
        permissionObj
      )
    } else if (shareDialog.itemType === 'folder') {
      result = await secretsStore.shareFolder(
        selectedItemId.value,
        shareData.userId,
        permissionObj
      )
    }
    if (result) {
      shareDialog.show = false
      // Reload the current item to show updated sharing info
      if (shareDialog.itemType === 'folder') {
        await secretsStore.fetchFolder(selectedItemId.value)
      } else if (shareDialog.itemType === 'secret') {
        await secretsStore.fetchSecret(selectedItemId.value)
      }
      // Show success notification
      const itemName = shareDialog.itemType === 'folder' ?
                      currentFolder.value?.name :
                      currentSecret.value?.name
      const userName = shareData.userName
      notificationsStore.showNotification({
        type: 'success',
        message: `Successfully shared ${shareDialog.itemType} "${itemName}" with ${userName}`
      })
    } else {
      notificationsStore.showNotification({
        type: 'error',
        message: `Failed to share ${shareDialog.itemType}`
      })
    }
  } catch (error) {
    // Show error notification instead of alert
    notificationsStore.showNotification({
      type: 'error',
      message: `Error sharing ${shareDialog.itemType}: ${error.response?.data?.error || error.message || 'Unknown error'}`
    })
  }
}

function navigateToFolder(folderId) {
  // Ensure the folder exists in our store
  const folder = secretsStore.folderById(folderId)
  if (folder) {
    // Select the folder
    selectedItemId.value = folderId.toString()
    selectedItemType.value = 'folder'
  } else {
    // Folder not found (console.error removed)
  }
}

// Refs for click-outside detection
const itemsListRef = ref(null)
const secretDetailsRef = ref(null)
const folderDetailsRef = ref(null)

// Function to handle clicks outside of items to dismiss selection
function handleOutsideClick(event) {
  // Don't process if we don't have any selection
  if (!selectedItemId.value) return
  // Skip processing if the event target is a button or any interactive element
  // This prevents the outside click from triggering when users interact with UI elements
  if (event.target.closest('button') ||
      event.target.closest('a') ||
      event.target.closest('.v-list-item') ||
      event.target.closest('.item-row')) {
    return
  }
  // Check if the click happened on a dialog
  const dialogs = document.querySelectorAll('.v-dialog--active')
  for (const dialog of dialogs) {
    if (dialog.contains(event.target)) {
      // Click was inside a dialog, don't clear selection
      return
    }
  }
  // Check if the click happened in the items list component
  if (itemsListRef.value && itemsListRef.value.$el.contains(event.target)) {
    // Click was inside the items list, let the component handle it
    return
  }
  // Check if the click happened in the details components
  if (
    (secretDetailsRef.value && secretDetailsRef.value.$el.contains(event.target)) ||
    (folderDetailsRef.value && folderDetailsRef.value.$el.contains(event.target))
  ) {
    // Click was inside the details panel, don't clear selection
    return
  }
  // Click was outside, clear the selection
  selectedItemId.value = null
  selectedItemType.value = null
}

// Add a computed property to check if user can add to current folder
const canAddToCurrentFolder = computed(() => {
  // If no folder is selected, user can add at root level
  if (!selectedItemType.value || selectedItemType.value !== 'folder') {
    return true;
  }
  // If a folder is selected, check if user has write permission
  if (currentFolder.value) {
    // If user is owner, they can add
    if (currentFolder.value.is_owner === true) {
      return true;
    }
    // Check explicit permissions
    if (currentFolder.value.permissions &&
        currentFolder.value.permissions.can_write === true) {
      return true;
    }
    return false;
  }
  return true;
});

// Function to handle moving a secret via drag and drop
async function moveSecret(moveData) {
  try {
    // Get the secret details
    const secret = secretsStore.secretById(moveData.secretId)
    if (!secret) {
      notificationsStore.showNotification({
        type: 'error',
        message: 'Error: Secret not found'
      })
      return
    }
    // Get the complete secret data with permissions and complete value
    // This is critical to ensure all data is preserved during the move
    await secretsStore.fetchSecret(secret.id)
    const completeSecretData = secretsStore.currentSecret
    if (!completeSecretData) {
      notificationsStore.showNotification({
        type: 'error',
        message: 'Error: Could not fetch secret details'
      })
      return
    }
    // Make direct API call to move endpoint instead of using updateSecret
    const response = await axios.post(`/api/secrets/${secret.id}/move`, {
      folder_id: moveData.targetFolderId
    })
    if (response.data) {
      // Show success notification
      notificationsStore.showNotification({
        type: 'success',
        message: `Moved "${moveData.secretName}" to ${moveData.targetFolderId ? `"${moveData.folderName}"` : 'Root'}`
      })
      // If moving from a folder, ensure the source folder is refreshed
      if (secret.folder_id) {
        // Check if this folder exists in the folders list (accessible to the user)
        const sourceFolder = secretsStore.folders.find(f => f.id === parseInt(secret.folder_id));
        if (sourceFolder) {
          // Only try to refresh folders the user has access to
          try {
            await secretsStore.fetchFolder(secret.folder_id);
          } catch (folderError) {
            // This error is expected when moving from inaccessible folders, so we ignore it
          }
        }
      }
      // If moving to a folder, ensure the target folder is refreshed and expanded
      if (moveData.targetFolderId) {
        try {
          await secretsStore.fetchFolder(moveData.targetFolderId);
          expandedFolderIds.value[moveData.targetFolderId] = true;
        } catch (folderError) {
          // This shouldn't happen since we're moving to a folder we should have access to
        }
      }
      // Fetch the updated secret to ensure all data is current
      await secretsStore.fetchSecret(secret.id)
      // Refresh overall secrets list to ensure UI is updated
      await loadSecrets()
    }
  } catch (error) {
    let errorMessage = 'Failed to move secret'
    if (error.response?.data?.msg) {
      errorMessage = error.response.data.msg
    } else if (error.message) {
      errorMessage = error.message
    }
    // Show error notification
    notificationsStore.showNotification({
      type: 'error',
      message: errorMessage
    })
  }
}

function handleSharedFolderCreation(sharingInfo) {
  // Get the folder ID from sharing info
  if (!sharingInfo.folderId) {
    // Fallback to selected item if available
    if (selectedItemId.value && selectedItemType.value === 'folder') {
      sharingInfo.folderId = selectedItemId.value;
    } else {
      return;
    }
  }
  const folderId = sharingInfo.folderId
  // Immediately mark the folder as shared in the UI
  const folderToUpdate = secretsStore.folderById(folderId);
  if (folderToUpdate) {
    // Update both properties to ensure UI updates correctly
    folderToUpdate.folder_type = 'shared';
    folderToUpdate.is_shared_folder = true;
    // Force a UI update by triggering reactivity
    secretsStore.folders = [...secretsStore.folders];
    if (currentFolder.value && currentFolder.value.id === parseInt(folderId)) {
      // Also update the current folder if it's selected
      currentFolder.value.folder_type = 'shared';
      currentFolder.value.is_shared_folder = true;
    }
  }
  // Collect all sharing promises to ensure we wait for all of them
  const sharingPromises = sharingInfo.users.map(async user => {
    try {
      // Convert UI permission value to API permission format
      const permissionObj = { can_read: false, can_write: false, can_delete: false }
      if (sharingInfo.permissions === 'read') {
        permissionObj.can_read = true
      } else if (sharingInfo.permissions === 'write') {
        permissionObj.can_read = true
        permissionObj.can_write = true
      } else if (sharingInfo.permissions === 'full') {
        permissionObj.can_read = true
        permissionObj.can_write = true
        permissionObj.can_delete = true
      }
      // Share the folder with this user
      const result = await secretsStore.shareFolder(
        folderId,
        user.userId,
        permissionObj
      )
      if (result) {
        // Show success notification
        const folderName = currentFolder.value?.name || 'folder'
        notificationsStore.showNotification({
          type: 'success',
          message: `Successfully shared folder "${folderName}" with ${user.userName}`
        })
        return true;
      }
      return false;
    } catch (error) {
      notificationsStore.showNotification({
        type: 'error',
        message: `Error sharing folder: ${error.response?.data?.error || error.message || 'Unknown error'}`
      })
      return false;
    }
  });
  // Execute all sharing operations and then refresh folder data
  Promise.all(sharingPromises).then(results => {
    // Reload the folder data to refresh the sharing info
    secretsStore.fetchFolder(folderId).then(updatedFolder => {
      // Force update the folders list to ensure UI reflects changes
      secretsStore.fetchFolders();
    });
  });
}

async function removeSecretFromFolder(data) {
  try {
    // Get the secret details
    const secret = secretsStore.secretById(data.secretId)
    if (!secret) {
      notificationsStore.showNotification({
        type: 'error',
        message: 'Error: Secret not found'
      })
      return
    }
    
    // Make API call to move the secret to null folder (remove from folder)
    await axios.post(`/api/secrets/${data.secretId}/move`, {
      folder_id: null // Setting to null means removing from folder
    })
    
    // Refresh the secrets list after changing
    await secretsStore.fetchSecrets()
    
    // Show success notification
    notificationsStore.showNotification({
      type: 'success',
      message: `Moved "${data.secretName}" to All Secrets`
    })
  } catch (error) {
    console.error('Error removing secret from folder:', error)
    notificationsStore.showNotification({
      type: 'error',
      message: 'Error removing secret from folder'
    })
  }
}
</script>

<style scoped>
/* No additional styles needed here as they've been moved to the individual components */
</style>