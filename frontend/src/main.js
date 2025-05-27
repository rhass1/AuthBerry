import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

// Import SCSS styles
import './assets/scss/main.scss'

// Vuetify
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import { aliases, mdi } from 'vuetify/iconsets/mdi'
import '@mdi/font/css/materialdesignicons.css'

// Import auth store to initialize it
import { useAuthStore } from './stores/auth'
// Import notifications store
import { useNotificationsStore } from './stores/notifications'
import { useSplashStore } from './stores/splash'

// Import Socket.IO client
import { io } from 'socket.io-client'
// Import socketService for E2EE over WebSockets
import socketService from './services/SocketService'

// Import sound plugin
import SoundPlugin from './plugins/SoundPlugin'

// Setup dayjs for date formatting
import dayjs from 'dayjs'
import utc from 'dayjs/plugin/utc'
import timezone from 'dayjs/plugin/timezone'
import localizedFormat from 'dayjs/plugin/localizedFormat'

// Configure dayjs
dayjs.extend(utc)
dayjs.extend(timezone)
dayjs.extend(localizedFormat)

// Use browser's timezone by default
const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone
dayjs.tz.setDefault(userTimezone)

// Setup axios defaults
import axios from 'axios'
axios.defaults.baseURL = window.location.origin  // Use the same origin as the frontend
axios.defaults.withCredentials = true

// Get CSRF token from meta tag
const csrfTokenMeta = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content')
if (csrfTokenMeta) {
  axios.defaults.headers.common['X-CSRF-TOKEN'] = csrfTokenMeta
}

// Setup auth token from localStorage if it exists
const token = localStorage.getItem('authToken')
if (token) {
  axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
}

// Configure Axios
axios.interceptors.request.use(
  config => {
    // Get the token from the store if available
    const authStore = useAuthStore()
    const storedToken = authStore.token
    
    // Set Authorization header if not already set
    if (storedToken && !config.headers.Authorization) {
      config.headers.Authorization = `Bearer ${storedToken}`
    }
    
    // Include CSRF token for mutating requests if available
    const cookieCsrfToken = document.cookie
      .split('; ')
      .find(row => row.startsWith('XSRF-TOKEN='))
      ?.split('=')[1]
      
    if (['post', 'put', 'patch', 'delete'].includes(config.method) && cookieCsrfToken) {
      config.headers['X-XSRF-TOKEN'] = decodeURIComponent(cookieCsrfToken)
    }
    
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
axios.interceptors.response.use(
  response => {
    // Capture CSRF token from response headers if present
    const responseCsrfToken = response.headers['x-csrf-token']
    if (responseCsrfToken) {
      document.cookie = `XSRF-TOKEN=${responseCsrfToken}; path=/`
    }
    
    return response
  },
  error => {
    // Let the auth store handle 401 errors
    if (error.response?.status === 401) {
      // The auth store will handle this in its interceptor
      // We avoid handling it here to prevent duplicate handling
      return Promise.reject(error)
    }
    
    return Promise.reject(error)
  }
)

const vuetify = createVuetify({
  components,
  directives,
  icons: {
    defaultSet: 'mdi',
    aliases,
    sets: {
      mdi,
    },
  },
  theme: {
    defaultTheme: 'dark',
    themes: {
      dark: {
        colors: {
          primary: '#00FF9C',
          secondary: '#0088FF',
          accent: '#8C52FF',
          error: '#FF5252',
          warning: '#FFC107',
          info: '#0088FF',
          success: '#4CAF50',
          background: '#0A0E14',
          surface: 'rgba(16, 23, 35, 0.7)',
        },
      },
    },
  },
})

// Setup SocketIO
const socket = io({
  autoConnect: false, // Don't connect automatically, we'll connect after auth
  withCredentials: true
})

// Export socket for use in components
export const socketIO = socket

// Initialize the app
const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(vuetify)
app.use(SoundPlugin)

// Initialize stores (must be after pinia is initialized)
const authStore = useAuthStore()
const splashStore = useSplashStore()

// Initialize socket service
try {
  // Check if browser supports required crypto API features
  if (window.crypto && window.crypto.subtle && 
      typeof window.crypto.subtle.generateKey === 'function' &&
      typeof window.crypto.subtle.deriveKey === 'function') {
    socketService.init()
  } else {
    // Fall back to standard connections without E2EE
  }
} catch (error) {
  // Continue without E2EE
}

// Initialize auth store state
authStore.init().then(() => {
  // Don't manually connect the old socket - we're now using socketService for E2EE
  if (authStore.isAuthenticated) {
    // Update user auth status with socketService if authenticated
    socketService.authenticate({ token: authStore.token })
      .then(() => {
        // SocketService authenticated
      })
      .catch(err => {
        // SocketService authentication error
      })
  }
  
  // Mount the app
  app.mount('#app')
}).catch(error => {
  app.mount('#app') // Still mount the app even if auth initialization fails
})

// Get CSRF token from cookies
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
}