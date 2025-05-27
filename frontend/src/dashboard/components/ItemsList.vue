<template>
  <div class="secrets-wrapper" :class="{'is-dragging': isDragging}">
    <div class="list-header">
      <h3 class="secrets-title">
        <v-icon color="primary" class="mr-1" size="small">mdi-database-lock</v-icon>
        Vault
      </h3>
      
      <!-- Mobile-only action buttons for quick access -->
      <div class="mobile-actions">
        <v-btn
          v-if="canAddItems"
          icon="mdi-plus"
          variant="text"
          color="primary"
          size="x-small"
          class="mr-1"
          @click.stop="openActionMenu"
          aria-label="Add new item"
        ></v-btn>
      </div>
    </div>
    
    <div class="secrets-list">
      <!-- Loading state -->
      <div v-if="loading" class="data-loading">
        <div class="cyber-spinner">
          <div class="spinner-ring"></div>
          <div class="spinner-ring"></div>
          <div class="spinner-dot"></div>
        </div>
      </div>
      
      <!-- Error message -->
      <div v-else-if="error" class="error-message">
        <v-icon color="error" class="mr-1">mdi-alert-circle</v-icon>
        {{ error }}
      </div>
      
      <!-- Empty state -->
      <div
        v-else-if="folders.length === 0 && secrets.length === 0"
        class="empty-state"
      >
        <div class="empty-icon">
          <v-icon color="primary" size="42">mdi-lock-outline</v-icon>
          <div class="icon-glow"></div>
        </div>
        <h3 class="empty-title">No Secrets or Folders Yet</h3>
        <p class="empty-subtitle">Create your first secret or folder to get started</p>
        <div class="empty-actions">
          <v-btn 
            color="primary" 
            variant="elevated"
            @click="$emit('create-secret')"
            class="neon-btn mt-4 mr-3"
            size="small"
          >
            <v-icon start>mdi-file-lock</v-icon>
            Create Secret
          </v-btn>
          <v-btn 
            color="info" 
            variant="elevated"
            @click="$emit('create-folder')"
            class="neon-btn mt-4"
            size="small"
          >
            <v-icon start>mdi-folder</v-icon>
            Create Folder
          </v-btn>
        </div>
      </div>
      
      <!-- No results for search -->
      <div
        v-else-if="isSearchActive && filteredFolders.length === 0 && filteredSecrets.length === 0"
        class="empty-state search-no-results"
      >
        <div class="empty-icon">
          <v-icon color="info" size="42">mdi-magnify</v-icon>
          <div class="icon-glow"></div>
        </div>
        <h3 class="empty-title">No matching results</h3>
        <p class="empty-subtitle">Try a different search term</p>
      </div>
      
      <!-- Folders and Secrets List -->
      <template v-else>
        <!-- ALL SECRETS FOLDER (Default container) -->
        <div class="folder-container system-folder">
          <div 
            :class="{ 
              'item-row': true,
              'folder-item': true,
              'all-secrets-folder': true,
              'selected-item': selectedItemType === 'all-secrets-folder',
              'folder-expanded': shouldAllSecretsFolderBeExpanded,
              'search-match': isSearchActive
            }"
            @click.stop
          >
            <div class="folder-header">
              <div class="folder-expand-icon" @click.stop="toggleAllSecretsExpand">
                <v-icon size="small">{{ shouldAllSecretsFolderBeExpanded ? 'mdi-chevron-down' : 'mdi-chevron-right' }}</v-icon>
              </div>
              
              <div class="item-icon" @click.stop="selectAllSecretsFolder">
                <v-icon 
                  color="accent" 
                  size="small"
                >
                  {{ shouldAllSecretsFolderBeExpanded ? 'mdi-folder-open' : 'mdi-folder' }}
                </v-icon>
              </div>
              
              <div class="item-details" @click.stop="selectAllSecretsFolder">
                <div class="item-name">
                  All Secrets
                  <v-chip
                    size="x-small"
                    label
                    color="info"
                    class="ml-2"
                  >
                    {{ allSecrets.length }}
                  </v-chip>
                </div>
                <div class="item-meta">
                  <small class="folder-description">All your secrets in one place</small>
                </div>
              </div>
            </div>
          </div>
          
          <!-- All Secrets Folder Contents -->
          <div 
            v-if="shouldAllSecretsFolderBeExpanded" 
            class="folder-contents"
          >
            <div
              v-for="secret in allSecrets"
              :key="`all-secrets-${secret.id}`"
              :class="{ 
                'selected-item': selectedItemType === 'secret' && selectedItemId === secret.id,
                'search-match': isSearchMatch('secret', secret.id),
                'item-dragging': draggedSecret && draggedSecret.id === secret.id
              }"
              @click.stop="selectSecret(secret.id, $event)"
              class="item-row secret-item folder-child-item"
              draggable="true"
              @dragstart="handleDragStart($event, secret)"
              @dragend="handleDragEnd"
            >
              <div class="item-icon">
                <v-icon :color="getTypeColor(secret.type)" size="small">
                  {{ getTypeIcon(secret.type) }}
                </v-icon>
              </div>
              
              <div class="item-details">
                <div class="item-name">{{ secret.name }}</div>
                <div class="item-meta">
                  <v-chip 
                    :color="getTypeColor(secret.type)" 
                    size="x-small" 
                    label
                    class="secret-type mr-1 mb-1"
                  >
                    {{ secret.type }}
                  </v-chip>
                  <div class="secret-tags" v-if="secret.tags && secret.tags.length > 0">
                    <v-chip
                      v-for="tag in secret.tags.slice(0, 2)" 
                      :key="tag"
                      size="x-small"
                      label
                      class="tag-chip mr-1 mb-1"
                      color="secondary"
                    >
                      {{ tag }}
                    </v-chip>
                    <span v-if="secret.tags.length > 2" class="more-tags">+{{ secret.tags.length - 2 }}</span>
                  </div>
                </div>
              </div>
            </div>
            
            <div v-if="allSecrets.length === 0" class="empty-folder-note">
              <span>No secrets added yet</span>
              <v-btn
                color="primary"
                variant="text"
                density="compact"
                size="x-small"
                class="ml-2 add-secret-btn"
                @click.stop="createSecret"
              >
                <v-icon size="x-small" class="mr-1">mdi-plus</v-icon>
                Add
              </v-btn>
            </div>
          </div>
        </div>
        
        <!-- SECTION DIVIDER: PRIVATE FOLDERS -->
        <div class="section-divider" v-if="privateFolders.length > 0 || isAdmin">
          <div class="section-title">
            <v-icon color="primary" size="x-small" class="mr-1">mdi-folder-lock</v-icon>
            Private Folders
          </div>
          <div class="section-actions">
            <v-btn
              v-if="canAddItems"
              icon="mdi-plus"
              variant="text"
              color="primary"
              size="x-small"
              @click.stop="createPrivateFolder"
              aria-label="Create private folder"
              class="section-action-btn"
            ></v-btn>
          </div>
        </div>
        
        <!-- PRIVATE FOLDERS -->
        <div
          v-for="folder in privateFolders"
          :key="`folder-${folder.id}`"
          class="folder-container"
          :class="{'folder-drop-target': isDragging && canWriteToFolder(folder)}"
          @dragover.prevent="handleFolderDragOver($event, folder)"
          @dragleave="handleFolderDragLeave($event, folder)"
          @drop="handleFolderDrop($event, folder)"
        >
          <div 
            :class="{ 
              'item-row': true,
              'folder-item': true,
              'selected-item': selectedItemType === 'folder' && selectedItemId === folder.id,
              'folder-expanded': shouldFolderBeExpanded(folder.id),
              'search-match': isSearchMatch('folder', folder.id),
              'folder-drag-over': folder.id === dropTargetId && canWriteToFolder(folder)
            }"
            @click.stop
          >
            <div class="folder-header">
              <div class="folder-expand-icon" @click.stop="toggleFolderExpand(folder.id, $event)">
                <v-icon size="small">{{ shouldFolderBeExpanded(folder.id) ? 'mdi-chevron-down' : 'mdi-chevron-right' }}</v-icon>
              </div>
              
              <div class="item-icon" @click.stop="selectFolder(folder.id, $event)">
                <v-icon 
                  color="primary" 
                  size="small"
                >
                  {{ shouldFolderBeExpanded(folder.id) ? 'mdi-folder-open' : 'mdi-folder-lock' }}
                </v-icon>
              </div>
              
              <div class="item-details" @click.stop="selectFolder(folder.id, $event)">
                <div class="item-name">
                  {{ folder.name }}
                </div>
                <div class="item-meta">
                  <div class="folder-tags" v-if="folder.tags && folder.tags.length > 0">
                    <v-chip
                      v-for="tag in folder.tags.slice(0, 2)" 
                      :key="tag"
                      size="x-small"
                      label
                      class="tag-chip mr-1 mb-1"
                      color="secondary"
                    >
                      {{ tag }}
                    </v-chip>
                    <span v-if="folder.tags.length > 2" class="more-tags">+{{ folder.tags.length - 2 }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Folder Contents (secrets inside this folder) -->
          <div 
            v-if="shouldFolderBeExpanded(folder.id)" 
            class="folder-contents"
          >
            <div
              v-for="secret in getFolderSecrets(folder.id)"
              :key="`folder-${folder.id}-secret-${secret.id}`"
              :class="{ 
                'selected-item': selectedItemType === 'secret' && selectedItemId === secret.id,
                'search-match': isSearchMatch('secret', secret.id),
                'item-dragging': draggedSecret && draggedSecret.id === secret.id
              }"
              @click.stop="selectSecret(secret.id, $event)"
              class="item-row secret-item folder-child-item"
              draggable="true"
              @dragstart="handleDragStart($event, secret)"
              @dragend="handleDragEnd"
            >
              <div class="item-icon">
                <v-icon :color="getTypeColor(secret.type)" size="small">
                  {{ getTypeIcon(secret.type) }}
                </v-icon>
              </div>
              
              <div class="item-details">
                <div class="item-name">{{ secret.name }}</div>
                <div class="item-meta">
                  <v-chip 
                    :color="getTypeColor(secret.type)" 
                    size="x-small" 
                    label
                    class="secret-type mr-1 mb-1"
                  >
                    {{ secret.type }}
                  </v-chip>
                  <div class="secret-tags" v-if="secret.tags && secret.tags.length > 0">
                    <v-chip
                      v-for="tag in secret.tags.slice(0, 2)" 
                      :key="tag"
                      size="x-small"
                      label
                      class="tag-chip mr-1 mb-1"
                      color="secondary"
                    >
                      {{ tag }}
                    </v-chip>
                    <span v-if="secret.tags.length > 2" class="more-tags">+{{ secret.tags.length - 2 }}</span>
                  </div>
                </div>
              </div>
              
              <div class="item-actions" @click.stop>
                <v-btn
                  icon="mdi-folder-remove-outline"
                  variant="text"
                  color="error"
                  size="x-small"
                  @click.stop="removeFromFolder(secret)"
                  class="remove-btn"
                  aria-label="Remove from folder"
                ></v-btn>
              </div>
            </div>
            
            <div v-if="getFolderSecrets(folder.id).length === 0" class="empty-folder-note">
              <span>No secrets in this folder</span>
              <v-btn
                v-if="canWriteToFolder(folder)"
                color="primary"
                variant="text"
                density="compact"
                size="x-small"
                class="ml-2 add-secret-btn"
                @click.stop="addSecretToFolder(folder.id)"
              >
                <v-icon size="x-small" class="mr-1">mdi-plus</v-icon>
                Add
              </v-btn>
            </div>
          </div>
        </div>
        
        <!-- SECTION DIVIDER: SHARED FOLDERS -->
        <div class="section-divider" v-if="sharedFolders.length > 0">
          <div class="section-title">
            <v-icon color="success" size="x-small" class="mr-1">mdi-folder-multiple</v-icon>
            Shared Folders
          </div>
        </div>
        
        <!-- SHARED FOLDERS -->
        <div
          v-for="folder in sharedFolders"
          :key="`shared-folder-${folder.id}`"
          class="folder-container shared-folder-container"
          :class="{'folder-drop-target': isDragging && canWriteToFolder(folder)}"
          @dragover.prevent="handleFolderDragOver($event, folder)"
          @dragleave="handleFolderDragLeave($event, folder)"
          @drop="handleFolderDrop($event, folder)"
        >
          <div 
            :class="{ 
              'item-row': true,
              'folder-item': true,
              'selected-item': selectedItemType === 'folder' && selectedItemId === folder.id,
              'folder-expanded': shouldFolderBeExpanded(folder.id),
              'search-match': isSearchMatch('folder', folder.id),
              'folder-drag-over': folder.id === dropTargetId && canWriteToFolder(folder)
            }"
            @click.stop
          >
            <div class="folder-header">
              <div class="folder-expand-icon" @click.stop="toggleFolderExpand(folder.id, $event)">
                <v-icon size="small">{{ shouldFolderBeExpanded(folder.id) ? 'mdi-chevron-down' : 'mdi-chevron-right' }}</v-icon>
              </div>
              
              <div class="item-icon" @click.stop="selectFolder(folder.id, $event)">
                <v-icon 
                  color="success" 
                  size="small"
                >
                  {{ shouldFolderBeExpanded(folder.id) 
                    ? 'mdi-folder-multiple-outline' 
                    : 'mdi-folder-multiple' 
                  }}
                </v-icon>
              </div>
              
              <div class="item-details" @click.stop="selectFolder(folder.id, $event)">
                <div class="item-name">
                  {{ folder.name }}
                  <v-chip
                    size="x-small"
                    label
                    color="success"
                    class="ml-2"
                  >
                    Shared
                  </v-chip>
                </div>
                <div class="item-meta">
                  <div class="folder-tags" v-if="folder.tags && folder.tags.length > 0">
                    <v-chip
                      v-for="tag in folder.tags.slice(0, 2)" 
                      :key="tag"
                      size="x-small"
                      label
                      class="tag-chip mr-1 mb-1"
                      color="secondary"
                    >
                      {{ tag }}
                    </v-chip>
                    <span v-if="folder.tags.length > 2" class="more-tags">+{{ folder.tags.length - 2 }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Folder Contents (secrets inside this folder) -->
          <div 
            v-if="shouldFolderBeExpanded(folder.id)" 
            class="folder-contents"
          >
            <div
              v-for="secret in getFolderSecrets(folder.id)"
              :key="`folder-${folder.id}-secret-${secret.id}`"
              :class="{ 
                'selected-item': selectedItemType === 'secret' && selectedItemId === secret.id,
                'search-match': isSearchMatch('secret', secret.id),
                'item-dragging': draggedSecret && draggedSecret.id === secret.id
              }"
              @click.stop="selectSecret(secret.id, $event)"
              class="item-row secret-item folder-child-item"
              draggable="true"
              @dragstart="handleDragStart($event, secret)"
              @dragend="handleDragEnd"
            >
              <div class="item-icon">
                <v-icon :color="getTypeColor(secret.type)" size="small">
                  {{ getTypeIcon(secret.type) }}
                </v-icon>
              </div>
              
              <div class="item-details">
                <div class="item-name">{{ secret.name }}</div>
                <div class="item-meta">
                  <v-chip 
                    :color="getTypeColor(secret.type)" 
                    size="x-small" 
                    label
                    class="secret-type mr-1 mb-1"
                  >
                    {{ secret.type }}
                  </v-chip>
                  <div class="secret-tags" v-if="secret.tags && secret.tags.length > 0">
                    <v-chip
                      v-for="tag in secret.tags.slice(0, 2)" 
                      :key="tag"
                      size="x-small"
                      label
                      class="tag-chip mr-1 mb-1"
                      color="secondary"
                    >
                      {{ tag }}
                    </v-chip>
                    <span v-if="secret.tags.length > 2" class="more-tags">+{{ secret.tags.length - 2 }}</span>
                  </div>
                </div>
              </div>
              
              <div class="item-actions" @click.stop>
                <v-btn
                  icon="mdi-folder-remove-outline"
                  variant="text"
                  color="error"
                  size="x-small"
                  @click.stop="removeFromFolder(secret)"
                  class="remove-btn"
                  aria-label="Remove from folder"
                ></v-btn>
              </div>
            </div>
            
            <div v-if="getFolderSecrets(folder.id).length === 0" class="empty-folder-note">
              <span>No secrets in this folder</span>
              <v-btn
                v-if="canWriteToFolder(folder)"
                color="primary"
                variant="text"
                density="compact"
                size="x-small"
                class="ml-2 add-secret-btn"
                @click.stop="addSecretToFolder(folder.id)"
              >
                <v-icon size="x-small" class="mr-1">mdi-plus</v-icon>
                Add
              </v-btn>
            </div>
          </div>
        </div>
      </template>
    </div>
    
    <!-- Quick action menu for mobile -->
    <v-menu
      v-model="showActionMenu"
      :close-on-content-click="false"
      location="bottom end"
      :attach="true"
      min-width="200"
      :z-index="9999"
      offset="5"
      class="mobile-action-menu"
      persistent
    >
      <v-list class="mobile-menu-list" @click.stop>
        <v-list-item 
          v-if="canAddItems"
          @click.stop="createSecretAndClose" 
          class="menu-item" 
          active-color="primary"
        >
          <v-list-item-title>
            <v-icon start>mdi-file-lock</v-icon>
            New Secret
          </v-list-item-title>
        </v-list-item>
        
        <v-list-item 
          v-if="canAddItems"
          @click.stop="createPrivateFolderAndClose" 
          class="menu-item" 
          active-color="primary"
        >
          <v-list-item-title>
            <v-icon start>mdi-folder-lock</v-icon>
            New Private Folder
          </v-list-item-title>
        </v-list-item>
        
        <v-divider></v-divider>
        
        <v-list-item @click.stop="showActionMenu = false" class="menu-item">
          <v-list-item-title class="text-center">
            Cancel
          </v-list-item-title>
        </v-list-item>
      </v-list>
    </v-menu>
    
    <!-- Toast notification for drag and drop operations -->
    <v-snackbar
      v-model="showToast"
      :color="toastColor"
      :timeout="3000"
      bottom
      right
    >
      {{ toastMessage }}
    </v-snackbar>
  </div>
