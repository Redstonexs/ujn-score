<script setup lang="ts">
</script>

<template>
  <div class="not-found">
    <div class="floating-shapes">
      <div class="shape shape-1"></div>
      <div class="shape shape-2"></div>
      <div class="shape shape-3"></div>
      <div class="shape shape-4"></div>
    </div>
    <div class="not-found-card">
      <div class="error-code">
        <span class="digit">4</span>
        <div class="zero">
          <div class="zero-inner"></div>
        </div>
        <span class="digit">4</span>
      </div>
      <h1>页面未找到</h1>
      <p class="subtitle">抱歉，您访问的页面不存在或已被移除</p>
      <div class="divider"></div>
      <p class="hint">请检查链接是否正确，或返回首页继续浏览</p>
      <router-link to="/" class="btn">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
          <polyline points="9 22 9 12 15 12 15 22"/>
        </svg>
        返回首页
      </router-link>
    </div>
  </div>
</template>

<style scoped>
.not-found {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
  position: relative;
  overflow: hidden;
}

.floating-shapes {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.shape {
  position: absolute;
  border-radius: 50%;
  opacity: 0.1;
}

.shape-1 {
  width: 300px;
  height: 300px;
  background: linear-gradient(135deg, #1890ff, #36cfc9);
  top: -100px;
  right: -100px;
  animation: float 20s infinite ease-in-out;
}

.shape-2 {
  width: 200px;
  height: 200px;
  background: linear-gradient(135deg, #722ed1, #eb2f96);
  bottom: 10%;
  left: -50px;
  animation: float 25s infinite ease-in-out reverse;
}

.shape-3 {
  width: 150px;
  height: 150px;
  background: linear-gradient(135deg, #52c41a, #95de64);
  top: 40%;
  right: 10%;
  animation: float 18s infinite ease-in-out;
}

.shape-4 {
  width: 100px;
  height: 100px;
  background: linear-gradient(135deg, #faad14, #ffc53d);
  bottom: 20%;
  right: 20%;
  animation: float 22s infinite ease-in-out reverse;
}

@keyframes float {
  0%, 100% {
    transform: translate(0, 0) rotate(0deg);
  }
  25% {
    transform: translate(30px, -30px) rotate(90deg);
  }
  50% {
    transform: translate(0, -60px) rotate(180deg);
  }
  75% {
    transform: translate(-30px, -30px) rotate(270deg);
  }
}

.not-found-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  padding: 56px 48px;
  text-align: center;
  max-width: 440px;
  width: 90%;
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.08),
    0 2px 8px rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.8);
  position: relative;
  z-index: 1;
  animation: card-in 0.6s ease;
}

@keyframes card-in {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.error-code {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 24px;
}

.digit {
  font-size: 80px;
  font-weight: 800;
  background: var(--primary-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
  animation: digit-bounce 2s infinite ease-in-out;
}

.digit:first-child {
  animation-delay: 0s;
}

.digit:last-child {
  animation-delay: 0.4s;
}

@keyframes digit-bounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

.zero {
  width: 70px;
  height: 80px;
  background: var(--primary-gradient);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  animation: zero-pulse 2s infinite ease-in-out;
  animation-delay: 0.2s;
}

@keyframes zero-pulse {
  0%, 100% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(24, 144, 255, 0.4);
  }
  50% {
    transform: scale(1.05);
    box-shadow: 0 0 20px 10px rgba(24, 144, 255, 0.2);
  }
}

.zero-inner {
  width: 30px;
  height: 40px;
  background: #fff;
  border-radius: 50%;
}

h1 {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.subtitle {
  font-size: 15px;
  color: var(--text-secondary);
  margin-bottom: 24px;
}

.divider {
  width: 60px;
  height: 3px;
  background: var(--primary-gradient);
  border-radius: 2px;
  margin: 0 auto 20px;
}

.hint {
  font-size: 13px;
  color: var(--text-hint);
  margin-bottom: 28px;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 28px;
  background: var(--primary-gradient);
  color: #fff;
  border-radius: 12px;
  text-decoration: none;
  font-size: 15px;
  font-weight: 500;
  transition: all 0.3s;
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.3);
}

.btn svg {
  width: 18px;
  height: 18px;
}

.btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(24, 144, 255, 0.4);
}

@media (max-width: 480px) {
  .not-found-card {
    padding: 40px 32px;
  }

  .digit {
    font-size: 60px;
  }

  .zero {
    width: 52px;
    height: 60px;
  }

  .zero-inner {
    width: 22px;
    height: 30px;
  }

  h1 {
    font-size: 20px;
  }

  .subtitle {
    font-size: 14px;
  }
}
</style>
