<script setup lang="ts">
import { useScoringStore } from '@/stores/scoring'

const store = useScoringStore()
</script>

<template>
  <div class="landing">
    <div class="landing-card">
      <div class="card-glow"></div>
      <div class="logo" v-if="store.siteConfig?.logo_image">
        <img :src="store.siteConfig.logo_image" alt="Logo" />
      </div>
      <div class="logo-placeholder" v-else>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
        </svg>
      </div>
      <h1>{{ store.siteConfig?.site_name || '评分系统' }}</h1>
      <p class="subtitle">请通过评委专属二维码或链接进入评分页面</p>
      <div class="divider"></div>
      <div class="actions">
        <router-link to="/manage" class="btn btn-outline admin-entry">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="icon">
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
            <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
          </svg>
          管理员入口
        </router-link>
      </div>
    </div>
    <div class="floating-shapes">
      <div class="shape shape-1"></div>
      <div class="shape shape-2"></div>
      <div class="shape shape-3"></div>
      <div class="shape shape-4"></div>
    </div>
  </div>
</template>

<style scoped>
.landing {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 20px;
  position: relative;
  overflow: hidden;
}

.landing-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: var(--radius-xl);
  padding: 56px 48px;
  text-align: center;
  max-width: 480px;
  width: 100%;
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.12),
    0 0 0 1px rgba(255, 255, 255, 0.5) inset;
  position: relative;
  z-index: 1;
  animation: slideUp 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.card-glow {
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, var(--primary-light) 0%, transparent 70%);
  opacity: 0.5;
  animation: rotate 20s linear infinite;
  pointer-events: none;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.logo {
  margin-bottom: 24px;
  animation: scaleIn 0.5s ease-out 0.2s both;
}

.logo img {
  height: 80px;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.1));
}

.logo-placeholder {
  width: 80px;
  height: 80px;
  margin: 0 auto 24px;
  background: var(--primary-gradient);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  animation: scaleIn 0.5s ease-out 0.2s both;
  box-shadow: 0 8px 24px rgba(24, 144, 255, 0.4);
}

.logo-placeholder svg {
  width: 40px;
  height: 40px;
}

h1 {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 12px;
  animation: slideUp 0.5s ease-out 0.3s both;
  background: linear-gradient(135deg, var(--text-primary) 0%, var(--text-secondary) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  color: var(--text-secondary);
  font-size: 16px;
  line-height: 1.6;
  margin-bottom: 32px;
  animation: slideUp 0.5s ease-out 0.4s both;
}

.divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, #e8e8e8, transparent);
  margin-bottom: 32px;
  animation: fadeIn 0.5s ease-out 0.5s both;
}

.actions {
  display: flex;
  flex-direction: column;
  gap: 16px;
  animation: slideUp 0.5s ease-out 0.6s both;
}

.admin-entry {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px 28px;
  font-size: 15px;
}

.admin-entry .icon {
  width: 18px;
  height: 18px;
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
  opacity: 0.1;
  animation: float 6s ease-in-out infinite;
}

.shape-1 {
  width: 300px;
  height: 300px;
  background: var(--primary-color);
  top: -100px;
  right: -100px;
  animation-delay: 0s;
}

.shape-2 {
  width: 200px;
  height: 200px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  bottom: -50px;
  left: -50px;
  animation-delay: 2s;
}

.shape-3 {
  width: 150px;
  height: 150px;
  background: var(--primary-color);
  top: 50%;
  left: 10%;
  animation-delay: 4s;
}

.shape-4 {
  width: 100px;
  height: 100px;
  background: linear-gradient(135deg, #f093fb, #f5576c);
  bottom: 20%;
  right: 10%;
  animation-delay: 1s;
}

/* 响应式适配 */
@media (max-width: 480px) {
  .landing-card {
    padding: 40px 24px;
    margin: 16px;
  }
  
  h1 {
    font-size: 26px;
  }
  
  .subtitle {
    font-size: 14px;
  }
}
</style>
