<template>
  <v-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" max-width="500px">
    <v-card class="dialog-card">
      <v-card-title class="dialog-title">
        <v-icon color="error" class="mr-2">mdi-alert</v-icon>
        {{ itemType === 'folder' ? 'Delete Folder' : 'Delete Secret' }}
      </v-card-title>
      <v-card-text class="dialog-text">
        <template v-if="itemType === 'folder'">
          Are you sure you want to delete this folder?
          All secrets within this folder will also be deleted.
          This action cannot be undone.
        </template>
        <template v-else>
          Are you sure you want to delete this secret?
          This action cannot be undone.
        </template>
      </v-card-text>
      
      <v-card-actions class="dialog-actions">
        <v-spacer></v-spacer>
        <v-btn
          variant="text"
          @click="cancel"
          class="cancel-btn"
        >
          Cancel
        </v-btn>
        <v-btn
          color="error"
          @click="confirmDelete"
          :loading="loading"
          class="delete-btn"
        >
          Delete
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  itemType: {
    type: String,
    required: true,
    validator: value => ['secret', 'folder'].includes(value)
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'confirm'])

function confirmDelete() {
  emit('confirm')
}

function cancel() {
  emit('update:modelValue', false)
}
</script>

<style scoped>
/* Dialog styling */
.dialog-card {
  background: #0F1620 !important;
  border: 1px solid rgba(0, 255, 156, 0.3) !important;
  box-shadow: 0 0 20px rgba(0, 0, 0, 0.7), 0 0 15px rgba(0, 255, 156, 0.3) !important;
  border-radius: 8px !important;
  overflow: hidden;
}

.dialog-title {
  font-size: 1.3rem !important;
  font-weight: 600 !important;
  padding: 20px 24px !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;
  background: rgba(15, 22, 32, 0.8) !important;
  display: flex;
  align-items: center;
}

.dialog-text {
  padding: 20px 24px !important;
  color: rgba(255, 255, 255, 0.8) !important;
}

.dialog-actions {
  padding: 16px 24px !important;
  border-top: 1px solid rgba(255, 255, 255, 0.1) !important;
}
</style> 