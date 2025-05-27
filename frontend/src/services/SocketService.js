import { io } from 'socket.io-client'
import CryptoService from './CryptoService'

class SocketService {
  constructor() {
    this.socket = null
    this.baseURL = window.location.origin
    this.connected = false
    this.authenticated = false
    this.cryptoState = {
      privateKey: null,
      publicKey: null,
      serverPublicKey: null,
      sharedKey: null,
      keyExchangeComplete: false
    }
    this.eventHandlers = {}
    this.pendingMessages = []
  }

  /**
   * Initialize the Socket.IO connection
   */
  init() {
    if (this.socket) {
      return
    }

    // Create a new Socket.IO instance
    this.socket = io(this.baseURL, {
      autoConnect: true,
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000
    })

    // Set up event listeners
    this.socket.on('connect', this.handleConnect.bind(this))
    this.socket.on('disconnect', this.handleDisconnect.bind(this))
    this.socket.on('error', this.handleError.bind(this))
    this.socket.on('server_public_key', this.handleServerPublicKey.bind(this))
    this.socket.on('key_exchange_complete', this.handleKeyExchangeComplete.bind(this))
    this.socket.on('authenticated', this.handleAuthenticated.bind(this))
    this.socket.on('auth_error', this.handleAuthError.bind(this))

    // Setup custom event listeners
    this.setupCustomEventListeners()

    return this.socket
  }

  /**
   * Handle socket connection
   */
  async handleConnect() {
    this.connected = true

    // Initiate key exchange
    await this.initiateKeyExchange()
  }

  /**
   * Handle socket disconnection
   */
  handleDisconnect() {
    this.connected = false
    this.authenticated = false
    this.cryptoState.keyExchangeComplete = false

    // Clear sensitive data
    this.cryptoState.privateKey = null
    this.cryptoState.publicKey = null
    this.cryptoState.serverPublicKey = null
    this.cryptoState.sharedKey = null
  }

  /**
   * Handle socket error
   * @param {Object} error - Error object
   */
  handleError(error) {
    this.emitLocalEvent('error', error)
  }

