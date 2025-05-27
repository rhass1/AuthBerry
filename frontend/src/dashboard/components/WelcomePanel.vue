<template>
  <!-- Loading state -->
  <div v-if="loading" class="welcome-panel-wrapper">
    <div class="cyber-loading-container">
      <div class="cyber-spinner">
        <div class="spinner-ring"></div>
        <div class="spinner-ring"></div>
        <div class="spinner-dot"></div>
      </div>
      <div class="loading-text">Loading your secure vault...</div>
    </div>
  </div>
  
  <!-- Empty state - No secrets or folders yet -->
  <div v-else-if="isEmpty" class="welcome-panel-wrapper empty-state">
    <div class="centered-content">
      <div class="welcome-header">
        <h1 class="glitch-text" :class="{ 'mobile-header': isMobile }">Welcome to Your Secure Hub</h1>
        <div class="welcome-divider"></div>
      </div>
      
      <div class="welcome-content">
        <p>Get started by creating your first secret or folder</p>
        
        <div class="action-buttons">
          <v-btn 
            color="primary" 
            prepend-icon="mdi-file-lock"
            @click="$emit('create-secret')"
            class="neon-btn mr-4"
            :block="isMobile"
            :size="isMobile ? 'large' : 'default'"
          >
            Create Secret
          </v-btn>
          <v-btn 
            color="info" 
            prepend-icon="mdi-folder"
            @click="$emit('create-folder')"
            class="neon-btn"
            :block="isMobile"
            :size="isMobile ? 'large' : 'default'"
          >
            Create Folder
          </v-btn>
        </div>
      </div>
    </div>
  </div>
  
  <!-- Regular welcome panel - User has folders/secrets but none selected -->
  <div v-else class="welcome-panel-wrapper">
    <div class="centered-content">
      <div class="welcome-header">
        <h1 class="glitch-text" :class="{ 'mobile-header': isMobile }">Welcome to Your Secure Hub</h1>
        <div class="welcome-divider"></div>
      </div>
      
      <div class="welcome-content">
        <p v-if="!isMobile">Select a secret or folder from the list to view its details, or create a new one to get started.</p>
        <p v-else>Select an item to view details</p>
        
        <div v-if="!isMobile" class="welcome-features">
          <div class="feature-card">
            <v-icon size="large" color="primary">mdi-shield-lock</v-icon>
            <h3>Secure Storage</h3>
            <p>Your secrets are encrypted</p>
          </div>
          
          <div class="feature-card">
            <v-icon size="large" color="info">mdi-folder-multiple</v-icon>
            <h3>Organization</h3>
            <p>Keep your secrets organized in folders</p>
          </div>
          
          <div class="feature-card">
            <v-icon size="large" color="success">mdi-account-multiple</v-icon>
            <h3>Collaboration</h3>
            <p>Share secrets securely with others</p>
          </div>
        </div>
        
        <div class="action-buttons">
          <v-btn 
            color="primary" 
            prepend-icon="mdi-file-lock"
            @click="$emit('create-secret')"
            class="neon-btn mr-4"
            :block="isMobile"
            :size="isMobile ? 'large' : 'default'"
          >
            Create Secret
          </v-btn>
          <v-btn 
            color="info" 
            prepend-icon="mdi-folder"
            @click="$emit('create-folder')"
            class="neon-btn"
            :block="isMobile"
            :size="isMobile ? 'large' : 'default'"
          >
            Create Folder
          </v-btn>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  loading: {
    type: Boolean,
    default: false
  },
  isEmpty: {
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

defineEmits(['create-secret', 'create-folder'])
</script>

<style scoped>
.welcome-panel-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: clamp(12px, 3vh, 24px);
  text-align: center;
  overflow-y: auto;
  max-height: 100%;
}

.centered-content {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  max-width: 800px;
  width: 100%;
  height: 100%;
  max-height: 800px;
  gap: clamp(16px, 3vh, 28px);
}

.welcome-header {
  width: 100%;
}

.glitch-text {
  font-size: clamp(1.8rem, 5vw, 2.5rem);
  font-weight: 700;
  color: #fff;
  position: relative;
  text-shadow: 
    0 0 3px rgba(0, 255, 156, 0.6),
    0 0 5px rgba(0, 255, 156, 0.3);
  background: linear-gradient(90deg, rgba(0, 255, 156, 0.9), rgba(0, 136, 255, 0.9));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: 1px;
  animation: textBreathe 4s infinite alternate;
}

