<script setup lang="ts">
// @ts-nocheck
import { reactive, ref, watch, onMounted, computed } from "vue";
import { showAlert } from "@/utils/dialog";

const props = defineProps<{ ctx: any }>();
const {
  activeTab,
  API,
  backgroundPreview,
  clearBackground,
  configForm,
  error,
  loadingConfig,
  onBackgroundChange,
  saveConfig,
  saveMessage,
  savingConfig,
  success,
  store,
  updateCategoryVoteSelectCount,
  scoresData,
} = props.ctx;

// 保存确认对话框状态
const saveConfirmModalVisible = ref(false);
const saveConfirmPassword = ref("");
const saveConfirmError = ref("");

// 快捷设置弹窗状态
const quickSettingModalVisible = ref(false);
const quickSettingMode = ref<"score" | "vote">("score");
const quickSettingScoreValueType = ref<
  "integer" | "decimal" | "integer_decimal"
>("integer");
const quickSettingScoreMin = ref<number>(1);
const quickSettingScoreMax = ref<number>(100);
const quickSettingAllowDuplicateScores = ref<boolean>(true);
const quickSettingExcludeExtremeScores = ref<boolean>(false);
const quickSettingVoteSelectCount = ref<number>(3);

// 本地状态存储每个类别的打分模式设置
const categoryModeSettings = reactive<
  Record<
    number,
    {
      scoring_mode: "score" | "vote";
      vote_select_count: number | null;
      // 分数模式相关设置
      score_value_type: "integer" | "decimal" | "integer_decimal" | null;
      score_min: number | null;
      score_max: number | null;
      allow_duplicate_scores: boolean | null;
      exclude_extreme_scores: boolean | null;
    }
  >
>({});

// 本地状态存储全局打分模式设置（用于编辑，避免直接修改 configForm）
const localScoringMode = ref<"score" | "vote">(configForm.scoring_mode);
const localScoreValueType = ref<"integer" | "decimal" | "integer_decimal">(
  configForm.score_value_type,
);
const localScoreMin = ref<number>(configForm.score_min);
const localScoreMax = ref<number>(configForm.score_max);
const localAllowDuplicateScores = ref<boolean>(
  configForm.allow_duplicate_scores,
);
const localExcludeExtremeScores = ref<boolean>(
  configForm.exclude_extreme_scores,
);
const localVoteSelectCount = ref<number>(configForm.vote_select_count);

// 从 configForm 同步本地状态
function syncLocalFromConfig() {
  localScoringMode.value = configForm.scoring_mode;
  localScoreValueType.value = configForm.score_value_type;
  localScoreMin.value = configForm.score_min;
  localScoreMax.value = configForm.score_max;
  localAllowDuplicateScores.value = configForm.allow_duplicate_scores;
  localExcludeExtremeScores.value = configForm.exclude_extreme_scores;
  localVoteSelectCount.value = configForm.vote_select_count;
}

// 将本地状态同步到 configForm（保存前调用）
function syncConfigFromLocal() {
  configForm.scoring_mode = localScoringMode.value;
  configForm.score_value_type = localScoreValueType.value;
  configForm.score_min = localScoreMin.value;
  configForm.score_max = localScoreMax.value;
  configForm.allow_duplicate_scores = localAllowDuplicateScores.value;
  configForm.exclude_extreme_scores = localExcludeExtremeScores.value;
  configForm.vote_select_count = localVoteSelectCount.value;
}

// 打开保存确认对话框
function openSaveConfirmModal() {
  if (localScoreMin.value >= localScoreMax.value) {
    showAlert("最高分必须大于最低分");
    return;
  }
  saveConfirmPassword.value = "";
  saveConfirmError.value = "";
  saveConfirmModalVisible.value = true;
}

// 关闭保存确认对话框
function closeSaveConfirmModal() {
  saveConfirmModalVisible.value = false;
  saveConfirmPassword.value = "";
  saveConfirmError.value = "";
}

// 确认保存
async function confirmSaveConfig() {
  if (saveConfirmPassword.value.trim() !== "jndx") {
    saveConfirmError.value = "确认码错误，请输入 jndx";
    return;
  }

  closeSaveConfirmModal();

  // 先将本地状态同步到 configForm
  syncConfigFromLocal();
  // 保存全局配置
  await saveConfig();
  // 保存所有类别的单独设置
  await saveAllCategorySettings();
}

// 处理保存配置（打开确认对话框）
async function handleSaveConfig() {
  openSaveConfirmModal();
}

