import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useSplashStore } from '@/stores/splash'
import axios from 'axios'

// Views
import HomeView from '@/views/HomeView.vue'
import NotFoundView from '@/views/NotFoundView.vue'
import SetupView from '@/views/SetupView.vue'

// Route definitions
const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView,
  },
  {
    path: '/setup',
    name: 'setup',
    component: SetupView
  },
  {
    path: '/splash',
    name: 'splash',
    component: () => import('@/views/SplashView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('@/views/DashboardView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/secrets',
    name: 'secrets',
    component: () => import('@/views/SecretsView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/secrets/:id',
    name: 'secret-detail',
    component: () => import('@/views/SecretDetailView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/profile',
    name: 'profile',
    component: () => import('@/views/ProfileView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/admin',
    name: 'admin',
    component: () => import('@/views/AdminView.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  // Redirect old auth routes to home with query param to trigger modal
  {
    path: '/login',
    redirect: to => {
      return { path: '/', query: { showModal: 'login', redirect: to.query.redirect || '/dashboard' } }
    }
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('@/views/RegisterView.vue')
  },
  // Redirect successful logins to splash screen
  {
    path: '/auth/success',
    redirect: '/splash'
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: NotFoundView
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guards
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  const splashStore = useSplashStore()
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  const requiresAdmin = to.matched.some(record => record.meta.requiresAdmin)

  // Initialize splash store
  splashStore.initialize()

  // Initialize auth status before proceeding - more aggressively
  if (!authStore.isAuthenticated || !authStore.user || !authStore.token) {
    await authStore.init()
  }

  // Ensure token is correctly set in axios headers whenever navigating
  if (authStore.token) {
    axios.defaults.headers.common['Authorization'] = `Bearer ${authStore.token}`
  }

  // Special handling for redirection from setup to other routes
  // This helps preserve authentication state during these redirections
  if (from.name === 'setup' && authStore.token) {
    // Force a refresh of user data when coming from setup
    await authStore.refreshUserData()
    
    // Re-apply token to axios headers
    if (authStore.token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${authStore.token}`
    }
  }

  let anyUsers = false
  let userCheckFailed = false
  
  try {
    anyUsers = await authStore.checkIfUsersExist()
  } catch (error) {
    userCheckFailed = true
    
    if (authStore.isAuthenticated && authStore.user) {
      anyUsers = true
    } else {
      anyUsers = false
    }
  }

  // Setup page logic - redirect away if users already exist
  if (to.name === 'setup') {
    if (anyUsers) {
      if (authStore.token || authStore.user || authStore.isAuthenticated) {
        try {
          await authStore.refreshUserData()
        } catch (error) {
          // If refresh fails, continue with what we have
        }
        
        if (authStore.token) {
          axios.defaults.headers.common['Authorization'] = `Bearer ${authStore.token}`
        }
        
        return next({ name: 'dashboard' })
      } else {
        return next({ name: 'home' })
      }
    }
    return next()
  }

  // If no users exist and not going to setup page, redirect to setup
  if (!anyUsers && !userCheckFailed && to.name !== 'setup') {
    return next({ name: 'setup' })
  }

  // For pages that require authentication
  if (requiresAuth) {
    // Get current authentication status
    const isAuthenticated = authStore.isAuthenticated

    // If not authenticated, redirect to home with login modal
    if (!isAuthenticated) {
      return next({
        path: '/',
        query: { showModal: 'login', redirect: to.fullPath }
      })
    }

    // Check if admin role is required
    if (requiresAdmin && !authStore.isAdmin) {
      return next('/')
    }

    // Splash screen logic:
    // Special post-login flow handling (except if coming directly from splash screen)
    if (to.path !== '/splash' && !splashStore.splashShown && from.path !== '/splash') {
      // Track login completion via local storage to detect new login sessions
      const lastLoginTime = localStorage.getItem('lastLoginTime')
      const currentTime = Date.now()

      // Consider login fresh if within last 2 seconds or no previous login recorded
      const isFreshLogin = !lastLoginTime || (currentTime - parseInt(lastLoginTime)) < 2000

      if (isFreshLogin) {
        // This appears to be a fresh login - update timestamp and show splash
        localStorage.setItem('lastLoginTime', currentTime.toString())
        return next({ name: 'splash' })
      }

      // For existing dashboards or other path navigations
      if (to.path === '/dashboard') {
        return next({ name: 'splash' })
      }
    }

    if (to.name === 'splash' && splashStore.splashShown) {
      return next({ name: 'dashboard' })
    }

    // User is authenticated and has required permissions, allow navigation
    return next()
  } else if (to.path === '/' && authStore.isAuthenticated) {
    // If authenticated user is trying to access home page, redirect to dashboard
    return next({ name: 'dashboard' })
  }

  // Default: allow navigation
  next()
})

// Add this for successful login redirection to splash screen instead of dashboard
const successRoutes = routes.find(route => route.path === '/auth/success')
if (successRoutes) {
  successRoutes.redirect = '/splash'
}

export default router