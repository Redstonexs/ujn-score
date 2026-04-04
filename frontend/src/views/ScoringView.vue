<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, computed } from "vue";
import { useRouter } from "vue-router";
import { useScoringStore } from "@/stores/scoring";
import { showAlert, showConfirm } from "@/utils/dialog";

const props = defineProps<{ token: string; categoryId: string }>();
const router = useRouter();
const store = useScoringStore();
const submitting = ref(false);
const submitError = ref("");
const submitSuccess = ref(false);
let syncTimer: number | null = null;

const categoryIdNum = computed(() => parseInt(props.categoryId));
const currentCategory = computed(() =>
  store.categories.find((c) => c.id === categoryIdNum.value),
);
const categoryParticipants = computed(() =>
  store.participants.filter((p) => p.category_id === categoryIdNum.value),
);
const siteConfig = computed(() => store.siteConfig);
const scoreStep = computed(() =>
  siteConfig.value?.score_value_type === "integer" ? "1" : "0.01",
);
const judgeDisplayName = computed(() => "评委老师");
const scoreRuleHint = computed(() => {
  if (!siteConfig.value) return "";
  const typeText =
    siteConfig.value.score_value_type === "decimal"
      ? "仅小数（最多两位）"
      : siteConfig.value.score_value_type === "integer_decimal"
        ? "整数或小数（最多两位）"
        : "仅整数";
  const duplicateText = siteConfig.value.allow_duplicate_scores
    ? "允许重复分数"
    : "不允许重复分数";
  return `请按规则打分：${typeText}，${duplicateText}，范围 ${siteConfig.value.score_min} - ${siteConfig.value.score_max}`;
});

const isSubmitted = computed(() =>
  store.isCategorySubmitted(categoryIdNum.value),
);

function normalizeScoreText(raw: string) {
  return raw.trim();
}

function normalizeComparableScore(value: number) {
  if (!siteConfig.value) return String(value);
  return siteConfig.value.score_value_type === "integer"
    ? String(Math.trunc(value))
    : value.toFixed(2);
}

function validateScoreInput(rawValue: string, participantId: number) {
  if (!siteConfig.value) {
    return { value: null, error: "评分规则未加载" };
  }

  const text = normalizeScoreText(rawValue);
  if (!text) {
    return { value: null, error: "" };
  }

  const pattern =
    siteConfig.value.score_value_type === "integer"
      ? /^-?\d+$/
      : siteConfig.value.score_value_type === "decimal"
        ? /^-?\d+\.\d{1,2}$/
        : /^-?\d+(\.\d{1,2})?$/;
  if (!pattern.test(text)) {
    return {
      value: null,
      error:
        siteConfig.value.score_value_type === "decimal"
          ? "当前规则只允许输入最多两位小数"
          : siteConfig.value.score_value_type === "integer_decimal"
            ? "当前规则只允许输入整数或最多两位小数"
            : "当前规则只允许输入整数",
    };
  }

  const value = Number(text);
  if (!Number.isFinite(value)) {
    return { value: null, error: "请输入有效分数" };
  }

  if (
    value < siteConfig.value.score_min ||
    value > siteConfig.value.score_max
  ) {
    return {
      value: null,
      error: `分数必须在 ${siteConfig.value.score_min} - ${siteConfig.value.score_max} 之间`,
    };
  }

  if (!siteConfig.value.allow_duplicate_scores) {
    const normalizedValue = normalizeComparableScore(value);
    const hasDuplicate = categoryParticipants.value.some((participant) => {
      if (participant.id === participantId) return false;
      const saved = store.getScore(categoryIdNum.value, participant.id);
      return (
        saved !== undefined &&
        normalizeComparableScore(saved) === normalizedValue
      );
    });
    if (hasDuplicate) {
      return { value: null, error: "当前规则不允许重复打分" };
    }
  }

  return { value, error: "" };
}

const allScoresValid = computed(() => {
  if (!siteConfig.value || !categoryParticipants.value.length) return false;
  return categoryParticipants.value.every((participant) => {
    const score = store.getScore(categoryIdNum.value, participant.id);
    if (score === undefined) return false;
    return !validateScoreInput(String(score), participant.id).error;
  });
});

