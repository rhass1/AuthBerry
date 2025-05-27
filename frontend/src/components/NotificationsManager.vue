<template>
  <div class="notifications-container">
    <transition-group name="notification">
      <div 
        v-for="notification in notificationsStore.notifications" 
        :key="notification.id"
        :class="['notification', `notification-${notification.type}`]"
      >
        <div class="notification-content">
          {{ notification.message }}
        </div>
        <button 
          class="notification-close" 
          @click="notificationsStore.removeNotification(notification.id)"
        >
          &times;
        </button>
      </div>
    </transition-group>
  </div>
</template>

<script setup>
import { useNotificationsStore } from '@/stores/notifications'

const notificationsStore = useNotificationsStore()
</script>

<style scoped>
.notifications-container {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 9999;
  max-width: 350px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.notification {
  padding: 12px 16px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  color: white;
  animation: slide-in 0.3s ease;
}

.notification-content {
  flex: 1;
  margin-right: 10px;
}

.notification-close {
  background: transparent;
  border: none;
  color: white;
  font-size: 18px;
  cursor: pointer;
  opacity: 0.7;
  transition: opacity 0.2s;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.notification-close:hover {
  opacity: 1;
}

.notification-success {
  background-color: #10B981;
}

.notification-error {
  background-color: #EF4444;
}

.notification-warning {
  background-color: #F59E0B;
}

.notification-info {
  background-color: #3B82F6;
}

/* Transitions */
.notification-enter-active, 
.notification-leave-active {
  transition: all 0.3s ease;
}

.notification-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.notification-leave-to {
  opacity: 0;
  transform: translateX(30px);
}

@keyframes slide-in {
  from {
    transform: translateX(30px);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}
</style> 