/**
 * Provides cryptographic operations for end-to-end encryption using Web Crypto API
 */
class CryptoService {
  /**
   * Generate a key pair for DHKE
   * Using P-256 curve for better browser compatibility
   * @returns {Promise<{privateKey: CryptoKey, publicKey: CryptoKey, publicKeyBase64: string}>}
   */
  static async generateKeyPair() {
    try {
      // Generate an ECDH key pair using the P-256 curve (widely supported)
      const keyPair = await window.crypto.subtle.generateKey(
        {
          name: 'ECDH',
          namedCurve: 'P-256'  // Using P-256 instead of X25519 for compatibility
        },
        true, // extractable
        ['deriveKey', 'deriveBits'] // key usages
      )

      // Export the public key to spki format to match backend expectations
      const publicKeyRaw = await window.crypto.subtle.exportKey('spki', keyPair.publicKey)

      // Convert to Base64 for transmission
      const publicKeyBase64 = this.arrayBufferToBase64(publicKeyRaw)

      return {
        privateKey: keyPair.privateKey,
        publicKey: keyPair.publicKey,
        publicKeyBase64
      }
    } catch (error) {
      throw new Error('Failed to generate encryption keys')
    }
  }

  /**
   * Import a public key from base64 string
   * @param {string} base64Key - Base64 encoded public key
   * @returns {Promise<CryptoKey>}
   */
  static async importPublicKey(base64Key) {
    try {
      const keyBuffer = this.base64ToArrayBuffer(base64Key)

      return await window.crypto.subtle.importKey(
        'spki', // Format matches backend's SubjectPublicKeyInfo format
        keyBuffer,
        {
          name: 'ECDH',
          namedCurve: 'P-256'  // Using P-256 instead of X25519 for compatibility
        },
        true, // extractable
        [] // no usages for public key alone
      )
    } catch (error) {
      throw new Error('Failed to import server public key')
    }
  }

  /**
   * Derive a shared secret using ECDH
   * This matches the backend implementation more closely by deriving with HKDF
   * @param {CryptoKey} privateKey - Our private key
   * @param {CryptoKey} publicKey - Other party's public key
   * @returns {Promise<CryptoKey>} - AES-GCM key derived from the shared secret
   */
  static async deriveSharedSecret(privateKey, publicKey) {
    try {
      // Derive shared bits
      const sharedSecret = await window.crypto.subtle.deriveBits(
        {
          name: 'ECDH',
          public: publicKey
        },
        privateKey,
        256 // length in bits
      )

      // Use HKDF to derive the key from shared secret (to match backend)
      const derivedKey = await window.crypto.subtle.importKey(
        'raw',
        sharedSecret,
        { name: 'HKDF' },
        false,
        ['deriveBits', 'deriveKey']
      );

      // Derive AES-GCM key using HKDF with the same info as backend
      const aesKey = await window.crypto.subtle.deriveKey(
        {
          name: 'HKDF',
          info: new TextEncoder().encode('AuthBerry E2EE Key'),
          salt: new Uint8Array(0), // No salt to match backend
          hash: 'SHA-256'
        },
        derivedKey,
        { name: 'AES-GCM', length: 256 },
        false, // not extractable
        ['encrypt', 'decrypt'] // usages
      );

      return aesKey;
    } catch (error) {
      throw new Error('Failed to establish secure communication')
    }
  }

  /**
   * Encrypt data using AES-GCM with the shared secret
   * @param {CryptoKey} key - AES-GCM key
   * @param {Object|string} data - Data to encrypt
   * @returns {Promise<string>} - Base64 encoded encrypted data
   */
  static async encrypt(key, data) {
    try {
      // Convert data to string if it's an object
      const dataStr = typeof data === 'object' ? JSON.stringify(data) : String(data)

      // Convert string to ArrayBuffer
      const dataBuffer = new TextEncoder().encode(dataStr)

      // Generate random IV (12 bytes for AES-GCM), same as backend
      const iv = window.crypto.getRandomValues(new Uint8Array(12))

      // Encrypt the data
      const ciphertext = await window.crypto.subtle.encrypt(
        {
          name: 'AES-GCM',
          iv
        },
        key,
        dataBuffer
      )

      // Combine IV and ciphertext
      const result = new Uint8Array(iv.length + ciphertext.byteLength)
      result.set(iv, 0)
      result.set(new Uint8Array(ciphertext), iv.length)

      // Return as base64
      return this.arrayBufferToBase64(result)
    } catch (error) {
      throw new Error('Failed to encrypt data')
    }
  }

  /**
   * Decrypt data using AES-GCM with the shared secret
   * @param {CryptoKey} key - AES-GCM key
   * @param {string} encryptedBase64 - Base64 encoded encrypted data
   * @returns {Promise<Object|string>} - Decrypted data
   */
  static async decrypt(key, encryptedBase64) {
    try {
      // Convert base64 to ArrayBuffer
      const encryptedData = this.base64ToArrayBuffer(encryptedBase64)

      // Extract IV (first 12 bytes) and ciphertext
      const iv = encryptedData.slice(0, 12)
      const ciphertext = encryptedData.slice(12)

      // Decrypt the data
      const decryptedBuffer = await window.crypto.subtle.decrypt(
        {
          name: 'AES-GCM',
          iv: iv
        },
        key,
        ciphertext
      )

      // Convert ArrayBuffer to string
      const decryptedStr = new TextDecoder().decode(decryptedBuffer)

      // Try to parse as JSON, if it fails return as string
      try {
        return JSON.parse(decryptedStr)
      } catch {
        return decryptedStr
      }
    } catch (error) {
      throw new Error('Failed to decrypt data')
    }
  }

  /**
   * Convert ArrayBuffer to Base64 string
   * @param {ArrayBuffer} buffer - Array buffer to convert
   * @returns {string} - Base64 string
   */
  static arrayBufferToBase64(buffer) {
    const bytes = new Uint8Array(buffer)
    let binary = ''
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i])
    }
    return btoa(binary)
  }

  /**
   * Convert Base64 string to ArrayBuffer
   * @param {string} base64 - Base64 string to convert
   * @returns {ArrayBuffer} - Array buffer
   */
  static base64ToArrayBuffer(base64) {
    const binaryString = atob(base64)
    const bytes = new Uint8Array(binaryString.length)
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i)
    }
    return bytes.buffer
  }
}

export default CryptoService