async function syncJudgeProgress() {
  try {
    await store.refreshJudgeState(props.token);
  } catch {
    // keep current screen, backend error will appear on next submit
  }
}

function handleVisibilityChange() {
  if (document.visibilityState === "visible") {
    syncJudgeProgress();
  }
}

onMounted(async () => {
  try {
    await store.authenticateJudge(props.token);
  } catch {
    router.push("/");
    return;
  }
  await store.fetchCategories();
  await store.fetchParticipants(categoryIdNum.value);
  syncTimer = window.setInterval(syncJudgeProgress, 8000);
  document.addEventListener("visibilitychange", handleVisibilityChange);
});

onBeforeUnmount(() => {
  if (syncTimer !== null) {
    window.clearInterval(syncTimer);
  }
  document.removeEventListener("visibilitychange", handleVisibilityChange);
});

function clearInvalidScore(
  participantId: number,
  target: HTMLInputElement,
  message: string,
) {
  store.clearScore(categoryIdNum.value, participantId);
  target.value = "";
  submitError.value = message;
  void showAlert(message);
}

function handleScoreInput(participantId: number, event: Event) {
  const target = event.target as HTMLInputElement;
  const rawValue = target.value;
  const { value, error } = validateScoreInput(rawValue, participantId);

  if (!normalizeScoreText(rawValue)) {
    store.clearScore(categoryIdNum.value, participantId);
    submitError.value = "";
    return;
  }

  if (error || value === null) {
    clearInvalidScore(participantId, target, error || "请输入有效分数");
    return;
  }

  store.setScore(categoryIdNum.value, participantId, value);
  submitError.value = "";
}

async function handleSubmit() {
  if (!allScoresValid.value || isSubmitted.value) return;
  if (!(await showConfirm("请再次确认本类别所有分数无误，确认后将提交且不可修改。")))
    return;

  submitting.value = true;
  submitError.value = "";
  try {
    await store.submitScores(categoryIdNum.value);
    submitSuccess.value = true;
    setTimeout(() => {
      router.push({ name: "judgeHome", params: { token: props.token } });
    }, 1500);
  } catch (e: any) {
    submitError.value = e.message;
  } finally {
    submitting.value = false;
  }
}

function goBack() {
  router.push({ name: "judgeHome", params: { token: props.token } });
}
</script>