</template>

<script setup>
import { computed, ref, watch, nextTick } from 'vue'

const props = defineProps({
  folders: {
    type: Array,
    default: () => []
  },
  secrets: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: ''
  },
  selectedItemId: {
    type: String,
    default: null
  },
  selectedItemType: {
    type: String,
    default: null
  },
  isAdmin: {
    type: Boolean,
    default: false
  },
  // Search functionality
  searchQuery: {
    type: String,
    default: ''
  },
  searchMatchingItems: {
    type: Object,
    default: () => ({ secrets: {}, folders: {} })
  },
  searchExpandedFolders: {
    type: Object,
    default: () => ({})
  },
  // Mobile view
  isMobile: {
    type: Boolean,
    default: false
  },
  userId: {
    type: String,
    default: ''
  }
})

const emit = defineEmits([
  'select-folder', 
  'select-secret', 
  'select-all-secrets-folder',
  'create-secret', 
  'create-folder',
  'add-secret-to-folder',
  'move-secret',
  'remove-from-folder'
])

// Track expanded folder state
const expandedFolders = ref({})
const allSecretsFolderExpanded = ref(true) // Default to expanded
const showActionMenu = ref(false)

// Drag and drop state
const isDragging = ref(false)
const draggedSecret = ref(null)
const dropTargetId = ref(null)
const isRootDropTargetActive = ref(false)

