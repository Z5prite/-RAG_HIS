<template>
  <div class="login-wrapper">
    <!-- Clinical Grid & Dynamic Heartbeat ECG Background -->
    <div class="medical-grid-bg">
      <div class="radial-glow"></div>
      <div class="horizontal-scanline"></div>
      
      <!-- Scrolling ECG Top Wave -->
      <svg class="heartbeat-svg heartbeat-top" viewBox="0 0 1000 100" preserveAspectRatio="none">
        <path class="heartbeat-path" d="M0,50 L100,50 Q110,40 115,50 L120,53 L125,10 L133,90 L138,48 L145,52 L155,50 Q165,38 175,50 L300,50 L350,50 Q360,40 365,50 L370,53 L375,10 L383,90 L388,48 L395,52 L405,50 Q415,38 425,50 L500,50 L600,50 Q610,40 615,50 L620,53 L625,10 L633,90 L638,48 L645,52 L655,50 Q665,38 675,50 L800,50 L850,50 Q860,40 865,50 L870,53 L875,10 L883,90 L888,48 L895,52 L905,50 Q915,38 925,50 L1000,50" />
      </svg>
      
      <!-- Scrolling ECG Bottom Wave -->
      <svg class="heartbeat-svg heartbeat-bottom" viewBox="0 0 1000 100" preserveAspectRatio="none">
        <path class="heartbeat-path" d="M0,50 L100,50 Q110,40 115,50 L120,53 L125,10 L133,90 L138,48 L145,52 L155,50 Q165,38 175,50 L300,50 L350,50 Q360,40 365,50 L370,53 L375,10 L383,90 L388,48 L395,52 L405,50 Q415,38 425,50 L500,50 L600,50 Q610,40 615,50 L620,53 L625,10 L633,90 L638,48 L645,52 L655,50 Q665,38 675,50 L800,50 L850,50 Q860,40 865,50 L870,53 L875,10 L883,90 L888,48 L895,52 L905,50 Q915,38 925,50 L1000,50" />
      </svg>
    </div>

    <!-- Center Tech-Medical Card -->
    <div class="login-card">
      <div class="card-header">
        <div class="brand-logo">
          <span class="logo-icon">⚕️</span>
          <div class="logo-pulse"></div>
        </div>
        <h2>HIS RAG</h2>
        <p class="brand-desc">临床决策支持与智能分诊系统</p>
        <div class="system-status">
          <span class="status-dot"></span>
          <span class="status-text">系统就绪 / TERMINAL ONLINE</span>
        </div>
      </div>

      <div class="form-container">
        <div class="input-group">
          <label class="input-label">账号 / USERNAME</label>
          <div class="input-wrapper">
            <svg class="input-icon" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
            <input 
              type="text" 
              v-model="username" 
              placeholder="请输入工号或账号" 
              @keyup.enter="handleLogin"
              class="form-input"
            />
            <div class="animated-underline"></div>
          </div>
        </div>

        <div class="input-group">
          <label class="input-label">密码 / PASSWORD</label>
          <div class="input-wrapper">
            <svg class="input-icon" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
            <input 
              type="password" 
              v-model="password" 
              placeholder="请输入密码" 
              @keyup.enter="handleLogin"
              class="form-input"
            />
            <div class="animated-underline"></div>
          </div>
        </div>

        <transition name="fade">
          <div v-if="errorMsg" class="error-msg">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="err-icon"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
            <span>{{ errorMsg }}</span>
          </div>
        </transition>

        <button class="login-btn" :class="{ 'loading': isLoading }" @click="handleLogin" :disabled="isLoading">
          <span v-if="!isLoading">进入接诊工作台</span>
          <span v-else class="loader"></span>
        </button>

        <div class="test-accounts">
          <div class="divider">
            <span>DEMO ACCOUNTS</span>
          </div>
          <div class="account-chips">
            <span class="account-chip" @click="fillAccount('admin', 'admin')">
              <strong>admin</strong> <span class="chip-role">管理员</span>
            </span>
            <span class="account-chip" @click="fillAccount('user', 'user')">
              <strong>user</strong> <span class="chip-role">医生</span>
            </span>
          </div>
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

