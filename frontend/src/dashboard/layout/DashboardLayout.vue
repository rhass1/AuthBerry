<template>
  <v-container fluid class="pa-0 dashboard-wrapper">
    <!-- Desktop layout -->
    <div v-if="!isMobile" class="dashboard-container desktop-layout">
      <!-- Left pane - Secrets list -->
      <div class="left-pane">
        <div class="cyberpunk-panel">
          <slot name="left-pane"></slot>
        </div>
      </div>

      <!-- Right pane - Secret or folder details -->
      <div class="right-pane" @click.stop>
        <div class="cyberpunk-panel">
          <slot name="right-pane"></slot>
        </div>
      </div>
      
      <!-- Dedicated outside click handler (desktop only) -->
      <div class="outside-click-detector" @click="handleOutsideClick"></div>
    </div>
    
    <!-- Mobile layout - stacked approach -->
    <div v-else class="dashboard-container mobile-layout">
      <!-- Top section - always visible (search and actions) -->
      <div class="mobile-top-section">
        <div class="cyberpunk-panel mobile-top-panel">
          <slot name="mobile-top"></slot>
        </div>
      </div>
      
      <!-- Main content area - item list -->
      <div class="mobile-content">
        <div class="cyberpunk-panel mobile-content-panel">
          <slot name="left-pane"></slot>
        </div>
      </div>
      
      <!-- Bottom section - item details when something is selected -->
      <div class="mobile-bottom-section" v-if="hasSelectedItem">
        <div class="cyberpunk-panel mobile-bottom-panel">
          <slot name="right-pane"></slot>
        </div>
      </div>
    </div>
    
    <slot name="dialogs"></slot>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue';
import { useSecretsStore } from '@/stores/secrets';
import { socketIO } from '@/main';

// Define emits to propagate click events and mobile state
const emit = defineEmits(['click', 'mobile-state-changed']);

// Define props
const props = defineProps({
  // Pass the selected item state from parent to determine layout
  hasSelectedItem: {
    type: Boolean,
    default: false
  }
});

// Mobile state management
const isMobile = ref(false);
const secretsStore = useSecretsStore();

// Handle outside clicks (desktop only)
function handleOutsideClick(event) {
  // Only handle direct clicks on this element, not bubbled events
  if (event.target.classList.contains('outside-click-detector')) {
    emit('click', event);
  }
}

// Handle screen resize to detect mobile view
function handleResize() {
  const wasMobile = isMobile.value;
  isMobile.value = window.innerWidth < 768;
  
  // Notify parent if mobile state changes
  if (wasMobile !== isMobile.value) {
    emit('mobile-state-changed', isMobile.value);
  }
}

// Setup socket listeners
function setupSocketListeners() {
  // No need to handle secret_shared here as it's already handled in the secrets store
  // The secrets store will automatically update the UI when it receives the event
}

// Setup resize listener on mount
onMounted(() => {
  handleResize(); // Check initial size
  window.addEventListener('resize', handleResize);
  setupSocketListeners();
});

// Clean up resize listener on unmount
onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize);
});
</script>

<style scoped>
/* Container wrapper */
.dashboard-wrapper {
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* Common styles */
.dashboard-container {
  position: relative;
  background-color: #0A0E14;
  width: 100%;
  flex: 1;
  display: flex;
}

/* Cyberpunk panel styling */
.cyberpunk-panel {
  background: #0F1620;
  border-radius: 8px;
  height: 100%;
  overflow: hidden;
  position: relative;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
}

.cyberpunk-panel::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #00FF9C, #00E6CC, #00A3FF, #8C52FF);
  z-index: 1;
}

/* Desktop layout styles */
.desktop-layout {
  overflow: hidden;
}

.left-pane {
  width: 35%;
  padding: 16px;
  padding-right: 8px;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow-y: auto;
}

.right-pane {
  width: 65%;
  padding: 16px;
  padding-left: 8px;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow-y: auto;
}

/* Outside click detector */
.outside-click-detector {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1;
  background: transparent;
  pointer-events: none;
}

/* Mobile layout styles */
.mobile-layout {
  flex-direction: column;
  overflow: hidden;
}

.mobile-top-section {
  flex-shrink: 0;
  padding: 8px;
  z-index: 10;
}

.mobile-top-panel {
  min-height: 60px;
}

.mobile-content {
  flex: 1 1 auto;
  padding: 0 8px;
  overflow-y: auto;
  position: relative;
  display: flex;
  flex-direction: column;
}

.mobile-content-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.mobile-bottom-section {
  flex-shrink: 0;
  padding: 8px;
  max-height: 50vh;
  transition: max-height 0.3s ease;
}

.mobile-bottom-panel {
  overflow-y: auto;
  max-height: calc(50vh - 16px);
}

/* Responsive design for tablets */
@media (min-width: 768px) and (max-width: 1023px) {
  .desktop-layout {
    flex-direction: column;
  }
  
  .left-pane, .right-pane {
    width: 100%;
  }
  
  .left-pane {
    max-height: 40vh;
    padding-bottom: 8px;
  }
  
  .right-pane {
    flex: 1;
    padding-top: 8px;
  }
}

@media (min-width: 1024px) and (max-width: 1279px) {
  .left-pane {
    width: 40%;
  }
  
  .right-pane {
    width: 60%;
  }
}
</style> 