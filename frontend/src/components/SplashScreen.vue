<template>
  <div class="splash-screen" :class="{ 'fade-out': isExiting }">
    <div class="encryption-background">
      <div class="encryption-grid"></div>
      <div class="encryption-binary"></div>
      <div class="encryption-hex"></div>
    </div>
    
    <div class="particles-container">
      <div v-for="i in 50" :key="i" class="particle"></div>
    </div>
    
    <div class="logo-container" :class="{ 'logo-container-active': isActive }">
      <div class="shield-container">
        <div class="shield-outer"></div>
        <div class="shield-middle"></div>
        <div class="shield-inner"></div>
      </div>
      
      <div class="logo-wrapper">
        <img src="/icons/authberry-logo.png" alt="AuthBerry" class="logo" />
      </div>

      <div class="energy-waves">
        <div class="wave wave-1"></div>
        <div class="wave wave-2"></div>
        <div class="wave wave-3"></div>
      </div>
    </div>

    <div v-if="showPlayButton" class="play-button-container" @click="playAudio">
      <div class="play-button">
        <v-icon color="primary">mdi-play-circle-outline</v-icon>
        <span>Start</span>
      </div>
    </div>

    <div class="terms-container">
      <div class="terms-wrapper">
        <span 
          v-for="(term, index) in securityTerms" 
          :key="index" 
          class="security-term"
          :style="{ 
            animationDelay: `${index * 0.5}s`,
            opacity: currentTermIndex >= index ? 1 : 0
          }"
        >{{ term }}</span>
      </div>
    </div>

    <div class="loading-container">
      <div class="progress-text">System Initialization...</div>
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: `${loadingProgress}%` }"></div>
      </div>
    </div>

    <audio ref="audioElement" preload="auto">
      <source src="../assets/sounds/splash-screen.mp3" type="audio/mp3">
    </audio>
  </div>
</template>

<script>
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useSplashStore } from '@/stores/splash'
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'

