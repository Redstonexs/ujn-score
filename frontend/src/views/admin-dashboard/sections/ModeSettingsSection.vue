<script setup lang="ts">
// @ts-nocheck
import { ref, watch, onMounted } from "vue";

const props = defineProps<{ ctx: any }>();
const {
  activeTab,
  configForm,
  error,
  loadingConfig,
  saveConfig,
  saveMessage,
  savingConfig,
  success,
  store,
  scoresData,
} = props.ctx;

// 本地状态存储全局打分模式设置（用于编辑，避免直接修改 configForm）
const localScoringMode = ref<"score" | "vote">(configForm.scoring_mode);
const localVoteTotalCount = ref<number>(configForm.vote_total_count);
const localVoteSelectCount = ref<number>(configForm.vote_select_count);

// 从 configForm 同步本地状态
function syncLocalFromConfig() {
  localScoringMode.value = configForm.scoring_mode;
  localVoteTotalCount.value = configForm.vote_total_count;
  localVoteSelectCount.value = configForm.vote_select_count;
}

// 将本地状态同步到 configForm（保存前调用）
function syncConfigFromLocal() {
  configForm.scoring_mode = localScoringMode.value;
  configForm.vote_total_count = localVoteTotalCount.value;
  configForm.vote_select_count = localVoteSelectCount.value;
}

// 监听 configForm 变化，同步到本地状态
watch(
  () => ({
    scoring_mode: configForm.scoring_mode,
    vote_total_count: configForm.vote_total_count,
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

// 处理保存配置
async function handleSaveConfig() {
  // 先将本地状态同步到 configForm
  syncConfigFromLocal();
  // 然后调用父组件的保存函数
  await saveConfig();
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
          <path
            d="M9 17v-2a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2v-2"
          />
          <path
            d="M17 17v-2a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2v-2"
          />
        </svg>
        全局打分模式设置
      </h3>
      <div
        v-if="hasAnyCategoryScores()"
        class="form-tip warning-tip"
        style="margin-bottom: 12px; color: #ff4d4f"
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
        已有类别收到评委打分，全局打分模式已锁定，无法切换
      </div>
      <div class="form-grid">
        <label class="form-field full-width">
          <span>打分模式</span>
          <select
            v-model="localScoringMode"
            class="input"
            :disabled="hasAnyCategoryScores()"
          >
            <option value="score">分数模式</option>
            <option value="vote">投票模式</option>
          </select>
        </label>
        <label class="form-field">
          <span>投票总数</span>
          <input
            v-model.number="localVoteTotalCount"
            type="number"
            min="1"
            class="input"
            placeholder="从多少人中选择"
          />
        </label>
        <label class="form-field">
          <span>选择人数</span>
          <input
            v-model.number="localVoteSelectCount"
            type="number"
            min="1"
            class="input"
            placeholder="选择多少人"
          />
        </label>
      </div>
      <div class="form-tip">
        注意：这些设置将作为所有类别的默认值，但每个类别可以单独设置。
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
</template>
