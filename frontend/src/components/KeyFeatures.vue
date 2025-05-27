<template>
  <div class="key-features-container">
    <h2 class="text-h4 text-center feature-heading mb-4 mb-sm-6">Key Features</h2>
    
    <v-row dense>
      <v-col
        v-for="(feature, index) in features"
        :key="index"
        cols="12" 
        sm="12"
        md="4"
        class="d-flex pa-2"
      >
        <div 
          class="feature-card d-flex flex-column align-center text-center pa-3"
          :class="`feature-${feature.color}`"
        >
          <div class="feature-icon-wrapper mb-2">
            <v-icon :size="$vuetify.display.xs ? 24 : 32" :color="feature.color">{{ feature.icon }}</v-icon>
            <div class="icon-glow" :style="{ backgroundColor: getGlowColor(feature.color) }"></div>
          </div>
          <h3 class="text-body-1 text-sm-h6 font-weight-bold mb-1" :class="`text-${feature.color}`">{{ feature.title }}</h3>
          <p class="text-caption text-sm-body-2 description-text">{{ feature.description }}</p>
          <div class="cyber-corner top-left"></div>
          <div class="cyber-corner top-right"></div>
          <div class="cyber-corner bottom-left"></div>
          <div class="cyber-corner bottom-right"></div>
        </div>
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { ref, defineProps, defineEmits } from 'vue'

const props = defineProps({
  features: {
    type: Array,
    default: () => []
  }
})

const getGlowColor = (color) => {
  const colorMap = {
    'success': 'rgba(76, 175, 80, 0.4)',
    'info': 'rgba(0, 136, 255, 0.4)',
    'warning': 'rgba(255, 193, 7, 0.4)'
  }
  
  return colorMap[color] || 'rgba(0, 255, 156, 0.4)'
}
</script>

<style scoped>
.key-features-container {
  width: 100%;
  padding: 0 4px;
}

.feature-heading {
  font-family: 'VT323', monospace;
  letter-spacing: 1px;
  color: rgba(255, 255, 255, 0.8);
  text-transform: uppercase;
  font-weight: bold;
  text-shadow: 0 0 8px rgba(0, 255, 156, 0.7);
}

.feature-card {
  height: 100%;
  width: 100%;
  border-radius: 8px;
  background: rgba(16, 23, 35, 0.7);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  position: relative;
  overflow: hidden;
  box-shadow: 0 0 15px rgba(0, 0, 0, 0.7), inset 0 0 30px rgba(0, 0, 0, 0.5);
}

.feature-success {
  box-shadow: 0 0 15px rgba(0, 0, 0, 0.7), inset 0 0 30px rgba(0, 0, 0, 0.5), 0 0 5px rgba(76, 175, 80, 0.5);
}

.feature-info {
  box-shadow: 0 0 15px rgba(0, 0, 0, 0.7), inset 0 0 30px rgba(0, 0, 0, 0.5), 0 0 5px rgba(0, 136, 255, 0.5);
}

.feature-warning {
  box-shadow: 0 0 15px rgba(0, 0, 0, 0.7), inset 0 0 30px rgba(0, 0, 0, 0.5), 0 0 5px rgba(255, 193, 7, 0.5);
}

.cyber-corner {
  position: absolute;
  width: 8px;
  height: 8px;
  z-index: 2;
}

.top-left {
  top: 0;
  left: 0;
  border-top: 2px solid rgba(0, 255, 156, 0.7);
  border-left: 2px solid rgba(0, 255, 156, 0.7);
}

.top-right {
  top: 0;
  right: 0;
  border-top: 2px solid rgba(0, 255, 156, 0.7);
  border-right: 2px solid rgba(0, 255, 156, 0.7);
}

.bottom-left {
  bottom: 0;
  left: 0;
  border-bottom: 2px solid rgba(0, 255, 156, 0.7);
  border-left: 2px solid rgba(0, 255, 156, 0.7);
}

.bottom-right {
  bottom: 0;
  right: 0;
  border-bottom: 2px solid rgba(0, 255, 156, 0.7);
  border-right: 2px solid rgba(0, 255, 156, 0.7);
}

.feature-icon-wrapper {
  position: relative;
  padding: 0.8rem;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.05);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1;
  box-shadow: 0 0 15px rgba(0, 0, 0, 0.5);
}

.icon-glow {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  filter: blur(15px);
  opacity: 0.7;
  z-index: -1;
}

.description-text {
  line-height: 1.3;
  color: rgba(255, 255, 255, 0.8);
  max-width: 60%;
  margin: 0 auto;
}

.text-success {
  color: rgb(76, 175, 80);
}

.text-info {
  color: rgb(0, 136, 255);
}

.text-warning {
  color: rgb(255, 193, 7);
}

@media (max-width: 600px) {
  .key-features-container {
    padding: 0 0.5rem;
  }
  
  .feature-card {
    padding: 0.5rem;
    margin-bottom: 0;
  }
  
  .feature-heading {
    margin-bottom: 0.5rem !important;
    font-size: 1.4rem !important;
  }
  
  .feature-icon-wrapper {
    padding: 0.5rem;
    margin-bottom: 0.3rem !important;
  }
  
  .cyber-corner {
    width: 5px;
    height: 5px;
  }
  
  .description-text {
    max-width: 100%;
    line-height: 1.2;
    margin-bottom: 0;
  }
}
</style> 