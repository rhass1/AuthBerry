import soundService from '../services/SoundService';

/**
 * Vue directive to add click sound to buttons
 * Usage: v-click-sound or v-click-sound="0.3" (to set custom volume)
 */
export const clickSound = {
  beforeMount(el, binding) {
    // Get volume from binding value or use default (0.5)
    const volume = typeof binding.value === 'number' ? binding.value : 0.5;
    
    // Add click event listener to play sound
    el._clickSoundHandler = () => {
      soundService.play('buttonClick', volume);
    };
    
    el.addEventListener('click', el._clickSoundHandler);
  },
  
  unmounted(el) {
    // Clean up event listener when directive is removed
    if (el._clickSoundHandler) {
      el.removeEventListener('click', el._clickSoundHandler);
      delete el._clickSoundHandler;
    }
  }
};

export default clickSound; 