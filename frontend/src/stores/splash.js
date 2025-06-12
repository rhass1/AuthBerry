import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useSplashStore = defineStore('splash', () => {
  // State
  const splashShown = ref(false)
  const splashVisible = ref(false)
  const splashMessage = ref('')

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

  function resetSplashState() {
    // Reset the splash state so it can be shown again
    splashShown.value = false
    localStorage.removeItem('splashScreenSeen')
  }

  function showSplash(message = '') {
    // Show the splash screen with an optional message
    splashVisible.value = true
    splashMessage.value = message
  }

  function hideSplash() {
    // Hide the splash screen
    splashVisible.value = false
    splashMessage.value = ''
  }

  return {
    splashShown,
    splashVisible,
    splashMessage,
    markSplashAsShown,
    initialize,
    resetSplashState,
    showSplash,
    hideSplash
  }
})