const fillAccount = (u, p) => {
  username.value = u
  password.value = p
}

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
  overflow: hidden;
  background-color: #fafafa;
  color: #0f172a;
}

/* --- Medical Grid & Scrolling ECG Background --- */
.medical-grid-bg {
  position: absolute;
  inset: 0;
  z-index: 1;
  background-color: #f8fafc;
  background-image: 
    /* Minor Lines: every 20px */
    linear-gradient(rgba(13, 148, 136, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(13, 148, 136, 0.04) 1px, transparent 1px),
    /* Major Lines: every 100px */
    linear-gradient(rgba(13, 148, 136, 0.1) 1.5px, transparent 1.5px),
    linear-gradient(90deg, rgba(13, 148, 136, 0.1) 1.5px, transparent 1.5px);
  background-size: 20px 20px, 20px 20px, 100px 100px, 100px 100px;
}

.radial-glow {
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 50% 40%, rgba(13, 148, 136, 0.07), transparent 60%);
  pointer-events: none;
}

.horizontal-scanline {
  position: absolute;
  width: 100%;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(13, 148, 136, 0.15), transparent);
  top: 0;
  animation: scan 8s linear infinite;
  pointer-events: none;
}

@keyframes scan {
  0% { top: -5%; }
  100% { top: 105%; }
}

/* ECG Heartbeat Lines Styling */
.heartbeat-svg {
  position: absolute;
  left: 0;
  width: 200%;
  height: 80px;
  pointer-events: none;
  z-index: 2;
  opacity: 0.18;
}

.heartbeat-top {
  top: 20%;
}

.heartbeat-bottom {
  bottom: 20%;
}

.heartbeat-path {
  stroke: #0d9488;
  stroke-width: 2;
  fill: none;
  stroke-linecap: round;
  stroke-linejoin: round;
  animation: ecgScroll 14s linear infinite;
  filter: drop-shadow(0 0 3px rgba(13, 148, 136, 0.4));
}

.heartbeat-bottom .heartbeat-path {
  stroke: #0f766e;
  animation-duration: 20s;
  animation-direction: reverse;
  filter: drop-shadow(0 0 3px rgba(15, 118, 110, 0.3));
}

@keyframes ecgScroll {
  0% { transform: translate3d(0, 0, 0); }
  100% { transform: translate3d(-50%, 0, 0); }
}

/* --- Medical Login Card --- */
.login-card {
  position: relative;
  z-index: 10;
  width: 100%;
  max-width: 440px;
  padding: 44px 40px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.95);
  box-shadow: 
    0 10px 30px -10px rgba(15, 23, 42, 0.04),
    0 20px 50px -15px rgba(15, 23, 42, 0.06),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
  border-radius: 20px;
  transition: transform 0.3s ease;
}

.card-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  margin-bottom: 36px;
}