<template>
  <div class="scoring-page">
    <div class="scoring-container">
      <!-- 顶部导航 -->
      <header class="scoring-header">
        <button class="back-btn" @click="goBack">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <line x1="19" y1="12" x2="5" y2="12" />
            <polyline points="12 19 5 12 12 5" />
          </svg>
          返回
        </button>
        <h1>{{ currentCategory?.name || "评分" }}</h1>
        <div class="judge-tag">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
          {{ judgeDisplayName }}
        </div>
      </header>

      <!-- 提交成功提示 -->
      <transition name="fade-scale">
        <div v-if="submitSuccess" class="success-overlay">
          <div class="success-card">
            <div class="success-icon">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2.5"
              >
                <polyline points="20 6 9 17 4 12" />
              </svg>
            </div>
            <h2>提交成功</h2>
            <p>正在返回...</p>
            <div class="progress-bar">
              <div class="progress-fill"></div>
            </div>
          </div>
        </div>
      </transition>

      <!-- 已提交提示 - 显示评分详情（只读） -->
      <div v-if="isSubmitted && !submitSuccess" class="submitted-content">
        <div class="submitted-header">
          <div class="submitted-badge">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <circle cx="12" cy="12" r="10" />
              <polyline points="8 12 11 15 16 9" />
            </svg>
            <span>已提交</span>
          </div>
          <h3>评分详情</h3>
          <p class="submitted-desc">您已完成此类别的评分，以下是您的评分记录</p>
        </div>

        <div class="scoring-table-wrap submitted-table-wrap">
          <table class="scoring-table">
            <thead>
              <tr>
                <th class="col-order">序号</th>
                <th class="col-name">选手信息</th>
                <th class="col-score">您的评分</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(p, idx) in categoryParticipants"
                :key="p.id"
                class="participant-row"
              >
                <td class="col-order">
                  <span class="order-badge">{{ idx + 1 }}</span>
                </td>
                <td class="col-name">
                  <div class="participant-info text-center">
                    <div class="participant-details">
                      <div class="participant-name">{{ p.name }}</div>
                      <div class="participant-college">
                        <span v-if="p.college" class="college-badge">{{
                          p.college
                        }}</span>
                        <span v-else class="college-empty">-</span>
                      </div>
                    </div>
                  </div>
                </td>
                <td class="col-score">
                  <div class="score-display">
                    <span class="score-value">{{
                      store.getScore(categoryIdNum, p.id) ?? "-"
                    }}</span>
                    <span class="score-unit">分</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="submitted-actions">
          <button class="btn btn-outline" @click="goBack">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <line x1="19" y1="12" x2="5" y2="12" />
              <polyline points="12 19 5 12 12 5" />
            </svg>
            返回首页
          </button>
        </div>
      </div>

      <!-- 评分表格 -->
      <div v-else-if="!submitSuccess" class="scoring-content">
        <div class="score-hint" v-if="store.siteConfig">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="16" x2="12" y2="12" />
            <line x1="12" y1="8" x2="12.01" y2="8" />
          </svg>
          {{ scoreRuleHint }}
        </div>

        <div class="scoring-table-wrap">
          <table class="scoring-table">
            <thead>
              <tr>
                <th class="col-order">序号</th>
                <th class="col-name">选手信息</th>
                <th class="col-score">分数</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(p, idx) in categoryParticipants"
                :key="p.id"
                class="participant-row"
              >
                <td class="col-order">
                  <span class="order-badge">{{ idx + 1 }}</span>
                </td>
                <td class="col-name">
                  <div class="participant-info text-center">
                    <div class="participant-details">
                      <div class="participant-name">{{ p.name }}</div>
                      <div class="participant-college">
                        <span v-if="p.college" class="college-badge">{{
                          p.college
                        }}</span>
                        <span v-else class="college-empty">-</span>
                      </div>
                    </div>
                  </div>
                </td>
                <td class="col-score">
                  <div class="score-input-wrapper">
                    <input
                      type="number"
                      class="score-input"
                      :min="store.siteConfig?.score_min || 1"
                      :max="store.siteConfig?.score_max || 100"
                      :value="store.getScore(categoryIdNum, p.id) ?? ''"
                      @input="handleScoreInput(p.id, $event)"
                      :placeholder="`${store.siteConfig?.score_min || 1}-${store.siteConfig?.score_max || 100}`"
                      :step="scoreStep"
                    />
                    <span class="score-unit">分</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 错误信息 -->
        <transition name="slide-down">
          <div v-if="submitError" class="error-msg">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            {{ submitError }}
          </div>
        </transition>

        <!-- 提交按钮 -->
        <div class="submit-area">
          <button
            class="btn btn-submit"
            :class="{
              'btn-primary': allScoresValid,
              'btn-disabled': !allScoresValid,
            }"
            :disabled="!allScoresValid || submitting"
            @click="handleSubmit"
          >
            <span v-if="submitting" class="spinner"></span>
            <svg
              v-else
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <polyline points="20 6 9 17 4 12" />
            </svg>
            {{ submitting ? "提交中..." : "确认提交" }}
          </button>
          <p class="submit-hint" v-if="!allScoresValid">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            请确保所有选手都已评分且分数在有效范围内
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.scoring-page {
  min-height: 100vh;
  padding: 20px;
}

.scoring-container {
  max-width: 800px;
  margin: 0 auto;
}

.scoring-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  margin-bottom: 24px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  animation: slideDown 0.5s ease-out;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: 15px;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: var(--radius-md);
  transition: all 0.3s;
}

.back-btn svg {
  width: 18px;
  height: 18px;
}