  /**
   * Set up custom event listeners
   */
  setupCustomEventListeners() {
    // Authentication responses
    this.socket.on('login_success', async (data) => {
      try {
        let decryptedData;
        if (data.encrypted) {
          try {
            decryptedData = await this.decrypt(data.encrypted);
          } catch (decryptError) {
            // Check if data might be sent unencrypted for compatibility
            if (data.user && data.tokens) {
              decryptedData = data;
            } else {
              throw decryptError;
            }
          }
        } else if (data.user && data.tokens) {
          // Fallback for unencrypted response
          decryptedData = data;
        } else {
          throw new Error('Invalid login response format');
        }

        this.emitLocalEvent('login_success', decryptedData);
      } catch (error) {
        this.emitLocalEvent('error', { message: 'Failed to process login response' });
        this.emitLocalEvent('login_error', { message: 'Failed to process login response' });
      }
    });

    this.socket.on('login_error', async (data) => {
      try {
        let errorData = { message: data.message || 'Login failed' };

        if (data.encrypted) {
          try {
            errorData = await this.decrypt(data.encrypted);
          } catch (decryptError) {
            // Keep the original error message if available
            if (data.message) {
              errorData = { message: data.message };
            } else if (data.error) {
              errorData = { message: data.error };
            }
          }
        } else if (data.error) {
          errorData = { message: data.error };
        }

        this.emitLocalEvent('login_error', errorData);
      } catch (error) {
        this.emitLocalEvent('error', { message: 'Failed to process login error' });
        this.emitLocalEvent('login_error', { message: 'Failed to process login error' });
      }
    });

    this.socket.on('register_success', async (data) => {
      try {
        let decryptedData;
        if (data.encrypted) {
          try {
            decryptedData = await this.decrypt(data.encrypted);
          } catch (decryptError) {
            // Check if data might be sent unencrypted for compatibility
            if (data.user && data.tokens) {
              decryptedData = data;
            } else {
              throw decryptError;
            }
          }
        } else if (data.user && data.tokens) {
          // Fallback for unencrypted response
          decryptedData = data;
        } else {
          throw new Error('Invalid register response format');
        }

        this.emitLocalEvent('register_success', decryptedData);
      } catch (error) {
        this.emitLocalEvent('error', { message: 'Failed to process registration response' });
        this.emitLocalEvent('register_error', { message: 'Failed to process registration response' });
      }
    });

    this.socket.on('register_error', async (data) => {
      try {
        let errorData = { message: data.message || 'Registration failed' };

        if (data.encrypted) {
          try {
            errorData = await this.decrypt(data.encrypted);
          } catch (decryptError) {
            // Keep the original error message if available
            if (data.message) {
              errorData = { message: data.message };
            } else if (data.error) {
              errorData = { message: data.error };
            }
          }
        } else if (data.error) {
          errorData = { message: data.error };
        }

        this.emitLocalEvent('register_error', errorData);
      } catch (error) {
        this.emitLocalEvent('error', { message: 'Failed to process registration error' });
        this.emitLocalEvent('register_error', { message: 'Failed to process registration error' });
      }
    });

    // Secrets and folders
    this.socket.on('secrets', async (data) => {
      try {
        let decryptedData;
        if (data.encrypted) {
          try {
            decryptedData = await this.decrypt(data.encrypted);
          } catch (decryptError) {
            // Check if data might be sent unencrypted for compatibility
            if (Array.isArray(data.secrets) || data.secrets) {
              decryptedData = data;
            } else {
              throw decryptError;
            }
          }
        } else if (Array.isArray(data.secrets) || data.secrets) {
          // Fallback for unencrypted response
          decryptedData = data;
        } else {
          throw new Error('Invalid secrets response format');
        }

        this.emitLocalEvent('secrets', decryptedData);
      } catch (error) {
        this.emitLocalEvent('error', { message: 'Failed to process secrets data' });
      }
    })

    this.socket.on('secret', async (data) => {
      try {
        let decryptedData;
        if (data.encrypted) {
          try {
            decryptedData = await this.decrypt(data.encrypted);
          } catch (decryptError) {
            // Check if data might be sent unencrypted for compatibility
            if (data.id && data.name && data.type) {
              decryptedData = data;
            } else {
              throw decryptError;
            }
          }
        } else if (data.id && data.name && data.type) {
          // Fallback for unencrypted response
          decryptedData = data;
        } else {
          throw new Error('Invalid secret response format');
        }

        this.emitLocalEvent('secret', decryptedData);
      } catch (error) {
        this.emitLocalEvent('error', { message: 'Failed to process secret data' });
      }
    })

    this.socket.on('secret_created', async (data) => {
      try {
        // Only process encrypted events
        if (!data.encrypted) {
          return;
        }

        let decryptedData;
        try {
          decryptedData = await this.decrypt(data.encrypted);
        } catch (decryptError) {
          return;
        }

        if (!decryptedData?.secret) {
          return;
        }

        this.emitLocalEvent('secret_created', decryptedData);
      } catch (error) {
        // Error handling secret created (console.error removed)
      }
    })

    this.socket.on('folders', async (data) => {
      try {
        // Check if data is already in the expected format
        if (Array.isArray(data) || (data && typeof data === 'object' && 'folders' in data)) {
          this.emitLocalEvent('folders', data);
          return;
        }

        // Handle encrypted data
        if (data.encrypted) {
          try {
            const decrypted = await this.decrypt(data.encrypted);
            this.emitLocalEvent('folders', decrypted);
          } catch (error) {
            // Fallback to original data
            this.emitLocalEvent('folders', data);
          }
        } else {
          this.emitLocalEvent('folders', data);
        }
      } catch (error) {
        // Error handling folders (console.error removed)
      }
    })

    this.socket.on('folder', async (data) => {
      try {
        // Check if data is already in the expected format
        if (data && typeof data === 'object' && 'id' in data) {
          this.emitLocalEvent('folder', data);
          return;
        }

        // Handle encrypted data
        if (data.encrypted) {
          try {
            const decrypted = await this.decrypt(data.encrypted);
            this.emitLocalEvent('folder', decrypted);
          } catch (error) {
            // Fallback to original data
            this.emitLocalEvent('folder', data);
          }
        } else {
          this.emitLocalEvent('folder', data);
        }
      } catch (error) {
        // Error handling folder (console.error removed)
      }
    })

    this.socket.on('folder_created', async (data) => {
      try {
        // Check if data is already in the expected format for folder creation
        if (data && typeof data === 'object' && ('folder_id' in data || 'id' in data)) {
          // Transform if needed
          if (data.folder_id && !data.id) {
            data = {
              id: data.folder_id,
              name: data.folder_name || 'New Folder',
              owner_id: data.owner_id,
              parent_id: data.parent_id
            };
          }

          this.emitLocalEvent('folder_created', data);
          return;
        }

        // Handle encrypted data
        if (data.encrypted) {
          try {
            const decrypted = await this.decrypt(data.encrypted);
            this.emitLocalEvent('folder_created', decrypted);
          } catch (error) {
            // Fallback to original data
            this.emitLocalEvent('folder_created', data);
          }
        } else {
          this.emitLocalEvent('folder_created', data);
        }
      } catch (error) {
        // Error handling folder created (console.error removed)
      }
    })
  }