// 获取分数模式的规则描述
function getScoreRuleDescription(settings: any) {
  const typeText =
    settings.score_value_type === "decimal"
      ? "仅小数"
      : settings.score_value_type === "integer_decimal"
        ? "整数和小数"
        : "仅整数";
  return `分数模式 | ${typeText} | ${settings.score_min}-${settings.score_max}分 | ${settings.allow_duplicate_scores ? "允许重复" : "不重复"} | ${settings.exclude_extreme_scores ? "去极值" : "保留全部分数"}`;
}

// 获取投票模式的规则描述
function getVoteRuleDescription(settings: any) {
  return `投票模式 | 选择${settings.vote_select_count}人`;
}

// 按规则分组的类别
const groupedCategories = computed(() => {
  const groups: Record<string, any[]> = {};

  store.categories.forEach((category: any) => {
    const settings = categoryModeSettings[category.id];
    if (!settings) return;

    const ruleKey =
      settings.scoring_mode === "vote"
        ? `vote_${settings.vote_select_count}`
        : `score_${settings.score_value_type}_${settings.score_min}_${settings.score_max}_${settings.allow_duplicate_scores}_${settings.exclude_extreme_scores}`;

    if (!groups[ruleKey]) {
      groups[ruleKey] = [];
    }
    groups[ruleKey].push({ category, settings });
  });

  return groups;
});

// 是否有多种不同的打分规则
const hasMultipleRules = computed(() => {
  return Object.keys(groupedCategories.value).length > 1;
});

// 监听 configForm 变化，同步到本地状态
watch(
  () => ({
    scoring_mode: configForm.scoring_mode,
    score_value_type: configForm.score_value_type,
    score_min: configForm.score_min,
    score_max: configForm.score_max,
    allow_duplicate_scores: configForm.allow_duplicate_scores,
    exclude_extreme_scores: configForm.exclude_extreme_scores,
    vote_select_count: configForm.vote_select_count,
  }),
  () => {
    syncLocalFromConfig();
  },
  { deep: true },
);

// 组件挂载时同步一次
onMounted(() => {
  syncLocalFromConfig();
});

// 初始化类别模式设置
function initCategoryModeSettings() {
  store.categories.forEach((category: any) => {
    if (!categoryModeSettings[category.id]) {
      // 如果类别没有设置过，使用全局设置作为默认值
      const effectiveMode =
        category.scoring_mode === "vote" || category.scoring_mode === "score"
          ? category.scoring_mode
          : localScoringMode.value;
      categoryModeSettings[category.id] = {
        scoring_mode: effectiveMode,
        vote_select_count:
          category.vote_select_count ?? localVoteSelectCount.value,
        // 分数模式设置 - 如果没有则使用全局设置
        score_value_type:
          category.score_value_type ?? localScoreValueType.value,
        score_min: category.score_min ?? localScoreMin.value,
        score_max: category.score_max ?? localScoreMax.value,
        allow_duplicate_scores:
          category.allow_duplicate_scores ?? localAllowDuplicateScores.value,
        exclude_extreme_scores:
          category.exclude_extreme_scores ?? localExcludeExtremeScores.value,
      };
    }
  });
}

// 监听类别变化，初始化设置
watch(() => store.categories, initCategoryModeSettings, {
  immediate: true,
  deep: true,
});

