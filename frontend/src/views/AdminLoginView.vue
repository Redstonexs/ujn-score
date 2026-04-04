<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useScoringStore } from '@/stores/scoring'

const router = useRouter()
const store = useScoringStore()
const password = ref('')
const error = ref('')
const loading = ref(false)
const showPassword = ref(false)

async function handleLogin() {
  if (!password.value.trim()) {
    error.value = '请输入密码'
    return
  }
  loading.value = true
  error.value = ''
  try {
    await store.verifyAdmin(password.value)
    router.push({ name: 'adminDashboard' })
  } catch (e: any) {
    error.value = e.message
    shakeCard()
  } finally {
    loading.value = false
  }
}

const cardRef = ref<HTMLElement | null>(null)
function shakeCard() {
  if (cardRef.value) {
    cardRef.value.classList.add('shake')
    setTimeout(() => {
      cardRef.value?.classList.remove('shake')
    }, 500)
  }
}
</script>

<template>
  <div class="admin-login">
    <div class="login-card" ref="cardRef">
      <div class="card-decoration">
        <div class="decoration-circle"></div>
        <div class="decoration-circle"></div>
      </div>
      
      <div class="login-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
          <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
        </svg>
      </div>
      
      <h1>管理后台</h1>
      <p class="subtitle">请输入管理员密码以继续</p>
      
      <form @submit.prevent="handleLogin">
        <div class="input-wrapper">
          <input
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            class="input password-input"
            placeholder="请输入密码"
            autofocus
          />
          <button 
            type="button" 
            class="toggle-password"
            @click="showPassword = !showPassword"
          >
            <svg v-if="showPassword" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
              <circle cx="12" cy="12" r="3"/>
            </svg>
            <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
              <line x1="1" y1="1" x2="23" y2="23"/>
            </svg>
          </button>
        </div>
        
        <transition name="fade">
          <div v-if="error" class="error-msg">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="12" y1="8" x2="12" y2="12"/>
              <line x1="12" y1="16" x2="12.01" y2="16"/>
            </svg>
            {{ error }}
          </div>
        </transition>
        
        <button type="submit" class="btn btn-primary login-btn" :disabled="loading">
          <span v-if="loading" class="spinner"></span>
          <span v-else>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/>
              <polyline points="10 17 15 12 10 7"/>
              <line x1="15" y1="12" x2="3" y2="12"/>
            </svg>
          </span>
          {{ loading ? '验证中...' : '登录' }}
        </button>
      </form>
      
      <router-link to="/" class="back-link">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="19" y1="12" x2="5" y2="12"/>
          <polyline points="12 19 5 12 12 5"/>
        </svg>
        返回首页
      </router-link>
    </div>
    
    <div class="floating-shapes">
      <div class="shape shape-1"></div>
      <div class="shape shape-2"></div>
      <div class="shape shape-3"></div>
    </div>
  </div>
</template>

<style scoped>
.admin-login {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 20px;
  position: relative;
  overflow: hidden;
}

.login-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: var(--radius-xl);
  padding: 48px 40px;
  text-align: center;
  max-width: 420px;
  width: 100%;
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.12),
    0 0 0 1px rgba(255, 255, 255, 0.5) inset;
  position: relative;
  z-index: 1;
  animation: slideUp 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.login-card.shake {
  animation: shake 0.5s ease-in-out;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
  20%, 40%, 60%, 80% { transform: translateX(5px); }
}

.card-decoration {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: var(--primary-gradient);
}

.card-decoration .decoration-circle {
  position: absolute;
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: var(--primary-light);
  filter: blur(40px);
}

.card-decoration .decoration-circle:first-child {
  top: -50px;
  left: -30px;
}

.card-decoration .decoration-circle:last-child {
  top: -30px;
  right: -20px;
  background: rgba(102, 126, 234, 0.2);
}

.login-icon {
  width: 72px;
  height: 72px;
  margin: 0 auto 24px;
  background: var(--primary-gradient);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 8px 24px rgba(24, 144, 255, 0.4);
  animation: scaleIn 0.5s ease-out 0.2s both;
}

.login-icon svg {
  width: 36px;
  height: 36px;
}

h1 {
  font-size: 26px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
  animation: slideUp 0.5s ease-out 0.3s both;
}

.subtitle {
  color: var(--text-secondary);
  font-size: 14px;
  margin-bottom: 32px;
  animation: slideUp 0.5s ease-out 0.4s both;
}

form {
  display: flex;
  flex-direction: column;
  gap: 16px;
  animation: slideUp 0.5s ease-out 0.5s both;
}

.input-wrapper {
  position: relative;
}

.password-input {
  padding-right: 48px;
}

.toggle-password {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.3s;
}

.toggle-password:hover {
  color: var(--primary-color);
}

.toggle-password svg {
  width: 20px;
  height: 20px;
}

.error-msg {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: var(--error-color);
  font-size: 14px;
  padding: 10px 16px;
  background: #fff2f0;
  border-radius: var(--radius-md);
  border: 1px solid #ffccc7;
}

.error-msg svg {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

.login-btn {
  width: 100%;
  padding: 14px;
  font-size: 16px;
  margin-top: 8px;
}

.login-btn svg {
  width: 18px;
  height: 18px;
}

.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.back-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-top: 28px;
  color: var(--text-muted);
  text-decoration: none;
  font-size: 14px;
  transition: all 0.3s;
  animation: fadeIn 0.5s ease-out 0.6s both;
}

.back-link svg {
  width: 16px;
  height: 16px;
  transition: transform 0.3s;
}

.back-link:hover {
  color: var(--primary-color);
}

.back-link:hover svg {
  transform: translateX(-3px);
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: all 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* 浮动装饰元素 */
.floating-shapes {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  overflow: hidden;
}

.shape {
  position: absolute;
  border-radius: 50%;
  opacity: 0.08;
  animation: float 8s ease-in-out infinite;
}

.shape-1 {
  width: 400px;
  height: 400px;
  background: var(--primary-color);
  top: -150px;
  right: -150px;
  animation-delay: 0s;
}

.shape-2 {
  width: 300px;
  height: 300px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  bottom: -100px;
  left: -100px;
  animation-delay: 3s;
}

.shape-3 {
  width: 200px;
  height: 200px;
  background: var(--primary-color);
  top: 40%;
  right: 10%;
  animation-delay: 5s;
}

@media (max-width: 480px) {
  .login-card {
    padding: 40px 24px;
    margin: 16px;
  }
  
  h1 {
    font-size: 22px;
  }
}
</style>