  /**
   * Handle the server's public key
   * @param {Object} data - Data containing the server's public key
   */
  async handleServerPublicKey(data) {
    try {
      // Import the server's public key
      const serverPublicKey = await CryptoService.importPublicKey(data.public_key)
      this.cryptoState.serverPublicKey = serverPublicKey

      // Derive the shared secret
      this.cryptoState.sharedKey = await CryptoService.deriveSharedSecret(
        this.cryptoState.privateKey,
        this.cryptoState.serverPublicKey
      )

      // Send our public key to the server
      this.socket.emit('client_public_key', {
        public_key: this.cryptoState.publicKeyBase64
      })

    } catch (error) {
      this.emitLocalEvent('error', { message: 'Failed to process server public key' })
    }
  }

  /**
   * Handle key exchange completion
   */
  handleKeyExchangeComplete() {
    this.cryptoState.keyExchangeComplete = true
    this.emitLocalEvent('key_exchange_complete', {})

    // Process any pending messages
    this.processPendingMessages()
  }

  /**
   * Handle authentication success
   * @param {Object} data - Authentication data
   */
  handleAuthenticated(data) {
    this.authenticated = true
    this.emitLocalEvent('authenticated', data)
  }

  /**
   * Handle authentication error
   * @param {Object} error - Error object
   */
  handleAuthError(error) {
    this.authenticated = false
    this.emitLocalEvent('auth_error', error)
  }

  /**
   * Initiate key exchange
   */
  async initiateKeyExchange() {
    try {
      // Generate client key pair
      const keyPair = await CryptoService.generateKeyPair()
      this.cryptoState.privateKey = keyPair.privateKey
      this.cryptoState.publicKey = keyPair.publicKey
      this.cryptoState.publicKeyBase64 = keyPair.publicKeyBase64

      // Send initiate key exchange event
      this.socket.emit('initiate_key_exchange')
    } catch (error) {
      this.emitLocalEvent('error', { message: 'Failed to initiate secure connection' })
    }
  }

  /**
   * Process any pending messages after key exchange
   */
  processPendingMessages() {
    if (this.pendingMessages.length > 0 && this.cryptoState.keyExchangeComplete) {
      this.pendingMessages.forEach(msg => {
        this.emit(msg.event, msg.data)
      })

      this.pendingMessages = []
    }
  }

