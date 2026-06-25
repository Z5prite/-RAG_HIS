<template>
  <div class="login-wrapper">
    <!-- Mesh Gradient Background -->
    <div class="mesh-bg">
      <div class="blob blob-1"></div>
      <div class="blob blob-2"></div>
      <div class="blob blob-3"></div>
    </div>

    <!-- Center Glass Card -->
    <div class="glass-card">
      <div class="card-header">
        <div class="brand-logo">
          <span class="logo-icon">⚕️</span>
        </div>
        <h2>HIS RAG</h2>
        <p>下一代智慧医疗数字助理</p>
      </div>

      <div class="form-container">
        <div class="input-group">
          <label>账号</label>
          <div class="input-wrapper">
            <input 
              type="text" 
              v-model="username" 
              placeholder="请输入工号或账号" 
              @keyup.enter="handleLogin"
            />
            <div class="animated-line"></div>
          </div>
        </div>

        <div class="input-group">
          <label>密码</label>
          <div class="input-wrapper">
            <input 
              type="password" 
              v-model="password" 
              placeholder="请输入密码" 
              @keyup.enter="handleLogin"
            />
            <div class="animated-line"></div>
          </div>
        </div>

        <transition name="fade">
          <div v-if="errorMsg" class="error-msg">
            {{ errorMsg }}
          </div>
        </transition>

        <button class="login-btn" :class="{ 'loading': isLoading }" @click="handleLogin" :disabled="isLoading">
          <span v-if="!isLoading">登录系统</span>
          <span v-else class="loader"></span>
        </button>

        <div class="test-accounts">
          <p>演示账号： <strong>admin</strong> (管理员) / <strong>user</strong> (医生)</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const emit = defineEmits(['login'])

const username = ref('')
const password = ref('')
const isLoading = ref(false)
const errorMsg = ref('')

const handleLogin = () => {
  if (!username.value || !password.value) {
    errorMsg.value = "请输入账号和密码"
    return
  }

  errorMsg.value = ''
  isLoading.value = true

  setTimeout(() => {
    if (username.value === 'admin' && password.value === 'admin') {
      emit('login', 'admin')
    } else if (username.value === 'user' && password.value === 'user') {
      emit('login', 'user')
    } else {
      errorMsg.value = "账号或密码错误"
    }
    isLoading.value = false
  }, 600)
}
</script>

<style scoped>
.login-wrapper {
  position: relative;
  width: 100vw;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: "Inter", -apple-system, sans-serif;
  overflow: hidden;
  background-color: #fafafa;
}

/* --- Mesh Gradient Background --- */
.mesh-bg {
  position: absolute;
  inset: 0;
  z-index: 1;
  overflow: hidden;
  background: #f8fafc;
}
.blob {
  position: absolute;
  filter: blur(80px);
  opacity: 0.6;
  animation: float 10s cubic-bezier(0.4, 0, 0.2, 1) infinite alternate;
}
.blob-1 {
  width: 500px;
  height: 500px;
  background: #c7d2fe; /* Soft Indigo */
  top: -10%;
  left: 10%;
}
.blob-2 {
  width: 600px;
  height: 600px;
  background: #e9d5ff; /* Soft Purple */
  bottom: -20%;
  right: -10%;
  animation-delay: -5s;
}
.blob-3 {
  width: 400px;
  height: 400px;
  background: #bfdbfe; /* Soft Blue */
  top: 40%;
  left: 40%;
  animation-delay: -2s;
}
@keyframes float {
  0% { transform: translate(0, 0) scale(1); }
  100% { transform: translate(50px, 30px) scale(1.1); }
}

/* --- Glassmorphism Card --- */
.glass-card {
  position: relative;
  z-index: 10;
  width: 100%;
  max-width: 420px;
  padding: 48px;
  background: rgba(255, 255, 255, 0.4);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.8); /* Inner glow */
  box-shadow: 0 30px 60px -12px rgba(15, 23, 42, 0.1);
  border-radius: 24px;
}

.card-header {
  text-align: center;
  margin-bottom: 40px;
}
.brand-logo {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  border-radius: 20px;
  background: linear-gradient(135deg, #0d9488, #0284c7);
  color: white;
  font-size: 32px;
  margin-bottom: 16px;
  box-shadow: 0 10px 20px rgba(13, 148, 136, 0.2);
}
.card-header h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
  letter-spacing: -0.5px;
}
.card-header p {
  margin: 0;
  font-size: 14px;
  color: #64748b;
}

/* --- Input Forms --- */
.input-group {
  margin-bottom: 28px;
  position: relative;
}
.input-group label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 8px;
}

.input-wrapper {
  position: relative;
  width: 100%;
}
.input-wrapper input {
  width: 100%;
  padding: 8px 0;
  font-size: 16px;
  color: #1e293b;
  background: transparent;
  border: none;
  border-bottom: 1px solid #cbd5e1;
  outline: none;
  transition: border-color 0.3s;
}
.input-wrapper input::placeholder {
  color: #94a3b8;
  font-weight: 400;
}

/* Animated Bottom Line */
.animated-line {
  position: absolute;
  bottom: 0;
  left: 50%;
  width: 0;
  height: 2px;
  background: linear-gradient(90deg, #0d9488, #0284c7);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  transform: translateX(-50%);
}
.input-wrapper input:focus ~ .animated-line {
  width: 100%;
}

/* --- Button --- */
.login-btn {
  width: 100%;
  height: 52px;
  margin-top: 10px;
  border: none;
  border-radius: 14px;
  background: linear-gradient(135deg, #0d9488 0%, #0284c7 100%);
  color: white;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 8px 20px rgba(13, 148, 136, 0.25);
}
.login-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 12px 24px rgba(13, 148, 136, 0.35);
}
.login-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

/* --- Misc --- */
.error-msg {
  color: #ef4444;
  font-size: 13px;
  text-align: center;
  margin-bottom: 16px;
}
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.test-accounts {
  margin-top: 24px;
  text-align: center;
}
.test-accounts p {
  margin: 0;
  font-size: 13px;
  color: #94a3b8;
}
.test-accounts strong {
  color: #475569;
}

.loader {
  border: 2px solid rgba(255,255,255,0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  animation: spin 1s linear infinite;
}
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
</style>
