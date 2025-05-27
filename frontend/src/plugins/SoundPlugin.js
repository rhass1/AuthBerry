import soundService from '../services/SoundService'
import { clickSound } from '../directives/clickSound'
import { useSoundStore } from '../stores/sound'

/**
 * Sound plugin for Vue
 * Registers the click-sound directive and automatically applies it to all buttons in the app
 */
export const SoundPlugin = {
  install(app) {
    // Register the directive
    app.directive('click-sound', clickSound)
    
    // Preload sounds
    soundService.preload('buttonClick', new URL('../assets/sounds/button-click.mp3', import.meta.url).href)
      .catch(error => {
        // Continue if sound loading fails, app should work without sounds
      })
    
    // Add a mutation observer to add the directive to all buttons automatically
    if (typeof window !== 'undefined') {
      const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          if (mutation.type === 'childList' && mutation.addedNodes.length) {
            mutation.addedNodes.forEach(node => {
              if (node.nodeType === Node.ELEMENT_NODE) {
                // Check for buttons in the added node itself
                if (node.tagName.toLowerCase() === 'button' || 
                    (node.classList && node.classList.contains('v-btn'))) {
                  applyDirectiveToElement(node);
                }
                
                // Check for buttons in children of the added node
                const buttons = node.querySelectorAll('button, .v-btn');
                buttons.forEach(applyDirectiveToElement);
              }
            });
          }
        });
      });
      
      // Start observing the document
      window.addEventListener('DOMContentLoaded', () => {
        observer.observe(document.body, {
          childList: true,
          subtree: true
        });
        
        // Apply to existing buttons
        const buttons = document.querySelectorAll('button, .v-btn');
        buttons.forEach(applyDirectiveToElement);
      });
      
      // Function to apply the click sound to elements
      function applyDirectiveToElement(el) {
        // Skip if already has the click handler
        if (el._clickSoundHandler) return;
        
        // Apply the click handler
        el._clickSoundHandler = () => {
          // Get the current volume from store
          // We use a function to get the store to avoid using it before Pinia is initialized
          const getVolumeFromStore = () => {
            try {
              const soundStore = useSoundStore();
              return soundStore.volume;
            } catch (error) {
              return 0.5; // Default if store not available
            }
          };
          
          soundService.play('buttonClick', getVolumeFromStore());
        };
        
        el.addEventListener('click', el._clickSoundHandler);
      }
    }
    
    // Expose soundService to components
    app.config.globalProperties.$sound = soundService;
  }
};

export default SoundPlugin; 