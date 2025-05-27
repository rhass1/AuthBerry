import { defineStore } from 'pinia'
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { useAuthStore } from './auth'
import { socketIO } from '@/main'

export const useSecretsStore = defineStore('secrets', () => {
  // State
  const secrets = ref([])
  const currentSecret = ref(null)
  const folders = ref([])
  const currentFolder = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // Get auth store for user ID
  const authStore = useAuthStore()

  // Getters
  const secretsCount = computed(() => secrets.value.length)
  const secretById = computed(() => (id) =>
    secrets.value.find(secret => secret.id === parseInt(id))
  )

  const foldersCount = computed(() => folders.value.length)
  const folderById = computed(() => (id) =>
    folders.value.find(folder => folder.id === parseInt(id))
  )

  // Get secrets by folder ID
  const secretsByFolderId = computed(() => (folderId) => {
    if (!folderId) return []

    return secrets.value.filter(secret => {
      return secret.folder_id === folderId ||
             (secret.folder_id && secret.folder_id.toString() === folderId.toString())
    })
  })

  // Actions
  async function fetchSecrets() {
    loading.value = true
    error.value = null

    try {
      const response = await axios.get('/api/secrets/')
      secrets.value = response.data.secrets || []
      return response.data.secrets
    } catch (err) {
      error.value = err.response?.data?.msg || 'Failed to fetch secrets'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchSecret(id) {
    loading.value = true
    error.value = null

    try {
      const response = await axios.get(`/api/secrets/${id}`)
      currentSecret.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.msg || 'Failed to fetch secret'
      return null
    } finally {
      loading.value = false
    }
  }

  async function createSecret(secretData) {
    loading.value = true
    error.value = null

    try {
      const apiData = {
        name: secretData.name,
        type: secretData.type,
        value: secretData.value,
        description: secretData.description || '',
        tags: Array.isArray(secretData.tags) ? secretData.tags : []
      }

      if (secretData.folder_id) {
        apiData.folder_id = parseInt(secretData.folder_id)
      } else {
        apiData.folder_id = null
      }

      const response = await axios.post('/api/secrets/', apiData)
      const newSecret = response.data

      if (newSecret && !newSecret.value && secretData.value) {
        newSecret.value = secretData.value
      }

      secrets.value.push(newSecret)
      currentSecret.value = newSecret

      return newSecret
    } catch (err) {
      error.value = err.response?.data?.msg || 'Failed to create secret'
      return null
    } finally {
      loading.value = false
    }
  }

  async function updateSecret(id, secretData) {
    loading.value = true
    error.value = null

    try {
      const apiData = {
        name: secretData.name,
        type: secretData.type,
        value: secretData.value,
        description: secretData.description || '',
        tags: Array.isArray(secretData.tags) ? secretData.tags : []
      }

      if (secretData.folder_id) {
        apiData.folder_id = parseInt(secretData.folder_id)
      } else {
        apiData.folder_id = null
      }

      const response = await axios.put(`/api/secrets/${id}`, apiData)
      const updatedSecret = response.data

      if (updatedSecret && !updatedSecret.value && secretData.value) {
        updatedSecret.value = secretData.value
      }

      const index = secrets.value.findIndex(s => s.id === parseInt(id))
      if (index !== -1) {
        secrets.value[index] = updatedSecret
      }

      if (currentSecret.value?.id === parseInt(id)) {
        currentSecret.value = updatedSecret
      }

      return updatedSecret
    } catch (err) {
      error.value = err.response?.data?.msg || 'Failed to update secret'
      return null
    } finally {
      loading.value = false
    }
  }

  async function deleteSecret(id) {
    loading.value = true
    error.value = null

    try {
      await axios.delete(`/api/secrets/${id}`)

      secrets.value = secrets.value.filter(s => s.id !== parseInt(id))

      if (currentSecret.value?.id === parseInt(id)) {
        currentSecret.value = null
      }

      return true
    } catch (err) {
      error.value = err.response?.data?.msg || 'Failed to delete secret'
      return false
    } finally {
      loading.value = false
    }
  }

  async function fetchFolders() {
    loading.value = true
    error.value = null

    try {
      const response = await axios.get('/api/folders/')
      folders.value = response.data.folders || response.data || []
      return folders.value
    } catch (err) {
      error.value = err.response?.data?.msg || 'Failed to fetch folders'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchFolder(id) {
    loading.value = true
    error.value = null

    try {
      const response = await axios.get(`/api/folders/${id}`)
      currentFolder.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.msg || 'Failed to fetch folder'
      return null
    } finally {
      loading.value = false
    }
  }

  async function createFolder(folderData) {
    loading.value = true
    error.value = null

    try {
      const apiData = {
        name: folderData.name,
        description: folderData.description || '',
        tags: Array.isArray(folderData.tags) ? folderData.tags : []
      }

      const response = await axios.post('/api/folders/', apiData)
      const newFolder = response.data

      folders.value.push(newFolder)
      currentFolder.value = newFolder

      return newFolder
    } catch (err) {
      error.value = err.response?.data?.msg || 'Failed to create folder'
      return null
    } finally {
      loading.value = false
    }
  }

  async function updateFolder(id, folderData) {
    loading.value = true
    error.value = null

    try {
      const apiData = {
        name: folderData.name,
        description: folderData.description || '',
        tags: Array.isArray(folderData.tags) ? folderData.tags : []
      }

      const response = await axios.put(`/api/folders/${id}`, apiData)
      const updatedFolder = response.data

      const index = folders.value.findIndex(f => f.id === parseInt(id))
      if (index !== -1) {
        folders.value[index] = updatedFolder
      }

      if (currentFolder.value?.id === parseInt(id)) {
        currentFolder.value = updatedFolder
      }

      return updatedFolder
    } catch (err) {
      error.value = err.response?.data?.msg || 'Failed to update folder'
      return null
    } finally {
      loading.value = false
    }
  }

  async function deleteFolder(id) {
    loading.value = true
    error.value = null

    try {
      await axios.delete(`/api/folders/${id}`)

      folders.value = folders.value.filter(f => f.id !== parseInt(id))

      if (currentFolder.value?.id === parseInt(id)) {
        currentFolder.value = null
      }

      return true
    } catch (err) {
      error.value = err.response?.data?.msg || 'Failed to delete folder'
      return false
    } finally {
      loading.value = false
    }
  }

  async function shareSecret(secretId, userId, permissions) {
    loading.value = true
    error.value = null

    try {
      const apiData = {
        user_id: parseInt(userId),
        permissions: permissions
      }

      const response = await axios.post(`/api/secrets/${secretId}/share`, apiData)

      // If we have the current secret loaded and it matches the shared one,
      // update its permissions in our local state
      if (currentSecret.value && currentSecret.value.id === parseInt(secretId)) {
        // If the API returns updated sharing info, use it
        if (response.data && response.data.shared_with) {
          currentSecret.value.shared_with = response.data.shared_with
        }
      }

      return response.data || true
    } catch (err) {
      error.value = err.response?.data?.msg || 'Failed to share secret'
      return null
    } finally {
      loading.value = false
    }
  }

  async function shareFolder(folderId, userId, permissions) {
    loading.value = true
    error.value = null

    try {
      const apiData = {
        user_id: parseInt(userId),
        permissions: permissions
      }

      const response = await axios.post(`/api/folders/${folderId}/share`, apiData)

      // If we have the current folder loaded and it matches the shared one,
      // update its permissions in our local state
      if (currentFolder.value && currentFolder.value.id === parseInt(folderId)) {
        // If the API returns updated sharing info, use it
        if (response.data && response.data.shared_with) {
          currentFolder.value.shared_with = response.data.shared_with
        }
      }

      return response.data || true
    } catch (err) {
      error.value = err.response?.data?.msg || 'Failed to share folder'
      return null
    } finally {
      loading.value = false
    }
  }

  async function fetchSecretFile(secretId) {
    loading.value = true
    error.value = null

    try {
      const response = await axios.get(`/api/secrets/${secretId}/file`, {
        responseType: 'arraybuffer'
      })

      return response
    } catch (err) {
      error.value = err.response?.data?.msg || 'Failed to fetch file'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function downloadFileSecret(secretId) {
    loading.value = true
    error.value = null

    try {
      const response = await axios.get(`/api/secrets/${secretId}/file`, {
        responseType: 'blob'
      })

      // Get the filename from the Content-Disposition header if available
      const contentDisposition = response.headers['content-disposition']
      let filename = `secret-${secretId}`

      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/)
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1]
        }
      }

      // Create a download link and click it
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)

      return true
    } catch (err) {
      error.value = err.response?.data?.msg || 'Failed to download file'
      throw err
    } finally {
      loading.value = false
    }
  }

  // Create a file secret (image or file)
  async function createSecretFile(secretData) {
    loading.value = true;
    error.value = null;

    try {
      // Create a FormData instance for the file upload
      const formData = new FormData();

      // Add basic secret information
      formData.append('name', secretData.name);
      formData.append('type', secretData.type);
      formData.append('description', secretData.description || '');

      // Add folder_id if it exists
      if (secretData.folder_id) {
        formData.append('folder_id', secretData.folder_id);
      }

      // Add tags if they exist
      if (Array.isArray(secretData.tags) && secretData.tags.length > 0) {
        formData.append('tags', JSON.stringify(secretData.tags));
      }

      // Handle the file data
      if (secretData.file instanceof File) {
        formData.append('file', secretData.file);
      } else if (secretData.fileData) {
        formData.append('file_data', secretData.fileData);
      } else if (typeof secretData.file === 'string' && secretData.file.startsWith('data:')) {
        // Handle base64 image data
        const response = await fetch(secretData.file);
        const blob = await response.blob();
        // Generate a filename if needed
        const filename = secretData.originalFilename || `${secretData.type}_${Date.now()}.${getExtensionFromMimeType(blob.type)}`;
        formData.append('file', new File([blob], filename, { type: blob.type }));
      } else {
        throw new Error('No valid file provided for file secret');
      }

      // Send the request with the proper Content-Type for form data
      const response = await axios.post('/api/secrets/file', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      const newSecret = response.data;

      // Add to local state
      secrets.value.push(newSecret);
      currentSecret.value = newSecret;

      return newSecret;
    } catch (err) {
      error.value = err.response?.data?.msg || 'Failed to create file secret';
      throw err;
    } finally {
      loading.value = false;
    }
  }

  // Helper function to determine file extension from MIME type
  function getExtensionFromMimeType(mimeType) {
    const mimeToExt = {
      'image/jpeg': 'jpg',
      'image/png': 'png',
      'image/gif': 'gif',
      'image/webp': 'webp',
      'image/svg+xml': 'svg'
    };
    return mimeToExt[mimeType] || 'bin';
  }

  // Socket.IO event handlers for real-time updates
  function setupSocketListeners() {
    // A placeholder function, assuming `decryptFromServer` is defined elsewhere or not needed for this task
    const decryptFromServer = (data) => data; // Simplified for example

    // Secret created in a shared folder
    socketIO.on('secret_created', (data) => {
      const decrypted = decryptFromServer(data.encrypted)
      if (decrypted?.secret) {
        secrets.value.push(decrypted.secret)
      }
    })

    // Secret shared with current user
    socketIO.on('secret_shared', (data) => {
      const decrypted = decryptFromServer(data.encrypted)
      if (decrypted?.secret) {
        const index = secrets.value.findIndex(s => s.id === decrypted.secret.id)
        if (index !== -1) {
          // Update existing secret
          secrets.value[index] = decrypted.secret
        } else {
          // Add new shared secret
          secrets.value.push(decrypted.secret)
        }

        // Update current secret if it's the one being shared
        if (currentSecret.value?.id === decrypted.secret.id) {
          currentSecret.value = decrypted.secret
        }
      }
    })

    // Secret unshared with current user
    socketIO.on('secret_unshared', (data) => {
      // If this event is for the current user, remove the secret from the list
      if (data.unshared_with_id === authStore.userId) {
        const secretId = parseInt(data.secret_id)
        secrets.value = secrets.value.filter(s => s.id !== secretId)

        // Reset current secret if it was the one unshared
        if (currentSecret.value?.id === secretId) {
          currentSecret.value = null
        }
      }
    })

    // Secret updated (by owner or collaborator)
    socketIO.on('secret_updated', (data) => {
      const decrypted = decryptFromServer(data.encrypted)
      if (decrypted?.secret) {
        const index = secrets.value.findIndex(s => s.id === decrypted.secret.id)
        if (index !== -1) {
          secrets.value[index] = decrypted.secret
        }
        if (currentSecret.value?.id === decrypted.secret.id) {
          currentSecret.value = decrypted.secret
        }
      }
    })

    // Secret deleted (by owner or admin)
    socketIO.on('secret_deleted', (data) => {
      const decrypted = decryptFromServer(data.encrypted)
      if (decrypted?.secret_id) {
        secrets.value = secrets.value.filter(s => s.id !== decrypted.secret_id)
        if (currentSecret.value?.id === decrypted.secret_id) {
          currentSecret.value = null
        }
      }
    })

    // Folder shared with current user
    socketIO.on('folder_shared', (data) => {
      // If this event is for the current user, fetch the new folder
      if (data.shared_with === authStore.userId) {
        fetchFolder(data.folder_id).then(folder => {
          if (folder && !folders.value.some(f => f.id === folder.id)) {
            folders.value.push(folder)
          }
        })
      }
    })

    // Folder unshared with current user
    socketIO.on('folder_unshared', (data) => {
      // If this event is for the current user, remove the folder from the list
      if (data.unshared_with_id === authStore.userId) {
        const folderId = parseInt(data.folder_id)
        folders.value = folders.value.filter(f => f.id !== folderId)

        // Reset current folder if it was the one unshared
        if (currentFolder.value?.id === folderId) {
          currentFolder.value = null
        }

        // Also remove any secrets that were in this folder
        secrets.value = secrets.value.filter(s => s.folder_id !== folderId)
      }
    })

    // Folder deleted (by owner or admin)
    socketIO.on('folder_deleted', (data) => {
      // Remove folder from local state if it exists
      const folderId = parseInt(data.folder_id)
      folders.value = folders.value.filter(f => f.id !== folderId)

      // Reset current folder if it was the one deleted
      if (currentFolder.value?.id === folderId) {
        currentFolder.value = null
      }

      // Also remove any secrets that were in this folder
      secrets.value = secrets.value.filter(s => s.folder_id !== folderId)
    })

    // New folder created that user has access to
    socketIO.on('folder_created', (data) => {
      // If this event indicates it's for the current user, fetch the new folder
      if (data.owner_id === authStore.userId || data.shared_with_ids?.includes(authStore.userId)) {
        fetchFolder(data.folder_id).then(folder => {
          if (folder && !folders.value.some(f => f.id === folder.id)) {
            folders.value.push(folder)
          }
        })
      }
    })

    // Secret moved to a shared folder
    socketIO.on('secret_moved', (data) => {
      // If this event is for the current user (they have access to the destination folder)
      const userId = parseInt(authStore.userId)
      if (data.users_to_notify && data.users_to_notify.includes(userId)) {
        const secretId = parseInt(data.secret_id)

        // Check if we already have this secret
        const existingSecret = secrets.value.find(s => s.id === secretId)

        if (existingSecret) {
          // Update the folder_id of the existing secret
          existingSecret.folder_id = data.folder_id

          // If we're currently viewing this folder, refresh it to show latest contents
          if (currentFolder.value && currentFolder.value.id === parseInt(data.folder_id)) {
            fetchFolder(data.folder_id)
          }
        } else {
          // Fetch the secret and add it to our list
          fetchSecret(secretId).then(secret => {
            if (secret && !secrets.value.some(s => s.id === secret.id)) {
              secrets.value.push(secret)
            }
          })
        }
      }
    })
  }

  // Initialize socket listeners
  setupSocketListeners()

  // Return store API
  return {
    // State
    secrets,
    currentSecret,
    folders,
    currentFolder,
    loading,
    error,

    // Getters
    secretsCount,
    secretById,
    foldersCount,
    folderById,
    secretsByFolderId,

    // Actions
    fetchSecrets,
    fetchSecret,
    fetchSecretFile,
    downloadFileSecret,
    createSecret,
    updateSecret,
    deleteSecret,
    fetchFolders,
    fetchFolder,
    createFolder,
    updateFolder,
    deleteFolder,
    shareSecret,
    shareFolder,
    createSecretFile
  }
})