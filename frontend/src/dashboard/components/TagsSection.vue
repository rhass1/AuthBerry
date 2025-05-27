<template>
  <div class="tags-section" v-if="item && item.tags && item.tags.length > 0">
    <div class="section-title">
      <v-icon color="secondary" class="mr-2" size="small">mdi-tag-multiple</v-icon>
      Tags
    </div>
    
    <div class="tags-container">
      <v-chip
        v-for="tag in item.tags" 
        :key="tag"
        size="small"
        label
        class="mr-2 mb-2 tag-chip"
        color="secondary"
      >
        {{ tag }}
      </v-chip>
    </div>
  </div>
</template>

<script setup>
import { reactive } from 'vue'

const props = defineProps({
  item: {
    type: Object,
    required: true
  },
  itemType: {
    type: String,
    required: true,
    validator: value => ['secret', 'folder'].includes(value)
  }
})

// Remove all tag management functions since they're no longer needed
</script>

<style scoped>
/* Tags section */
.tags-section {
  margin-bottom: 24px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 8px;
  padding: 16px;
  position: relative;
}

.section-title {
  font-size: 1rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 12px;
  display: flex;
  align-items: center;
}

.tags-container {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
}

.tag-chip {
  font-size: 0.8rem !important;
  opacity: 0.9;
}
</style> 