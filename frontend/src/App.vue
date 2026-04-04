<script setup lang="ts">
import { onMounted } from "vue";
import { useScoringStore } from "@/stores/scoring";

const store = useScoringStore();

onMounted(async () => {
  await store.fetchSiteConfig();
});
</script>

<template>
  <div
    class="app-container"
    :style="{
      '--primary-color': store.siteConfig?.primary_color || '#1890ff',
      '--primary-light': store.siteConfig?.primary_color
        ? `${store.siteConfig.primary_color}20`
        : '#1890ff20',
      '--primary-gradient': store.siteConfig?.primary_color
        ? `linear-gradient(135deg, ${store.siteConfig.primary_color} 0%, ${adjustColor(store.siteConfig.primary_color, -20)} 100%)`
        : 'linear-gradient(135deg, #1890ff 0%, #096dd9 100%)',
      backgroundImage: store.siteConfig?.background_image
        ? `linear-gradient(rgba(255, 255, 255, 0.12), rgba(255, 255, 255, 0.12)), url(${store.siteConfig.background_image})`
        : undefined,
    }"
  >
    <RouterView />
  </div>
</template>

<script lang="ts">
function adjustColor(color: string, amount: number): string {
  const hex = color.replace("#", "");
  const r = Math.max(
    0,
    Math.min(255, parseInt(hex.substring(0, 2), 16) + amount),
  );
  const g = Math.max(
    0,
    Math.min(255, parseInt(hex.substring(2, 4), 16) + amount),
  );
  const b = Math.max(
    0,
    Math.min(255, parseInt(hex.substring(4, 6), 16) + amount),
  );
  return `#${r.toString(16).padStart(2, "0")}${g.toString(16).padStart(2, "0")}${b.toString(16).padStart(2, "0")}`;
}
</script>

<style>
*,
*::before,
*::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family:
    -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue",
    Arial, "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  background-attachment: fixed;
  color: #333;
}

.app-container {
  min-height: 100vh;
  background-repeat: no-repeat;
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
  animation: fadeIn 0.5s ease-out;
}

:root {
  --primary-color: #1890ff;
  --primary-light: #1890ff20;
  --primary-gradient: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
  --success-color: #52c41a;
  --warning-color: #faad14;
  --error-color: #ff4d4f;
  --text-primary: #1a1a1a;
  --text-secondary: #666;
  --text-muted: #999;
  --bg-white: rgba(255, 255, 255, 0.95);
  --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.06);
  --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.12);
  --shadow-glow: 0 0 20px rgba(24, 144, 255, 0.3);
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 24px;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.9);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes pulse {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}

@keyframes float {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

@keyframes bounce {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-5px);
  }
}

/* 全局按钮样式 */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 24px;
  border-radius: var(--radius-md);
  font-size: 15px;
  font-weight: 500;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: none;
  position: relative;
  overflow: hidden;
}

.btn::before {
  content: "";
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.2),
    transparent
  );
  transition: left 0.5s;
}

.btn:hover::before {
  left: 100%;
}

.btn-primary {
  background: var(--primary-gradient);
  color: #fff;
  box-shadow: 0 4px 14px rgba(24, 144, 255, 0.4);
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(24, 144, 255, 0.5);
}

.btn-primary:active:not(:disabled) {
  transform: translateY(0);
}

.btn-primary:disabled {
  background: #d9d9d9;
  box-shadow: none;
  cursor: not-allowed;
}

.btn-outline {
  border: 2px solid var(--primary-color);
  color: var(--primary-color);
  background: transparent;
}

.btn-outline:hover:not(:disabled) {
  background: var(--primary-color);
  color: #fff;
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.btn-danger {
  background: linear-gradient(135deg, #ff4d4f 0%, #cf1322 100%);
  color: #fff;
  box-shadow: 0 4px 14px rgba(255, 77, 79, 0.4);
}

.btn-danger:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(255, 77, 79, 0.5);
}

/* 全局输入框样式 */
.input {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e8e8e8;
  border-radius: var(--radius-md);
  font-size: 15px;
  outline: none;
  transition: all 0.3s ease;
  background: #fff;
}

.input:hover {
  border-color: #d9d9d9;
}

.input:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px var(--primary-light);
}

/* 全局卡片样式 */
.card {
  background: var(--bg-white);
  backdrop-filter: blur(20px);
  border-radius: var(--radius-lg);
  padding: 32px;
  box-shadow: var(--shadow-lg);
  border: 1px solid rgba(255, 255, 255, 0.2);
  animation: slideUp 0.5s ease-out;
}

/* 滚动条美化 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 选中文字样式 */
::selection {
  background: var(--primary-light);
  color: var(--primary-color);
}
</style>
