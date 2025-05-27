/**
 * Sound Service for managing audio effects
 */
class SoundService {
  constructor() {
    this.sounds = {};
    this.enabled = true;
  }

  /**
   * Preload a sound file
   * @param {string} id - Unique identifier for the sound
   * @param {string} path - Path to the sound file
   * @returns {Promise} - Promise that resolves when the sound is loaded
   */
  preload(id, path) {
    return new Promise((resolve, reject) => {
      const audio = new Audio();
      audio.src = path;
      
      audio.addEventListener('canplaythrough', () => {
        this.sounds[id] = audio;
        resolve(audio);
      }, { once: true });
      
      audio.addEventListener('error', (error) => {
        reject(error);
      }, { once: true });
      
      // Start loading the audio file
      audio.load();
    });
  }

  /**
   * Play a sound by its ID
   * @param {string} id - Unique identifier for the sound
   * @param {number} volume - Volume level (0-1)
   * @returns {Promise} - Promise that resolves when the sound starts playing
   */
  play(id, volume = 0.5) {
    if (!this.enabled || !this.sounds[id]) return Promise.resolve();
    
    // Clone the audio to allow for multiple simultaneous plays
    const sound = this.sounds[id].cloneNode();
    sound.volume = volume;
    
    return sound.play().catch(error => {
      // Autoplay policy might block this, but we should silently fail
      // instead of breaking the UI functionality
    });
  }

  /**
   * Toggle sound on/off
   * @param {boolean} state - If provided, set the enabled state to this value
   * @returns {boolean} - The new enabled state
   */
  toggle(state = null) {
    if (state !== null) {
      this.enabled = Boolean(state);
    } else {
      this.enabled = !this.enabled;
    }
    return this.enabled;
  }
}

export default new SoundService(); 