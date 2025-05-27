<template>
  <div class="folder-details-wrapper">
    <div class="folder-header">
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

      <div class="folder-title-row">
        <div class="folder-title">
          <v-icon
            :color="folder.is_shared_folder ? 'success' : 'primary'"
            size="small"
            class="mr-2"
          >{{ folder.is_shared_folder ? 'mdi-folder-multiple' : 'mdi-folder-lock' }}</v-icon>
          <h2>{{ folder.name }}</h2>
          <v-chip
            v-if="folder.is_shared_folder"
            size="x-small"
            label
            color="success"
            class="ml-2"
          >
            Shared Folder
          </v-chip>
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

    <div v-if="folder.description" class="folder-description-section">
      <h3>Description</h3>
      <p class="description-content">{{ folder.description }}</p>
    </div>

    <div class="folder-type-section">
      <h3>Folder Type</h3>
      <div class="folder-type-container">
        <div class="folder-type-indicator">
          <v-icon
            :color="folder.is_shared_folder ? 'success' : 'primary'"
            size="small"
            class="mr-2"
          >{{ folder.is_shared_folder ? 'mdi-folder-multiple' : 'mdi-folder-lock' }}</v-icon>
          <span class="folder-type-name">
            {{ folder.is_shared_folder ? 'Shared Folder' : 'Private Folder' }}
          </span>
        </div>

        <div class="folder-type-description-wrapper" :class="folder.is_shared_folder ? 'shared-description' : 'private-description'">
          <p class="folder-type-description">
            {{ folder.is_shared_folder
              ? 'Secrets in this folder inherit sharing permissions automatically. When you share this folder, all contained secrets are shared too.'
              : 'Secrets need to be shared individually.' }}
          </p>
        </div>
      </div>
    </div>

    <div class="folder-contents-section">
      <div class="contents-header">
        <h3>Contents</h3>
        <v-btn
          v-if="hasEditPermission"
          prepend-icon="mdi-plus"
          color="primary"
          size="small"
          class="add-btn neon-btn"
          @click="$emit('add-secret')"
        >
          Add Secret
        </v-btn>
      </div>

      <div v-if="folderContents.length === 0" class="empty-contents">
        <p>This folder is empty</p>
        <v-btn
          v-if="hasEditPermission"
          prepend-icon="mdi-plus"
          color="primary"
          size="small"
          class="mt-2 neon-btn"
          @click="$emit('add-secret')"
        >
          Add Secret
        </v-btn>
      </div>

      <div v-else class="contents-list">
        <div
          v-for="secret in folderContents"
          :key="secret.id"
          class="secret-item"
          @click="selectSecret(secret.id)"
        >
          <div class="secret-icon">
            <v-icon :color="getTypeColor(secret.type)" size="small">
              {{ getTypeIcon(secret.type) }}
            </v-icon>
          </div>

          <div class="secret-details">
            <div class="secret-name">{{ secret.name }}</div>
            <div class="secret-meta">
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

          <div class="secret-actions">
            <v-icon size="small" color="primary">mdi-chevron-right</v-icon>
          </div>
        </div>
      </div>
    </div>

    <div class="folder-tags-section" v-if="tags.length > 0">
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

    <div class="folder-footer">
      <div class="metadata">
        <div class="meta-item" v-if="folder.created_at">
          <span class="meta-label">Created:</span>
          <span class="meta-value">{{ formatDate(folder.created_at) }}</span>
        </div>
        <div class="meta-item" v-if="folder.updated_at">
          <span class="meta-label">Last Updated:</span>
          <span class="meta-value">{{ formatDate(folder.updated_at) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed, defineProps, defineEmits } from 'vue'
import { useSecretsStore } from '@/stores/secrets'

const props = defineProps({
  folder: {
    type: Object,
    required: true
  },
  folderContents: {
    type: Object,
    default: () => ({ secrets: [] })
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

const emit = defineEmits(['edit', 'delete', 'share', 'add-secret', 'select-secret', 'update:tags', 'back'])

// Local state
const tags = ref([])

// Add the store reference
const secretsStore = useSecretsStore()

// Add this computed property
const hasDeletePermission = computed(() => {
  // If the user is the owner, they can delete
  if (props.folder && props.folder.is_owner === true) {
    return true;
  }

  // Check explicit permissions
  if (props.folder &&
      props.folder.permissions &&
      props.folder.permissions.can_delete === true) {
    return true;
  }

  // No delete permission
  return false;
});

// Add these computed properties
const hasEditPermission = computed(() => {
  // If the user is the owner, they can edit
  if (props.folder && props.folder.is_owner === true) {
    return true;
  }

  // Check explicit permissions
  if (props.folder &&
      props.folder.permissions &&
      props.folder.permissions.can_write === true) {
    return true;
  }

  return false;
});

const hasSharePermission = computed(() => {
  // If the user is the owner, they can share
  if (props.folder && props.folder.is_owner === true) {
    return true;
  }

  // Check explicit permissions
  if (props.folder &&
      props.folder.permissions &&
      props.folder.permissions.can_share === true) {
    return true;
  }

  return false;
});

// Initialize tags when folder changes
watch(() => props.folder, (newFolder) => {
  if (newFolder && newFolder.tags) {
    tags.value = [...newFolder.tags]
  } else {
    tags.value = []
  }
}, { immediate: true })

// Helper functions
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

// Emit select-secret event when a secret is clicked
function selectSecret(id) {
  emit('select-secret', id)
}

// Format dates
function formatDate(dateString) {
  const date = new Date(dateString)
  return date.toLocaleString()
}
</script>

<style scoped>
.folder-details-wrapper {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 24px;
  position: relative;
  overflow-y: auto;
}

/* Mobile styles */
@media (max-width: 767px) {
  .folder-details-wrapper {
    padding: 16px;
  }
}

/* Header styling */
.folder-header {
  margin-bottom: 20px;
}

.mobile-back-btn {
  margin-bottom: 8px;
}

.folder-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.folder-title {
  display: flex;
  align-items: center;
}

.folder-title h2 {
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

/* Description section */
.folder-description-section {
  margin-bottom: 24px;
}

.folder-description-section h3 {
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

/* Folder Type Section */
.folder-type-section {
  margin-bottom: 24px;
}

.folder-type-section h3 {
  font-size: 1.1rem;
  font-weight: 500;
  margin: 0 0 8px 0;
  color: rgba(255, 255, 255, 0.9);
}

.folder-type-container {
  display: flex;
  flex-direction: column;
}

.folder-type-indicator {
  display: flex;
  align-items: center;
  background-color: rgba(15, 22, 32, 0.3);
  padding: 8px 12px;
  border-radius: 6px 6px 0 0;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-bottom: none;
}

.folder-type-name {
  font-size: 0.95rem;
  font-weight: 500;
  margin-left: 8px;
}

.folder-type-description-wrapper {
  padding: 10px 14px;
  border-radius: 0 0 6px 6px;
  font-size: 0.9rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  margin-top: -1px;
}

.private-description {
  background-color: rgba(0, 255, 156, 0.05);
  border-color: rgba(0, 255, 156, 0.2);
}

.shared-description {
  background-color: rgba(33, 150, 243, 0.05);
  border-color: rgba(33, 150, 243, 0.2);
}

.folder-type-description {
  margin: 0;
  color: rgba(255, 255, 255, 0.8);
  line-height: 1.4;
}

/* Contents section */
.folder-contents-section {
  margin-bottom: 24px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  padding: 16px;
  border: 1px solid rgba(0, 255, 156, 0.1);
}

.contents-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.contents-header h3 {
  font-size: 1.1rem;
  font-weight: 500;
  margin: 0;
  color: rgba(255, 255, 255, 0.9);
}

.add-btn {
  background: linear-gradient(135deg, rgba(0, 255, 156, 0.25), rgba(0, 163, 255, 0.25));
  border: 1px solid rgba(0, 255, 156, 0.3);
  box-shadow:
    0 0 5px rgba(0, 255, 156, 0.5),
    0 0 10px rgba(0, 255, 156, 0.2);
  transition: all 0.2s ease;
}

.neon-btn:hover {
  background: linear-gradient(135deg, rgba(0, 255, 156, 0.35), rgba(0, 163, 255, 0.35));
  border: 1px solid rgba(0, 255, 156, 0.5);
  box-shadow:
    0 0 10px rgba(0, 255, 156, 0.7),
    0 0 15px rgba(0, 255, 156, 0.3);
  transform: translateY(-1px);
}

.empty-contents {
  text-align: center;
  padding: 24px 0;
  color: rgba(255, 255, 255, 0.5);
}

.contents-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.secret-item {
  display: flex;
  align-items: center;
  padding: 12px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.05);
  cursor: pointer;
  transition: all 0.2s ease;
}

.secret-item:hover {
  background: rgba(255, 255, 255, 0.08);
  transform: translateY(-1px);
}

.secret-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 24px;
  margin-right: 12px;
}

.secret-details {
  flex-grow: 1;
  min-width: 0;
}

.secret-name {
  font-size: 0.95rem;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 4px;
}

.secret-meta {
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

.secret-actions {
  margin-left: 8px;
}

/* Tags section */
.folder-tags-section {
  margin-bottom: 24px;
}

.folder-tags-section h3 {
  font-size: 1.1rem;
  font-weight: 500;
  margin: 0 0 8px 0;
  color: rgba(255, 255, 255, 0.9);
}

.tags-container {
  min-height: 50px;
}

/* Footer with metadata */
.folder-footer {
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

/* Mobile optimization */
@media (max-width: 767px) {
  .folder-title h2 {
    font-size: 1.3rem;
  }

  .action-buttons {
    gap: 1px;
  }

  .folder-contents-section {
    padding: 12px;
  }

  .secret-item {
    padding: 16px 12px;
  }

  .secret-name {
    font-size: 1rem;
  }

  .metadata {
    flex-direction: column;
  }

  .meta-item {
    margin-bottom: 8px;
  }
}
</style>