.back-btn:hover {
  color: var(--primary-color);
  background: var(--primary-light);
}

.scoring-header h1 {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
}

.judge-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--primary-gradient);
  color: #fff;
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
}

.judge-tag svg {
  width: 14px;
  height: 14px;
}

.scoring-content {
  animation: slideUp 0.5s ease-out;
}

.score-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: white;
  padding: 14px 20px;
  border-radius: var(--radius-md);
  margin-bottom: 20px;
  color: var(--primary-color);
  font-size: 14px;
  font-weight: 500;
  border: 1px solid rgba(24, 144, 255, 0.2);
}

.score-hint svg {
  width: 18px;
  height: 18px;
}

.scoring-table-wrap {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: var(--radius-lg);
  padding: 8px;
  box-shadow: var(--shadow-md);
  overflow: hidden;
}

.scoring-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}

.scoring-table th {
  background: #fafafa;
  padding: 16px;
  text-align: left;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.scoring-table th.col-name {
  text-align: center;
}

.scoring-table td {
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.scoring-table tr:last-child td {
  border-bottom: none;
}

.participant-row {
  transition: background 0.3s;
}

.participant-row:hover {
  background: rgba(24, 144, 255, 0.02);
}

.col-order {
  width: 60px;
  text-align: center;
}

.order-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: var(--primary-light);
  color: var(--primary-color);
  border-radius: 50%;
  font-weight: 600;
  font-size: 16px;
}

.col-score {
  width: 180px;
}

.col-name {
  text-align: center;
}

.college-badge {
  display: inline-block;
  padding: 4px 12px;
  background: linear-gradient(
    135deg,
    rgba(24, 144, 255, 0.1) 0%,
    rgba(102, 126, 234, 0.1) 100%
  );
  color: var(--primary-color);
  border-radius: 12px;
  font-size: 14px;
  font-weight: 500;
  border: 1px solid rgba(24, 144, 255, 0.2);
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.college-empty {
  color: var(--text-muted);
  font-size: 14px;
}

.participant-info {
  display: flex;
  align-items: center;
  gap: 14px;
}

.participant-info.text-center {
  justify-content: center;
  text-align: center;
}

.photo-wrapper {
  flex-shrink: 0;
}

.participant-photo {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #f0f0f0;
  box-shadow: var(--shadow-sm);
}

.photo-placeholder {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
}

.photo-placeholder svg {
  width: 24px;
  height: 24px;
}

.participant-details {
  flex: 1;
  min-width: 0;
}

.participant-name {
  font-weight: 600;
  font-size: 17px;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.participant-college {
  margin-top: 4px;
}

.participant-desc {
  font-size: 13px;
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.score-input-wrapper {
  display: flex;
  align-items: center;
  gap: 6px;
}

.score-input {
  width: 80px;
  padding: 10px 12px;
  border: 2px solid #e8e8e8;
  border-radius: var(--radius-md);
  font-size: 18px;
  font-weight: 600;
  text-align: center;
  outline: none;
  transition: all 0.3s;
  appearance: textfield;
  -moz-appearance: textfield;
}

.score-input::-webkit-inner-spin-button,
.score-input::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.score-input:hover {
  border-color: #d9d9d9;
}

.score-input:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px var(--primary-light);
}

.score-unit {
  font-size: 16px;
  color: var(--text-muted);
}

.error-msg {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--error-color);
  text-align: center;
  padding: 14px 20px;
  margin-top: 16px;
  background: #fff2f0;
  border: 1px solid #ffccc7;
  border-radius: var(--radius-md);
  font-size: 14px;
}

.error-msg svg {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.submit-area {
  text-align: center;
  padding: 32px 0;
}

.btn-submit {
  min-width: 200px;
  padding: 14px 32px;
  font-size: 16px;
  font-weight: 600;
  border-radius: var(--radius-md);
  border: none;
  cursor: pointer;
  transition: all 0.3s;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.btn-submit.btn-primary {
  background: var(--primary-gradient);
  color: #fff;
  box-shadow: 0 4px 14px rgba(24, 144, 255, 0.4);
}

.btn-submit.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(24, 144, 255, 0.5);
}

.btn-submit.btn-disabled {
  background: #f5f5f5;
  color: var(--text-muted);
  cursor: not-allowed;
}

.btn-submit svg {
  width: 20px;
  height: 20px;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.submit-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: var(--text-muted);
  font-size: 13px;
  margin-top: 12px;
}

.submit-hint svg {
  width: 14px;
  height: 14px;
}

/* 已提交提示 - 查看模式 */
.submitted-content {
  animation: slideUp 0.5s ease-out;
}

.submitted-header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: var(--radius-lg);
  padding: 32px;
  text-align: center;
  box-shadow: var(--shadow-md);
  margin-bottom: 24px;
}

.submitted-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);
  color: #fff;
  padding: 10px 20px;
  border-radius: 100px;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 16px;
  box-shadow: 0 4px 12px rgba(82, 196, 26, 0.3);
}

