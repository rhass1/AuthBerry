import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'
import router from '../router'
import socketService from '../services/SocketService'

let refreshTokenPromise = null

// On app initialization, clear any invalid tokens
if (typeof window !== 'undefined') {
  // Don't clear tokens at all - this was causing the issue
  // Removing token clearing on setup page to prevent session loss
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: localStorage.getItem('authToken') || null,
    refreshToken: localStorage.getItem('refreshToken') || null,
    loading: false,
    error: null,
    lastTokenRefresh: parseInt(localStorage.getItem('lastTokenRefresh')) || null,
    refreshingToken: false,
    anyUsersExist: false,
    socketConnected: false,
    socketAuthenticated: false,
    initializingAuth: false
  }),

  getters: {
    isAuthenticated: (state) => {
      // More comprehensive check that combines multiple conditions
      // This helps prevent auth state loss during redirections
      return (
        // Check if there's a token either in state or localStorage
        (!!state.token || !!localStorage.getItem('authToken')) &&
        // And check if we have a user object 
        // (either in state or we can try to parse from localStorage as a fallback)
        (!!state.user || !!localStorage.getItem('authUser'))
      )
    },
    isAdmin: (state) => state.user?.role === 'admin',
    isUser: (state) => state.user?.role === 'user',
    getUser: (state) => state.user,
    getToken: (state) => state.token,
    isLoading: (state) => state.loading,
    getError: (state) => state.error,
    getUserRole: (state) => state.user?.role,
    getLastTokenRefresh: (state) => state.lastTokenRefresh,
    displayName: (state) => {
      if (!state.user) return null

      if (state.user.first_name && state.user.last_name) {
        return `${state.user.first_name} ${state.user.last_name}`
      }

      return state.user.username
    },
    profilePhoto: (state) => {
      if (!state.user?.profile_photo_url) return null
      
      if (state.user.profile_photo_url.startsWith('http')) {
        return state.user.profile_photo_url
      }
      
      return `${window.location.origin}${state.user.profile_photo_url}`
    },
    userRole: (state) => state.user?.role || null,
    username: (state) => state.user?.username || null,
    userId: (state) => state.user?.id || null,
  },

  actions: {
    setUser(user) {
      if (user) {
        this.user = user
        localStorage.setItem('authUser', JSON.stringify(user))
      } else {
        this.user = null
        localStorage.removeItem('authUser')
      }
    },

    setToken(token, refreshToken = null) {
      try {
        // Store the token in state
        this.token = token
        
        // Store tokens in both sessionStorage and localStorage for better persistence
        localStorage.setItem('authToken', token)

        if (refreshToken) {
          this.refreshToken = refreshToken
          localStorage.setItem('refreshToken', refreshToken)
        }

        // Set token for API requests
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`

      } catch (error) {
        // Error setting token (console.error removed)
      }
    },

    setLoading(status) {
      this.loading = status
    },

    setError(error) {
      this.error = error
    },

    async init() {
      this.initializingAuth = true

      // Initialize socket connection for authentication
      socketService.init()

      // Set up socket event handlers
      socketService.on('connect', this.handleSocketConnect)
      socketService.on('disconnect', this.handleSocketDisconnect)
      socketService.on('auth_success', this.handleSocketAuthSuccess)
      socketService.on('auth_error', this.handleSocketAuthError)

      try {
        // Get token from localStorage for better persistence
        const token = localStorage.getItem('authToken')

        if (token) {
          try {
            // Set token in state and for API requests
            this.token = token
            axios.defaults.headers.common['Authorization'] = `Bearer ${token}`

            // Refresh user data
            const userData = await this.refreshUserData()

            if (!userData) {
              // Clear invalid token
              this.clearAuthentication()
              return
            }

            // If socket is connected and we have a user but socket is not authenticated, authenticate it
            if (socketService.isConnected && !socketService.isAuthenticated) {
              if (socketService.keyExchangeComplete) {
                await this.authenticateSocket(token)
              } else {
                // Wait for key exchange and then authenticate
                socketService.once('key_exchange_completed', async () => {
                  await this.authenticateSocket(token)
                })
              }
            }
          } catch (error) {
            this.clearAuthentication()
          }
        }

      } catch (error) {
        this.clearAuthentication()
      } finally {
        this.initializingAuth = false

        // Set up axios interceptors
        this.setupAxiosInterceptors()
      }
    },

    // Authenticate socket with token
    async authenticateSocket(token) {
      if (!token || !socketService.connected) {
        return false
      }

      // Ensure socketService is initialized
      if (!socketService.socket) {
        socketService.init()
      }

      try {
        // Authenticate the socket with the token
        // Send the token string directly - the SocketService will handle formatting
        await socketService.authenticate(token)

        this.socketAuthenticated = true
        return true
      } catch (error) {
        this.socketAuthenticated = false
        return false
      }
    },

    // Save auth state to local storage
    saveAuth() {
      if (this.token && this.user) {
        localStorage.setItem('authToken', this.token)
        localStorage.setItem('authUser', JSON.stringify(this.user))
      }
    },

    // Clear auth state
    clearAuth() {
      if (window.location.pathname === '/setup') {
        // Don't do anything if we're on the setup page
        // This prevents auth state loss during redirection from setup
        return;
      }
      this.user = null
      this.token = null
      localStorage.removeItem('authToken')
      localStorage.removeItem('authUser')
      delete axios.defaults.headers.common['Authorization']
    },

    // Login with username and password
    async login(usernameOrCredentials, password) {
      try {
        this.error = null
        this.loading = true

        // Extract username and password whether passed as separate arguments or as an object
        let username, pwd;

        if (typeof usernameOrCredentials === 'object' && usernameOrCredentials !== null) {
          // Handle the case where credentials are passed as an object
          const credentials = usernameOrCredentials;
          username = credentials.username;
          pwd = credentials.password;
        } else {
          // Handle the case where username and password are passed as separate arguments
          username = usernameOrCredentials;
          pwd = password;
        }

        // Validate we have both username and password
        if (!username || !pwd) {
          this.error = 'Username and password are required';
          return false;
        }

        // Check if we should use socketService or HTTP
        if (socketService.isConnected && socketService.keyExchangeComplete) {
          // Use socket for secure login
          const response = await socketService.login({
            username,
            password: pwd
          });

          // Check if login was successful
          if (response && response.user && response.tokens) {
            // Set user data
            this.setUser(response.user);

            // Set tokens
            this.setToken(response.tokens.access_token || response.tokens.access,
                         response.tokens.refresh_token || response.tokens.refresh);

            // Mark this as a fresh login for splash screen logic
            localStorage.setItem('lastLoginTime', Date.now().toString());

            return true;
          } else {
            this.error = 'Invalid login response from server';
            return false;
          }
        } else {
          // Fallback to HTTP login
          const response = await axios.post('/api/auth/login', {
            username,
            password: pwd
          });

          // Check if login was successful
          if (response.data && response.data.user && response.data.tokens) {
            // Set user data
            this.setUser(response.data.user);

            // Set tokens
            this.setToken(response.data.tokens.access_token || response.data.tokens.access,
                         response.data.tokens.refresh_token || response.data.tokens.refresh);

            // Mark this as a fresh login for splash screen logic
            localStorage.setItem('lastLoginTime', Date.now().toString());

            return true;
          } else {
            this.error = 'Invalid login response from server';
            return false;
          }
        }
      } catch (error) {
        this.error = error.response?.data?.msg || error.message || 'Login failed';
        return false;
      } finally {
        this.loading = false;
      }
    },

    // Refresh tokens
    async refreshToken() {
      try {
        // Check if we have a refresh token
        const refreshToken = localStorage.getItem('refreshToken')
        if (!refreshToken) {
          return false
        }

        // Attempt to refresh the token
        const response = await axios.post('/api/auth/refresh', {
          refresh_token: refreshToken
        })

        // Check if token refresh was successful
        if (response.data && response.data.tokens) {
          // Set new tokens
          this.setToken(response.data.tokens.access, response.data.tokens.refresh)
          return true
        } else {
          this.clearAuthentication()
          return false
        }
      } catch (error) {
        this.clearAuthentication()
        return false
      }
    },

    // Log out user
    async logout() {
      this.loading = true

      try {
        // Only make API call if we have a token
        if (this.token) {
          try {
            // Use socket if connected, otherwise fallback to HTTP
            if (socketService.connected && this.socketAuthenticated) {
              await socketService.emit('logout', {})
            } else {
              await axios.post('/api/auth/logout')
            }
          } catch (error) {
            // Continue with local logout regardless of server error
          }
        }

        // Clear socket authentication
        this.socketAuthenticated = false

        // Clear auth state locally
        this.clearAuth()

        // Redirect to home page
        if (router.currentRoute.value.path !== '/') {
          router.push('/')
        }

        return true
      } catch (error) {
        return false
      } finally {
        this.loading = false
      }
    },

    // Register new user using WebSocket
    async register(userData) {
      this.loading = true
      this.error = null

      try {
        // First try WebSocket registration
        try {
          // Check if socket is connected
          if (!socketService.connected) {
            socketService.init()

            // Wait for connection to establish
            await new Promise((resolve, reject) => {
              const timeout = setTimeout(() => {
                socketService.off('connect', handler)
                reject(new Error('Socket connection timeout'))
              }, 5000)

              const handler = () => {
                clearTimeout(timeout)
                socketService.off('connect', handler)
                resolve()
              }

              socketService.on('connect', handler)

              // If already connected, resolve immediately
              if (socketService.connected) {
                clearTimeout(timeout)
                resolve()
              }
            })
          }

          // Wait for key exchange to complete
          if (!socketService.cryptoState.keyExchangeComplete) {
            // Set up a one-time listener for key exchange completion
            await new Promise((resolve, reject) => {
              const timeout = setTimeout(() => {
                socketService.off('key_exchange_complete', handler)
                reject(new Error('Key exchange timeout'))
              }, 5000)

              const handler = () => {
                clearTimeout(timeout)
                socketService.off('key_exchange_complete', handler)
                resolve()
              }

              socketService.on('key_exchange_complete', handler)

              // If key exchange is already complete, resolve immediately
              if (socketService.cryptoState.keyExchangeComplete) {
                clearTimeout(timeout)
                resolve()
              }
            })
          }

          // Register using WebSocket
          const result = await socketService.register(userData)

          // Extract user and tokens from response
          const user = result.user
          const accessToken = result.tokens.access_token
          const refreshToken = result.tokens.refresh_token

          // Set state
          this.setToken(accessToken, refreshToken)
          this.setUser(user)

          // Apply the token to all future requests
          axios.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`

          // Set socket as authenticated
          this.socketAuthenticated = true

          return true
        } catch (wsError) {
          // If WebSocket registration fails, try HTTP registration as fallback
          // HTTP registration
          const response = await axios.post('/api/auth/register', userData)

          // Extract user and tokens from response
          const result = response.data
          const user = result.user
          const accessToken = result.access_token
          const refreshToken = result.refresh_token

          if (!accessToken || !user) {
            throw new Error('Missing required authentication data')
          }

          // Store tokens and user data
          this.setToken(accessToken, refreshToken)
          this.setUser(user)

          // Apply the token to all future requests
          axios.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`

          // Reset error state
          this.error = null

          return true
        }
      } catch (error) {
        this.error = error.message || 'Registration failed. Please try again.'
        return false
      } finally {
        this.loading = false
      }
    },

    // Setup initial admin user
    async setupAdmin(userData) {
      this.loading = true
      this.error = null

      try {
        const response = await axios.post('/api/auth/setup', userData)

        // Extract user and tokens
        const { user, tokens } = response.data

        // Set auth state
        this.setToken(tokens.access_token, tokens.refresh_token)
        this.setUser(user)

        // Save auth state to localStorage for persistence
        localStorage.setItem('authToken', tokens.access_token)
        localStorage.setItem('authUser', JSON.stringify(user))
        
        // Apply the token to all future requests
        axios.defaults.headers.common['Authorization'] = `Bearer ${tokens.access_token}`

        // Update local state flag
        this.anyUsersExist = true

        // Mark this as a fresh login for splash screen logic
        localStorage.setItem('lastLoginTime', Date.now().toString());

        return true
      } catch (error) {
        this.error = error.response?.data?.msg || 'Admin setup failed. Please try again.'
        return false
      } finally {
        this.loading = false
      }
    },

    // Refresh user data from server
    async refreshUserData() {
      try {
        const token = localStorage.getItem('authToken')
        if (token) {
          axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
          this.token = token
        }

        const response = await axios.get('/api/auth/me')

        if (response && response.data && response.data.user) {
          this.user = response.data.user

          if (response.data.workspace) {
            this.workspace = response.data.workspace
          }

          return response.data.user
        } else {
          return null
        }
      } catch (error) {
        if (error.response && (error.response.status === 401 || error.response.status === 403 || error.response.status === 404)) {
          this.clearAuthentication()
        }
        return null
      }
    },

    // Update user profile
    async updateProfile(userData) {
      this.loading = true
      this.error = null

      try {
        const response = await axios.put('/api/auth/profile', userData)

        // Update local user data
        this.user = response.data.user

        return true
      } catch (error) {
        this.error = error.response?.data?.msg || 'Profile update failed. Please try again.'
        return false
      } finally {
        this.loading = false
      }
    },

    // Update profile photo with base64 encoded image data
    async updateProfilePhoto(photoBlob) {
      if (!this.user) return false

      this.loading = true
      this.error = null

      try {
        const formData = new FormData()
        formData.append('photo', photoBlob)

        const response = await axios.post('/api/users/profile-photo', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })

        if (response.data && response.data.user) {
          this.user = {
            ...this.user,
            profile_photo_url: response.data.user.profile_photo_url
          }

          this.saveAuth()
          return true
        } else {
          throw new Error('Invalid response format')
        }
      } catch (error) {
        this.error = error.response?.data?.msg || 'Failed to update profile photo'
        return false
      } finally {
        this.loading = false
      }
    },

    // Update user password
    async updatePassword(passwordData) {
      if (!this.user) return false

      this.loading = true
      this.error = null

      try {
        const response = await axios.put('/api/auth/update-password', {
          current_password: passwordData.currentPassword,
          new_password: passwordData.newPassword
        })

        // Reset error state on success
        this.error = null
        return true
      } catch (error) {
        // Set specific error message based on the response
        if (error.response?.status === 401) {
          this.error = 'Current password is incorrect. Please try again.'
        } else if (error.response?.data?.msg) {
          this.error = error.response.data.msg
        } else {
          this.error = 'Failed to update password. Please try again later.'
        }

        return false
      } finally {
        this.loading = false
      }
    },

    // Check authentication status with the server
    async checkAuthStatus() {
      try {
        // First check if we already have a token and user
        if (this.token && this.user) {
          // Update localStorage to ensure consistency
          this.saveAuth()

          // Set the Authorization header
          axios.defaults.headers.common['Authorization'] = `Bearer ${this.token}`;

          // Return true since we're already authenticated
          return true;
        }

        // If no token/user in memory, try to get status from server
        const response = await axios.get('/api/auth/status');

        // If the server says we're authenticated, update our store
        if (response.data.isAuthenticated && response.data.user) {
          this.user = response.data.user;
          return true;
        }

        return false;
      } catch (error) {
        return false;
      }
    },

    // Fetch user data from server
    async fetchUser() {
      if (!this.token) {
        return false;
      }

      try {
        // Make sure Authorization header is set
        axios.defaults.headers.common['Authorization'] = `Bearer ${this.token}`;

        // Get detailed user info
        const response = await axios.get('/api/auth/get-current-user');

        if (response.data && response.data.user) {
          // Update user in store
          this.user = {
            ...this.user,
            ...response.data.user
          };

          // Update localStorage
          this.saveAuth();
          return true;
        }

        return false;
      } catch (error) {
        // If unauthorized, clear auth state
        if (error.response?.status === 401) {
          this.clearAuth();
        }

        return false;
      }
    },

    // Set up axios interceptors for automatic token refresh
    setupAxiosInterceptors() {
      // Remove any existing interceptors to avoid duplicates
      if (this.responseInterceptor) {
        axios.interceptors.response.eject(this.responseInterceptor)
      }

      // Add response interceptor for handling 401 errors
      this.responseInterceptor = axios.interceptors.response.use(
        response => response,
        async error => {
          // Extract request config for potential retry
          const originalRequest = error.config

          // If we get a 401 Unauthorized error and haven't already retried
          if (error.response?.status === 401 && !originalRequest._retry && this.refreshToken) {
            originalRequest._retry = true

            try {
              // Only attempt refresh once at a time
              if (!refreshTokenPromise) {
                refreshTokenPromise = axios.post('/api/auth/refresh', {
                  refresh_token: this.refreshToken
                })

                const response = await refreshTokenPromise

                if (!response.data.access_token) {
                  throw new Error('No access token in refresh response')
                }

                const newToken = response.data.access_token

                // Update token in store and localStorage
                this.setToken(newToken, this.refreshToken)

                // Update Authorization header for future requests
                axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`

                // Update original request with new token
                originalRequest.headers['Authorization'] = `Bearer ${newToken}`

                // Retry original request with new token
                return axios(originalRequest)
              } else {
                // Another request is already refreshing the token, wait for it
                await refreshTokenPromise

                // Update the request with the new token from the store
                originalRequest.headers['Authorization'] = `Bearer ${this.token}`

                // Retry original request with new token
                return axios(originalRequest)
              }
            } catch (refreshError) {
              // Clear auth state on refresh failure
              this.clearAuth()

              // Redirect to login
              router.push({
                path: '/',
                query: { showModal: 'login', redirect: router.currentRoute.value.fullPath }
              })

              return Promise.reject(refreshError)
            } finally {
              refreshTokenPromise = null
            }
          }

          // For all other errors, just reject
          return Promise.reject(error)
        }
      )
    },

    // Check if any users exist in the system
    async checkIfUsersExist() {
      try {
        const timestamp = Date.now()
        const response = await axios.get(`/api/auth/check-users-exist?t=${timestamp}`, {
          withCredentials: false,
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          },
          timeout: 5000
        })
        this.anyUsersExist = response.data.users_exist
        return this.anyUsersExist
      } catch (error) {
        if (error.response?.status === 431) {
          try {
            const fallbackResponse = await fetch(`/api/auth/check-users-exist?t=${Date.now()}`, {
              method: 'GET',
              headers: {
                'Accept': 'application/json'
              },
              credentials: 'omit'
            })
            const data = await fallbackResponse.json()
            this.anyUsersExist = data.users_exist
            return this.anyUsersExist
          } catch (fallbackError) {
            return false
          }
        }
        return false
      }
    },

    async fetchUserProfile() {
      if (!this.token) {
        return { success: false, error: 'Not authenticated' }
      }

      try {
        const response = await axios.get('/api/auth/me')
        this.setUser(response.data.user)
        return { success: true, user: response.data.user }
      } catch (error) {
        // If token expired, try to refresh
        if (error.response?.status === 401 && this.refreshToken) {
          try {
            await this.refreshUserToken()
            // Try again with new token
            const retryResponse = await axios.get('/api/auth/me')
            this.setUser(retryResponse.data.user)
            return { success: true, user: retryResponse.data.user }
          } catch (refreshError) {
            this.logout()
            return { success: false, error: 'Session expired. Please login again.' }
          }
        }

        return { success: false, error: error.response?.data?.msg || 'Failed to load profile' }
      }
    },

    async refreshUserToken() {
      if (!this.refreshToken) {
        return false;
      }

      try {
        // Store original header
        const originalAuthHeader = axios.defaults.headers.common['Authorization'];

        // Remove expired token from request
        delete axios.defaults.headers.common['Authorization'];

        // Use the refresh token to get a new access token
        const response = await axios.post('/api/auth/refresh', {
          refresh_token: this.refreshToken
        });

        if (!response.data.access_token) {
          throw new Error('No access token in refresh response');
        }

        const { access_token, refresh_token } = response.data;

        // Update tokens
        this.setToken(access_token, refresh_token || this.refreshToken);

        // Apply the new token to all future requests
        axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;

        return true;
      } catch (error) {
        // If refresh fails, log the user out
        this.logout();
        return false;
      }
    },

    // Clear authentication state
    clearAuthentication() {
      // Don't clear authentication if navigating from setup page to dashboard/home
      if (window.location.pathname === '/setup') {
        // When on setup page, only clear if not authenticated
        // This preserves authentication for redirects to dashboard
        if (this.isAuthenticated) {
          return;
        }
      }
      
      // Clear token from both storages
      localStorage.removeItem('authToken')
      localStorage.removeItem('refreshToken')
      sessionStorage.removeItem('authToken')
      sessionStorage.removeItem('refreshToken')

      // Clear authentication state
      this.user = null
      this.isAuthenticated = false // This was missing, added for consistency

      // Clear Authorization header
      delete axios.defaults.headers.common['Authorization']

      // Clear error
      this.error = null

      // Log out from socket if connected
      if (socketService.isConnected && socketService.isAuthenticated) {
        socketService.emit('logout', {})
      }
    },

    handleSocketConnect() {
      this.socketConnected = true
    },

    handleSocketDisconnect() {
      this.socketConnected = false
      this.socketAuthenticated = false
    },

    handleSocketAuthSuccess() {
      this.socketAuthenticated = true
    },

    handleSocketAuthError(error) {
      this.socketAuthenticated = false
    }
  }
})