// Toast notification
const showToast = ref(false)
const toastMessage = ref('')
const toastColor = ref('success')

// Determine if search is active
const isSearchActive = computed(() => 
  props.searchQuery && props.searchQuery.trim().length > 0
)

// Filter folders into private and shared
const privateFolders = computed(() => {
  return props.folders.filter(folder => !folder.is_shared_folder)
})

const sharedFolders = computed(() => {
  return props.folders.filter(folder => folder.is_shared_folder)
})

// Get filtered secrets for search
const filteredSecrets = computed(() => {
  if (!isSearchActive.value) return props.secrets
  
  return props.secrets.filter(secret => props.searchMatchingItems.secrets[secret.id] === true)
})

// Get filtered folders for search
const filteredFolders = computed(() => {
  if (!isSearchActive.value) return props.folders
  
  return props.folders.filter(folder => props.searchMatchingItems.folders[folder.id] === true)
})

// All Secrets Folder: Computed property to get all secrets for the all-secrets folder
const allSecrets = computed(() => {
  // If search is active, return only matching secrets
  if (isSearchActive.value) {
    return props.secrets.filter(secret => props.searchMatchingItems.secrets[secret.id] === true)
  }
  
  // Otherwise, return all secrets
  return props.secrets
})

// Computed: Should All Secrets folder be expanded
const shouldAllSecretsFolderBeExpanded = computed(() => {
  // If search is active, expand to show search results
  if (isSearchActive.value) {
    // Check if any secret matches the search
    const hasMatchingSecrets = props.secrets.some(secret => 
      props.searchMatchingItems.secrets[secret.id] === true
    )
    return hasMatchingSecrets
  }
  
  return allSecretsFolderExpanded.value
})

