import { defineStore } from 'pinia'
import { ref } from 'vue'
import soundService from '../services/SoundService'

export const useSoundStore = defineStore('sound', () => {
  // State
  const enabled = ref(true)
  const volume = ref(0.5)

  // Get values from localStorage if available
  const initFromStorage = () => {
    const storedEnabled = localStorage.getItem('soundEnabled')
    const storedVolume = localStorage.getItem('soundVolume')
    
    if (storedEnabled !== null) {
      enabled.value = storedEnabled === 'true'
      soundService.toggle(enabled.value)
    }
    
    if (storedVolume !== null) {
      volume.value = parseFloat(storedVolume)
    }
  }
  
  // Initialize on store creation
  initFromStorage()
  
  // Actions
  const toggleSound = (state = null) => {
    if (state !== null) {
      enabled.value = Boolean(state)
    } else {
      enabled.value = !enabled.value
    }
    
    // Update sound service
    soundService.toggle(enabled.value)
    
    // Save to localStorage
    localStorage.setItem('soundEnabled', enabled.value.toString())
    
    return enabled.value
  }
  
  const setVolume = (newVolume) => {
    // Ensure volume is between 0 and 1
    volume.value = Math.max(0, Math.min(1, newVolume))
    
    // Save to localStorage
    localStorage.setItem('soundVolume', volume.value.toString())
    
    return volume.value
  }
  
  return {
    enabled,
    volume,
    toggleSound,
    setVolume
  }
}) 