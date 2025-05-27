<template>
  <v-container>
    <div class="panel glass">
      <div class="panel-header">
        <h1 class="text-h4 terminal-text">My Secrets</h1>
        <v-btn 
          color="primary" 
          prepend-icon="mdi-plus"
          class="btn-cyber"
          @click="openCreateDialog"
        >
          New Secret
        </v-btn>
      </div>
      
      <!-- Loading state -->
      <div v-if="secretsStore.loading" class="d-flex justify-center align-center py-lg">
        <div class="loading-spinner"></div>
      </div>
      
      <!-- Error message -->
      <div v-if="secretsStore.error" class="alert alert-cyber alert-error mb-md">
        {{ secretsStore.error }}
      </div>
      
      <!-- Empty state -->
      <div
        v-if="!secretsStore.loading && secretsStore.secrets.length === 0"
        class="terminal pa-lg text-center"
      >
        <v-icon 
          size="64"
          color="primary"
          class="mb-md"
        >
          mdi-lock-outline
        </v-icon>
        <h3 class="text-h5 mb-sm">No Secrets Yet</h3>
        <p class="text-body-1 mb-md">Create your first secret to get started.</p>
        <v-btn 
          color="primary" 
          class="btn-cyber"
          @click="openCreateDialog"
        >
          Create a Secret
        </v-btn>
      </div>
      
      <!-- Secrets list -->
      <div v-else-if="!secretsStore.loading" class="card-container">
        <div class="filters mb-md">
          <v-text-field
            v-model="search"
            append-inner-icon="mdi-magnify"
            label="Search"
            single-line
            hide-details
            density="compact"
            variant="outlined"
            class="glass-input mr-md"
            bg-color="transparent"
          ></v-text-field>
          
          <v-spacer></v-spacer>
          
          <v-select
            v-model="typeFilter"
            :items="typeOptions"
            label="Type"
            density="compact"
            hide-details
            variant="outlined"
            class="glass-input mx-md"
            style="max-width: 150px"
            bg-color="transparent"
          ></v-select>
          
          <v-btn-toggle
            v-model="view"
            density="compact"
            color="primary"
            class="view-toggle"
          >
            <v-btn value="card" icon="mdi-view-grid" variant="outlined" class="btn-toggle"></v-btn>
            <v-btn value="list" icon="mdi-view-list" variant="outlined" class="btn-toggle"></v-btn>
          </v-btn-toggle>
        </div>
        
        <!-- Card view -->
        <div v-if="view === 'card'" class="card-grid">
          <div 
            v-for="secret in filteredSecrets" 
            :key="secret.id"
            class="card card-cyber"
          >
            <div class="card-header d-flex justify-space-between align-center">
              <h3 class="card-title text-truncate">{{ secret.name }}</h3>
            </div>
            
            <div class="card-body">
              <div class="mb-sm">
                <v-chip 
                  :color="getTypeColor(secret.type)" 
                  size="small" 
                  class="mr-2"
                >
                  {{ secret.type }}
                </v-chip>
                <span class="text-caption">
                  {{ formatDate(secret.created_time) }}
                </span>
              </div>
              
              <!-- Add an icon preview for image files -->
              <div v-if="secret.type === 'image'" class="file-preview-card">
                <v-icon size="48" color="success">mdi-file-image</v-icon>
                <div class="file-type-label">Image</div>
              </div>
              
              <div class="d-flex align-center mt-2">
                <v-icon size="small" class="mr-1">mdi-account</v-icon>
                <span>Owner ID: {{ secret.owner_id }}</span>
              </div>
            </div>
            
            <div class="card-actions">
              <v-btn
                icon
                variant="text"
                color="primary"
                :to="{ name: 'secret-detail', params: { id: secret.id }}"
                class="neon-text"
              >
                <v-icon>mdi-eye</v-icon>
              </v-btn>
              
              <v-btn
                icon
                variant="text"
                color="warning"
                @click.stop="openEditDialog(secret)"
                class="neon-text"
              >
                <v-icon>mdi-pencil</v-icon>
              </v-btn>
              
              <v-spacer></v-spacer>
              
              <v-btn
                icon
                variant="text"
                color="error"
                @click.stop="confirmDelete(secret)"
                class="neon-text"
              >
                <v-icon>mdi-delete</v-icon>
              </v-btn>
            </div>
          </div>
        </div>
        
        <!-- List view -->
        <div v-else class="card glass">
          <v-list bg-color="transparent">
            <v-list-item
              v-for="secret in filteredSecrets"
              :key="secret.id"
              :to="{ name: 'secret-detail', params: { id: secret.id }}"
              class="list-item mb-xs"
            >
              <template v-slot:prepend>
                <v-icon :color="getTypeColor(secret.type)">
                  {{ getTypeIcon(secret.type) }}
                </v-icon>
              </template>
              
              <v-list-item-title class="text-white">{{ secret.name }}</v-list-item-title>
              
              <v-list-item-subtitle>
                <v-chip 
                  :color="getTypeColor(secret.type)" 
                  size="x-small" 
                  class="mr-2"
                >
                  {{ secret.type }}
                </v-chip>
                Created: {{ formatDate(secret.created_time) }}
              </v-list-item-subtitle>
              
              <template v-slot:append>
                <div class="d-flex align-center">
                  <v-btn
                    icon
                    variant="text"
                    color="warning"
                    size="small"
                    @click.stop.prevent="openEditDialog(secret)"
                    class="mr-1"
                  >
                    <v-icon>mdi-pencil</v-icon>
                  </v-btn>
                  
                  <v-btn
                    icon
                    variant="text"
                    color="error"
                    size="small"
                    @click.stop.prevent="confirmDelete(secret)"
                  >
                    <v-icon>mdi-delete</v-icon>
                  </v-btn>
                </div>
              </template>
            </v-list-item>
          </v-list>
        </div>
      </div>
    </div>
    
    <!-- Create/Edit Secret Dialog -->
    <v-dialog
      v-model="secretDialog.show"
      max-width="600px"
    >
      <v-card class="card-glass">
        <v-card-title class="text-h5 terminal-text">
          {{ secretDialog.isEdit ? 'Edit Secret' : 'Create New Secret' }}
        </v-card-title>
        
        <v-card-text>
          <v-form @submit.prevent="saveSecret" ref="secretForm">
            <v-text-field
              v-model="secretDialog.form.name"
              label="Secret Name"
              required
              variant="outlined"
              bg-color="transparent"
              class="glass-input mb-md"
              :rules="[v => !!v || 'Name is required']"
            ></v-text-field>
            
            <v-select
              v-model="secretDialog.form.type"
              label="Secret Type"
              :items="typeOptions"
              required
              variant="outlined"
              bg-color="transparent"
              class="glass-input mb-md"
              :rules="[v => !!v || 'Type is required']"
            ></v-select>
            
            <v-textarea
              v-model="secretDialog.form.value"
              label="Secret Value"
              required
              variant="outlined"
              bg-color="transparent"
              class="glass-input mb-md"
              :rules="[v => !!v || 'Value is required']"
              rows="5"
            ></v-textarea>
            
            <v-text-field
              v-model="secretDialog.form.description"
              label="Description"
              variant="outlined"
              bg-color="transparent"
              class="glass-input mb-md"
            ></v-text-field>
          </v-form>
        </v-card-text>
        
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            variant="text"
            @click="secretDialog.show = false"
          >
            Cancel
          </v-btn>
          <v-btn
            color="primary"
            @click="saveSecret"
            :loading="secretsStore.loading"
            class="btn-cyber"
          >
            {{ secretDialog.isEdit ? 'Update' : 'Create' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    
    <!-- Delete Confirmation Dialog -->
    <v-dialog
      v-model="deleteDialog.show"
      max-width="400px"
    >
      <v-card class="card-terminal">
        <v-card-title class="text-error">
          Confirm Delete
        </v-card-title>
        
        <v-card-text>
          Are you sure you want to delete the secret <strong>{{ deleteDialog.secret?.name }}</strong>? 
          This action cannot be undone.
        </v-card-text>
        
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            variant="text"
            @click="deleteDialog.show = false"
          >
            Cancel
          </v-btn>
          <v-btn
            color="error"
            @click="deleteSecret"
            :loading="secretsStore.loading"
          >
            Delete
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSecretsStore } from '@/stores/secrets'
import { useAuthStore } from '@/stores/auth'
import dayjs from 'dayjs'

const secretsStore = useSecretsStore()
const authStore = useAuthStore()

// View options
const view = ref('card')
const search = ref('')
const typeFilter = ref('all')

// Type options for filtering and form
const typeOptions = [
  { title: 'All Types', value: 'all' },
  { title: 'Plaintext', value: 'plaintext' },
  { title: 'Image', value: 'image' },
]

// Form dialogs
const secretForm = ref(null)
const secretDialog = reactive({
  show: false,
  isEdit: false,
  form: {
    id: null,
    name: '',
    type: 'plaintext',
    value: '',
    description: ''
  }
})

const deleteDialog = reactive({
  show: false,
  secret: null
})

// Computed filtered secrets
const filteredSecrets = computed(() => {
  let filtered = secretsStore.secrets
  
  // Filter by search term
  if (search.value) {
    const searchTerm = search.value.toLowerCase()
    filtered = filtered.filter(secret => 
      secret.name.toLowerCase().includes(searchTerm)
    )
  }
  
  // Filter by type
  if (typeFilter.value !== 'all') {
    filtered = filtered.filter(secret => 
      secret.type === typeFilter.value
    )
  }
  
  return filtered
})

// Fetch secrets on component mount with a better approach
onMounted(() => {
  // Instead of immediately trying to fetch and retrying once, which often fails
  // due to timing issues with authentication, we'll use a polling approach
  
  // Track how many attempts we've made
  let attempts = 0;
  // Max number of attempts before giving up
  const maxAttempts = 5;
  // Time between attempts in ms
  const retryInterval = 400;
  
  // Function to try fetching secrets with exponential backoff
  const attemptFetch = () => {
    attempts++;
    
    // Try fetching secrets
    secretsStore.fetchSecrets()
      .then(() => {
        // Success! No need to retry
      })
      .catch(err => {
        // Only retry if we haven't hit the maximum attempts
        // and if the error is a 401 (which indicates auth may not be ready)
        if (attempts < maxAttempts && err.response?.status === 401) {
          // Wait longer between each retry
          setTimeout(attemptFetch, retryInterval * attempts);
        }
      });
  };
  
  // Start the first attempt with a delay to give authentication time to settle
  setTimeout(attemptFetch, 500);
})

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

// Format date to user's local timezone
function formatDate(dateString) {
  return dayjs.utc(dateString).local().format('MMM D, YYYY')
}

// Dialog handlers
function openCreateDialog() {
  secretDialog.isEdit = false
  secretDialog.form = {
    id: null,
    name: '',
    type: 'plaintext',
    value: '',
    description: ''
  }
  secretDialog.show = true
}

function openEditDialog(secret) {
  secretDialog.isEdit = true
  // We need to fetch the secret to get the decrypted value
  secretsStore.fetchSecret(secret.id).then(fullSecret => {
    if (fullSecret) {
      secretDialog.form = {
        id: fullSecret.id,
        name: fullSecret.name,
        type: fullSecret.type,
        value: fullSecret.value,
        description: fullSecret.description
      }
      secretDialog.show = true
    }
  })
}

function confirmDelete(secret) {
  deleteDialog.secret = secret
  deleteDialog.show = true
}

// CRUD operations
async function saveSecret() {
  if (!secretForm.value.validate()) return
  
  if (secretDialog.isEdit) {
    await secretsStore.updateSecret(secretDialog.form.id, secretDialog.form)
  } else {
    await secretsStore.createSecret(secretDialog.form)
  }
  
  secretDialog.show = false
}

async function deleteSecret() {
  if (!deleteDialog.secret) return
  
  await secretsStore.deleteSecret(deleteDialog.secret.id)
  deleteDialog.show = false
}
</script>

<style scoped>
.filters {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.view-toggle {
  border: 1px solid rgba(0, 136, 255, 0.3);
  border-radius: 8px;
  overflow: hidden;
}

.btn-toggle {
  border: none !important;
}

.card-container {
  position: relative;
}

.list-item {
  transition: all 0.25s ease;
  border-radius: 8px;
  margin-bottom: 4px;
}

.list-item:hover {
  background-color: rgba(255, 255, 255, 0.05);
}

/* File preview in card styling */
.file-preview-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 10px;
  margin: 8px 0;
  background-color: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
  text-align: center;
}

.file-type-label {
  margin-top: 4px;
  font-size: 0.85rem;
  opacity: 0.8;
}

@media (max-width: 639px) {
  .filters {
    flex-direction: column;
    align-items: stretch;
  }
  
  .filters > * {
    margin: 4px 0 !important;
    width: 100%;
  }
}
</style> 