// Mobile action menu
function openActionMenu() {
  showActionMenu.value = true
}

// Check if an item matches the search
function isSearchMatch(type, id) {
  if (!isSearchActive.value) return false
  
  if (type === 'secret') {
    return props.searchMatchingItems.secrets[id] === true
  } else if (type === 'folder') {
    return props.searchMatchingItems.folders[id] === true
  }
  
  return false
}

// Determine if a folder should be expanded (user toggle or search match)
function shouldFolderBeExpanded(folderId) {
  // If search is active and this folder should be expanded due to search
  if (isSearchActive.value && props.searchExpandedFolders[folderId]) {
    return true
  }
  
  // Otherwise use the manual expand/collapse state
  return expandedFolders.value[folderId]
}

// Automatically expand a folder when it's selected
watch(() => props.selectedItemId, (newId) => {
  if (props.selectedItemType === 'folder' && newId) {
    expandedFolders.value[newId] = true
  }
})

// Watch for search-related folder expansions
watch(() => props.searchExpandedFolders, (newExpandedFolders) => {
  if (isSearchActive.value) {
    // Update our local expanded state to include search matches
    Object.keys(newExpandedFolders).forEach(folderId => {
      if (newExpandedFolders[folderId]) {
        expandedFolders.value[folderId] = true
      }
    })
  }
}, { deep: true })

