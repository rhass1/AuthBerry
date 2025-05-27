import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useSplashStore = defineStore('splash', () => {
  // State
  const splashShown = ref(false)

  // Actions
  function markSplashAsShown() {
    // Only mark if not already shown
    if (splashShown.value === true) {
      return
    }

    splashShown.value = true
    localStorage.setItem('splashScreenSeen', 'true')
  }

  function initialize() {
    // Check if the splash screen has been shown in this session
    const hasSeenSplash = localStorage.getItem('splashScreenSeen') === 'true'
    splashShown.value = hasSeenSplash
  }

  return {
    splashShown,
    markSplashAsShown,
    initialize
  }
})