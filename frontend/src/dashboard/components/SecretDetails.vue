<template>
  <div class="secret-details-wrapper">
    <div class="secret-header">
      <v-btn
        v-if="isMobile"
        icon="mdi-arrow-left"
        variant="text"
        color="primary"
        class="mobile-back-btn mr-2"
        @click="$emit('back')"
        size="small"
      >
        <v-icon>mdi-arrow-left</v-icon>
      </v-btn>

      <div class="secret-title-row">
        <div class="secret-title">
          <v-icon
            :color="getTypeColor(secret.type)"
            size="small"
            class="mr-2"
          >{{ getTypeIcon(secret.type) }}</v-icon>
          <h2>{{ secret.name }}</h2>
        </div>

        <div class="action-buttons">
          <v-btn
            v-if="hasEditPermission"
            icon="mdi-pencil"
            variant="text"
            color="primary"
            @click="$emit('edit')"
            size="small"
            class="action-btn"
          >
            <v-icon>mdi-pencil</v-icon>
          </v-btn>
          <v-btn
            v-if="hasSharePermission"
            icon="mdi-share-variant"
            variant="text"
            color="secondary"
            @click="$emit('share')"
            size="small"
            class="action-btn"
          >
            <v-icon>mdi-share-variant</v-icon>
          </v-btn>
        </div>
      </div>
    </div>

    <div class="secret-meta">
      <v-chip
        :color="getTypeColor(secret.type)"
        size="small"
        label
        class="secret-type mr-2"
      >
        {{ secret.type }}
      </v-chip>

      <div v-if="secret.folder_id" class="folder-link">
        <v-icon size="small" :color="isFolderShared ? 'success' : 'primary'" class="mr-1">
          {{ isFolderShared ? 'mdi-folder-multiple' : 'mdi-folder-lock' }}
        </v-icon>
        <a
          href="#"
          @click.prevent="$emit('navigate-to-folder', secret.folder_id)"
          class="folder-name"
        >
          {{ folderName }}
        </a>
      </div>
    </div>

    <div class="secret-value-section">
      <div class="section-header">
        <h3>{{ secret.type === 'image' ? 'Image' : 'Secret Value' }}</h3>
        <div class="value-actions">
          <template v-if="secret.type === 'plaintext'">
            <v-btn
              icon="mdi-content-copy"
              variant="text"
              color="primary"
              size="small"
              @click="copyValue"
              class="copy-btn"
            >
              <v-icon>mdi-content-copy</v-icon>
            </v-btn>
            <v-btn
              icon
              variant="text"
              color="primary"
              size="small"
              @click="toggleMask"
            >
              <v-icon>{{ masked ? 'mdi-eye' : 'mdi-eye-off' }}</v-icon>
            </v-btn>
          </template>

          <template v-else-if="secret.type === 'image'">
            <v-btn
              icon
              variant="text"
              color="primary"
              size="small"
              @click="toggleMask"
            >
              <v-icon>{{ masked ? 'mdi-eye' : 'mdi-eye-off' }}</v-icon>
            </v-btn>

            <v-btn
              v-if="imageSource && !masked"
              icon="mdi-fullscreen"
              variant="text"
              color="primary"
              size="small"
              @click="viewFullscreen"
              class="fullscreen-btn"
            >
              <v-icon>mdi-fullscreen</v-icon>
            </v-btn>
          </template>
        </div>
      </div>

      <div class="secret-value">
        <template v-if="secret.type === 'plaintext'">
          <pre v-if="!masked" class="value-content">{{ secret.value }}</pre>
          <pre v-else class="value-content masked">{{ maskedValue }}</pre>
        </template>

        <template v-else-if="secret.type === 'image'">
          <div class="image-container">
            <div v-if="downloading" class="image-loading">
              <v-progress-circular indeterminate color="primary"></v-progress-circular>
              <div class="mt-2">Loading image...</div>
            </div>

            <img
              v-else-if="imageSource && !masked"
              :src="imageSource"
              class="image-preview"
              alt="Image preview"
              @error="handleImageError"
            />

            <div v-else-if="imageSource && masked" class="masked-image">
              <div class="image-mask">
                <v-icon size="large" color="primary">mdi-file-image</v-icon>
                <p class="masked-image-text">Image content hidden</p>
                <p class="masked-image-hint">Click the eye icon to reveal</p>
              </div>
            </div>

            <div v-else class="image-placeholder">
              <v-icon color="warning" size="large">mdi-image-off</v-icon>
              <div class="mt-2">{{ imageError || 'Image not available' }}</div>
              <v-btn
                v-if="imageError"
                color="primary"
                size="small"
                class="mt-3"
                @click="retryLoadImage"
              >
                Retry
              </v-btn>
            </div>

            <div v-if="imageSource && !masked" class="image-actions">
              <v-btn
                color="primary"
                size="small"
                @click="downloadImage"
                class="download-btn"
                prepend-icon="mdi-download"
              >
                DOWNLOAD
              </v-btn>
            </div>
          </div>
        </template>

        </div>
    </div>

    <div v-if="secret.description" class="secret-description-section">
      <h3>Description</h3>
      <p class="description-content">{{ secret.description }}</p>
    </div>

    <div class="secret-tags-section" v-if="tags.length > 0">
      <h3>Tags</h3>
      <div class="tags-container">
        <v-chip
          v-for="tag in tags"
          :key="tag"
          size="small"
          label
          class="mr-2 mb-2"
          color="secondary"
        >
          {{ tag }}
        </v-chip>
      </div>
    </div>

    <div class="secret-footer">
      <div class="metadata">
        <div class="meta-item" v-if="secret.created_at">
          <span class="meta-label">Created:</span>
          <span class="meta-value">{{ formatDate(secret.created_at) }}</span>
        </div>
        <div class="meta-item" v-if="secret.updated_at">
          <span class="meta-label">Last Updated:</span>
          <span class="meta-value">{{ formatDate(secret.updated_at) }}</span>
        </div>
      </div>
    </div>

    <div class="copy-toast" :class="{ 'show': showCopyToast }">
      <v-icon color="success" size="small">mdi-check-circle</v-icon>
      Copied to clipboard!
    </div>

    <div v-if="isFullscreen && imageSource && !masked" class="fullscreen-viewer" @click="exitFullscreen">
      <div class="fullscreen-header">
        <v-btn
          color="white"
          size="small"
          @click.stop="exitFullscreen"
          class="close-btn"
          prepend-icon="mdi-close"
        >
          CLOSE
        </v-btn>

        <v-btn
          color="white"
          size="small"
          @click.stop="downloadImage"
          class="download-btn"
          prepend-icon="mdi-download"
        >
          DOWNLOAD
        </v-btn>
      </div>

      <img
        :src="imageSource"
        class="fullscreen-image"
        alt="Fullscreen image"
        @click.stop
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useSecretsStore } from '@/stores/secrets'
import axios from 'axios'

