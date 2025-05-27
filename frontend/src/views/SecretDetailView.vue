<template>
  <v-container fluid class="container-custom">
    <div v-if="secretsStore.loading" class="d-flex justify-center py-8">
      <v-progress-circular indeterminate color="primary" size="64"></v-progress-circular>
    </div>

    <v-alert
      v-if="secretsStore.error"
      type="error"
      variant="tonal"
      class="mb-4"
    >
      {{ secretsStore.error }}
    </v-alert>

    <template v-if="secret && !secretsStore.loading">
      <div class="d-flex flex-wrap justify-space-between align-center mb-4">
        <div>
          <div class="d-flex align-center">
            <v-btn 
              icon 
              variant="text" 
              color="primary"
              :to="{ name: 'secrets' }"
              class="mr-2"
            >
              <v-icon>mdi-arrow-left</v-icon>
            </v-btn>
            <h1 class="text-h4">{{ secret.name }}</h1>
          </div>
          <div class="ml-12 mt-1">
            <v-chip
              :color="getTypeColor(secret.type)"
              size="small"
              class="mr-2"
            >
              {{ secret.type }}
            </v-chip>
            <span class="text-caption">
              Last updated: {{ formatDate(secret.last_modified) }}
            </span>
          </div>
        </div>
        
        <div>
          <v-btn 
            color="warning" 
            variant="outlined"
            class="mr-2"
            @click="editSecret"
          >
            <v-icon left>mdi-pencil</v-icon>
            Edit
          </v-btn>
          <v-btn 
            color="error" 
            variant="outlined"
            @click="confirmDelete"
          >
            <v-icon left>mdi-delete</v-icon>
            Delete
          </v-btn>
        </div>
      </div>

      <!-- File Secret Display -->
      <v-card v-if="isFileSecret" class="mb-4 file-card">
        <v-card-title class="text-h6">
          <v-icon :color="getTypeColor(secret.type)" class="mr-2">{{ getTypeIcon(secret.type) }}</v-icon>
          {{ getFileTypeLabel() }}
          <v-spacer></v-spacer>
          <v-btn
            v-if="!isImageType"
            color="primary"
            variant="text"
            @click="downloadFile"
            :loading="downloading"
            :disabled="downloading"
          >
            <v-icon start>mdi-download</v-icon>
            Download
          </v-btn>
        </v-card-title>
        
        <v-card-text class="file-card-content">
          <div v-if="loading" class="d-flex flex-column align-center py-4">
            <v-progress-circular indeterminate color="primary"></v-progress-circular>
            <div class="mt-2">Loading file preview...</div>
          </div>
          
          <div v-else-if="fileError" class="d-flex flex-column align-center py-4 text-error">
            <v-icon color="error" size="large">mdi-alert-circle</v-icon>
            <div class="mt-2">{{ fileError }}</div>
          </div>
          
          <div v-else-if="filePreview" class="file-preview-container">
            <img 
              v-if="isImageType"
              :src="filePreview" 
              class="image-preview" 
              alt="Image preview"
            />
            <div v-else class="text-center py-4">
              <v-icon size="large" :color="getTypeColor(secret.type)">
                {{ getTypeIcon(secret.type) }}
              </v-icon>
              <div class="mt-2">
                Original filename: {{ secret.original_filename || 'Unknown' }}
              </div>
              <div v-if="secret.file_size" class="mt-1">
                Size: {{ formatFileSize(secret.file_size) }}
              </div>
            </div>
          </div>
          
          <div v-if="secret.description" class="description-container mt-4">
            <div class="font-weight-bold mb-2">Description:</div>
            <div>{{ secret.description }}</div>
          </div>
        </v-card-text>
      </v-card>

      <!-- Plaintext Secret Display -->
      <v-card v-else class="mb-4">
        <v-card-title class="text-h6">
          <v-icon color="primary" class="mr-2">mdi-text-box</v-icon>
          Secret Value
        </v-card-title>
        
        <v-card-text>
          <div class="position-relative">
            <v-textarea
              v-model="secret.value"
              readonly
              filled
              auto-grow
              hide-details
              class="secret-content mb-2"
              :class="{ 'blur-content': !showSecret }"
            ></v-textarea>
            
            <div class="secret-actions">
              <v-btn
                :icon="showSecret ? 'mdi-eye-off' : 'mdi-eye'"
                variant="text"
                color="primary"
                @click="showSecret = !showSecret"
                class="mr-2"
              ></v-btn>
              
              <v-btn
                icon="mdi-content-copy"
                variant="text"
                color="primary"
                @click="copyToClipboard(secret.value)"
              ></v-btn>
            </div>
          </div>
          
          <v-alert
            v-if="copySuccess"
            type="success"
            variant="tonal"
            density="compact"
            class="mt-2"
          >
            Secret copied to clipboard!
          </v-alert>
          
          <div v-if="secret.description" class="description-container mt-4">
            <div class="font-weight-bold mb-2">Description:</div>
            <div>{{ secret.description }}</div>
          </div>
        </v-card-text>
      </v-card>

      <v-card>
        <v-card-title class="text-h6">
          <v-icon color="info" class="mr-2">mdi-information</v-icon>
          Secret Information
        </v-card-title>
        
        <v-card-text>
          <v-list>
            <v-list-item>
              <template v-slot:prepend>
                <v-icon color="primary">mdi-tag</v-icon>
              </template>
              <v-list-item-title>ID</v-list-item-title>
              <v-list-item-subtitle>{{ secret.id }}</v-list-item-subtitle>
            </v-list-item>
            
            <v-list-item>
              <template v-slot:prepend>
                <v-icon color="primary">mdi-account</v-icon>
              </template>
              <v-list-item-title>Owner</v-list-item-title>
              <v-list-item-subtitle>ID: {{ secret.owner_id }}</v-list-item-subtitle>
            </v-list-item>
            
            <v-list-item>
              <template v-slot:prepend>
                <v-icon color="primary">mdi-calendar</v-icon>
              </template>
              <v-list-item-title>Created</v-list-item-title>
              <v-list-item-subtitle>{{ formatDate(secret.created_time) }}</v-list-item-subtitle>
            </v-list-item>
            
            <v-list-item v-if="secret.tags && secret.tags.length > 0">
              <template v-slot:prepend>
                <v-icon color="primary">mdi-tag-multiple</v-icon>
              </template>
              <v-list-item-title>Tags</v-list-item-title>
              <v-list-item-subtitle>
                <v-chip
                  v-for="tag in secret.tags"
                  :key="tag"
                  size="x-small"
                  color="secondary"
                  class="mr-1 mb-1"
                >
                  {{ tag }}
                </v-chip>
              </v-list-item-subtitle>
            </v-list-item>
            
            <v-list-item v-if="secret.folder_id">
              <template v-slot:prepend>
                <v-icon color="primary">{{ secret.folder_is_shared ? 'mdi-folder-multiple' : 'mdi-folder-lock' }}</v-icon>
              </template>
              <v-list-item-title>Folder</v-list-item-title>
              <v-list-item-subtitle>{{ getFolderName(secret.folder_id) }}</v-list-item-subtitle>
            </v-list-item>
          </v-list>
        </v-card-text>
      </v-card>
    </template>

    <!-- Edit Dialog -->
    <SecretDialog
      v-model="showEditDialog"
      :is-edit="true"
      :secret="secret"
      :loading="secretsStore.loading"
      :folder-options="folderOptions"
      :suggested-tags="suggestedTags"
      @save="updateSecret"
      @delete="deleteSecret"
    />

    <!-- Delete Confirmation Dialog -->
    <DeleteDialog
      v-model="showDeleteDialog"
      title="Delete Secret"
      :text="`Are you sure you want to delete the secret '${secret?.name}'? This action cannot be undone.`"
      @confirm="deleteSecret"
    />
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSecretsStore } from '@/stores/secrets'
import { useAuthStore } from '@/stores/auth'
import SecretDialog from '@/dashboard/dialogs/SecretDialog.vue'
import dayjs from 'dayjs'
import DeleteDialog from '@/dashboard/dialogs/DeleteDialog.vue'