.submitted-badge svg {
  width: 18px;
  height: 18px;
}

.submitted-header h3 {
  font-size: 22px;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.submitted-desc {
  color: var(--text-secondary);
  font-size: 14px;
}

.submitted-table-wrap {
  margin-bottom: 24px;
}

.score-display {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 10px 16px;
  background: linear-gradient(135deg, #f6ffed 0%, #e6f7d9 100%);
  border-radius: var(--radius-md);
  border: 2px solid #b7eb8f;
}

.score-value {
  font-size: 18px;
  font-weight: 700;
  color: #52c41a;
  min-width: 40px;
  text-align: center;
}

.score-display .score-unit {
  font-size: 13px;
  color: #73d13d;
  font-weight: 500;
}

.submitted-actions {
  display: flex;
  justify-content: center;
  padding: 16px 0;
}

.submitted-actions .btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  border: 1px solid #d9d9d9;
  background: #fff;
  color: var(--text-primary);
}

.submitted-actions .btn:hover {
  border-color: var(--primary-color);
  color: var(--primary-color);
  background: rgba(24, 144, 255, 0.02);
}

.submitted-actions .btn svg {
  width: 18px;
  height: 18px;
}

/* 成功提示 */
.success-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  animation: fadeIn 0.3s ease-out;
}

.success-card {
  background: #fff;
  border-radius: var(--radius-xl);
  padding: 48px;
  text-align: center;
  box-shadow: var(--shadow-lg);
  animation: scaleIn 0.4s ease-out;
  min-width: 280px;
}

.success-icon {
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
  animation: pulse 1s ease-in-out infinite;
}

.success-icon svg {
  width: 40px;
  height: 40px;
}

.success-card h2 {
  color: var(--success-color);
  margin-bottom: 8px;
  font-size: 22px;
}

.success-card p {
  color: var(--text-secondary);
  margin-bottom: 20px;
}

.success-card .progress-bar {
  height: 4px;
  background: #f0f0f0;
  border-radius: 2px;
  overflow: hidden;
}

.success-card .progress-fill {
  height: 100%;
  background: var(--success-color);
  border-radius: 2px;
  animation: progress 1.5s ease-out forwards;
}

@keyframes progress {
  from {
    width: 0;
  }
  to {
    width: 100%;
  }
}

/* 过渡动画 */
.fade-scale-enter-active,
.fade-scale-leave-active {
  transition: all 0.3s ease;
}

.fade-scale-enter-from,
.fade-scale-leave-to {
  opacity: 0;
  transform: scale(0.9);
}

.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

@media (max-width: 640px) {
  .scoring-header {
    flex-wrap: wrap;
    gap: 12px;
    padding: 16px;
  }

  .scoring-header h1 {
    order: -1;
    width: 100%;
    text-align: center;
  }

  .scoring-table th,
  .scoring-table td {
    padding: 12px;
  }

  .participant-photo,
  .photo-placeholder {
    width: 40px;
    height: 40px;
  }

  .score-input {
    width: 70px;
    padding: 8px;
  }

  .submitted-notice {
    padding: 32px 24px;
  }
}
</style>