// Helper: Get secrets belonging to a specific folder
function getFolderSecrets(folderId) {
  // If search is active, filter folder secrets by search matches too
  if (isSearchActive.value) {
    return props.secrets.filter(secret => {
      if (!secret.folder_id) return false
      const secretFolderId = parseInt(secret.folder_id)
      return secretFolderId === parseInt(folderId) && props.searchMatchingItems.secrets[secret.id] === true
    })
  }
  
  // Otherwise get all secrets in this folder
  return props.secrets.filter(secret => {
    if (!secret.folder_id) return false
    return parseInt(secret.folder_id) === parseInt(folderId)
  })
}

// Check if we can show Add Secret/Folder buttons based on current selection
const canAddItems = computed(() => {
  // If "All Secrets" folder is selected, always allow adding
  if (props.selectedItemType === 'all-secrets-folder') {
    return true
  }
  
  // If a folder is selected, check if user has write permission
  if (props.selectedItemType === 'folder' && props.selectedItemId) {
    const folder = props.folders.find(f => f.id.toString() === props.selectedItemId.toString())
    return canWriteToFolder(folder)
  }
  
  return true
})

// Toggle All Secrets folder expand/collapse
function toggleAllSecretsExpand() {
  allSecretsFolderExpanded.value = !allSecretsFolderExpanded.value
}

// Toggle folder expand/collapse
function toggleFolderExpand(folderId, event) {
  if (event) {
    event.stopPropagation()
  }
  expandedFolders.value[folderId] = !expandedFolders.value[folderId]
}

// Select All Secrets folder
function selectAllSecretsFolder() {
  emit('select-all-secrets-folder')
}

// Add a secret to a specific folder
function addSecretToFolder(folderId) {
  emit('add-secret-to-folder', folderId)
}

// Create a new secret (will go into All Secrets folder)
function createSecret() {
  emit('create-secret')
}

// Create a new private folder
function createPrivateFolder() {
  emit('create-folder', { isShared: false })
}

// Helper functions
function getTypeColor(type) {
  switch (type) {
    case 'plaintext': return 'primary'
    case 'image': return 'success'
    default: return 'grey'
  }
}

function getTypeIcon(type) {
  switch (type) {
    case 'plaintext': return 'mdi-text-box'
    case 'image': return 'mdi-file-image'
    default: return 'mdi-file'
  }
}

// Actions
function selectSecret(id, event) {
  if (event) {
    event.preventDefault()
    event.stopPropagation()
  }
  emit('select-secret', id)
}

function selectFolder(id, event) {
  if (event) {
    event.preventDefault()
    event.stopPropagation()
  }
  emit('select-folder', id)
}

function createSecretAndClose() {
  createSecret()
  showActionMenu.value = false
}

function createPrivateFolderAndClose() {
  createPrivateFolder()
  showActionMenu.value = false
}

// Check if user has write permissions for a folder
function canWriteToFolder(folder) {
  // If the user is the owner, they can write
  if (folder && folder.is_owner === true) {
    return true
  }
  
  // Check explicit permissions
  if (folder && 
      folder.permissions && 
      folder.permissions.can_write === true) {
    return true
  }
  
  return false
}