// Get route and store references
const route = useRoute()
const router = useRouter()
const secretsStore = useSecretsStore()
const authStore = useAuthStore()

// UI state
const showSecret = ref(false)
const copySuccess = ref(false)
const loading = ref(false)
const fileError = ref(null)
const filePreview = ref(null)
const downloading = ref(false)
const showEditDialog = ref(false)
const showDeleteDialog = ref(false)

// Fetch secret by ID from route params
const secretId = computed(() => route.params.id)

onMounted(async () => {
  if (secretId.value) {
    await secretsStore.fetchSecret(secretId.value)
    
    // If this is a file secret, fetch the file content
    if (isFileSecret.value) {
      await loadFilePreview()
    }
  }
})

// Watch for changes to fetch the secret again if needed
watch(secretId, async (newId) => {
  if (newId) {
    await secretsStore.fetchSecret(newId)
    
    // If this is a file secret, fetch the file content
    if (isFileSecret.value) {
      await loadFilePreview()
    }
  }
})

// Get the secret from the store
const secret = computed(() => secretsStore.currentSecret)

// Determine if the secret is a file-based secret
const isFileSecret = computed(() => {
  return secret.value && ['image'].includes(secret.value.type)
})

// Determine if the secret is an image
const isImageType = computed(() => {
  return secret.value && secret.value.type === 'image'
})