const props = defineProps({
  secret: {
    type: Object,
    required: true
  },
  isMobile: {
    type: Boolean,
    default: false
  },
  isAdmin: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['edit', 'delete', 'share', 'navigate-to-folder', 'back'])

const secretsStore = useSecretsStore()
const masked = ref(true)
const tags = ref([])
const showCopyToast = ref(false)
const downloading = ref(false)
const imageSource = ref(null)
const isFullscreen = ref(false)
const imageError = ref(null)
let currentBlobUrl = null

// Find folder name if the secret is in a folder
const folderName = computed(() => {
  if (!props.secret.folder_id) return ''

  const folder = secretsStore.folderById(props.secret.folder_id)
  return folder ? folder.name : ''
})

// Check if the folder is a shared folder
const isFolderShared = computed(() => {
  if (!props.secret.folder_id) return false

  const folder = secretsStore.folderById(props.secret.folder_id)
  return folder ? folder.is_shared_folder === true : false
})

// Masked value for secure display
const maskedValue = computed(() => {
  if (!props.secret.value) return ''
  return '•'.repeat(Math.min(props.secret.value.length, 30))
})

// Add these computed properties
const hasEditPermission = computed(() => {
  // FIRST CHECK: Direct owner check - most reliable
  if (props.secret && props.secret.owner_id) {
    const ownerId = typeof props.secret.owner_id === 'string'
      ? props.secret.owner_id
      : props.secret.owner_id.toString();

    const userId = typeof secretsStore.userId === 'string'
      ? secretsStore.userId
      : secretsStore.userId?.toString();

    if (ownerId === userId) {
      return true;
    }
  }

  // SECOND CHECK: Check explicit permissions in permissions object
  if (props.secret &&
      props.secret.permissions &&
      props.secret.permissions.can_write === true) {
    return true;
  }

  // THIRD CHECK: If permissions say user is owner
  if (props.secret &&
      props.secret.permissions &&
      props.secret.permissions.is_owner === true) {
    return true;
  }

  return false;
});

const hasSharePermission = computed(() => {
  // FIRST CHECK: Direct owner check - most reliable
  if (props.secret && props.secret.owner_id) {
    const ownerId = typeof props.secret.owner_id === 'string'
      ? props.secret.owner_id
      : props.secret.owner_id.toString();

    const userId = typeof secretsStore.userId === 'string'
      ? secretsStore.userId
      : secretsStore.userId?.toString();

    if (ownerId === userId) {
      return true;
    }
  }

  // SECOND CHECK: Check explicit permissions in permissions object
  if (props.secret &&
      props.secret.permissions &&
      props.secret.permissions.can_write === true) { // Note: can_write often implies can_share in simpler systems
    return true;
  }

  // THIRD CHECK: If permissions say user is owner
  if (props.secret &&
      props.secret.permissions &&
      props.secret.permissions.is_owner === true) {
    return true;
  }
  // FOURTH CHECK: Explicit can_share permission
   if (props.secret &&
      props.secret.permissions &&
      props.secret.permissions.can_share === true) {
    return true;
  }

  return false;
});

// Add this computed property
const hasDeletePermission = computed(() => {
  // If the user is the owner, they can delete
  if (props.secret && props.secret.owner_id) {
     const ownerId = typeof props.secret.owner_id === 'string'
      ? props.secret.owner_id
      : props.secret.owner_id.toString();
    const userId = typeof secretsStore.userId === 'string'
      ? secretsStore.userId
      : secretsStore.userId?.toString();
    if (ownerId === userId) {
      return true;
    }
  }

  // Check explicit permissions
  if (props.secret &&
      props.secret.permissions &&
      props.secret.permissions.can_delete === true) {
    return true;
  }
 // Check if permissions object says is_owner (as a fallback)
  if (props.secret &&
      props.secret.permissions &&
      props.secret.permissions.is_owner === true) {
    return true;
  }

  // No delete permission
  return false;
});

// Update tags
watch(() => props.secret, (newSecret) => {
  // Reset states
  masked.value = true
  imageSource.value = null
  imageError.value = null

  // Clean up any previous blob URLs
  cleanupBlobUrls()

  // Update tags
  if (newSecret && newSecret.tags) {
    tags.value = [...newSecret.tags]
  } else {
    tags.value = []
  }

  // For image type secrets, load the image
  if (newSecret && newSecret.type === 'image') {
    loadImagePreview(newSecret.id)
  }
}, { immediate: true })

// Toggle masked value
function toggleMask() {
  masked.value = !masked.value
}

// Copy to clipboard
function copyValue() {
  if (!props.secret || !props.secret.value) return;

  // Use modern clipboard API with fallback
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(props.secret.value)
      .then(() => {
        showCopyToast.value = true;
        setTimeout(() => {
          showCopyToast.value = false;
        }, 2000);
      })
      .catch(error => {
        fallbackCopyToClipboard(props.secret.value);
      });
  } else {
    // Fallback for browsers without clipboard API
    fallbackCopyToClipboard(props.secret.value);
  }
}

