<template>
  <div class="action-bar">
    <div class="search-container" @click.stop>
      <v-text-field
        v-model="searchModel"
        prepend-inner-icon="mdi-magnify"
        placeholder="Search Secrets"
        single-line
        hide-details
        density="compact"
        variant="plain"
        class="search-field"
        @update:model-value="updateSearch"
        clearable
        @click.stop
      ></v-text-field>
    </div>
    
    <v-menu 
      v-model="menuOpen"
      offset-y 
      location="bottom end" 
      :z-index="9999"
      min-width="200"
      :close-on-content-click="false"
      :close-on-click="true"
      :attach="true"
    >
      <template v-slot:activator="{ props }">
        <v-btn 
          color="primary" 
          icon="mdi-plus"
          v-bind="props"
          class="neon-btn action-btn"
          size="small"
          aria-label="Create new item"
          @click.stop
        >
          <v-icon>mdi-plus</v-icon>
        </v-btn>
      </template>
      <v-list class="neon-glass-menu" @click.stop>
        <v-list-item @click.stop="createSecretAndClose" class="menu-item" active-color="primary">
          <template v-slot:prepend>
            <v-icon color="primary">mdi-file-lock</v-icon>
          </template>
          <v-list-item-title>New Secret</v-list-item-title>
        </v-list-item>
        
        <v-list-item @click.stop="createFolderAndClose" class="menu-item" active-color="primary">
          <template v-slot:prepend>
            <v-icon color="primary">mdi-folder-lock</v-icon>
          </template>
          <v-list-item-title>New Folder</v-list-item-title>
        </v-list-item>
      </v-list>
    </v-menu>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  search: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:search', 'create-secret', 'create-folder'])

// Local model for v-model binding
const searchModel = ref(props.search)
const menuOpen = ref(false)

// Watch for prop changes to update local model
watch(() => props.search, (newVal) => {
  searchModel.value = newVal
})

// Emit search updates to parent with debounce
function updateSearch(value) {
  const trimmedValue = value ? value.trim() : ''
  emit('update:search', trimmedValue)
}

function createSecret() {
  emit('create-secret')
}

function createFolder() {
  emit('create-folder')
}

function createSecretAndClose() {
  createSecret()
  closeMenu()
}

function createFolderAndClose() {
  createFolder()
  closeMenu()
}

function closeMenu() {
  menuOpen.value = false
}
</script>

<style scoped>
/* Action bar with search */
.action-bar {
  display: flex;
  align-items: center;
  padding: 8px 16px;
  border-bottom: 1px solid rgba(0, 136, 255, 0.2);
  background: rgba(15, 22, 32, 0.6);
  flex-wrap: nowrap;
}

.search-container {
  flex-grow: 1;
  margin-right: 8px;
  min-width: 0; /* Important for proper flex sizing */
}

.search-field {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
  transition: background 0.3s ease;
  height: 40px;
}

.search-field:hover, .search-field:focus-within {
  background: rgba(255, 255, 255, 0.1);
}

.search-field :deep(.v-field__input) {
  padding-top: 8px;
  min-height: 40px;
}

.search-field :deep(.v-field__prepend-inner) {
  padding-top: 8px;
}

.action-btn {
  flex-shrink: 0;
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

.neon-glass-menu {
  background: rgba(15, 22, 32, 0.95) !important;
  border: 1px solid rgba(0, 255, 156, 0.3) !important;
  box-shadow: 0 0 15px rgba(0, 255, 156, 0.3) !important;
  backdrop-filter: blur(10px) !important;
}

.menu-item {
  min-height: 48px; /* Ensure touch-friendly size */
}

/* Responsive styles for mobile */
@media (max-width: 768px) {
  .action-bar {
    padding: 8px 12px;
  }
  
  .search-field {
    height: 36px;
  }
  
  .search-field :deep(.v-field__input) {
    font-size: 14px;
    padding-top: 6px;
    min-height: 36px;
  }
  
  .search-field :deep(.v-field__prepend-inner) {
    padding-top: 6px;
  }
  
  .search-field :deep(.v-field__clearable) {
    padding-top: 6px;
  }
  
  /* Fix for menus on mobile */
  :deep(.v-overlay) {
    z-index: 9999 !important;
    backdrop-filter: none !important;
    -webkit-backdrop-filter: none !important;
  }
  
  :deep(.v-menu__content) {
    background: rgba(15, 22, 32, 0.95) !important;
    border: 1px solid rgba(0, 255, 156, 0.3) !important;
    box-shadow: 0 0 15px rgba(0, 255, 156, 0.4) !important;
    backdrop-filter: none !important;
    max-height: none !important;
  }
  
  :deep(.menu-item) {
    min-height: 48px !important;
  }
  
  /* Make sure the dropdown is fully visible */
  :deep(.v-overlay__content) {
    max-height: none !important;
    backdrop-filter: none !important;
    -webkit-backdrop-filter: none !important;
  }
  
  :deep(.v-overlay__scrim) {
    backdrop-filter: none !important;
    -webkit-backdrop-filter: none !important;
  }
}

@media (max-width: 480px) {
  .action-bar {
    padding: 6px 10px;
  }
  
  .search-field :deep(.v-field__input) {
    font-size: 13px;
  }
  
  .search-field::placeholder {
    font-size: 13px;
  }
}
</style> 