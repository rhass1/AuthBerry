<template>
  <div class="password-strength-container" v-if="password">
    <div class="strength-label d-flex justify-space-between">
      <span>Strength:</span>
      <span :class="strengthColorClass">{{ strengthText }}</span>
    </div>
    <div class="strength-meter">
      <div 
        class="strength-meter-fill" 
        :style="{
          width: `${passwordStrength}%`, 
          backgroundColor: strengthColor
        }"
      ></div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, defineProps, defineEmits } from 'vue';

const props = defineProps({
  password: {
    type: String,
    required: true
  }
});

const emit = defineEmits(['update:strength']);

const passwordStrength = ref(0);
const strengthText = ref('');
const strengthColor = ref('');
const strengthColorClass = ref('');

const calculatePasswordStrength = (pwd) => {
  if (!pwd) {
    passwordStrength.value = 0;
    strengthText.value = '';
    strengthColor.value = '';
    strengthColorClass.value = '';
    emit('update:strength', 0);
    return;
  }
  
  let strength = 0;
  
  if (pwd.length >= 16) {
    strength += 35;
  } else if (pwd.length >= 12) {
    strength += 25;
  } else if (pwd.length >= 8) {
    strength += 15;
  } else if (pwd.length >= 6) {
    strength += 5;
  }
  
  if (/[A-Z]/.test(pwd)) strength += 10;
  if (/[a-z]/.test(pwd)) strength += 8;
  if (/[0-9]/.test(pwd)) strength += 8;
  if (/[^A-Za-z0-9]/.test(pwd)) strength += 14;
  
  if (/(.)\1{2,}/.test(pwd)) strength -= 15;
  
  const sequences = [
    'abcdefghijklmnopqrstuvwxyz',
    'qwertyuiop',
    'asdfghjkl',
    'zxcvbnm',
    '01234567890'
  ];
  
  for (const seq of sequences) {
    for (let i = 0; i < seq.length - 2; i++) {
      const fragment = seq.substring(i, i + 3).toLowerCase();
      if (pwd.toLowerCase().includes(fragment)) {
        strength -= 10;
        break;
      }
    }
  }
  
  if (/^[A-Za-z]+$/.test(pwd) || /^[0-9]+$/.test(pwd)) {
    strength -= 15;
  }
  
  const commonPatterns = [
    'password', 'admin', '123456', 'qwerty', 'welcome', 
    'abc123', 'letmein', 'monkey', 'login', '12345'
  ];
  
  for (const pattern of commonPatterns) {
    if (pwd.toLowerCase().includes(pattern)) {
      strength -= 20;
      break;
    }
  }
  
  passwordStrength.value = Math.max(0, Math.min(100, strength));
  
  if (passwordStrength.value >= 80) {
    strengthText.value = 'Strong';
    strengthColor.value = '#00ff9c';
    strengthColorClass.value = 'text-success';
  } else if (passwordStrength.value >= 50) {
    strengthText.value = 'Medium';
    strengthColor.value = '#eacc13';
    strengthColorClass.value = 'text-warning';
  } else {
    strengthText.value = 'Weak';
    strengthColor.value = '#ff5252';
    strengthColorClass.value = 'text-error';
  }
  
  emit('update:strength', passwordStrength.value);
};

watch(() => props.password, (newPassword) => {
  calculatePasswordStrength(newPassword);
}, { immediate: true });
</script>

<style scoped>
.password-strength-container {
  padding: 0.5rem 0;
}

.strength-label {
  font-size: 0.9rem;
  margin-bottom: 0.25rem;
  font-family: var(--font-heading);
  letter-spacing: 0.5px;
}

.text-success {
  color: #00ff9c;
  text-shadow: 0 0 8px rgba(0, 255, 156, 0.7);
}

.text-warning {
  color: #eacc13;
  text-shadow: 0 0 8px rgba(234, 204, 19, 0.7);
}

.text-error {
  color: #ff5252;
  text-shadow: 0 0 8px rgba(255, 82, 82, 0.7);
}

.strength-meter {
  height: 6px;
  background-color: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  position: relative;
  overflow: hidden;
  box-shadow: inset 0 0 5px rgba(0, 0, 0, 0.5);
}

.strength-meter-fill {
  height: 100%;
  transition: width 0.3s ease, background-color 0.3s ease;
  position: relative;
  border-radius: 2px;
  box-shadow: 0 0 10px currentColor;
}

.strength-meter-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, 
    transparent 0%, 
    rgba(255, 255, 255, 0.2) 50%, 
    transparent 100%);
  animation: glitch 1.5s cubic-bezier(.25, .46, .45, .94) infinite;
}

@keyframes glitch {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}
</style> 