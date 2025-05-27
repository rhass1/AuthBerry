import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useNotificationsStore = defineStore('notifications', () => {
  // State
  const notifications = ref([])
  
  // Add a notification
  function showNotification(message, type = 'info', timeout = 5000) {
    const id = Date.now()
    const notification = {
      id,
      message,
      type,
      timeout
    }
    
    notifications.value.push(notification)
    
    // Auto-remove after timeout
    if (timeout > 0) {
      setTimeout(() => {
        removeNotification(id)
      }, timeout)
    }
    
    return id
  }
  
  // Remove a notification by ID
  function removeNotification(id) {
    const index = notifications.value.findIndex(n => n.id === id)
    if (index !== -1) {
      notifications.value.splice(index, 1)
    }
  }
  
  // Clear all notifications
  function clearNotifications() {
    notifications.value = []
  }
  
  return {
    notifications,
    showNotification,
    removeNotification,
    clearNotifications
  }
}) 