// Fallback copy method using textarea
function fallbackCopyToClipboard(text) {
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
      showCopyToast.value = true;
      setTimeout(() => {
        showCopyToast.value = false;
      }, 2000);
    }
  } catch (err) {
    // Error already handled by removing console.error
  }
}

// Format dates
function formatDate(dateString) {
  const date = new Date(dateString)
  return date.toLocaleString()
}

// Icon and color mapping by secret type
function getTypeIcon(type) {
  switch (type) {
    case 'plaintext': return 'mdi-text-box'
    case 'image': return 'mdi-file-image'
    default: return 'mdi-file'
  }
}

function getTypeColor(type) {
  switch (type) {
    case 'plaintext': return 'primary'
    case 'image': return 'success'
    default: return 'grey'
  }
}

// Helper function to load image preview
async function loadImagePreview(secretId) {
  if (!secretId) return;

  try {
    downloading.value = true;

    const response = await secretsStore.fetchSecretFile(secretId);

    // Create a blob URL for the image
    const blob = new Blob([response.data], { type: response.headers['content-type'] || 'image/png' });
    const url = URL.createObjectURL(blob);

    // Clean up any previous blob URL
    cleanupBlobUrls();

    // Store the new URL
    currentBlobUrl = url;
    imageSource.value = url;
  } catch (error) {
    imageSource.value = null;
    imageError.value = 'Failed to load image. Please try again later.'
  } finally {
    downloading.value = false;
  }
}

