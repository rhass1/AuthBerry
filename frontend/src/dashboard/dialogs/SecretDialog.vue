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
        <v-toolbar-title>{{ isEdit ? 'Edit Secret' : 'Create New Secret' }}</v-toolbar-title>
        <v-spacer></v-spacer>
        <v-btn color="primary" @click="save" :loading="loading" variant="text">
          Save
        </v-btn>
      </v-toolbar>

      <v-card-title v-if="!isMobile" class="dialog-title">
        <span>{{ isEdit ? 'Edit Secret' : 'Create New Secret' }}</span>
        <v-chip
          v-if="currentFolderName"
          size="small"
          :color="currentFolderIsShared ? 'success' : 'primary'"
          class="ml-3"
          :prepend-icon="currentFolderIsShared ? 'mdi-folder-multiple' : 'mdi-folder-lock'"
        >
          {{ currentFolderName }}
        </v-chip>
      </v-card-title>

      <v-card-text :class="{'mobile-content': isMobile}" class="dialog-content">
        <v-form @submit.prevent="save" ref="form">
          <div class="form-row">
            <v-text-field
              v-model="formData.name"
              label="Secret Name"
              required
              variant="outlined"
              class="form-field"
              :rules="[v => !!v || 'Name is required']"
              bg-color="rgba(15, 22, 32, 0.3)"
            ></v-text-field>
          </div>

          <div class="form-row type-selection">
            <v-select
              v-model="formData.type"
              label="Secret Type"
              :items="typeOptions"
              required
              variant="outlined"
              class="form-field"
              :rules="[v => !!v || 'Type is required']"
              @update:model-value="handleTypeChange"
              bg-color="rgba(15, 22, 32, 0.3)"
            ></v-select>
          </div>

          <div class="form-row">
            <div class="folder-selection">
              <v-select
                v-if="!inFolder"
                v-model="formData.folder_id"
                label="Folder (Optional)"
                :items="folderOptions"
                variant="outlined"
                class="form-field"
                clearable
                :hint="folderHint"
                persistent-hint
                bg-color="rgba(15, 22, 32, 0.3)"
              >
                <template v-slot:item="{ item, props }">
                  <v-list-item v-bind="props" :title="item.raw.title">
                    <template v-slot:prepend>
                      <v-icon :color="item.raw.is_shared ? 'success' : 'primary'" class="mr-2" size="default">
                        {{ item.raw.is_shared ? 'mdi-folder-multiple' : 'mdi-folder-lock' }}
                      </v-icon>
                    </template>
                    <div :class="item.raw.is_shared ? 'shared-folder-item' : 'private-folder-item'">
                      {{ item.raw.title }}
                    </div>
                  </v-list-item>
                </template>
                <template v-slot:selection="{ item }">
                  <div class="d-flex align-center">
                    <v-icon :color="item.is_shared ? 'success' : 'primary'" size="default" class="mr-2">
                      {{ item.is_shared ? 'mdi-folder-multiple' : 'mdi-folder-lock' }}
                    </v-icon>
                    <div :class="item.is_shared ? 'shared-folder-item' : 'private-folder-item'">
                      {{ item.title }}
                    </div>
                  </div>
                </template>
              </v-select>

              <div v-else class="folder-info">
                <div class="folder-label">Folder:</div>
                <v-chip
                  :color="currentFolderIsShared ? 'success' : 'primary'"
                  size="small"
                  :prepend-icon="currentFolderIsShared ? 'mdi-folder-multiple' : 'mdi-folder-lock'"
                >
                  {{ currentFolderName }}
                </v-chip>
                <div class="folder-hint">This secret will be added to the selected folder</div>
              </div>
            </div>
          </div>

          <div v-if="isFileType" class="file-upload-container">
            <v-file-input
              v-model="formData.file"
              :label="`Upload ${formData.type.toUpperCase()} File`"
              variant="outlined"
              class="form-field"
              :rules="[v => !!v || 'File is required']"
              :accept="fileAcceptTypes"
              prepend-icon="mdi-file-upload"
              :show-size="true"
              truncate-length="25"
              @update:model-value="handleFileChange"
            ></v-file-input>

            <div v-if="filePreview" class="file-preview">
              <div class="preview-header">Preview:</div>
              <img
                v-if="isImageType"
                :src="filePreview"
                class="image-preview"
              />
            </div>
          </div>

          <v-textarea
            v-if="formData.type === 'plaintext'"
            v-model="formData.value"
            label="Secret Value"
            required
            variant="outlined"
            class="form-field"
            :rules="[v => !!v || 'Value is required']"
            :auto-grow="true"
            rows="5"
          ></v-textarea>

          <v-textarea
            v-model="formData.description"
            label="Description (Optional)"
            variant="outlined"
            class="form-field"
            :auto-grow="true"
            rows="3"
          ></v-textarea>

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
            Delete This Secret
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
import { ref, computed, reactive, watch, onMounted, onBeforeUnmount } from 'vue'
import axios from 'axios'
import { useSecretsStore } from '@/stores/secrets'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  isEdit: {
    type: Boolean,
    default: false
  },
  secret: {
    type: Object,
    default: () => ({
      id: null,
      name: '',
      type: 'plaintext',
      value: '',
      description: '',
      folder_id: null,
      tags: []
    })
  },
  inFolder: {
    type: Boolean,
    default: false
  },
  folderId: {
    type: String,
    default: null
  },
  folderOptions: {
    type: Array,
    default: () => []
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

const emit = defineEmits(['update:modelValue', 'save', 'delete'])

const secretsStore = useSecretsStore()
const form = ref(null)
const filePreview = ref(null)

// Track if we're on mobile
const isMobile = ref(false)

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

// Type options for the form
const typeOptions = [
  { title: 'Plain Text', value: 'plaintext' },
  { title: 'Image', value: 'image' }
]

// Form data
const formData = reactive({
  id: props.secret?.id || null,
  name: props.secret?.name || '',
  type: props.secret?.type || 'plaintext',
  value: props.secret?.value || '',
  description: props.secret?.description || '',
  folder_id: props.secret?.folder_id || null,
  tags: Array.isArray(props.secret?.tags) ? [...props.secret.tags] : [],
  file: null, // For file uploads
  originalFilename: props.secret?.original_filename || null
})

// Computed
const currentFolderName = computed(() => {
  if (props.inFolder) {
    // If we're explicitly in a folder, find it by ID
    const folder = props.folderOptions.find(f => f.value === props.folderId)
    return folder?.title || 'Selected Folder'
  } else if (formData.folder_id) {
    // If we have a folder_id in the form data
    const folder = props.folderOptions.find(f => f.value === formData.folder_id)
    return folder?.title || null
  }
  return null
})

const currentFolderIsShared = computed(() => {
  if (props.inFolder) {
    const folder = props.folderOptions.find(f => f.value === props.folderId)
    return folder?.is_shared === true
  } else if (formData.folder_id) {
    const folder = props.folderOptions.find(f => f.value === formData.folder_id)
    return folder?.is_shared === true
  }
  return false
})

const folderHint = computed(() => {
  return formData.folder_id
    ? "This secret will be organized within the selected folder"
    : "No folder selected - this will be a root-level secret"
})

const isFileType = computed(() => {
  return ['image'].includes(formData.type)
})

const isImageType = computed(() => {
  return formData.type === 'image'
})

const fileAcceptTypes = computed(() => {
  switch(formData.type) {
    case 'image': return '.png,.jpg,.jpeg,image/png,image/jpeg'
    default: return null
  }
})

// Watch for changes to the secret prop to update form data
watch(() => props.secret, (newSecret) => {
  if (newSecret) {
    formData.id = newSecret.id || null
    formData.name = newSecret.name || ''
    formData.type = newSecret.type || 'plaintext'
    formData.value = newSecret.value || ''
    formData.description = newSecret.description || ''
    formData.folder_id = newSecret.folder_id || null
    formData.tags = Array.isArray(newSecret.tags) ? [...newSecret.tags] : []
    formData.file = newSecret.file || null
    formData.originalFilename = newSecret.original_filename || null

    // If it's a file type secret, load the file preview
    if (newSecret.id && isFileType.value) {
      loadFilePreview(newSecret.id)
    } else {
      filePreview.value = null
    }
  }
}, { deep: true, immediate: true })

// Watch for changes to folderId to update folder_id when in folder mode
watch(() => props.folderId, (newId) => {
  if (props.inFolder && newId) {
    formData.folder_id = newId
  }
}, { immediate: true })

// Functions
function handleTypeChange() {
  // Reset file and preview when type changes
  formData.file = null
  filePreview.value = null
}

function handleFileChange(file) {
  if (!file) {
    filePreview.value = null
    return
  }

  // Create a preview for the selected file
  const reader = new FileReader()
  reader.onload = (e) => {
    filePreview.value = e.target.result
  }
  reader.readAsDataURL(file)
}

async function loadFilePreview(secretId) {
  try {
    // Get the file content for preview
    const response = await secretsStore.fetchSecretFile(secretId)

    // Create a preview URL
    const blob = new Blob([response.data], { type: response.headers['content-type'] })
    const url = URL.createObjectURL(blob)
    filePreview.value = url
  } catch (error) {
    filePreview.value = null
  }
}

function cancel() {
  // Reset form and close dialog
  emit('update:modelValue', false)
}

function confirmDelete() {
  emit('delete', formData.id)
}

function save() {
  if (!form.value.validate()) return

  // Create a safe copy of form data to avoid reactivity issues
  const safeData = { ...formData }

  // Ensure ID is properly retained for editing existing secrets
  if (props.isEdit && props.secret && props.secret.id) {
    safeData.id = props.secret.id
  }

  // Emit save event with the data
  emit('save', safeData)
}
</script>

<style scoped>
.dialog-card {
  background: linear-gradient(to bottom right, rgba(15, 22, 32, 0.95), rgba(25, 35, 48, 0.95)) !important;
  border: 1px solid rgba(0, 255, 156, 0.2) !important;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3) !important;
  overflow: hidden;
  display: flex;
  flex-direction: column;
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
  overflow-y: auto;
  max-height: 65vh; /* Prevent excessive scrolling */
}