  /**
   * Encrypt data before sending
   * @param {Object|string} data - Data to encrypt
   * @returns {Promise<string>} - Encrypted data as base64 string
   */
  async encrypt(data) {
    if (!this.cryptoState.sharedKey || !this.cryptoState.keyExchangeComplete) {
      throw new Error('Secure channel not established')
    }

    try {
      const result = await CryptoService.encrypt(this.cryptoState.sharedKey, data);
      return result;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Decrypt received data
   * @param {string} encryptedBase64 - Base64 encoded encrypted data
   * @returns {Promise<Object|string>} - Decrypted data
   */
  async decrypt(encryptedBase64) {
    if (!this.cryptoState.sharedKey || !this.cryptoState.keyExchangeComplete) {
      throw new Error('Secure channel not established')
    }

    try {
      // If the data comes directly from websocket, it might be wrapped in an object
      let dataToDecrypt = encryptedBase64;
      if (typeof encryptedBase64 === 'object' && encryptedBase64.hasOwnProperty('encrypted')) {
        dataToDecrypt = encryptedBase64.encrypted;
      }

      // Validate that we're decrypting a string
      if (typeof dataToDecrypt !== 'string') {
        throw new Error('Invalid encrypted data format');
      }

      const result = await CryptoService.decrypt(this.cryptoState.sharedKey, dataToDecrypt)
      return result;
    } catch (error) {
      throw error;
    }
  }

  /**
   * Register a listener for a custom event
   * @param {string} event - Event name
   * @param {Function} callback - Callback function
   */
  on(event, callback) {
    if (!this.eventHandlers[event]) {
      this.eventHandlers[event] = []
    }

    this.eventHandlers[event].push(callback)
  }

  /**
   * Remove a listener for a custom event
   * @param {string} event - Event name
   * @param {Function} callback - Callback function to remove
   */
  off(event, callback) {
    if (this.eventHandlers[event]) {
      this.eventHandlers[event] = this.eventHandlers[event].filter(
        handler => handler !== callback
      )
    }
  }

  /**
   * Emit an event to local listeners
   * @param {string} event - Event name
   * @param {Object} data - Event data
   */
  emitLocalEvent(event, data) {
    if (this.eventHandlers[event]) {
      this.eventHandlers[event].forEach(callback => {
        try {
          callback(data)
        } catch (error) {
          // Error in event handler (console.error removed)
        }
      })
    }
  }

  /**
   * Emit an event to the server
   * @param {string} event - Event name
   * @param {Object} data - Event data
   * @param {boolean} encrypt - Whether to encrypt the data
   */
  async emit(event, data = {}, encryptData = true) { // Renamed 'encrypt' to 'encryptData' to avoid conflict
    if (!this.socket || !this.connected) {
      this.emitLocalEvent('error', { message: 'Not connected to server' })
      return
    }

    // If encryption is required but key exchange is not complete,
    // add to pending messages
    if (encryptData && !this.cryptoState.keyExchangeComplete) {
      this.pendingMessages.push({ event, data })
      return
    }

    try {
      // If encryption is required, encrypt the data
      if (encryptData) {
        const encryptedPayload = await this.encrypt(data) // Changed variable name
        this.socket.emit(event, { encrypted: encryptedPayload })
      } else {
        // Otherwise, send as is
        this.socket.emit(event, data)
      }
    } catch (error) {
      this.emitLocalEvent('error', { message: `Failed to send ${event} message` })
    }
  }

  /**
   * Authenticate the socket connection with a token
   * @param {Object} tokenData - Token data
   * @returns {Promise<boolean>} - Success status
   */
  async authenticate(tokenData) {
    return new Promise((resolve, reject) => {
      try {
        if (!tokenData || (!tokenData.token && !tokenData.token?.token)) {
          reject(new Error('Missing authentication token'))
          return
        }

        const authSuccessHandler = (data) => {
          this.socket.off('auth_success', authSuccessHandler)
          this.socket.off('auth_error', authErrorHandler)
          this.authenticated = true
          resolve(true)
        }

        const authErrorHandler = (error) => {
          this.socket.off('auth_success', authSuccessHandler)
          this.socket.off('auth_error', authErrorHandler)
          this.authenticated = false
          reject(new Error(error.message || 'Authentication failed'))
        }

        this.socket.once('auth_success', authSuccessHandler)
        this.socket.once('auth_error', authErrorHandler)

        // Ensure the token is a string
        const tokenString = typeof tokenData === 'string'
          ? tokenData
          : (typeof tokenData.token === 'string'
            ? tokenData.token
            : (tokenData.token?.token || ''));

        // Emit the authenticate event with the token in format expected by server
        this.emit('authenticate', { token: tokenString })
      } catch (error) {
        reject(error)
      }
    })
  }

  /**
   * Login with credentials
   * @param {Object} credentials - Login credentials
   * @returns {Promise<Object>} - Login response
   */
  async login(credentials) {
    return new Promise((resolve, reject) => {
      try {
        if (!this.socket || !this.socket.connected) {
          reject(new Error('Socket not connected'))
          return
        }

        if (!credentials || !credentials.username || !credentials.password) {
          reject(new Error('Missing required login credentials'))
          return
        }

        const loginSuccessHandler = async (data) => {
          this.socket.off('login_success', loginSuccessHandler)
          this.socket.off('login_error', loginErrorHandler)
          resolve(data)
        }

        const loginErrorHandler = (error) => {
          this.socket.off('login_success', loginSuccessHandler)
          this.socket.off('login_error', loginErrorHandler)
          reject(new Error(error.message || 'Login failed'))
        }

        this.socket.once('login_success', loginSuccessHandler)
        this.socket.once('login_error', loginErrorHandler)

        // Send the login request
        this.emit('login', credentials)
      } catch (error) {
        reject(error)
      }
    })
  }

  /**
   * Register a new user
   * @param {Object} userData - User registration data
   * @returns {Promise<Object>} - Registration result
   */
  async register(userData) {
    return new Promise((resolve, reject) => {
      if (!this.connected) {
        reject(new Error('Not connected to server'))
        return
      }

      if (!this.cryptoState.keyExchangeComplete) {
        reject(new Error('Secure channel not established'))
        return
      }

      // One-time event listeners for this registration attempt
      const registerSuccessHandler = (data) => {
        this.off('register_success', registerSuccessHandler)
        this.off('register_error', registerErrorHandler)
        resolve(data)
      }

      const registerErrorHandler = (error) => {
        this.off('register_success', registerSuccessHandler)
        this.off('register_error', registerErrorHandler)
        reject(new Error(error.message || error.error || 'Registration failed'))
      }

      // Register one-time listeners
      this.on('register_success', registerSuccessHandler)
      this.on('register_error', registerErrorHandler)

      // Send register request
      this.emit('register', userData)
    })
  }

  /**
   * Disconnect from the server
   */
  disconnect() {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
      this.connected = false
      this.authenticated = false

      // Clear crypto state
      this.cryptoState = {
        privateKey: null,
        publicKey: null,
        serverPublicKey: null,
        sharedKey: null,
        keyExchangeComplete: false
      }

      this.pendingMessages = []
    }
  }
}

// Create a singleton instance
const socketService = new SocketService()

export default socketService