.mobile-header {
  font-size: 1.8rem;
  margin-bottom: 10px;
}

.welcome-divider {
  width: clamp(120px, 20%, 150px);
  height: 3px;
  background: linear-gradient(90deg, #00FF9C, #00E6CC, #00A3FF);
  margin: clamp(12px, 2vh, 16px) auto;
  position: relative;
  border-radius: 3px;
}

.welcome-divider::before,
.welcome-divider::after {
  content: '';
  position: absolute;
  top: 0;
  width: 5px;
  height: 3px;
  background: #fff;
  opacity: 0;
  filter: blur(2px);
  animation: sparkle 2s infinite;
}

.welcome-divider::before {
  left: 30%;
  animation-delay: 0.5s;
}

.welcome-divider::after {
  left: 70%;
  animation-delay: 1s;
}

.welcome-content {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.welcome-content p {
  font-size: clamp(0.9rem, 2vw, 1.1rem);
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: clamp(16px, 3vh, 24px);
  line-height: 1.5;
}

.welcome-features {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: clamp(16px, 3vw, 24px);
  margin-bottom: clamp(20px, 3vh, 30px);
}

.feature-card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  padding: clamp(16px, 3vw, 24px);
  width: clamp(150px, 25%, 200px);
  transition: all 0.3s ease;
  border: 1px solid rgba(0, 255, 156, 0.15);
  position: relative;
  overflow: hidden;
}

.feature-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(0, 255, 156, 0.7), transparent);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
}

.feature-card:hover::before {
  opacity: 1;
}

.feature-card h3 {
  margin-top: 16px;
  font-size: 1.2rem;
  font-weight: 600;
  color: #fff;
}

.feature-card p {
  font-size: 0.9rem;
  margin-top: 8px;
  margin-bottom: 0;
  color: rgba(255, 255, 255, 0.6);
}

.action-buttons {
  display: flex;
  justify-content: center;
  margin-top: clamp(12px, 2vh, 20px);
}

/* For mobile */
@media (max-width: 767px) {
  .welcome-panel-wrapper {
    padding: 12px;
    justify-content: center;
  }
  
  .centered-content {
    gap: 16px;
  }
  
  .welcome-content p {
    font-size: 1rem;
    margin-bottom: 16px;
  }
  
  .action-buttons {
    flex-direction: column;
    gap: 12px;
    width: 100%;
  }
  
  .action-buttons .v-btn {
    margin-right: 0 !important;
  }
}

/* Cyber loading animation */
.cyber-loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
}

.cyber-spinner {
  position: relative;
  width: 60px;
  height: 60px;
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
  width: 10px;
  height: 10px;
  background: #8C52FF;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  box-shadow: 0 0 10px rgba(140, 82, 255, 0.7);
}

.loading-text {
  font-size: 1.2rem;
  color: rgba(255, 255, 255, 0.7);
  animation: pulse 1.5s infinite alternate;
}

/* Empty state */
.empty-state {
  justify-content: center;
}

/* Animations */
@keyframes sparkle {
  0%, 100% { opacity: 0; }
  50% { opacity: 1; }
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes pulse {
  0% { opacity: 0.5; }
  100% { opacity: 1; }
}

@keyframes textBreathe {
  0% { 
    filter: brightness(0.95); 
    text-shadow: 
      0 0 2px rgba(0, 255, 156, 0.5),
      0 0 5px rgba(0, 255, 156, 0.2);
  }
  100% { 
    filter: brightness(1.05); 
    text-shadow: 
      0 0 3px rgba(0, 255, 156, 0.6),
      0 0 7px rgba(0, 255, 156, 0.3);
  }
}

/* Responsive design */
@media (max-width: 600px) {
  .glitch-text {
    font-size: 1.8rem;
  }
  
  .welcome-divider {
    width: 120px;
    margin: 12px auto;
  }
  
  .feature-card {
    width: 100%;
    padding: 16px;
  }
}

/* Neon button styling */
.neon-btn {
  position: relative;
  overflow: hidden;
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
</style> 