.form-row {
  margin-bottom: 20px;
  max-width: 500px;
  margin-left: auto;
  margin-right: auto;
}

.type-selection {
  max-width: 300px;
}

.folder-info {
  background-color: rgba(33, 150, 243, 0.05);
  padding: 12px;
  border-radius: 8px;
  border: 1px solid rgba(33, 150, 243, 0.2);
}

.folder-label {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 6px;
}

.folder-hint {
  font-size: 0.8rem;
  color: rgba(33, 150, 243, 0.8);
  margin-top: 8px;
}

.file-upload-container {
  border: 1px dashed rgba(0, 255, 156, 0.3);
  padding: 16px;
  border-radius: 8px;
  background-color: rgba(0, 255, 156, 0.05);
  margin-bottom: 20px;
}

.file-preview {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.preview-header {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 8px;
}

.image-preview {
  max-width: 100%;
  max-height: 250px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
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
  margin-top: auto;
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

  .type-selection {
    max-width: 100%;
  }

  .dialog-content {
    max-height: none; /* On mobile, let the content flow naturally */
  }
}

/* Folder dropdown styling */
.shared-folder-item {
  color: rgba(76, 175, 80, 0.9);
  font-weight: 500;
  padding-left: 4px;
  border-left: 2px solid rgba(76, 175, 80, 0.5);
}

.private-folder-item {
  color: rgba(0, 176, 255, 0.9);
  font-weight: 500;
  padding-left: 4px;
  border-left: 2px solid rgba(0, 176, 255, 0.5);
}
</style>