export default {
  name: 'SplashScreen',
  setup() {
    const router = useRouter()
    const authStore = useAuthStore()
    const splashStore = useSplashStore()
    
    const audioElement = ref(null)
    const loadingProgress = ref(0)
    const isActive = ref(false)
    const isExiting = ref(false)
    const showSkipButton = ref(false)
    const currentTermIndex = ref(-1)
    const showPlayButton = ref(false)
    const audioPlaying = ref(false)
    
    // Security terms for typewriter effect
    const securityTerms = [
      'ENCRYPTING DATA',
      'VERIFYING IDENTITY',
      'SECURING CONNECTION',
      'GENERATING KEYS',
      'INITIALIZING PROTECTION'
    ]
    
    // Progress bar animation
    let progressInterval = null
    
    // Start progress bar animation
    const startProgressAnimation = () => {
      progressInterval = setInterval(() => {
        if (loadingProgress.value < 100) {
          loadingProgress.value += 100 / (9 * 10) // 9 seconds total, updating 10 times per second
        } else {
          clearInterval(progressInterval)
          progressInterval = null // Set to null after clearing
          exitSplashScreen()
        }
      }, 100)
    }
    
    // Start terms animation
    let termsInterval = null
    const startTermsAnimation = () => {
      termsInterval = setInterval(() => {
        if (currentTermIndex.value < securityTerms.length - 1) {
          currentTermIndex.value++
        } else {
          clearInterval(termsInterval)
          termsInterval = null // Set to null after clearing
        }
      }, 1500)
    }
    
    // Exit animation and navigate to dashboard
    const exitSplashScreen = () => {
      // Only proceed if not already exiting
      if (isExiting.value) return
      
      isExiting.value = true
      
      // Clear any remaining intervals to be safe
      if (progressInterval) {
        clearInterval(progressInterval)
        progressInterval = null
      }
      
      if (termsInterval) {
        clearInterval(termsInterval)
        termsInterval = null
      }
      
      // Set the splash seen flag using the store
      try {
        splashStore.markSplashAsShown()
      } catch (error) {
        console.error('Error marking splash as shown:', error)
      }
      
      // Wait for exit animation to complete before navigating
      setTimeout(() => {
        try {
          // Check if user is authenticated before navigating to dashboard
          if (authStore.isAuthenticated) {
            router.push('/dashboard').catch(err => {
              console.error('Navigation error:', err)
              // If navigation fails, try direct navigation
              window.location.href = '/dashboard'
            })
          } else {
            console.warn('User not authenticated, redirecting to login')
            router.push('/login').catch(err => {
              console.error('Navigation error:', err)
              window.location.href = '/login'
            })
          }
        } catch (error) {
          console.error('Error during navigation:', error)
          // Fallback to direct navigation
          window.location.href = '/dashboard'
        }
      }, 1000)
    }
    
    // Play audio manually (for browsers with autoplay restrictions)
    const playAudio = () => {
      if (audioElement.value) {
        try {
          audioElement.value.play()
            .then(() => {
              audioPlaying.value = true
              showPlayButton.value = false
              
              // Start animations if not already started
              if (!progressInterval) startProgressAnimation()
              if (!termsInterval) startTermsAnimation()
            })
            .catch((error) => {
              console.error('Audio playback issue encountered:', error)
            })
        } catch (error) {
          console.error('Error playing audio:', error)
        }
      }
    }
    
    // Lifecycle hooks
    onMounted(() => {
      // Show the splash screen content with a slight delay
      setTimeout(() => {
        isActive.value = true
      }, 300)
      
      // Start playing audio with a slight delay
      setTimeout(() => {
        if (audioElement.value) {
          // Handle autoplay restrictions by adding user interaction trigger
          const attemptPlay = () => {
            try {
              if (audioElement.value) {
                audioElement.value.volume = 1.0; // Ensure volume is set to max
                const playPromise = audioElement.value.play();
                
                if (playPromise !== undefined) {
                  playPromise.then(() => {
                    audioPlaying.value = true;
                    // Start animations
                    startProgressAnimation()
                    startTermsAnimation()
                  }).catch((error) => {
                    console.warn('Audio autoplay unavailable:', error);
                    // Show play button since autoplay was prevented
                    showPlayButton.value = true;
                  });
                }
              }
            } catch (error) {
              console.error('Error during audio play attempt:', error);
              // Ensure animations start even if audio fails
              startProgressAnimation();
              startTermsAnimation();
            }
          };
          
          attemptPlay();
        } else {
          // If audio element isn't available, still start animations
          startProgressAnimation();
          startTermsAnimation();
        }
      }, 500)
      
      // Only start animations automatically if we can play audio
      if (!showPlayButton.value) {
        // Start progress animation
        startProgressAnimation()
        
        // Start terms animation
        startTermsAnimation()
      }
    })
    
    onBeforeUnmount(() => {
      // Clean up intervals
      clearInterval(progressInterval)
      clearInterval(termsInterval)
      
      // Stop audio
      if (audioElement.value) {
        audioElement.value.pause()
      }
    })
    
    return {
      audioElement,
      loadingProgress,
      isActive,
      isExiting,
      showPlayButton,
      securityTerms,
      currentTermIndex,
      playAudio
    }
  }
}
</script>

<style lang="scss" scoped>
@use '../assets/scss/utils/variables' as vars;
@use '../assets/scss/utils/animations';

.splash-screen {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: vars.$background;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  overflow: hidden;
  transition: opacity 1s ease;
  
  &.fade-out {
    opacity: 0;
  }
}

