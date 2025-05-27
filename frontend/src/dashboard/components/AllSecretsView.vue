<template>
  <div class="all-secrets-view-container">
    <div class="header-area">
      <div class="header-left">
        <v-btn
          v-if="isMobile"
          icon="mdi-arrow-left"
          variant="text"
          @click="$emit('back')"
          class="back-button"
          size="small"
        ></v-btn>
        <div class="title">
          <v-icon color="accent" size="large" class="mr-2">mdi-folder</v-icon>
          <h1>All Secrets</h1>
        </div>
      </div>
      <div class="header-actions">
        <v-btn
          color="primary"
          variant="elevated"
          prepend-icon="mdi-plus"
          class="create-btn"
          @click="$emit('create-secret')"
          size="small"
        >
          New Secret
        </v-btn>
      </div>
    </div>
    
    <div class="main-content">
      <div class="folder-details">
        <div class="info-section">
          <div class="info-box">
            <div class="info-label">Description</div>
            <div class="info-value">All your secrets in a single view.</div>
          </div>
          <div class="info-box">
            <div class="info-label">Count</div>
            <div class="info-value">{{ secrets.length }} secrets</div>
          </div>
        </div>
      </div>
      
      <div class="section-header">
        <h2>Contents</h2>
        <div class="right-container">
          <span v-if="filteredSecrets.length" class="item-counter">{{ filteredSecrets.length }} item{{ filteredSecrets.length !== 1 ? 's' : '' }}</span>
        </div>
      </div>
      
      <!-- Loading indicator -->
      <div v-if="loading" class="loading-container">
        <div class="cyber-spinner">
          <div class="spinner-ring"></div>
          <div class="spinner-ring"></div>
          <div class="spinner-dot"></div>
        </div>
      </div>
      
      <!-- Empty state -->
      <div v-else-if="secrets.length === 0" class="empty-state">
        <div class="empty-icon">
          <v-icon size="48" color="accent">mdi-file-lock-outline</v-icon>
          <div class="icon-glow"></div>
        </div>
        <h3 class="empty-title">No Secrets Yet</h3>
        <p class="empty-subtitle">Create your first secret to get started</p>
        <v-btn
          color="primary"
          variant="elevated"
          @click="$emit('create-secret')"
          prepend-icon="mdi-plus"
          class="mt-4"
        >
          Create Secret
        </v-btn>
      </div>
      
      <!-- Secret list -->
      <div v-else class="contents-list">
        <div
          v-for="secret in filteredSecrets"
          :key="secret.id"
          class="secret-item"
          @click="$emit('select-secret', secret.id)"
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
                class="type-chip"
              >
                {{ secret.type }}
              </v-chip>
              <template v-if="secret.tags && secret.tags.length > 0">
                <v-chip
                  v-for="tag in secret.tags.slice(0, 2)"
                  :key="tag"
                  size="x-small"
                  label
                  color="secondary"
                  class="tag-chip ml-1"
                >
                  {{ tag }}
                </v-chip>
                <span v-if="secret.tags.length > 2" class="more-tags">+{{ secret.tags.length - 2 }}</span>
              </template>
            </div>
          </div>
          <div class="secret-actions">
            <v-icon size="small">mdi-chevron-right</v-icon>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  secrets: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
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

const emit = defineEmits(['create-secret', 'select-secret', 'back'])

// Filter not really needed now but added for future use if filtering is needed
const filteredSecrets = computed(() => {
  return props.secrets
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
</script>

<style scoped>
.all-secrets-view-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: rgba(15, 22, 32, 0.6);
  border-radius: 8px;
  overflow: hidden;
}

.header-area {
  background: rgba(15, 22, 32, 0.4);
  padding: 16px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.header-left {
  display: flex;
  align-items: center;
}

.title {
  display: flex;
  align-items: center;
}

.title h1 {
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0;
  color: rgba(255, 255, 255, 0.9);
}

.main-content {
  flex: 1;
  overflow-y: auto;
  padding: 0 24px 24px;
}

.folder-details {
  margin-top: 24px;
  margin-bottom: 32px;
}

.info-section {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
}

.info-box {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  padding: 12px 16px;
  flex: 1;
  min-width: 200px;
}

.info-label {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 6px;
}

.info-value {
  font-size: 0.95rem;
  color: rgba(255, 255, 255, 0.9);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h2 {
  font-size: 1.1rem;
  font-weight: 500;
  margin: 0;
  color: rgba(255, 255, 255, 0.8);
}

.item-counter {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.6);
}

/* Contents list */
.contents-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.secret-item {
  display: flex;
  align-items: center;
  padding: 14px 16px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.secret-item:hover {
  background: rgba(255, 255, 255, 0.06);
  transform: translateY(-1px);
}

.secret-icon {
  margin-right: 16px;
  opacity: 0.85;
}

.secret-details {
  flex: 1;
}

.secret-name {
  font-size: 0.95rem;
  font-weight: 500;
  margin-bottom: 6px;
  color: rgba(255, 255, 255, 0.9);
}

.secret-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}

.type-chip, .tag-chip {
  margin-right: 6px;
  margin-bottom: 4px;
}

.more-tags {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.5);
  margin-left: 4px;
}

.secret-actions {
  opacity: 0.5;
  transition: opacity 0.2s ease;
}

.secret-item:hover .secret-actions {
  opacity: 0.8;
}

/* Empty state */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.empty-icon {
  position: relative;
  margin-bottom: 24px;
}

.icon-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 70px;
  height: 70px;
  background: radial-gradient(circle, rgba(140, 82, 255, 0.2) 0%, transparent 70%);
  border-radius: 50%;
  z-index: -1;
}

.empty-title {
  font-size: 1.3rem;
  font-weight: 500;
  margin-bottom: 12px;
  color: rgba(255, 255, 255, 0.9);
}

.empty-subtitle {
  font-size: 0.95rem;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 24px;
}

/* Loading */
.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 60px 0;
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

/* Mobile styles */
@media (max-width: 768px) {
  .header-area {
    padding: 12px 16px;
  }
  
  .title h1 {
    font-size: 1.3rem;
  }
  
  .main-content {
    padding: 0 16px 16px;
  }
  
  .info-box {
    min-width: 0;
    width: 100%;
  }
  
  .secret-item {
    padding: 12px;
  }
  
  .back-button {
    margin-right: 8px;
  }
}
</style> 