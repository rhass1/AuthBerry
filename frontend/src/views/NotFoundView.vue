<template>
  <v-container class="d-flex flex-column align-center justify-center" style="min-height: 70vh;">
    <v-card elevation="2" max-width="500" class="text-center pa-4">
      <v-card-title class="text-h3 primary--text">404</v-card-title>
      <v-card-subtitle class="text-h5 mb-4">Page Not Found</v-card-subtitle>
      
      <v-card-text>
        <p class="text-body-1 mb-4">The page you're looking for doesn't exist or has been moved.</p>
        <v-icon size="x-large" color="primary" class="mb-4">mdi-map-marker-question</v-icon>
      </v-card-text>
      
      <v-card-actions class="justify-center">
        <v-btn color="primary" to="/" size="large">
          Return Home
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-container>
</template>

<script setup>
// No logic needed for this component
</script> 