.brand-logo {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 60px;
  height: 60px;
  border-radius: 16px;
  background: linear-gradient(135deg, #0d9488, #0f766e);
  color: white;
  font-size: 28px;
  margin-bottom: 16px;
  box-shadow: 0 8px 16px rgba(13, 148, 136, 0.2);
}

.logo-pulse {
  position: absolute;
  inset: -4px;
  border: 2px solid #0d9488;
  border-radius: 20px;
  opacity: 0;
  animation: logoGlow 2.5s infinite;
}

@keyframes logoGlow {
  0% { transform: scale(0.95); opacity: 0.5; }
  50% { transform: scale(1.1); opacity: 0; }
  100% { transform: scale(0.95); opacity: 0; }
}

.card-header h2 {
  margin: 0 0 6px 0;
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.02em;
}

.brand-desc {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #64748b;
  font-weight: 500;
}

.system-status {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 4px 10px;
  background: rgba(13, 148, 136, 0.06);
  border: 1px solid rgba(13, 148, 136, 0.15);
  border-radius: 6px;
}

.status-dot {
  width: 6px;
  height: 6px;
  background-color: #0d9488;
  border-radius: 50%;
  animation: beacon 1.8s infinite;
}

.status-text {
  font-size: 11px;
  font-family: ui-monospace, SFMono-Regular, monospace;
  font-weight: 600;
  color: #0f766e;
  letter-spacing: 0.05em;
}

@keyframes beacon {
  0% { transform: scale(0.9); opacity: 1; box-shadow: 0 0 0 0 rgba(13, 148, 136, 0.7); }
  70% { transform: scale(1.1); opacity: 0.4; box-shadow: 0 0 0 5px rgba(13, 148, 136, 0); }
  100% { transform: scale(0.9); opacity: 1; box-shadow: 0 0 0 0 rgba(13, 148, 136, 0); }
}

/* --- Input Groups --- */
.form-container {
  display: flex;
  flex-direction: column;
}

.input-group {
  margin-bottom: 24px;
  position: relative;
}

.input-label {
  display: block;
  font-size: 11px;
  font-family: ui-monospace, SFMono-Regular, monospace;
  font-weight: 700;
  color: #64748b;
  margin-bottom: 8px;
  letter-spacing: 0.05em;
}

.input-wrapper {
  position: relative;
  width: 100%;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 0;
  color: #94a3b8;
  pointer-events: none;
  transition: color 0.3s;
}

.form-input {
  width: 100%;
  padding: 10px 0 10px 28px;
  font-size: 15px;
  color: #0f172a;
  background: transparent;
  border: none;
  border-bottom: 1px solid #cbd5e1;
  outline: none;
  transition: border-color 0.3s;
}

.form-input::placeholder {
  color: #94a3b8;
  font-weight: 400;
}

/* Underline Animation */
.animated-underline {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 0;
  height: 2px;
  background: linear-gradient(90deg, #0d9488, #0f766e);
  transition: width 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}

.form-input:focus ~ .animated-underline {
  width: 100%;
}

.form-input:focus ~ .input-icon {
  color: #0d9488;
}

/* --- Error Messages --- */
.error-msg {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #e11d48;
  background: #fef2f2;
  border: 1px solid #fecaca;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 20px;
}

.err-icon {
  flex-shrink: 0;
}

.fade-enter-active, .fade-leave-active {
  transition: all 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* --- Submit Button --- */
.login-btn {
  position: relative;
  width: 100%;
  height: 50px;
  border: none;
  border-radius: 12px;
  background: linear-gradient(135deg, #0d9488, #0f766e);
  color: white;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 12px rgba(13, 148, 136, 0.15);
}

.login-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(13, 148, 136, 0.25);
}

.login-btn:active:not(:disabled) {
  transform: translateY(0);
}

.login-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* --- Demo Accounts Footer --- */
.test-accounts {
  margin-top: 32px;
  text-align: center;
}

.divider {
  position: relative;
  margin-bottom: 16px;
}

.divider::before {
  content: "";
  position: absolute;
  left: 0;
  top: 50%;
  width: 100%;
  height: 1px;
  background-color: #e2e8f0;
}

.divider span {
  position: relative;
  background-color: #ffffff;
  padding: 0 12px;
  font-size: 10px;
  font-family: ui-monospace, SFMono-Regular, monospace;
  font-weight: 700;
  color: #94a3b8;
  letter-spacing: 0.1em;
}

.account-chips {
  display: flex;
  justify-content: center;
  gap: 12px;
}

.account-chip {
  padding: 6px 12px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 13px;
  color: #334155;
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;
}

.account-chip:hover {
  background: rgba(13, 148, 136, 0.05);
  border-color: rgba(13, 148, 136, 0.3);
  color: #0d9488;
}

.account-chip strong {
  font-family: ui-monospace, SFMono-Regular, monospace;
  color: #0f172a;
}

.account-chip:hover strong {
  color: #0d9488;
}

.chip-role {
  font-size: 11px;
  color: #64748b;
  margin-left: 4px;
}

/* Loader */
.loader {
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
