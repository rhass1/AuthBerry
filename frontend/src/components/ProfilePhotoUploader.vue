<template>
  <div class="profile-photo-uploader">
    <div class="photo-container">
      <div class="photo-preview" v-if="previewUrl">
        <div class="photo-circle">
          <img :src="previewUrl" alt="Profile photo preview" />
        </div>
      </div>
      
      <div class="photo-placeholder" v-else>
        <v-icon size="48" color="grey lighten-1">mdi-account-circle</v-icon>
      </div>

      <div class="photo-overlay" @click="triggerFileInput">
        <v-icon color="white" size="24">mdi-camera</v-icon>
      </div>
    </div>

    <input
      type="file"
      ref="fileInput"
      accept="image/png, image/jpeg"
      style="display: none"
      @change="onFileSelected"
    />
    
    <div v-if="photoError" class="photo-error text-error text-center">
      {{ photoError }}
    </div>

    <v-dialog v-model="showCropDialog" max-width="500px">
      <v-card class="crop-dialog">
        <v-card-title class="text-h5">
          Adjust Your Profile Photo
        </v-card-title>
        
        <v-card-text class="pa-0">
          <div v-if="imageUrl" class="cropper-container">
            <Cropper
              ref="cropperRef"
              :src="imageUrl"
              :stencil-component="CircleStencil"
              :stencil-props="{
                aspectRatio: 1,
                minAspectRatio: 1,
                maxAspectRatio: 1
              }"
              :resize-image="{
                touch: true,
                wheel: true,
                resize: true
              }"
              :checkOrientation="true"
              image-restriction="stencil"
              background-class="bg-dark"
              @ready="onCropperReady"
              class="cyberpunk-cropper"
            />
          </div>
        </v-card-text>
        
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="error" variant="text" @click="cancelCrop">
            Cancel
          </v-btn>
          <v-btn color="primary" @click="processCrop">
            Save
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { Cropper, CircleStencil } from 'vue-advanced-cropper';
import 'vue-advanced-cropper/dist/style.css';

const props = defineProps({
  initialPhotoData: {
    type: String,
    default: null
  }
});

const emit = defineEmits(['update:photo']);

const fileInput = ref(null);
const cropperRef = ref(null);
const showCropDialog = ref(false);
const photoError = ref(null);
const photoSelected = ref(false);

const imageUrl = ref(null);
const previewUrl = ref(null);
const imageType = ref('image/png');

onMounted(() => {
  if (props.initialPhotoData) {
    if (props.initialPhotoData.startsWith('http') || props.initialPhotoData.startsWith('/api/')) {
      if (props.initialPhotoData.startsWith('/api/')) {
        previewUrl.value = `${window.location.origin}${props.initialPhotoData}`
      } else {
        previewUrl.value = props.initialPhotoData
      }
    } else {
      previewUrl.value = props.initialPhotoData
    }
    photoSelected.value = true
  }
});

function onCropperReady() {
  if (cropperRef.value) {
    setTimeout(() => {
      cropperRef.value.refresh();
    }, 50);
  }
}

function triggerFileInput() {
  fileInput.value.click();
}

function onFileSelected(event) {
  const file = event.target.files[0];
  if (!file) return;

  if (!file.type.match('image/jpeg') && !file.type.match('image/png')) {
    photoError.value = 'Please select a JPEG or PNG image';
    return;
  }

  if (file.size > 5 * 1024 * 1024) {
    photoError.value = 'Image size should be less than 5MB';
    return;
  }

  imageType.value = file.type;
  photoError.value = null;

  if (imageUrl.value) {
    URL.revokeObjectURL(imageUrl.value);
  }
  imageUrl.value = URL.createObjectURL(file);
  
  showCropDialog.value = true;

  setTimeout(() => {
    if (cropperRef.value) {
      cropperRef.value.refresh();
    }
  }, 100);
}

function cancelCrop() {
  showCropDialog.value = false;
  
  if (imageUrl.value) {
    URL.revokeObjectURL(imageUrl.value);
    imageUrl.value = null;
  }
}

function processCrop() {
  if (!cropperRef.value || !imageUrl.value) return;
  
  try {
    const { coordinates, canvas } = cropperRef.value.getResult();
    
    if (canvas) {
      let finalCanvas = canvas;
      const MAX_SIZE = 800;
      
      if (canvas.width > MAX_SIZE || canvas.height > MAX_SIZE) {
        const resizeCanvas = document.createElement('canvas');
        const ctx = resizeCanvas.getContext('2d');
        
        const scaleFactor = MAX_SIZE / Math.max(canvas.width, canvas.height);
        resizeCanvas.width = canvas.width * scaleFactor;
        resizeCanvas.height = canvas.height * scaleFactor;
        
        ctx.drawImage(canvas, 0, 0, resizeCanvas.width, resizeCanvas.height);
        finalCanvas = resizeCanvas;
      }
      
      previewUrl.value = finalCanvas.toDataURL(imageType.value, 0.85);
      photoSelected.value = true;
      
      finalCanvas.toBlob((blob) => {
        if (blob) {
          emit('update:photo', blob);
        }
      }, imageType.value, 0.85);
    }
  } catch (error) {
  }
  
  showCropDialog.value = false;
  
  URL.revokeObjectURL(imageUrl.value);
  imageUrl.value = null;
}
</script>

<style scoped>
.profile-photo-uploader {
  width: 100%;
  height: 100%;
  position: relative;
  max-width: 200px;
  max-height: 200px;
  margin: 0 auto;
}

.photo-container {
  width: 100%;
  height: 100%;
  position: relative;
  cursor: pointer;
  aspect-ratio: 1/1;
}

.photo-preview, .photo-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  overflow: hidden;
  background-color: rgba(15, 22, 32, 0.5);
  max-width: 200px;
  max-height: 200px;
}

.photo-circle {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  max-width: 200px;
  max-height: 200px;
}

.photo-circle img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.photo-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
  border-radius: 50%;
}

.photo-container:hover .photo-overlay {
  opacity: 1;
}

.photo-error {
  position: absolute;
  bottom: -24px;
  left: 0;
  right: 0;
  text-align: center;
  color: #ff5252;
  font-size: 0.875rem;
}

.crop-dialog :deep(.v-card-text) {
  padding: 0;
  overflow: hidden;
}

.cropper-container {
  position: relative;
  height: 350px;
  width: 100%;
  background-color: #0f1621;
}

:deep(.cyberpunk-cropper) {
  background-color: #0f1621;
  border-radius: 0;
  height: 100%;
  max-height: 350px;
}

:deep(.vue-advanced-cropper__image) {
  height: auto !important;
}

:deep(.vue-advanced-cropper__foreground) {
  border-radius: 50%;
  background-color: rgba(0, 0, 0, 0.5);
}

:deep(.vue-advanced-cropper__boundary) {
  border: none;
}

:deep(.vue-circle-stencil) {
  border: 2px solid #00ff9c !important;
  box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.5), 0 0 15px rgba(0, 255, 156, 0.7) !important;
}

:deep(.vue-circle-stencil__handlers) {
  border-color: #00ff9c !important;
}

:deep(.vue-advanced-cropper__background) {
  background-color: transparent !important;
}

:deep(.bg-dark) {
  background-color: #0f1621 !important;
}
</style> 