// Function to format dates
const formatDate = (dateString) => {
  if (!dateString) return 'Unknown'
  return dayjs(dateString).format('MMMM D, YYYY h:mm A')
}

// Format file size in human-readable format
const formatFileSize = (bytes) => {
  if (!bytes) return 'Unknown'
  
  const units = ['B', 'KB', 'MB', 'GB']
  let size = bytes
  let unitIndex = 0
  
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  
  return `${size.toFixed(1)} ${units[unitIndex]}`
}

// Get color based on secret type
const getTypeColor = (type) => {
  switch(type) {
    case 'plaintext': return 'blue'
    case 'image': return 'green'
    default: return 'grey'
  }
}

// Get icon based on secret type
const getTypeIcon = (type) => {
  switch(type) {
    case 'plaintext': return 'mdi-text-box'
    case 'image': return 'mdi-file-image'
    default: return 'mdi-file'
  }
}

// Get file type label
const getFileTypeLabel = () => {
  if (!secret.value) return 'File'
  
  switch(secret.value.type) {
    case 'image': return 'Image File'
    default: return 'File'
  }
}

// Load file preview
const loadFilePreview = async () => {
  if (!secret.value || !secret.value.id) return
  
  loading.value = true
  fileError.value = null
  filePreview.value = null
  
  try {
    const response = await secretsStore.fetchSecretFile(secret.value.id)
    
    if (response && response.data) {
      // For images, create a blob URL
      if (isImageType.value) {
        const blob = new Blob([response.data], { type: secret.value.file_mime_type })
        filePreview.value = URL.createObjectURL(blob)
      }
    } else {
      fileError.value = 'Could not load file preview'
    }
  } catch (error) {
    console.error('Error loading file preview:', error)
    fileError.value = error.message || 'Failed to load file preview'
  } finally {
    loading.value = false
  }
}

// Download file
const downloadFile = async () => {
  if (!secret.value || !secret.value.id) return
  
  downloading.value = true
  
  try {
    await secretsStore.downloadFileSecret(secret.value.id)
  } catch (error) {
    console.error('Error downloading file:', error)
  } finally {
    downloading.value = false
  }
}

// Copy to clipboard
const copyToClipboard = async (text) => {
  if (!text) return;
  
  // Use modern clipboard API with fallback
  if (navigator.clipboard && navigator.clipboard.writeText) {
    try {
      await navigator.clipboard.writeText(text);
      copySuccess.value = true;
      setTimeout(() => {
        copySuccess.value = false;
      }, 3000);
    } catch (error) {
      console.error('Clipboard API error:', error);
      fallbackCopyToClipboard(text);
    }
  } else {
    // Fallback for browsers without clipboard API
    fallbackCopyToClipboard(text);
  }
}

// Fallback copy method using textarea
const fallbackCopyToClipboard = (text) => {
  try {
    // Create temporary textarea
    const textArea = document.createElement('textarea');
    textArea.value = text;
    
    // Make it invisible but part of the document
    textArea.style.position = 'fixed';
    textArea.style.opacity = '0';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    
    // Select and copy
    textArea.focus();
    textArea.select();
    const successful = document.execCommand('copy');
    
    // Remove the temporary element
    document.body.removeChild(textArea);
    
    if (successful) {
      copySuccess.value = true;
      setTimeout(() => {
        copySuccess.value = false;
      }, 3000);
    } else {
      console.error('Fallback clipboard copy failed');
    }
  } catch (err) {
    console.error('Fallback clipboard error:', err);
  }
}

// Open edit dialog
const editSecret = () => {
  showEditDialog.value = true
}

// Handle secret update
const handleSecretUpdated = (updatedSecret) => {
  secretsStore.setCurrentSecret(updatedSecret)
  showEditDialog.value = false
  
  // Reload file preview if this is a file secret
  if (isFileSecret.value) {
    loadFilePreview()
  }
}