/* Encryption Background */
.encryption-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  opacity: 0.2;
  z-index: 1;
  
  .encryption-grid {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-image: 
      linear-gradient(to right, rgba(vars.$primary-green, 0.1) 1px, transparent 1px),
      linear-gradient(to bottom, rgba(vars.$primary-green, 0.1) 1px, transparent 1px);
    background-size: 20px 20px;
    animation: gridMove 20s linear infinite;
  }
  
  .encryption-binary {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    font-family: monospace;
    color: rgba(vars.$primary-green, 0.2);
    font-size: 12px;
    overflow: hidden;
    
    &::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: repeating-linear-gradient(
        transparent 0%,
        transparent 97%,
        rgba(vars.$primary-green, 0.2) 100%
      );
      animation: binaryScroll 20s linear infinite;
    }
  }
  
  .encryption-hex {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    opacity: 0.15;
    background-image: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M54.627 0l.83.828-1.415 1.415L51.8 0h2.827zM5.373 0l-.83.828L5.96 2.243 8.2 0H5.374zM48.97 0l3.657 3.657-1.414 1.414L46.143 0h2.828zM11.03 0L7.372 3.657 8.787 5.07 13.857 0H11.03zm32.284 0L49.8 6.485 48.384 7.9l-7.9-7.9h2.83zm-24.57 0l-5.485 5.486 1.414 1.414 7.9-7.9h-2.83zm16.627 0l-1.414 1.414 3.657 3.657h-2.829L27.8 0h2.83zM10.97 0L9.555 1.414 5.9 5.07H8.73L16.628 0h-5.657zm5.657 0l4.242 4.242L18.456 7.9 13.8 0h2.83zm12.73 0l1.415 1.414 2.242-2.242L26.8 0h2.828zm-18.457 0L7.828 3.172 6.414 4.586 0 0h10.97zM27.8 0L22.344 5.457 23.757 6.87l9.9-9.9L27.8 0zm-12.73 0l-6.97 6.97 1.415 1.414 9.9-9.9L15.07 0H5.374zm36.456 0L33.657 8.172 32.244 9.586 39.8 0h2.128zm-40.628 0l-2.06 2.06L.824 3.414 0 0h1.2zm35.196 0l6.478 6.478L40.02 10.9l-12.673-12.7L38.628 0z' fill='%2300FF9C' fill-opacity='0.1' fill-rule='evenodd'/%3E%3C/svg%3E");
    animation: hexMove 30s linear infinite;
  }
}

/* Particles Effect */
.particles-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 2;
  overflow: hidden;
}

.particle {
  position: absolute;
  width: 4px;
  height: 4px;
  background-color: vars.$primary-green;
  border-radius: 50%;
  opacity: 0;
  animation: particleFloat 9s ease-in infinite;
  
  @for $i from 1 through 50 {
    &:nth-child(#{$i}) {
      left: random(100) * 1%;
      top: random(100) * 1%;
      animation-delay: random(9000) * 0.001s;
      animation-duration: (5 + random(4)) * 1s;
      transform: scale(0.3 + random(7) * 0.1);
      opacity: 0.1 + random(9) * 0.1;
    }
  }
}

/* Logo Container */
.logo-container {
  position: relative;
  width: 200px;
  height: 200px;
  margin-bottom: 40px;
  z-index: 10;
  opacity: 0;
  transform: scale(0.8);
  transition: all 1.5s cubic-bezier(0.34, 1.56, 0.64, 1);
  
  &-active {
    opacity: 1;
    transform: scale(1);
  }
}

/* Shield Animation */
.shield-container {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 9;
  
  .shield-outer,
  .shield-middle,
  .shield-inner {
    position: absolute;
    top: 50%;
    left: 50%;
    border-radius: 50%;
    transform: translate(-50%, -50%);
    opacity: 0;
    animation: shieldPulse 4s ease-in-out infinite;
  }
  
  .shield-outer {
    width: 200px;
    height: 200px;
    border: 2px solid rgba(vars.$primary-blue, 0.3);
    animation-delay: 0s;
  }
  
  .shield-middle {
    width: 160px;
    height: 160px;
    border: 3px solid rgba(vars.$primary-purple, 0.5);
    animation-delay: 0.5s;
  }
  
  .shield-inner {
    width: 120px;
    height: 120px;
    border: 4px solid rgba(vars.$primary-green, 0.7);
    animation-delay: 1s;
  }
}

/* Logo Wrapper */
.logo-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10;
  
  .logo {
    width: 120px;
    height: auto;
    animation: logoGlow 3s ease-in-out infinite alternate;
  }
}

/* Energy Waves */
.energy-waves {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 100%;
  height: 100%;
  z-index: 8;
  
  .wave {
    position: absolute;
    top: 50%;
    left: 50%;
    border-radius: 50%;
    transform: translate(-50%, -50%) scale(0);
    background: radial-gradient(
      circle,
      rgba(vars.$primary-green, 0.7) 0%,
      rgba(vars.$primary-blue, 0.2) 50%,
      transparent 70%
    );
    opacity: 0;
    animation: waveExpand 4s ease-out infinite;
    
    &-1 {
      width: 300px;
      height: 300px;
      animation-delay: 0s;
    }
    
    &-2 {
      width: 350px;
      height: 350px;
      animation-delay: 1s;
    }
    
    &-3 {
      width: 400px;
      height: 400px;
      animation-delay: 2s;
    }
  }
}