// Drag and drop functionality
function handleDragStart(event, secret) {
  isDragging.value = true
  draggedSecret.value = secret
  
  // Add class to parent element to help with styling
  document.querySelector('.secrets-wrapper').classList.add('isDragging')
  
  // Set data for drag operation
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/plain', JSON.stringify({
    secretId: secret.id,
    currentFolderId: secret.folder_id || null
  }))
  
  // Add a visual drag helper
  const dragIcon = document.createElement('div')
  dragIcon.classList.add('drag-icon')
  dragIcon.textContent = secret.name
  document.body.appendChild(dragIcon)
  event.dataTransfer.setDragImage(dragIcon, 0, 0)
  
  // Remove the drag helper after it's been used
  setTimeout(() => {
    document.body.removeChild(dragIcon)
  }, 0)
}

function handleDragEnd() {
  isDragging.value = false
  draggedSecret.value = null
  dropTargetId.value = null
  isRootDropTargetActive.value = false
  
  // Remove class from parent element
  document.querySelector('.secrets-wrapper').classList.remove('isDragging')
}

function handleFolderDragOver(event, folder) {
  // Only allow drop if we have permission and not dropping on itself
  if (canWriteToFolder(folder)) {
    event.preventDefault()
    dropTargetId.value = folder.id
    isRootDropTargetActive.value = false
    
    // Set the drop effect
    event.dataTransfer.dropEffect = 'move'
  }
}

function handleFolderDragLeave(event, folder) {
  // Check if we're actually leaving the folder element
  // This prevents the leave event from triggering when moving over child elements
  const rect = event.currentTarget.getBoundingClientRect()
  const x = event.clientX
  const y = event.clientY
  
  if (x < rect.left || x >= rect.right || y < rect.top || y >= rect.bottom) {
    dropTargetId.value = null
  }
}

function handleFolderDrop(event, folder) {
  event.preventDefault()
  const data = JSON.parse(event.dataTransfer.getData('text/plain'))
  
  // Reset drag state
  isDragging.value = false
  dropTargetId.value = null
  
  // Get the secret being moved
  const secretId = data.secretId
  const currentFolderId = data.currentFolderId
  const secret = props.secrets.find(s => s.id.toString() === secretId.toString())
  
  if (!secret) {
    showToastMessage('Error: Secret not found', 'error')
    return
  }
  
  // Don't do anything if dropped on the same folder
  if (currentFolderId && currentFolderId.toString() === folder.id.toString()) {
    showToastMessage('Secret is already in this folder', 'info')
    return
  }
  
  // Check permissions based on destination and secret permissions
  let canDrop = true
  let errorMessage = ''
  
  // Check if this is a Shared folder or not owned by current user
  const isUserOwnedRegularFolder = folder.is_owner === true && !folder.is_shared_folder
  
  // For user's own Regular folders, always allow drop (backend will handle proper permissions)
  if (!isUserOwnedRegularFolder) {
    // For Shared folders or other users' folders, check if user has necessary permissions:
    // 1. Check if user has write permission to the folder
    const hasWriteAccessToFolder = canWriteToFolder(folder)
    
    // 2. Check if user has write permission to the secret
    // Allow if user is the owner of the secret OR has explicit write permission
    const isSecretOwner = secret.owner_id && secret.owner_id.toString() === props.userId.toString()
    const hasWriteAccessToSecret = isSecretOwner || (secret.permissions && secret.permissions.can_write === true)
    
    canDrop = hasWriteAccessToFolder && hasWriteAccessToSecret
    
    if (!hasWriteAccessToFolder) {
      errorMessage = 'You need write permission to add secrets to this folder'
    } else if (!hasWriteAccessToSecret) {
      errorMessage = 'You need write permission on this secret to move it to a Shared folder'
    }
  }
  
  if (!canDrop) {
    showToastMessage(errorMessage, 'error')
    return
  }
  
  // Emit the move event
  emit('move-secret', {
    secretId,
    targetFolderId: folder.id,
    secretName: secret.name,
    folderName: folder.name
  })
  
  // Show success toast
  showToastMessage(`Moved "${secret.name}" to "${folder.name}"`, 'success')
  
  // Expand the target folder to show the newly added secret
  expandedFolders.value[folder.id] = true
}

// Toast message helper
function showToastMessage(message, color = 'success') {
  toastMessage.value = message
  toastColor.value = color
  showToast.value = true
}

function removeFromFolder(secret) {
  // Check if user has permission to modify this secret
  const isSecretOwner = secret.owner_id && secret.owner_id.toString() === props.userId.toString();
  const hasWriteAccessToSecret = isSecretOwner || (secret.permissions && secret.permissions.can_write === true);
  
  if (!hasWriteAccessToSecret) {
    showToastMessage('You need write permission on this secret to remove it from the folder', 'error');
    return;
  }
  
  // Emit event to handle removing the secret from its folder
  emit('remove-from-folder', {
    secretId: secret.id,
    secretName: secret.name,
    currentFolderId: secret.folder_id
  });
  
  // Show success toast
  showToastMessage(`Removed "${secret.name}" from folder. Still available in All Secrets.`, 'success');
}
</script>