// Function to clean up blob URLs
function cleanupBlobUrls() {
  if (currentBlobUrl) {
    URL.revokeObjectURL(currentBlobUrl);
    currentBlobUrl = null;
  }
}

// Handle image error
function handleImageError() {
  imageSource.value = null;
  imageError.value = 'Failed to load image. Please try again later.'
}

// Function to download the image
function downloadImage() {
  if (!props.secret || !props.secret.id || !imageSource.value) return;

  try {
    // For already loaded images, we can just use the blob URL
    if (imageSource.value.startsWith('blob:')) {
      const link = document.createElement('a');
      link.href = imageSource.value;

      // Set the download filename
      const filename = props.secret.name || `image-secret-${props.secret.id}`;
      link.download = filename.endsWith('.png') ? filename : `${filename}.png`; // Basic extension handling

      // Append to body, click and remove
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } else {
      // For other cases, fetch the file again
      downloading.value = true;

      secretsStore.downloadFileSecret(props.secret.id)
        .finally(() => {
          downloading.value = false;
        });
    }
  } catch (error) {
    downloading.value = false;
  }
}

// Function to view image in fullscreen mode
function viewFullscreen() {
  if (!imageSource.value || masked.value) return;
  isFullscreen.value = true;
}

// Function to exit fullscreen mode
function exitFullscreen() {
  isFullscreen.value = false;
}

// Function to retry loading the image
function retryLoadImage() {
  imageError.value = null; // Clear previous error
  loadImagePreview(props.secret.id)
}

// Add the onBeforeUnmount hook
onBeforeUnmount(() => {
  // Clean up blob URLs when component is destroyed
  cleanupBlobUrls();
});
</script>

<style scoped>
.secret-details-wrapper {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 24px;
  position: relative;
  overflow-y: auto;
}

/* Mobile styles */
@media (max-width: 767px) {
  .secret-details-wrapper {
    padding: 16px;
  }
}

/* Header styling */
.secret-header {
  margin-bottom: 20px;
}

.mobile-back-btn {
  margin-bottom: 8px;
}

.secret-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.secret-title {
  display: flex;
  align-items: center;
}

