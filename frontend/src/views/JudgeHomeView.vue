<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useScoringStore } from '@/stores/scoring'

const props = defineProps<{ token: string }>()
const router = useRouter()
const store = useScoringStore()
const authError = ref('')
let syncTimer: number | null = null

async function syncJudgeProgress() {
  try {
    await store.refreshJudgeState(props.token)
  } catch (e: any) {
    authError.value = e.message
  }
}

function handleVisibilityChange() {
  if (document.visibilityState === 'visible') {
    syncJudgeProgress()
  }
}

onMounted(async () => {
  try {
    await store.authenticateJudge(props.token)
    await store.fetchCategories()
    syncTimer = window.setInterval(syncJudgeProgress, 8000)
    document.addEventListener('visibilitychange', handleVisibilityChange)
  } catch (e: any) {
    authError.value = e.message
  }
})

onBeforeUnmount(() => {
  if (syncTimer !== null) {
    window.clearInterval(syncTimer)
  }
  document.removeEventListener('visibilitychange', handleVisibilityChange)
})

function goToScoring(categoryId: number) {
  router.push({ name: 'scoring', params: { token: props.token, categoryId: String(categoryId) } })
}

function isSubmitted(categoryId: number) {
  return store.isCategorySubmitted(categoryId)
}

const completedCount = computed(() =>
  store.categories.filter(c => isSubmitted(c.id)).length
)

const progressPercent = computed(() => {
  if (store.categories.length === 0) return 0
  return Math.round((completedCount.value / store.categories.length) * 100)
})

const judgeDisplayName = computed(() => '评委老师')
</script>

<template>
  <div class="judge-home">
    <!-- 错误状态 -->
    <div v-if="authError" class="error-card">
      <div class="error-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
      </div>
      <h2>访问失败</h2>
      <p>{{ authError }}</p>
    </div>

    <!-- 加载状态 -->
    <div v-else-if="store.loading" class="loading-card">
      <div class="spinner"></div>
      <p>正在验证身份...</p>
    </div>

    <!-- 正常状态 -->
    <div v-else-if="store.judgeInfo" class="home-container">
      <header class="page-header">
        <div class="header-content">
          <h1>{{ store.siteConfig?.site_name || '评分系统' }}</h1>
          <div class="judge-badge">
            <div class="avatar">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
            </div>
            <div class="judge-info">
              <span class="judge-name">{{ judgeDisplayName }}</span>
              <span class="judge-progress">{{ completedCount }}/{{ store.categories.length }} 已完成</span>
            </div>
          </div>
        </div>
        
        <!-- 进度条 -->
        <div class="progress-bar-container">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: `${progressPercent}%` }"></div>
          </div>
          <span class="progress-text">{{ progressPercent }}%</span>
        </div>
      </header>

      <div class="categories-grid">
        <div
          v-for="(cat, index) in store.categories"
          :key="cat.id"
          class="category-card"
          :class="{ submitted: isSubmitted(cat.id) }"
          :style="{ animationDelay: `${index * 0.1}s` }"
          @click="goToScoring(cat.id)"
        >
          <div class="card-header">
            <div class="card-status" :class="{ done: isSubmitted(cat.id) }">
              <svg v-if="isSubmitted(cat.id)" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
              </svg>
              {{ isSubmitted(cat.id) ? '已提交' : '待评分' }}
            </div>
          </div>
          
          <h3>{{ cat.name }}</h3>
          
          <div class="card-meta">
            <div class="meta-item">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
              </svg>
              {{ cat.participant_count }} 名选手
            </div>
          </div>
          
          <p v-if="cat.description" class="card-desc">{{ cat.description }}</p>
          
          <div class="card-action">
            <button class="btn btn-primary">
              {{ isSubmitted(cat.id) ? '查看评分' : '开始评分' }}
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="9 18 15 12 9 6"/>
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- 全部完成提示 -->
      <transition name="celebrate">
        <div v-if="completedCount === store.categories.length && store.categories.length > 0" class="all-done">
          <div class="celebration">
            <div class="confetti"></div>
            <div class="confetti"></div>
            <div class="confetti"></div>
            <div class="confetti"></div>
            <div class="confetti"></div>
          </div>
          <div class="done-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="16 12 12 8 8 12"/>
              <line x1="12" y1="16" x2="12" y2="8"/>
            </svg>
          </div>
          <h2>所有评分已完成</h2>
          <p>感谢您的参与！您的评分已成功提交。</p>
        </div>
      </transition>
    </div>
  </div>
</template>

<style scoped>
.judge-home {
  min-height: 100vh;
  padding: 20px;
}

.error-card,
.loading-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 80vh;
  text-align: center;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: var(--radius-xl);
  padding: 48px;
  max-width: 400px;
  margin: 0 auto;
  box-shadow: var(--shadow-lg);
  animation: scaleIn 0.5s ease-out;
}