<style scoped>
/* Secrets and folders list */
.secrets-wrapper {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  padding: 16px;
  overflow: hidden;
  height: 100%;
}

/* Section dividers */
.section-divider {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 24px 0 12px;
  padding: 0 8px;
}

.section-title {
  font-size: 0.8rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.6);
  display: flex;
  align-items: center;
}

.section-actions {
  display: flex;
}

.section-action-btn {
  opacity: 0.7;
}

.section-action-btn:hover {
  opacity: 1;
}

/* System folder (All Secrets) */
.system-folder {
  margin-bottom: 16px;
}

.all-secrets-folder {
  border-left: 2px solid var(--v-accent-base, #8c52ff);
  background: rgba(140, 82, 255, 0.05) !important;
}

.all-secrets-folder:hover {
  background: rgba(140, 82, 255, 0.1) !important;
}

.folder-description {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

/* Shared folder specific styling */
.shared-folder-container {
  margin-bottom: 10px;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.secrets-title {
  font-size: 0.9rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.7);
  display: flex;
  align-items: center;
  margin: 0;
}

.mobile-actions {
  display: none;
}

.secrets-list {
  overflow-y: auto;
  flex-grow: 1;
  margin: 0 -8px;
  scroll-behavior: smooth;
  -webkit-overflow-scrolling: touch;
}

.item-row {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  padding: 12px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.03);
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}

.item-row:hover {
  background: rgba(255, 255, 255, 0.05);
  transform: translateY(-1px);
}

.item-row::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  width: 3px;
  background: transparent;
  transition: background 0.2s ease;
}

.selected-item {
  background: rgba(0, 255, 156, 0.1) !important;
}

.selected-item::before {
  background: #00FF9C;
  box-shadow: 0 0 10px rgba(0, 255, 156, 0.7);
}

/* Search match highlighting */
.search-match {
  background: rgba(0, 136, 255, 0.15) !important;
  animation: pulse-highlight 2s infinite alternate;
}

.search-match::after {
  content: '';
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(0, 136, 255, 0.7);
  box-shadow: 0 0 8px rgba(0, 136, 255, 0.7);
}

.search-match:hover {
  background: rgba(0, 136, 255, 0.2) !important;
}

@keyframes pulse-highlight {
  0% {
    box-shadow: 0 0 5px rgba(0, 136, 255, 0.3);
  }
  100% {
    box-shadow: 0 0 12px rgba(0, 136, 255, 0.6);
  }
}

/* Empty search results */
.search-no-results {
  opacity: 0.8;
}

/* Folder specific styles */
.folder-container {
  margin-bottom: 8px;
}

.folder-header {
  width: 100%;
  display: flex;
  align-items: center;
}

.folder-expand-icon {
  margin-right: 6px;
  width: 24px;
  height: 24px;
  opacity: 0.6;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.folder-expand-icon:hover {
  opacity: 1;
}

.folder-expanded {
  background: rgba(0, 163, 255, 0.05) !important;
  margin-bottom: 0;
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0;
}

.folder-contents {
  margin-left: 20px;
  padding-left: 15px;
  border-left: 1px dashed rgba(0, 163, 255, 0.4);
  margin-bottom: 8px;
}

.folder-child-item {
  background: rgba(255, 255, 255, 0.02);
}

.empty-folder-note {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
  padding: 8px 12px;
  display: flex;
  align-items: center;
}

.add-secret-btn {
  opacity: 0.7;
}

.add-secret-btn:hover {
  opacity: 1;
}

.item-icon {
  min-width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
  opacity: 0.8;
}

.item-details {
  flex-grow: 1;
  min-width: 0;
}

.item-name {
  font-size: 0.95rem;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 4px;
}

.item-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}

.secret-type {
  font-size: 0.7rem;
  padding: 0 8px;
  height: 16px !important;
}

.tag-chip {
  font-size: 0.7rem !important;
  padding: 0 8px;
  height: 16px !important;
  opacity: 0.9;
}

.more-tags {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.6);
  margin-left: 4px;
}

.folder-item .item-icon {
  color: #00A3FF;
}

.secret-tags, .folder-tags {
  display: inline-flex;
  flex-wrap: wrap;
}

/* Item actions */
.item-actions {
  display: flex;
  align-items: center;
  margin-left: 4px;
}

.remove-btn {
  opacity: 0.7;
  transition: opacity 0.2s ease;
}

.remove-btn:hover {
  opacity: 1;
}

/* Loading spinner */
.data-loading {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px 0;
}

.cyber-spinner {
  position: relative;
  width: 40px;
  height: 40px;
}

.spinner-ring {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border: 2px solid transparent;
  border-top-color: #00FF9C;
  border-radius: 50%;
  animation: spin 1.5s linear infinite;
}

.spinner-ring:nth-child(2) {
  border-top-color: #00A3FF;
  animation-delay: 0.5s;
}

.spinner-dot {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 8px;
  height: 8px;
  background: #8C52FF;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  box-shadow: 0 0 10px rgba(140, 82, 255, 0.7);
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Error message */
.error-message {
  margin: 16px;
  padding: 8px 12px;
  background: rgba(255, 59, 48, 0.1);
  border-left: 3px solid #FF3B30;
  color: #FF3B30;
  border-radius: 4px;
  display: flex;
  align-items: center;
}

/* Empty state */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 16px;
  text-align: center;
}