// Confirm delete
const confirmDelete = () => {
  showDeleteDialog.value = true
}

// Handle delete
const handleDelete = async () => {
  const deleted = await secretsStore.deleteSecret(secret.value.id)
  if (deleted) {
    // Redirect back to secrets list
    router.push({ name: 'secrets' })
  }
}

// Computed properties
const folderOptions = computed(() => {
  if (!secretsStore.folders) return []
  return secretsStore.folders.map(folder => ({
    title: folder.name,
    value: folder.id,
    is_shared: folder.is_shared_folder === true
  }))
})

const suggestedTags = computed(() => {
  // Get all unique tags from all secrets
  if (!secretsStore.secrets) return []
  
  const tagSet = new Set()
  secretsStore.secrets.forEach(s => {
    if (s.tags && Array.isArray(s.tags)) {
      s.tags.forEach(tag => tagSet.add(tag))
    }
  })
  
  return Array.from(tagSet)
})

// Update secret
const updateSecret = async (secretData) => {
  try {
    // Handle form data for file uploads
    if (secretData.file) {
      const formData = new FormData()
      formData.append('file', secretData.file)
      formData.append('secret_name', secretData.name)
      
      if (secretData.description) {
        formData.append('description', secretData.description)
      }
      
      if (secretData.tags && secretData.tags.length > 0) {
        formData.append('tags', JSON.stringify(secretData.tags))
      }
      
      if (secretData.folder_id) {
        formData.append('folder_id', secretData.folder_id)
      }
      
      await secretsStore.updateSecret(secret.value.id, formData, true)
    } else {
      // Regular update (no file)
      await secretsStore.updateSecret(secret.value.id, {
        secret_name: secretData.name,
        description: secretData.description,
        tags: secretData.tags,
        folder_id: secretData.folder_id,
        value: secretData.value
      })
    }
    
    // Refresh the secret details
    await secretsStore.fetchSecret(secret.value.id)
    if (isFileSecret.value) {
      await loadFilePreview()
    }
  } catch (error) {
    console.error('Error updating secret:', error)
  }
}

// Delete secret
const deleteSecret = async () => {
  try {
    await handleDelete()
  } catch (error) {
    console.error('Error deleting secret:', error)
  }
}

// Watch for ID changes
watch(() => route.params.id, (newId, oldId) => {
  if (newId && newId !== oldId) {
    secretsStore.fetchSecret(newId)
    if (isFileSecret.value) {
      loadFilePreview()
    }
  }
})

// Lifecycle hooks
onMounted(() => {
  // Fetch folders for the dropdown
  secretsStore.fetchFolders()
  
  // Fetch the initial secret
  loadFilePreview()
})

// Clean up object URLs when component is unmounted
onBeforeUnmount(() => {
  if (filePreview.value) {
    URL.revokeObjectURL(filePreview.value)
  }
})

// Get folder name from folder ID
function getFolderName(folderId) {
  if (!folderId) return 'None';
  
  const folder = secretsStore.folderById(folderId);
  if (folder) {
    return folder.name;
  }
  
  return `ID: ${folderId}`;
}

// Computed to check if the secret's folder is shared
const isSecretFolderShared = computed(() => {
  if (!secret.value || !secret.value.folder_id) return false;
  
  const folder = secretsStore.folderById(secret.value.folder_id);
  return folder && folder.is_shared_folder === true;
});

// Add folder_is_shared to the secret object for the template
watch(() => secret.value, (newSecret) => {
  if (newSecret && newSecret.folder_id) {
    newSecret.folder_is_shared = isSecretFolderShared.value;
  }
}, { immediate: true, deep: true });
</script>

<style scoped>
.container-custom {
  max-width: 1000px;
  margin: 0 auto;
}

.secret-content {
  font-family: monospace;
  background-color: rgba(0, 0, 0, 0.05);
}

.blur-content {
  filter: blur(8px);
  user-select: none;
}

.blur-content:hover {
  filter: blur(6px);
}

.secret-actions {
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 2;
  background-color: rgba(0, 0, 0, 0.4);
  border-radius: 8px;
  padding: 4px;
}

.image-preview {
  max-width: 100%;
  max-height: 600px;
  object-fit: contain;
  margin: 0 auto;
  display: block;
  border-radius: 4px;
}

.file-card-content {
  min-height: 300px;
}

.description-container {
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding-top: 16px;
}

.file-preview-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}
</style> 