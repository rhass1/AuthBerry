<template>
  <SplashScreen />
</template>

<script>
import SplashScreen from '@/components/SplashScreen.vue'
import { useSplashStore } from '@/stores/splash'
import { onMounted, onBeforeUnmount } from 'vue'

export default {
  name: 'SplashView',
  components: {
    SplashScreen
  },
  setup() {
    const splashStore = useSplashStore()
    
    // Don't mark splash as shown on mount - let SplashScreen component do this
    // when it completes animation, so the user actually sees the splash screen
    
    return {}
  }
}
</script> 