/* Security Terms */
.terms-container {
  position: relative;
  margin-bottom: 40px;
  z-index: 10;
  height: 30px;
  
  .terms-wrapper {
    position: relative;
    text-align: center;
  }
  
  .security-term {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    font-family: monospace;
    font-size: 1.4rem;
    letter-spacing: 2px;
    text-align: center;
    color: vars.$primary-green;
    transition: opacity 0.5s ease;
    animation: typewriter 1.5s steps(20, end);
    white-space: nowrap;
    overflow: hidden;
    
    &::after {
      content: '|';
      animation: blink 1s infinite;
    }
  }
}

/* Loading Container */
.loading-container {
  position: relative;
  width: 80%;
  max-width: 400px;
  margin-top: 20px;
  z-index: 10;
  
  .progress-text {
    font-family: monospace;
    font-size: 0.9rem;
    color: rgba(vars.$primary-green, 0.7);
    text-align: center;
    margin-bottom: 10px;
    letter-spacing: 1px;
  }
  
  .progress-bar {
    width: 100%;
    height: 4px;
    background-color: rgba(255, 255, 255, 0.1);
    border-radius: 2px;
    overflow: hidden;
    
    .progress-fill {
      height: 100%;
      background: linear-gradient(
        90deg,
        vars.$primary-green,
        vars.$primary-blue,
        vars.$primary-purple,
        vars.$primary-blue,
        vars.$primary-green
      );
      background-size: 200% 100%;
      animation: gradientShift 2s linear infinite;
      transition: width 0.1s linear;
    }
  }
}

/* Play Button */
.play-button-container {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 100;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  
  .play-button {
    background-color: rgba(vars.$background, 0.6);
    border: 1px solid vars.$primary-green;
    border-radius: 50%;
    width: 80px;
    height: 80px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    box-shadow: 0 0 20px rgba(vars.$primary-green, 0.5);
    animation: pulse 2s infinite;
    
    .v-icon {
      font-size: 36px;
      color: vars.$primary-green;
    }
    
    span {
      color: vars.$primary-green;
      font-size: 0.8rem;
      margin-top: 4px;
    }
  }
}

/* Animations */
@keyframes gridMove {
  0% { background-position: 0 0; }
  100% { background-position: 20px 20px; }
}

@keyframes binaryScroll {
  0% { transform: translateY(0); }
  100% { transform: translateY(100%); }
}

@keyframes hexMove {
  0% { background-position: 0 0; }
  100% { background-position: 100px 100px; }
}

@keyframes particleFloat {
  0% {
    transform: translateY(0) scale(0);
    opacity: 0;
  }
  20% {
    opacity: 0.7;
  }
  100% {
    transform: translateY(-100vh) scale(1);
    opacity: 0;
  }
}

@keyframes shieldPulse {
  0% {
    transform: translate(-50%, -50%) scale(0.9);
    opacity: 0;
  }
  50% {
    opacity: 1;
  }
  100% {
    transform: translate(-50%, -50%) scale(1.2);
    opacity: 0;
  }
}

@keyframes logoGlow {
  0% {
    filter: drop-shadow(0 0 5px rgba(vars.$primary-green, 0.5));
  }
  50% {
    filter: drop-shadow(0 0 15px rgba(vars.$primary-blue, 0.7));
  }
  100% {
    filter: drop-shadow(0 0 20px rgba(vars.$primary-purple, 0.9));
  }
}

@keyframes waveExpand {
  0% {
    transform: translate(-50%, -50%) scale(0);
    opacity: 0.7;
  }
  100% {
    transform: translate(-50%, -50%) scale(1);
    opacity: 0;
  }
}

@keyframes typewriter {
  from { width: 0; }
  to { width: 100%; }
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

@keyframes gradientShift {
  0% { background-position: 0% 0; }
  100% { background-position: 200% 0; }
}

@keyframes pulse {
  0% {
    transform: scale(1);
    box-shadow: 0 0 10px rgba(vars.$primary-green, 0.5);
  }
  50% {
    transform: scale(1.05);
    box-shadow: 0 0 20px rgba(vars.$primary-green, 0.7);
  }
  100% {
    transform: scale(1);
    box-shadow: 0 0 10px rgba(vars.$primary-green, 0.5);
  }
}
</style> 