.error-icon {
  width: 72px;
  height: 72px;
  background: linear-gradient(135deg, #ff4d4f 0%, #cf1322 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  margin-bottom: 20px;
  animation: bounce 1s ease infinite;
}

.error-icon svg {
  width: 36px;
  height: 36px;
}

.error-card h2 {
  color: var(--error-color);
  margin-bottom: 8px;
  font-size: 22px;
}

.error-card p {
  color: var(--text-secondary);
  margin-bottom: 24px;
}

.loading-card .spinner {
  width: 48px;
  height: 48px;
  border: 3px solid #f3f3f3;
  border-top-color: var(--primary-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

.loading-card p {
  color: var(--text-secondary);
}

.home-container {
  max-width: 900px;
  margin: 0 auto;
}

.page-header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: var(--radius-lg);
  padding: 24px 32px;
  margin-bottom: 24px;
  box-shadow: var(--shadow-md);
  animation: slideDown 0.5s ease-out;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 16px;
}

.page-header h1 {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  background: linear-gradient(135deg, var(--text-primary) 0%, var(--text-secondary) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.judge-badge {
  display: flex;
  align-items: center;
  gap: 12px;
  background: linear-gradient(135deg, rgba(24, 144, 255, 0.1) 0%, rgba(102, 126, 234, 0.1) 100%);
  padding: 8px 16px;
  border-radius: 50px;
  border: 1px solid rgba(24, 144, 255, 0.2);
}

.avatar {
  width: 36px;
  height: 36px;
  background: var(--primary-gradient);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.avatar svg {
  width: 20px;
  height: 20px;
}

.judge-info {
  display: flex;
  flex-direction: column;
}

.judge-name {
  font-weight: 600;
  color: var(--primary-color);
  font-size: 14px;
}

.judge-progress {
  color: var(--text-muted);
  font-size: 12px;
}

.progress-bar-container {
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-bar {
  flex: 1;
  height: 8px;
  background: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--primary-gradient);
  border-radius: 4px;
  transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.4);
}

.progress-text {
  font-size: 14px;
  font-weight: 600;
  color: var(--primary-color);
  min-width: 40px;
  text-align: right;
}

.categories-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  padding: 8px 0;
}

.category-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: var(--radius-lg);
  padding: 24px;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: var(--shadow-sm);
  border: 2px solid transparent;
  position: relative;
  overflow: hidden;
  animation: slideUp 0.5s ease-out backwards;
}

.category-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--primary-gradient);
  transform: scaleX(0);
  transition: transform 0.3s ease;
}

.category-card:not(.submitted):hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
  border-color: var(--primary-color);
}

.category-card:not(.submitted):hover::before {
  transform: scaleX(1);
}

.category-card.submitted {
  opacity: 0.8;
  cursor: default;
  background: rgba(245, 245, 245, 0.95);
}

.category-card.submitted::before {
  transform: scaleX(1);
  background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);
}

.card-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 12px;
}

.card-status {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  background: rgba(24, 144, 255, 0.1);
  color: var(--primary-color);
}

.card-status.done {
  background: rgba(82, 196, 26, 0.1);
  color: var(--success-color);
}

.card-status svg {
  width: 14px;
  height: 14px;
}

.category-card h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.card-meta {
  margin-bottom: 12px;
}

.meta-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-secondary);
}

.meta-item svg {
  width: 16px;
  height: 16px;
}

.card-desc {
  font-size: 13px;
  color: var(--text-muted);
  line-height: 1.5;
  margin-bottom: 16px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-action {
  margin-top: auto;
}

.card-action .btn {
  width: 100%;
  padding: 10px 20px;
  font-size: 14px;
}

.card-action .btn svg {
  width: 16px;
  height: 16px;
}

.done-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  width: 100%;
  padding: 10px 20px;
  background: rgba(82, 196, 26, 0.1);
  color: var(--success-color);
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
}

.done-badge svg {
  width: 16px;
  height: 16px;
}

/* 全部完成提示 */
.all-done {
  background: linear-gradient(135deg, rgba(82, 196, 26, 0.1) 0%, rgba(56, 158, 13, 0.1) 100%);
  border: 2px solid rgba(82, 196, 26, 0.3);
  border-radius: var(--radius-xl);
  padding: 48px;
  text-align: center;
  margin-top: 32px;
  position: relative;
  overflow: hidden;
  animation: celebrate 0.6s ease-out;
}

@keyframes celebrate {
  0% {
    opacity: 0;
    transform: scale(0.9);
  }
  50% {
    transform: scale(1.02);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

.celebration {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  overflow: hidden;
}

.confetti {
  position: absolute;
  width: 10px;
  height: 10px;
  background: var(--primary-color);
  animation: confetti-fall 3s ease-out infinite;
}

.confetti:nth-child(1) { left: 10%; animation-delay: 0s; background: #ff6b6b; }
.confetti:nth-child(2) { left: 30%; animation-delay: 0.5s; background: #4ecdc4; }
.confetti:nth-child(3) { left: 50%; animation-delay: 1s; background: #ffe66d; }
.confetti:nth-child(4) { left: 70%; animation-delay: 1.5s; background: #a8e6cf; }
.confetti:nth-child(5) { left: 90%; animation-delay: 2s; background: #ff8b94; }

@keyframes confetti-fall {
  0% {
    transform: translateY(-100%) rotate(0deg);
    opacity: 1;
  }
  100% {
    transform: translateY(100vh) rotate(720deg);
    opacity: 0;
  }
}

.done-icon {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  margin: 0 auto 20px;
  box-shadow: 0 8px 24px rgba(82, 196, 26, 0.4);
  animation: pulse 2s ease-in-out infinite;
}

.done-icon svg {
  width: 40px;
  height: 40px;
}

.all-done h2 {
  font-size: 24px;
  color: var(--success-color);
  margin-bottom: 8px;
}

.all-done p {
  color: var(--text-secondary);
}

.celebrate-enter-active,
.celebrate-leave-active {
  transition: all 0.5s ease;
}

.celebrate-enter-from,
.celebrate-leave-to {
  opacity: 0;
  transform: scale(0.9);
}

@media (max-width: 640px) {
  .page-header {
    padding: 20px;
  }
  
  .header-content {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .categories-grid {
    grid-template-columns: 1fr;
  }
  
  .all-done {
    padding: 32px 20px;
  }
}
</style>