// 保存单个类别的设置
async function saveCategorySettings(categoryId: number) {
  const settings = categoryModeSettings[categoryId];
  if (!settings) return;

  try {
    const body: any = {
      scoring_mode: settings.scoring_mode,
    };

    // 根据模式添加对应的设置
    if (settings.scoring_mode === "vote") {
      body.vote_select_count = settings.vote_select_count;
      // 清空分数模式设置
      body.score_value_type = null;
      body.score_min = null;
      body.score_max = null;
      body.allow_duplicate_scores = null;
      body.exclude_extreme_scores = null;
    } else if (settings.scoring_mode === "score") {
      body.vote_select_count = null;
      // 分数模式设置
      body.score_value_type = settings.score_value_type;
      body.score_min = settings.score_min;
      body.score_max = settings.score_max;
      body.allow_duplicate_scores = settings.allow_duplicate_scores;
      body.exclude_extreme_scores = settings.exclude_extreme_scores;
    }

    const res = await fetch(
      `${API.adminCategoryUpdate(categoryId)}?password=${encodeURIComponent(store.adminPassword)}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      },
    );

    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.error || "更新失败");
    }
  } catch (err: any) {
    throw new Error(err.message || "更新类别打分模式失败");
  }
}

// 保存所有类别的单独设置
async function saveAllCategorySettings() {
  const errors: string[] = [];

  for (const categoryIdStr in categoryModeSettings) {
    const categoryId = parseInt(categoryIdStr);
    try {
      await saveCategorySettings(categoryId);
    } catch (err: any) {
      errors.push(`类别 ${categoryId}: ${err.message}`);
    }
  }

  // 刷新类别数据
  await store.fetchCategories();

  // 如果有错误，显示错误信息
  if (errors.length > 0) {
    alert(errors.join("\n"));
  }
}

// 从本地状态获取默认值（用于初始化类别设置）
function getDefaultScoreSettings() {
  return {
    score_value_type: localScoreValueType.value || "integer",
    score_min: localScoreMin.value ?? 1,
    score_max: localScoreMax.value ?? 100,
    allow_duplicate_scores: localAllowDuplicateScores.value ?? true,
    exclude_extreme_scores: localExcludeExtremeScores.value ?? false,
  };
}

// 打开快捷设置弹窗
function openQuickSettingModal() {
  // 使用当前本地状态作为默认值
  quickSettingMode.value = localScoringMode.value;
  quickSettingScoreValueType.value = localScoreValueType.value;
  quickSettingScoreMin.value = localScoreMin.value;
  quickSettingScoreMax.value = localScoreMax.value;
  quickSettingAllowDuplicateScores.value = localAllowDuplicateScores.value;
  quickSettingExcludeExtremeScores.value = localExcludeExtremeScores.value;
  quickSettingVoteSelectCount.value = localVoteSelectCount.value;
  quickSettingModalVisible.value = true;
}

// 关闭快捷设置弹窗
function closeQuickSettingModal() {
  quickSettingModalVisible.value = false;
}

// 应用快捷设置并同步到所有类别
function applyQuickSettingAndSync() {
  if (quickSettingScoreMin.value >= quickSettingScoreMax.value) {
    showAlert("最高分必须大于最低分");
    return;
  }

  // 更新本地状态
  localScoringMode.value = quickSettingMode.value;
  localScoreValueType.value = quickSettingScoreValueType.value;
  localScoreMin.value = quickSettingScoreMin.value;
  localScoreMax.value = quickSettingScoreMax.value;
  localAllowDuplicateScores.value = quickSettingAllowDuplicateScores.value;
  localExcludeExtremeScores.value = quickSettingExcludeExtremeScores.value;
  localVoteSelectCount.value = quickSettingVoteSelectCount.value;

  // 同步到所有类别
  for (const category of store.categories) {
    // 如果该类别已有评委打分，则跳过
    if (hasCategoryScores(category.id)) {
      continue;
    }

    // 更新类别的本地设置
    const settings = categoryModeSettings[category.id];
    if (settings) {
      settings.scoring_mode = quickSettingMode.value;
      if (quickSettingMode.value === "vote") {
        settings.vote_select_count = quickSettingVoteSelectCount.value;
        settings.score_value_type = null;
        settings.score_min = null;
        settings.score_max = null;
        settings.allow_duplicate_scores = null;
        settings.exclude_extreme_scores = null;
      } else {
        settings.vote_select_count = null;
        settings.score_value_type = quickSettingScoreValueType.value;
        settings.score_min = quickSettingScoreMin.value;
        settings.score_max = quickSettingScoreMax.value;
        settings.allow_duplicate_scores =
          quickSettingAllowDuplicateScores.value;
        settings.exclude_extreme_scores =
          quickSettingExcludeExtremeScores.value;
      }
    }
  }

  closeQuickSettingModal();
}

// 当切换到分数模式时，使用全局默认值
function initScoreSettings(categoryId: number) {
  const settings = categoryModeSettings[categoryId];
  if (!settings) return;

  const defaults = getDefaultScoreSettings();
  if (settings.score_value_type === null) {
    settings.score_value_type = defaults.score_value_type;
  }
  if (settings.score_min === null) {
    settings.score_min = defaults.score_min;
  }
  if (settings.score_max === null) {
    settings.score_max = defaults.score_max;
  }
  if (settings.allow_duplicate_scores === null) {
    settings.allow_duplicate_scores = defaults.allow_duplicate_scores;
  }
  if (settings.exclude_extreme_scores === null) {
    settings.exclude_extreme_scores = defaults.exclude_extreme_scores;
  }
}

// 当切换到投票模式时，初始化选择人数
function initVoteSettings(categoryId: number) {
  const settings = categoryModeSettings[categoryId];
  if (!settings) return;

  if (
    settings.vote_select_count === null ||
    settings.vote_select_count === undefined
  ) {
    settings.vote_select_count = localVoteSelectCount.value || 1;
  }
}

// 获取类别实际使用的打分模式（使用本地状态，反映编辑中的值）
function getEffectiveScoringMode(category: any): "score" | "vote" {
  const settings = categoryModeSettings[category.id];
  if (settings) {
    return settings.scoring_mode;
  }
  return localScoringMode.value;
}

// 判断某个类别是否有评委打分（分数模式）或投票（投票模式）
function hasCategoryScores(categoryId: number): boolean {
  if (!scoresData?.value) return false;
  // 检查分数模式
  const categoryScores = scoresData.value.scores?.[categoryId];
  if (categoryScores) {
    for (const judgeId in categoryScores) {
      const judgeScores = categoryScores[judgeId];
      if (judgeScores && Object.keys(judgeScores).length > 0) {
        return true;
      }
    }
  }
  // 检查投票模式
  const categoryVotes = scoresData.value.votes?.[categoryId];
  if (categoryVotes) {
    for (const judgeId in categoryVotes) {
      const judgeVotes = categoryVotes[judgeId];
      if (judgeVotes && judgeVotes.length > 0) {
        return true;
      }
    }
  }
  return false;
}

// 判断是否有任何类别已有评委打分
function hasAnyCategoryScores(): boolean {
  if (!store.categories || store.categories.length === 0) return false;
  return store.categories.some((category: any) =>
    hasCategoryScores(category.id),
  );
}
</script>

<template>
  <div class="tab-content">
    <div class="section" v-if="loadingConfig">
      <div class="loading-state">
        <div class="spinner"></div>
        <p>加载配置中...</p>
      </div>
    </div>
    <div class="section" v-else>
      <h3>
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <circle cx="12" cy="12" r="3" />
          <path
            d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"
          />
        </svg>
        基础设置
      </h3>
      <div class="form-grid">
        <label class="form-field">
          <span>活动标题</span>
          <input
            v-model="configForm.site_name"
            class="input"
            placeholder="请输入活动标题"
          />
        </label>
        <label class="form-field">
          <span>前端基础地址</span>
          <input
            v-model="configForm.base_url"
            class="input"
            placeholder="https://example.com"
          />
        </label>
        <label class="form-field">
          <span>主题色</span>
          <div class="color-input-wrapper">
            <input
              v-model="configForm.primary_color"
              class="input"
              placeholder="#1890ff"
            />
            <input
              type="color"
              v-model="configForm.primary_color"
              class="color-picker"
            />
          </div>
        </label>
        <label class="form-field">
          <span>管理员密码</span>
          <input
            v-model="configForm.admin_password"
            class="input"
            type="text"
          />
        </label>
      </div>
      <div class="switch-list inline-switch-list" style="margin-top: 16px">
        <label class="switch-item">
          <div class="switch">
            <input v-model="configForm.allow_scoring" type="checkbox" />
            <span class="slider"></span>
          </div>
          <span class="switch-label">允许评委提交评分</span>
        </label>
      </div>

      <h3 style="margin-top: 24px">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <path
            d="M9 17v-2a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2v-2"
          />
          <path
            d="M17 17v-2a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2v-2"
          />
        </svg>
        模式设置
      </h3>

      <!-- 快捷设置按钮 -->
      <div class="quick-setting-section">
        <button
          class="btn btn-primary quick-setting-btn"
          @click="openQuickSettingModal"
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            style="
              width: 18px;
              height: 18px;
              vertical-align: middle;
              margin-right: 8px;
            "
          >
            <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
          </svg>
          快捷设置
        </button>
        <div
          class="form-tip"
          style="margin-top: 8px; font-size: 12px; color: #666"
        >
          快速设置所有类别的打分模式（已有评委打分的类别不会被修改）
        </div>
      </div>

      <!-- 每个类别的单独设置 -->
      <div class="category-mode-settings" style="margin-top: 24px">
        <div class="form-tip" style="margin-bottom: 12px">
          <strong>类别单独设置</strong>：为每个类别设置独立的打分模式
        </div>
        <div v-if="store.categories.length === 0" class="empty-state">
          暂无类别，请先添加类别。
        </div>
        <div v-else class="category-mode-list">
          <div
            class="category-mode-row"
            v-for="category in store.categories"
            :key="category.id"
          >
            <div class="category-mode-info">
              <span class="category-mode-name">{{ category.name }}</span>
              <span
                class="category-mode-badge"
                :class="getEffectiveScoringMode(category)"
              >
                {{
                  getEffectiveScoringMode(category) === "vote" ? "投票" : "打分"
                }}
              </span>
            </div>
            <div class="category-mode-fields">
              <label class="form-field">
                <span>打分模式</span>
                <div
                  v-if="hasCategoryScores(category.id)"
                  class="form-tip warning-tip"
                  style="margin-bottom: 4px; color: #ff4d4f; font-size: 12px"
                >
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    style="
                      width: 12px;
                      height: 12px;
                      vertical-align: middle;
                      margin-right: 2px;
                    "
                  >
                    <path
                      d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"
                    />
                    <line x1="12" y1="9" x2="12" y2="13" />
                    <line x1="12" y1="17" x2="12.01" y2="17" />
                  </svg>
                  已有评委打分，模式已锁定
                </div>
                <select
                  v-model="categoryModeSettings[category.id].scoring_mode"
                  class="input"
                  :disabled="hasCategoryScores(category.id)"
                  @change="
                    categoryModeSettings[category.id].scoring_mode === 'score'
                      ? initScoreSettings(category.id)
                      : categoryModeSettings[category.id].scoring_mode ===
                          'vote'
                        ? initVoteSettings(category.id)
                        : null
                  "
                >
                  <option value="score">分数模式</option>
                  <option value="vote">投票模式</option>
                </select>
              </label>
              <!-- 投票模式设置 -->
              <template
                v-if="categoryModeSettings[category.id].scoring_mode === 'vote'"
              >
                <label class="form-field">
                  <span>选择人数</span>
                  <input
                    v-model.number="
                      categoryModeSettings[category.id].vote_select_count
                    "
                    type="number"
                    min="1"
                    class="input"
                    placeholder="选择人数"
                  />
                </label>
              </template>
              <!-- 分数模式设置 -->
              <template
                v-if="
                  categoryModeSettings[category.id].scoring_mode === 'score'
                "
              >
                <label class="form-field">
                  <span>打分类型</span>
                  <select
                    v-model="categoryModeSettings[category.id].score_value_type"
                    class="input"
                  >
                    <option value="integer">整数</option>
                    <option value="decimal">小数</option>
                    <option value="integer_decimal">整数和小数</option>
                  </select>
                </label>
                <label class="form-field">
                  <span>最低分</span>
                  <input
                    v-model.number="categoryModeSettings[category.id].score_min"
                    type="number"
                    class="input"
                    :step="
                      categoryModeSettings[category.id].score_value_type ===
                      'integer'
                        ? '1'
                        : '0.01'
                    "
                  />
                </label>
                <label class="form-field">
                  <span>最高分</span>
                  <input
                    v-model.number="categoryModeSettings[category.id].score_max"
                    type="number"
                    class="input"
                    :step="
                      categoryModeSettings[category.id].score_value_type ===
                      'integer'
                        ? '1'
                        : '0.01'
                    "
                  />
                </label>
              </template>
            </div>
            <!-- 分数模式额外选项 -->
            <div
              v-if="categoryModeSettings[category.id].scoring_mode === 'score'"
              class="category-mode-extra-options"
            >
              <label class="switch-item">
                <div class="switch">
                  <input
                    v-model="
                      categoryModeSettings[category.id].allow_duplicate_scores
                    "
                    type="checkbox"
                  />
                  <span class="slider"></span>
                </div>
                <span class="switch-label">允许重复分数</span>
              </label>
              <label class="switch-item">
                <div class="switch">
                  <input
                    v-model="
                      categoryModeSettings[category.id].exclude_extreme_scores
                    "
                    type="checkbox"
                  />
                  <span class="slider"></span>
                </div>
                <span class="switch-label">去掉最高分和最低分</span>
              </label>
            </div>
          </div>
        </div>
      </div>

      <h3 style="margin-top: 24px">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
          <circle cx="8.5" cy="8.5" r="1.5" />
          <polyline points="21 15 16 10 5 21" />
        </svg>
        背景设置
      </h3>
      <div class="upload-panel">
        <label class="file-input-wrapper">
          <input
            type="file"
            class="file-input"
            accept="image/*"
            @change="onBackgroundChange"
          />
          <span class="file-input-text">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
            选择背景图片
          </span>
        </label>
        <button class="btn btn-outline" @click="clearBackground">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <polyline points="3 6 5 6 21 6" />
            <path
              d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"
            />
          </svg>
          清除背景
        </button>
      </div>
      <div
        v-if="backgroundPreview"
        class="preview-card background-preview-card"
      >
        <div class="background-preview-frame">
          <img
            :src="backgroundPreview"
            alt="背景预览"
            class="background-preview"
          />
        </div>
      </div>

      <div
        v-if="saveMessage"
        class="message-box"
        :class="{
          success:
            saveMessage.includes('成功') || saveMessage.includes('已保存'),
          error: saveMessage.includes('失败') || saveMessage.includes('错误'),
        }"
      >
        <svg
          v-if="saveMessage.includes('成功') || saveMessage.includes('已保存')"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <polyline points="20 6 9 17 4 12" />
        </svg>
        <svg
          v-else
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
        {{ saveMessage }}
      </div>
      <div class="button-row">
        <button
          class="btn btn-primary"
          :disabled="savingConfig"
          @click="handleSaveConfig"
        >
          <span v-if="savingConfig" class="spinner"></span>
          <svg
            v-else
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path
              d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"
            />
            <polyline points="17 21 17 13 7 13 7 21" />
            <polyline points="7 3 7 8 15 8" />
          </svg>
          {{ savingConfig ? "保存中..." : "保存配置" }}
        </button>
      </div>
    </div>
  </div>

  <!-- 保存确认对话框 -->
  <div
    v-if="saveConfirmModalVisible"
    class="modal-overlay save-confirm-modal"
    @click.self="closeSaveConfirmModal"
  >
    <div class="modal-card save-confirm-card">
      <button class="modal-close" @click="closeSaveConfirmModal">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </button>
      <h3 class="modal-title">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          style="
            width: 24px;
            height: 24px;
            vertical-align: middle;
            margin-right: 8px;
          "
        >
          <path
            d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"
          />
          <line x1="12" y1="9" x2="12" y2="13" />
          <line x1="12" y1="17" x2="12.01" y2="17" />
        </svg>
        确认保存配置
      </h3>

      <div class="save-confirm-content">
        <!-- 类别规则分组 -->
        <div v-if="store.categories.length > 0" class="rule-section">
          <div class="rule-section-title">
            各类别打分规则
            <span v-if="hasMultipleRules" class="multi-rule-tag">多种规则</span>
          </div>

          <div class="category-rules-list">
            <div
              v-for="(group, ruleKey) in groupedCategories"
              :key="ruleKey"
              class="rule-group"
            >
              <div class="rule-group-header">
                <span
                  class="rule-group-badge"
                  :class="group[0].settings.scoring_mode"
                >
                  {{
                    group[0].settings.scoring_mode === "vote" ? "投票" : "分数"
                  }}
                </span>
                <span class="rule-group-desc">
                  <template v-if="group[0].settings.scoring_mode === 'score'">
                    {{
                      group[0].settings.score_value_type === "integer"
                        ? "整数"
                        : group[0].settings.score_value_type === "decimal"
                          ? "小数"
                          : "整数/小数"
                    }}
                    | {{ group[0].settings.score_min }}-{{
                      group[0].settings.score_max
                    }}分 |
                    {{
                      group[0].settings.allow_duplicate_scores
                        ? "可重复"
                        : "不可重复"
                    }}
                    |
                    {{
                      group[0].settings.exclude_extreme_scores
                        ? "去极值"
                        : "全保留"
                    }}
                  </template>
                  <template v-else>
                    选{{ group[0].settings.vote_select_count }}人
                  </template>
                </span>
                <span class="rule-group-count">{{ group.length }}个类别</span>
              </div>
              <div class="rule-group-categories">
                <span
                  v-for="item in group"
                  :key="item.category.id"
                  class="category-tag"
                >
                  {{ item.category.name }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="rule-section empty">暂无类别</div>

        <!-- 确认码输入 -->
        <div class="confirm-input-section">
          <label class="confirm-label">
            请输入确认码 <strong>jndx</strong> 以保存配置：
          </label>
          <input
            v-model="saveConfirmPassword"
            type="text"
            class="confirm-input"
            placeholder="请输入 jndx"
            @keyup.enter="confirmSaveConfig"
          />
          <div v-if="saveConfirmError" class="confirm-error">
            {{ saveConfirmError }}
          </div>
        </div>
      </div>

      <div class="button-row compact">
        <button class="btn btn-outline" @click="closeSaveConfirmModal">
          取消
        </button>
        <button class="btn btn-primary" @click="confirmSaveConfig">
          确认保存
        </button>
      </div>
    </div>
  </div>

  <!-- 快捷设置弹窗 -->
  <div
    v-if="quickSettingModalVisible"
    class="modal-overlay quick-setting-modal"
    @click.self="closeQuickSettingModal"
  >
    <div class="modal-card quick-setting-card">
      <button class="modal-close" @click="closeQuickSettingModal">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </button>
      <h3 class="modal-title">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          style="
            width: 24px;
            height: 24px;
            vertical-align: middle;
            margin-right: 8px;
          "
        >
          <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
        </svg>
        快捷设置
      </h3>

      <div class="quick-setting-content">
        <div
          v-if="hasAnyCategoryScores()"
          class="form-tip warning-tip"
          style="
            margin-bottom: 16px;
            color: #ff4d4f;
            padding: 12px;
            background: #fff2f0;
            border-radius: 8px;
          "
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            style="
              width: 16px;
              height: 16px;
              vertical-align: middle;
              margin-right: 4px;
            "
          >
            <path
              d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"
            />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
          已有类别收到评委打分，快捷设置仅对未打分的类别生效
        </div>

        <div class="form-grid">
          <label class="form-field full-width">
            <span>打分模式</span>
            <select v-model="quickSettingMode" class="input">
              <option value="score">分数模式</option>
              <option value="vote">投票模式</option>
            </select>
          </label>
        </div>

        <div v-if="quickSettingMode === 'score'" class="quick-setting-options">
          <div class="form-grid">
            <label class="form-field">
              <span>合法打分类型</span>
              <select v-model="quickSettingScoreValueType" class="input">
                <option value="integer">整数</option>
                <option value="decimal">小数</option>
                <option value="integer_decimal">整数和小数</option>
              </select>
            </label>
            <label class="form-field">
              <span>最低分</span>
              <input
                v-model.number="quickSettingScoreMin"
                class="input"
                type="number"
                :step="quickSettingScoreValueType === 'integer' ? '1' : '0.01'"
              />
            </label>
            <label class="form-field">
              <span>最高分</span>
              <input
                v-model.number="quickSettingScoreMax"
                class="input"
                type="number"
                :step="quickSettingScoreValueType === 'integer' ? '1' : '0.01'"
              />
            </label>
          </div>

          <div class="switch-list inline-switch-list" style="margin-top: 16px">
            <label class="switch-item">
              <div class="switch">
                <input
                  v-model="quickSettingAllowDuplicateScores"
                  type="checkbox"
                />
                <span class="slider"></span>
              </div>
              <span class="switch-label">打分是否允许重复</span>
            </label>
            <label class="switch-item">
              <div class="switch">
                <input
                  v-model="quickSettingExcludeExtremeScores"
                  type="checkbox"
                />
                <span class="slider"></span>
              </div>
              <span class="switch-label">统计时去掉最高分和最低分</span>
            </label>
          </div>
        </div>

        <div v-else class="quick-setting-options">
          <div class="form-grid">
            <label class="form-field">
              <span>选择人数</span>
              <input
                v-model.number="quickSettingVoteSelectCount"
                type="number"
                min="1"
                class="input"
                placeholder="评委要选多少人"
              />
            </label>
          </div>
        </div>
      </div>

      <div class="button-row compact">
        <button class="btn btn-outline" @click="closeQuickSettingModal">
          取消
        </button>
        <button class="btn btn-primary" @click="applyQuickSettingAndSync">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            style="
              width: 16px;
              height: 16px;
              vertical-align: middle;
              margin-right: 6px;
            "
          >
            <path
              d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.3"
            />
          </svg>
          同步
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.global-mode-setting {
  padding: 16px;
  background: #f9f9f9;
  border-radius: 8px;
  border: 1px solid #e8e8e8;
}

.category-mode-settings {
  margin-top: 24px;
}

.category-mode-settings .empty-state {
  padding: 24px;
  text-align: center;
  color: #999;
  background: #f9f9f9;
  border-radius: 8px;
}

.category-mode-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.category-mode-row {
  display: flex;
  align-items: center;
  padding: 16px;
  background: #f5f5f5;
  border-radius: 8px;
  border: 1px solid #e8e8e8;
}

.category-mode-info {
  flex: 0 0 200px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.category-mode-name {
  font-weight: 500;
  color: #333;
  font-size: 14px;
}

.category-mode-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  width: fit-content;
}

.category-mode-badge.vote {
  background: #e6f7ff;
  color: #1890ff;
}

.category-mode-badge.score {
  background: #f6ffed;
  color: #52c41a;
}

.category-mode-row {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  padding: 16px;
  background: #f5f5f5;
  border-radius: 8px;
  border: 1px solid #e8e8e8;
  gap: 12px;
}

.category-mode-info {
  flex: 0 0 150px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.category-mode-name {
  font-weight: 500;
  color: #333;
  font-size: 14px;
}

.category-mode-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  width: fit-content;
}

.category-mode-badge.vote {
  background: #e6f7ff;
  color: #1890ff;
}

.category-mode-badge.score {
  background: #f6ffed;
  color: #52c41a;
}

.category-mode-fields {
  flex: 1;
  display: flex;
  gap: 12px;
  align-items: flex-end;
  flex-wrap: nowrap;
  min-width: 0;
}

.category-mode-fields .form-field {
  flex: 0 0 auto;
  min-width: 100px;
  max-width: 150px;
  margin: 0;
}

.category-mode-fields .form-field span {
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
  white-space: nowrap;
}

.category-mode-extra-options {
  flex: 0 0 100%;
  margin-top: 8px;
  padding-top: 12px;
  border-top: 1px dashed #ddd;
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}

.category-mode-extra-options .switch-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
}

.category-mode-extra-options .switch-label {
  font-size: 13px;
  color: #666;
  white-space: nowrap;
}

/* 兼容旧样式 */
.category-vote-settings {
  margin-top: 16px;
}

.category-vote-settings .empty-state {
  padding: 24px;
  text-align: center;
  color: #999;
  background: #f9f9f9;
  border-radius: 8px;
}

.category-vote-row {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  margin-bottom: 8px;
  background: #f5f5f5;
  border-radius: 8px;
}

.category-vote-row .category-name {
  flex: 0 0 200px;
  font-weight: 500;
  color: #333;
}

.category-vote-row .category-vote-fields {
  flex: 1;
  display: flex;
  gap: 16px;
}

.category-vote-row .form-field {
  flex: 1;
  max-width: 250px;
}

/* 保存确认对话框样式 */
.save-confirm-modal .modal-card {
  max-width: 640px;
  width: 90vw;
  max-height: 85vh;
  overflow-y: auto;
}

.save-confirm-content {
  padding: 0 24px 20px;
}

.rule-section {
  margin-bottom: 20px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.rule-section.empty {
  text-align: center;
  color: #94a3b8;
  padding: 32px;
}

.rule-section-title {
  font-size: 14px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.multi-rule-tag {
  font-size: 11px;
  padding: 2px 8px;
  background: #fef3c7;
  color: #d97706;
  border-radius: 4px;
  font-weight: 500;
}

.rule-badge {
  display: inline-block;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 12px;
}

.rule-badge.vote {
  background: #e0f2fe;
  color: #0284c7;
}

.rule-badge.score {
  background: #dcfce7;
  color: #16a34a;
}

.rule-detail {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.rule-item {
  font-size: 13px;
  color: #64748b;
  padding: 4px 10px;
  background: white;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
}

.category-rules-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.rule-group {
  background: white;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
}

.rule-group-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #f1f5f9;
  border-bottom: 1px solid #e2e8f0;
}

.rule-group-badge {
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 4px;
  font-weight: 600;
}

.rule-group-badge.vote {
  background: #e0f2fe;
  color: #0284c7;
}

.rule-group-badge.score {
  background: #dcfce7;
  color: #16a34a;
}

.rule-group-desc {
  flex: 1;
  font-size: 13px;
  color: #64748b;
}

.rule-group-count {
  font-size: 12px;
  color: #94a3b8;
  background: white;
  padding: 2px 8px;
  border-radius: 4px;
}

.rule-group-categories {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px 16px;
}

.category-tag {
  font-size: 12px;
  padding: 4px 10px;
  background: #f1f5f9;
  color: #475569;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
}

.confirm-input-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px dashed #cbd5e1;
}

.confirm-label {
  display: block;
  font-size: 14px;
  color: #475569;
  margin-bottom: 10px;
}

.confirm-input {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  font-size: 14px;
  transition: all 0.2s;
}

.confirm-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.confirm-error {
  margin-top: 8px;
  font-size: 13px;
  color: #ef4444;
}

/* 快捷设置区域样式 */
.quick-setting-section {
  margin: 16px 0;
  padding: 20px;
  background: color-mix(in srgb, var(--primary-color) 10%, white);
  border-radius: 12px;
  border: 1px solid color-mix(in srgb, var(--primary-color) 30%, white);
  text-align: center;
}

.quick-setting-btn {
  font-size: 16px;
  padding: 12px 32px;
  background: var(--primary-gradient);
  box-shadow: 0 4px 14px
    color-mix(in srgb, var(--primary-color) 35%, transparent);
}

.quick-setting-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px
    color-mix(in srgb, var(--primary-color) 45%, transparent);
}

/* 快捷设置弹窗样式 */
.quick-setting-modal .modal-card {
  max-width: 520px;
  width: 90vw;
}

.quick-setting-content {
  padding: 0 24px 20px;
}

.quick-setting-options {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px dashed #e2e8f0;
}
</style>