.empty-icon {
  position: relative;
  margin-bottom: 16px;
}

.icon-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 50px;
  height: 50px;
  background: radial-gradient(circle, rgba(0, 255, 156, 0.3) 0%, transparent 70%);
  border-radius: 50%;
  z-index: -1;
}

.empty-title {
  font-size: 1.2rem;
  font-weight: 500;
  margin-bottom: 8px;
  color: rgba(255, 255, 255, 0.9);
}

.empty-subtitle {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 24px;
}

.empty-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
}

.neon-btn {
  position: relative;
  overflow: hidden;
  border-radius: 4px;
  transition: all 0.3s ease;
}

.neon-btn::after {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(0, 255, 156, 0.3) 0%, transparent 70%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.neon-btn:hover::after {
  opacity: 1;
}

/* Drag & Drop Styles */
.item-dragging {
  opacity: 0.6 !important;
  transform: scale(0.98) !important;
  box-shadow: 0 0 15px rgba(0, 255, 156, 0.5) !important;
}

.folder-drop-target {
  position: relative;
  z-index: 5;
}

.folder-drag-over {
  background-color: rgba(0, 163, 255, 0.2) !important;
  border: 2px dashed rgba(0, 163, 255, 0.7) !important;
  transform: translateY(-2px) !important;
  box-shadow: 0 5px 15px rgba(0, 163, 255, 0.3) !important;
}

.root-drop-zone {
  height: 40px;
  margin: 10px 5px;
  border-radius: 6px;
  border: 2px dashed rgba(255, 255, 255, 0.3);
  background: rgba(255, 255, 255, 0.05);
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.global-drop-zone {
  position: sticky;
  top: 0;
  z-index: 100;
  margin-bottom: 15px;
  background: rgba(0, 0, 0, 0.3);
  animation: pulse-glow 1.5s infinite alternate;
}

@keyframes pulse-glow {
  0% {
    box-shadow: 0 0 5px rgba(0, 255, 156, 0.3);
  }
  100% {
    box-shadow: 0 0 15px rgba(0, 255, 156, 0.6);
  }
}

.root-drop-zone.drop-zone-active {
  background: rgba(0, 255, 156, 0.1);
  border-color: rgba(0, 255, 156, 0.5);
  box-shadow: 0 0 10px rgba(0, 255, 156, 0.3);
  transform: scale(1.02);
}

.drop-zone-content {
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
}

/* Custom drag image (created in JS) */
.drag-icon {
  position: absolute;
  top: -1000px;
  background: rgba(0, 0, 0, 0.8);
  border: 1px solid rgba(0, 255, 156, 0.5);
  color: #00FF9C;
  padding: 5px 10px;
  border-radius: 4px;
  font-size: 12px;
  pointer-events: none;
  z-index: 9999;
  max-width: 200px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Force root drop zone to display when dragging */
.secrets-wrapper {
  position: relative;
}

.secrets-wrapper.isDragging .global-drop-zone {
  display: flex !important;
}

/* Responsive styles for mobile devices */
@media (max-width: 768px) {
  .secrets-wrapper {
    padding: 12px;
  }
  
  .mobile-actions {
    display: flex;
  }
  
  .item-row {
    padding: 14px 12px;
    margin-bottom: 6px;
  }
  
  .folder-expand-icon {
    width: 32px;
    height: 32px;
  }
  
  .item-icon {
    min-width: 32px;
    height: 32px;
  }
  
  .folder-contents {
    margin-left: 16px;
    padding-left: 12px;
  }
  
  .item-name {
    font-size: 0.9rem;
  }
  
  .empty-folder-note {
    padding: 10px 12px;
  }
  
  .empty-actions {
    flex-direction: column;
    align-items: center;
  }
  
  .empty-actions .v-btn {
    margin-right: 0 !important;
    margin-bottom: 8px;
    width: 100%;
    max-width: 200px;
  }
  
  /* Mobile menu fixes */
  :deep(.v-overlay) {
    z-index: 9999 !important;
    backdrop-filter: none !important;
    -webkit-backdrop-filter: none !important;
  }
  
  :deep(.mobile-action-menu) {
    backdrop-filter: none !important;
    -webkit-backdrop-filter: none !important;
    position: absolute !important;
  }
  
  :deep(.mobile-menu-list) {
    background: rgba(15, 22, 32, 0.95) !important;
    border: 1px solid rgba(0, 255, 156, 0.3) !important;
    box-shadow: 0 0 15px rgba(0, 255, 156, 0.4) !important;
  }
  
  :deep(.menu-item) {
    min-height: 48px !important;
    padding: 0 16px !important;
  }
}

@media (max-width: 480px) {
  .secrets-wrapper {
    padding: 10px;
  }
  
  .item-row {
    padding: 12px 10px;
  }
  
  .item-name {
    font-size: 0.85rem;
  }
  
  .tag-chip, .secret-type {
    font-size: 0.65rem !important;
    height: 14px !important;
    padding: 0 6px;
  }
}
</style> 