.secret-title h2 {
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.action-buttons {
  display: flex;
  gap: 4px;
}

.action-btn {
  opacity: 0.7;
  transition: opacity 0.2s ease;
}

.action-btn:hover {
  opacity: 1;
}

/* Meta section */
.secret-meta {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.secret-type {
  font-weight: 500;
}

.folder-link {
  display: flex;
  align-items: center;
  font-size: 0.9rem;
}

.folder-name {
  color: #00A3FF;
  text-decoration: none;
  transition: color 0.2s ease;
}

.folder-name:hover {
  color: #00E6CC;
  text-decoration: underline;
}

/* Value section */
.secret-value-section {
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 24px;
  border: 1px solid rgba(0, 255, 156, 0.1);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.section-header h3 {
  font-size: 1.1rem;
  font-weight: 500;
  margin: 0;
  color: rgba(255, 255, 255, 0.9);
}

.value-actions {
  display: flex;
  gap: 4px;
}

.secret-value {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
  padding: 12px;
  position: relative;
  min-height: 60px;
  overflow: hidden;
}

/* Description section */
.secret-description-section {
  margin-bottom: 24px;
}

.secret-description-section h3 {
  font-size: 1.1rem;
  font-weight: 500;
  margin: 0 0 8px 0;
  color: rgba(255, 255, 255, 0.9);
}

.description-content {
  white-space: pre-wrap;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.5;
}

/* Tags section */
.secret-tags-section {
  margin-bottom: 24px;
}

.secret-tags-section h3 {
  font-size: 1.1rem;
  font-weight: 500;
  margin: 0 0 8px 0;
  color: rgba(255, 255, 255, 0.9);
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
}

/* Footer with metadata */
.secret-footer {
  margin-top: auto;
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.metadata {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
}

.meta-item {
  margin-bottom: 4px;
}

.meta-label {
  margin-right: 4px;
  font-weight: 500;
}

/* Copy toast */
.copy-toast {
  position: fixed;
  bottom: -50px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.8);
  padding: 8px 16px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: bottom 0.3s ease;
  z-index: 1000;
}

.copy-toast.show {
  bottom: 20px;
}

/* Mobile optimization */
@media (max-width: 767px) {
  .secret-title h2 {
    font-size: 1.3rem;
  }

  .action-buttons {
    gap: 1px;
  }

  .secret-value-section {
    padding: 12px;
  }

  .metadata {
    flex-direction: column;
  }

  .meta-item {
    margin-bottom: 8px;
  }

  .image-container {
    max-height: 60vh;
    overflow: auto;
  }

  .image-preview {
    max-height: 55vh;
  }

  .fullscreen-image {
    max-width: 95vw;
    max-height: 80vh;
  }
}

.image-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 20px;
  color: rgba(255, 255, 255, 0.7);
}

.image-preview {
  max-width: 100%;
  max-height: 500px;
  border-radius: 4px;
}

.image-container {
  position: relative;
}

.image-loading {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.image-actions {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  gap: 4px;
}

.download-btn {
  opacity: 0.7;
  transition: opacity 0.2s ease;
}

.download-btn:hover {
  opacity: 1;
}

.fullscreen-viewer {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.9);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.fullscreen-header {
  position: absolute;
  top: 0;
  right: 0;
  padding: 16px;
  display: flex;
  gap: 8px;
}

.fullscreen-image {
  max-width: 90vw;
  max-height: 90vh;
  object-fit: contain;
}

.close-btn {
  opacity: 0.7;
  transition: opacity 0.2s ease;
}

.close-btn:hover {
  opacity: 1;
}

.masked-image {
  position: relative;
  width: 100%;
  min-height: 200px;
  background-color: rgba(0, 0, 0, 0.05);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border: 1px dashed rgba(0, 0, 0, 0.2);
}

.image-mask {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  text-align: center;
}

.masked-image-text {
  margin-top: 1rem;
  font-weight: 500;
  font-size: 1.1rem;
  color: var(--v-primary-base);
}

.masked-image-hint {
  margin-top: 0.5rem;
  font-size: 0.9rem;
  opacity: 0.7;
}
</style>