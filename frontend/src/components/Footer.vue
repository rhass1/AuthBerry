<template>
  <v-footer app class="bg-background text-center d-flex justify-center border-top footer-compact">
    <div class="cyber-footer">
      <div class="footer-content">
        <span class="app-name">AUTHBERRY</span>
        <span class="app-version">v0.1.0</span>
        <span class="footer-text"> © 2025 Ryland Hassell. All rights reserved.</span>
        
        <v-btn
          v-if="isAdmin"
          variant="text"
          size="small"
          color="warning"
          class="ml-2 admin-link"
          :to="{ name: 'admin' }"
          density="compact"
        >
          <v-icon size="small" start>mdi-shield-account</v-icon>
          Admin
        </v-btn>

        <!-- Sound Toggle Button -->
        <v-btn
          variant="text"
          size="small"
          :color="soundStore.enabled ? 'info' : 'grey'"
          class="ml-2 sound-toggle"
          @click="toggleSound"
          density="compact"
        >
          <v-icon size="small">{{ soundStore.enabled ? 'mdi-volume-high' : 'mdi-volume-off' }}</v-icon>
        </v-btn>
      </div>
    </div>
  </v-footer>
</template>

<script setup>
import { useSoundStore } from '@/stores/sound'

const props = defineProps({
  isAdmin: {
    type: Boolean,
    default: false
  }
})

const soundStore = useSoundStore()

const toggleSound = () => {
  soundStore.toggleSound()
}
</script>

<style scoped>
.bg-background {
  background-color: var(--v-background-base, #0A0E14) !important;
}

.border-top {
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  position: relative;
}

.border-top::before {
  content: '';
  position: absolute;
  top: -1px;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(0, 255, 156, 0.3), transparent);
}

.footer-text {
  font-family: 'Poppins', sans-serif;
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.875rem;
  letter-spacing: 0.5px;
}

.cyber-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
}

.footer-content {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 6px;
}

.app-name {
  font-family: 'VT323', monospace;
  color: rgba(0, 255, 156, 0.9);
  font-size: 1rem;
  letter-spacing: 1px;
  font-weight: bold;
  text-shadow: 0 0 5px rgba(0, 255, 156, 0.5);
}

.app-version {
  font-family: 'VT323', monospace;
  color: rgba(0, 255, 156, 0.9);
  font-size: 0.875rem;
  letter-spacing: 0.5px;
}

.terminal-text {
  font-family: 'VT323', monospace;
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.8rem;
  opacity: 0.7;
}

.terminal-prompt {
  color: rgba(0, 255, 156, 0.9);
  margin-right: 5px;
  font-family: 'VT323', monospace;
  font-size: 0.8rem;
}

.terminal-cursor {
  display: inline-block;
  animation: blink 1s infinite steps(1);
  color: rgba(0, 255, 156, 0.9);
  font-family: 'VT323', monospace;
  font-size: 0.8rem;
  margin-left: 3px;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.footer-compact {
  padding: min(4px, 0.5vh) !important;
  min-height: auto !important;
  height: auto !important;
  flex-shrink: 0;
}

@media (max-height: 700px) {
  .footer-text {
    font-size: 0.75rem;
  }
  
  .app-name, .app-version {
    font-size: 0.8rem;
  }
  
  .footer-compact {
    padding: 3px !important;
  }
}

.admin-link, .sound-toggle {
  opacity: 0.7;
  transition: opacity 0.3s ease;
  margin-left: 8px;
}

.admin-link:hover, .sound-toggle:hover {
  opacity: 1;
}
</style> 