<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { useScoringStore } from "@/stores/scoring";
import API, { resolveAssetUrl } from "@/config/api";

type TabKey = "overview" | "settings" | "judges" | "scores" | "import";

interface AdminConfig {
  site_name: string;
  primary_color: string;
  score_min: number;
  score_max: number;
  score_value_type: "integer" | "decimal" | "integer_decimal";
  allow_duplicate_scores: boolean;
  allow_scoring: boolean;
  exclude_extreme_scores: boolean;
  background_image: string | null;
  admin_password: string;
  base_url: string;
  admin_url: string;
  participant_sheet_name: string;
  category_field_name: string;
  participant_field_name: string;
  order_field_name: string;
}

interface JudgeRow {
  id: number;
  name: string;
  display_name?: string;
  token: string;
  is_active: boolean;
  scoring_url: string;
  qrcode_url: string;
  created_at: string;
}

const router = useRouter();
const store = useScoringStore();

const activeTab = ref<TabKey>("overview");
const judges = ref<JudgeRow[]>([]);
const scoresData = ref<any>(null);
const loadingConfig = ref(false);
const loadingJudges = ref(false);
const loadingScores = ref(false);
const savingConfig = ref(false);
const importing = ref(false);
const importResult = ref("");
const saveMessage = ref("");
const clearBackgroundRequested = ref(false);

const newJudgeCount = ref(5);

// 手动导入相关
const manualImportData = ref("");
const manualImporting = ref(false);
const manualImportResult = ref("");

const importFile = ref<File | null>(null);
const backgroundFile = ref<File | null>(null);
const backgroundPreview = ref("");
const QR_FILENAME_PATTERN_STORAGE_KEY = "judge_qr_filename_pattern";
const judgeQrFilenamePattern = ref("{index}_{judge_display_name}");

const qrModalVisible = ref(false);
const qrTitle = ref("");
const qrImageUrl = ref("");
const qrTargetUrl = ref("");

// 删除评委弹窗相关
const deleteModalVisible = ref(false);
const deleteTargetJudge = ref<JudgeRow | null>(null);
const deleteConfirmPassword = ref("");
const deleteLoading = ref(false);
const DELETE_CONFIRM_PASSWORD = "jndx";

function createDefaultConfig(): AdminConfig {
  return {
    site_name: "评分系统",
    primary_color: "#1890ff",
    score_min: 1,
    score_max: 100,
    score_value_type: "integer",
    allow_duplicate_scores: true,
    allow_scoring: true,
    exclude_extreme_scores: false,
    background_image: null,
    admin_password: store.adminPassword || "admin123",
    base_url: "http://localhost:5173",
    admin_url: "http://localhost:5173/manage",
    participant_sheet_name: "选手数据",
    category_field_name: "类别",
    participant_field_name: "选手",
    order_field_name: "序号",
  };
}

const configForm = reactive<AdminConfig>(createDefaultConfig());

const adminQrUrl = computed(
  () =>
    `${API.adminQrcode}?password=${encodeURIComponent(store.adminPassword)}`,
);
const scoreRuleText = computed(
  () =>
    `${configForm.score_value_type === "decimal" ? "仅小数" : configForm.score_value_type === "integer_decimal" ? "整数和小数" : "仅整数"}；${configForm.allow_duplicate_scores ? "允许重复分数" : "不允许重复分数"}；打分范围 ${configForm.score_min}-${configForm.score_max}；${configForm.exclude_extreme_scores ? "统计时去掉最高分和最低分（至少 3 位评委打分时生效）" : "统计时保留全部分数"}`,
);

function loadStoredJudgeQrPattern() {
  if (typeof window === "undefined") return;
  const storedPattern = window.localStorage.getItem(
    QR_FILENAME_PATTERN_STORAGE_KEY,
  );
  if (storedPattern?.trim()) {
    judgeQrFilenamePattern.value = storedPattern.trim();
  }
}

watch(judgeQrFilenamePattern, (value) => {
  if (typeof window === "undefined") return;
  const normalized = value.trim() || "{index}_{judge_display_name}";
  window.localStorage.setItem(QR_FILENAME_PATTERN_STORAGE_KEY, normalized);
});

onMounted(async () => {
  loadStoredJudgeQrPattern();
  if (!store.isAdmin) {
    router.push({ name: "adminLogin" });
    return;
  }
  await Promise.all([store.fetchCategories(), loadConfig(), loadJudges()]);
});

async function loadConfig() {
  loadingConfig.value = true;
  try {
    const res = await fetch(
      `${API.adminConfig}?password=${encodeURIComponent(store.adminPassword)}`,
    );
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "加载配置失败");
    Object.assign(configForm, createDefaultConfig(), data);
    backgroundPreview.value = resolveAssetUrl(data.background_image) || "";
  } catch (error: any) {
    saveMessage.value = error.message || "加载配置失败";
  } finally {
    loadingConfig.value = false;
  }
}

async function loadJudges() {
  loadingJudges.value = true;
  try {
    const res = await fetch(
      `${API.adminJudges}?password=${encodeURIComponent(store.adminPassword)}`,
    );
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "加载评委失败");
    judges.value = data.judges || [];
  } catch (error) {
    console.error(error);
  } finally {
    loadingJudges.value = false;
  }
}

async function loadScores() {
  loadingScores.value = true;
  try {
    const res = await fetch(
      `${API.adminScores}?password=${encodeURIComponent(store.adminPassword)}`,
    );
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "加载评分失败");
    scoresData.value = data;
  } catch (error) {
    console.error(error);
  } finally {
    loadingScores.value = false;
  }
}

function buildSaveRuleConfirmText() {
  return [
    "请确认以下基础设置规则：",
    `- 合法打分类型：${configForm.score_value_type === "decimal" ? "仅小数" : configForm.score_value_type === "integer_decimal" ? "整数和小数" : "仅整数"}`,
    `- 分数范围：${configForm.score_min} - ${configForm.score_max}`,
    `- 是否允许重复分数：${configForm.allow_duplicate_scores ? "允许" : "不允许"}`,
    `- 是否允许评委提交评分：${configForm.allow_scoring ? "允许" : "不允许"}`,
    `- 统计规则：${configForm.exclude_extreme_scores ? "去掉最高分和最低分" : "保留全部分数"}`,
    "",
    "请输入 jndx 确认保存：",
  ].join("\n");
}

async function saveConfig() {
  if (configForm.score_min >= configForm.score_max) {
    alert("最高分必须大于最低分");
    return;
  }

  const confirmText = window.prompt(buildSaveRuleConfirmText(), "");
  if (confirmText === null) return;
  if (confirmText.trim() !== "jndx") {
    alert("未输入正确确认码，配置未保存");
    return;
  }

  savingConfig.value = true;
  saveMessage.value = "";
  try {
    const formData = new FormData();
    formData.append("password", store.adminPassword);
    formData.append("site_name", configForm.site_name);
    formData.append("primary_color", configForm.primary_color);
    formData.append("score_min", String(configForm.score_min));
    formData.append("score_max", String(configForm.score_max));
    formData.append("score_value_type", configForm.score_value_type);
    formData.append(
      "allow_duplicate_scores",
      String(configForm.allow_duplicate_scores),
    );
    formData.append("allow_scoring", String(configForm.allow_scoring));
    formData.append(
      "exclude_extreme_scores",
      String(configForm.exclude_extreme_scores),
    );
    formData.append("admin_password", configForm.admin_password);
    formData.append("base_url", configForm.base_url);
    formData.append(
      "participant_sheet_name",
      configForm.participant_sheet_name,
    );
    formData.append("category_field_name", configForm.category_field_name);
    formData.append(
      "participant_field_name",
      configForm.participant_field_name,
    );
    formData.append("order_field_name", configForm.order_field_name);
    formData.append("clear_background", String(clearBackgroundRequested.value));
    if (backgroundFile.value) {
      formData.append("background_image", backgroundFile.value);
    }

    const res = await fetch(API.adminConfigUpdate, {
      method: "POST",
      body: formData,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "保存失败");

    Object.assign(configForm, data.config);
    store.adminPassword = configForm.admin_password;
    saveMessage.value = data.message || "配置已保存";
    clearBackgroundRequested.value = false;
    backgroundFile.value = null;
    backgroundPreview.value =
      resolveAssetUrl(data.config.background_image) || "";
    await store.fetchSiteConfig();
  } catch (error: any) {
    saveMessage.value = error.message || "保存失败";
  } finally {
    savingConfig.value = false;
  }
}

function onBackgroundChange(event: Event) {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0] || null;
  backgroundFile.value = file;
  clearBackgroundRequested.value = false;
  if (file) {
    backgroundPreview.value = URL.createObjectURL(file);
  }
}

function clearBackground() {
  backgroundFile.value = null;
  clearBackgroundRequested.value = true;
  backgroundPreview.value = "";
}

async function handleCreateJudges() {
  try {
    const count = newJudgeCount.value;
    if (count <= 0) {
      alert("请输入有效数量");
      return;
    }

    const res = await fetch(API.adminJudgesBatch, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        password: store.adminPassword,
        count: count,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "创建失败");
    alert(`成功创建 ${data.count} 名评委`);
    await loadJudges();
  } catch (error: any) {
    alert(error.message || "创建失败");
  }
}

async function handleImport() {
  if (!importFile.value) {
    importResult.value = "请先选择 Excel 文件";
    return;
  }
  importing.value = true;
  importResult.value = "";
  try {
    const formData = new FormData();
    formData.append("password", store.adminPassword);
    formData.append("file", importFile.value);
    const res = await fetch(API.adminImport, {
      method: "POST",
      body: formData,
    });
    const data = await res.json();
    importResult.value = data.message || data.error || "导入完成";
    if (!res.ok) throw new Error(importResult.value);
    await store.fetchCategories();
    importFile.value = null;
  } catch (error: any) {
    importResult.value = error.message || "导入失败";
  } finally {
    importing.value = false;
  }
}

function onImportFileChange(event: Event) {
  const target = event.target as HTMLInputElement;
  importFile.value = target.files?.[0] || null;
}

// 手动导入处理函数
async function handleManualImport() {
  const lines = manualImportData.value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  if (lines.length === 0) {
    manualImportResult.value = "请输入选手数据";
    return;
  }

  // 解析数据
  const participants: Array<{
    category: string;
    name: string;
    order?: number;
  }> = [];
  const errors: string[] = [];

  lines.forEach((line, index) => {
    const parts = line.split(",").map((p) => p.trim());
    if (parts.length < 2) {
      errors.push(`第 ${index + 1} 行格式错误：${line}`);
      return;
    }

    const category = parts[0];
    const name = parts[1];
    const order = parts[2] ? parseInt(parts[2], 10) : undefined;

    if (!category || !name) {
      errors.push(`第 ${index + 1} 行类别或姓名为空`);
      return;
    }

    participants.push({ category, name, order });
  });

  if (errors.length > 0) {
    manualImportResult.value = "格式错误：\n" + errors.join("\n");
    return;
  }

  manualImporting.value = true;
  manualImportResult.value = "";

  try {
    const res = await fetch(API.adminImport, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        password: store.adminPassword,
        participants: participants,
      }),
    });

    const data = await res.json();
    manualImportResult.value = data.message || data.error || "导入完成";
    if (!res.ok) throw new Error(manualImportResult.value);

    await store.fetchCategories();
    manualImportData.value = "";
  } catch (error: any) {
    manualImportResult.value = error.message || "导入失败";
  } finally {
    manualImporting.value = false;
  }
}

async function handleClearScores() {
  if (!confirm("确定要清空所有评分记录吗？此操作不可恢复。")) return;

  const clearPassword = window.prompt("请输入清空评分密码：");
  if (clearPassword === null) return;
  if (!clearPassword.trim()) {
    alert("请输入清空评分密码");
    return;
  }

  try {
    const res = await fetch(API.adminClear, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        password: store.adminPassword,
        clear_password: clearPassword,
      }),
    });
    const data = await res.json();
    alert(data.message || data.error || "操作完成");
    if (res.ok) {
      await Promise.all([loadScores(), loadJudges()]);
    }
  } catch (error) {
    console.error(error);
  }
}

function exportAllJudgeQrcodes() {
  const params = new URLSearchParams({
    password: store.adminPassword,
    pattern: judgeQrFilenamePattern.value || "{index}_{judge_display_name}",
  });
  window.open(`${API.adminJudgeQrcodesExport}?${params.toString()}`, "_blank");
}

function handleExport() {
  window.open(
    `${API.adminExport}?password=${encodeURIComponent(store.adminPassword)}`,
    "_blank",
  );
}

function downloadTemplate() {
  window.open(
    `${API.adminTemplate}?password=${encodeURIComponent(store.adminPassword)}`,
    "_blank",
  );
}

function getJudgeDisplayName(
  judge: JudgeRow | { id: number; display_name?: string },
) {
  return judge.display_name || `评委${judge.id}`;
}

function openQrModal(title: string, imageUrl: string, targetUrl: string) {
  qrTitle.value = title;
  qrImageUrl.value = imageUrl;
  qrTargetUrl.value = targetUrl;
  qrModalVisible.value = true;
}

function showJudgeQr(judge: JudgeRow) {
  openQrModal(
    `${judge.display_name || `评委${judge.id}`} - 评委二维码`,
    API.judgeQrcode(judge.token),
    judge.scoring_url,
  );
}

function showAdminQr() {
  openQrModal("管理员入口二维码", adminQrUrl.value, configForm.admin_url);
}

function closeQrModal() {
  qrModalVisible.value = false;
}

// 删除评委相关函数
function confirmDeleteJudge(judge: JudgeRow) {
  deleteTargetJudge.value = judge;
  deleteConfirmPassword.value = "";
  deleteModalVisible.value = true;
}

function closeDeleteModal() {
  deleteModalVisible.value = false;
  deleteTargetJudge.value = null;
  deleteConfirmPassword.value = "";
}

async function handleDeleteJudge() {
  if (!deleteTargetJudge.value) return;

  if (deleteConfirmPassword.value !== DELETE_CONFIRM_PASSWORD) {
    alert("密码错误，请输入正确的确认密码");
    return;
  }

  deleteLoading.value = true;
  try {
    const res = await fetch(
      `${API.adminJudgeDelete(deleteTargetJudge.value.id)}?password=${encodeURIComponent(store.adminPassword)}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      },
    );

    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.error || "删除失败");
    }

    alert("评委删除成功");
    closeDeleteModal();
    await loadJudges();
  } catch (err: any) {
    alert(err.message || "删除评委失败");
  } finally {
    deleteLoading.value = false;
  }
}

function copyLink(url: string) {
  navigator.clipboard
    .writeText(url)
    .then(() => {
      alert("链接已复制");
    })
    .catch(() => {
      prompt("请手动复制链接：", url);
    });
}

function getJudgeScoreStatus(
  categoryId: number,
  judgeId: number,
  participantId: number,
) {
  return (
    scoresData.value?.scores?.[categoryId]?.[judgeId]?.[participantId] !==
    undefined
  );
}

function getJudgeCategoryCompletedCount(category: any, judgeId: number) {
  const participants = category?.participants || [];
  return participants.filter((participant: any) =>
    getJudgeScoreStatus(category.id, judgeId, participant.id),
  ).length;
}

function getJudgeCategoryProgressPercent(category: any, judgeId: number) {
  const total = category?.participants?.length || 0;
  if (!total) return 0;
  return Math.round(
    (getJudgeCategoryCompletedCount(category, judgeId) / total) * 100,
  );
}

function switchTab(tab: TabKey) {
  activeTab.value = tab;
  if (tab === "scores" && !scoresData.value) {
    loadScores();
  }
}

function logout() {
  store.reset();
  router.push({ name: "adminLogin" });
}

// 获取选手的统计数据，如果没有则返回 null
function getParticipantStat(categoryId: number, participantId: number) {
  const stats = scoresData.value?.statistics?.[categoryId] || [];
  return stats.find((s: any) => s.participant_id === participantId) || null;
}

// 获取选手在已评分选手中的排名
function getParticipantRank(categoryId: number, participantId: number) {
  const stats = scoresData.value?.statistics?.[categoryId] || [];
  const index = stats.findIndex((s: any) => s.participant_id === participantId);
  return index >= 0 ? index + 1 : null;
}
</script>

<template>
  <div class="admin-dashboard">
    <header class="admin-header">
      <div class="header-brand">
        <div class="brand-icon">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
            <path d="M7 11V7a5 5 0 0 1 10 0v4" />
          </svg>
        </div>
        <div class="brand-text">
          <h1>{{ configForm.site_name || "管理后台" }}</h1>
          <p class="header-subtitle">系统管理与配置中心</p>
        </div>
      </div>
      <button class="logout-btn" @click="logout">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
          <polyline points="16 17 21 12 16 7" />
          <line x1="21" y1="12" x2="9" y2="12" />
        </svg>
        退出
      </button>
    </header>

    <nav class="tab-nav">
      <button
        v-for="tab in [
          {
            key: 'overview',
            label: '概览',
            icon: 'M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z M9 22V12h6v10',
          },
          {
            key: 'settings',
            label: '基础设置',
            icon: 'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z',
          },
          {
            key: 'judges',
            label: '评委管理',
            icon: 'M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2 M9 7a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M23 21v-2a4 4 0 0 0-3-3.87 M16 3.13a4 4 0 0 1 0 7.75',
          },
          {
            key: 'scores',
            label: '成绩统计',
            icon: 'M12 20V10 M18 20V4 M6 20v-4',
          },
          {
            key: 'import',
            label: '数据导入',
            icon: 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z M14 2v6h6 M16 13H8 M16 17H8 M10 9H8',
          },
        ]"
        :key="tab.key"
        :class="['tab-btn', { active: activeTab === tab.key }]"
        @click="switchTab(tab.key as TabKey)"
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <path :d="tab.icon" />
        </svg>
        {{ tab.label }}
      </button>
    </nav>

    <div class="tab-content" v-if="activeTab === 'overview'">
      <div class="stat-grid">
        <div class="stat-card">
          <div class="stat-icon judges">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
              <path d="M16 3.13a4 4 0 0 1 0 7.75" />
            </svg>
          </div>
          <div class="stat-number">{{ judges.length }}</div>
          <div class="stat-label">评委总数</div>
        </div>
        <div class="stat-card">
          <div class="stat-icon categories">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path
                d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"
              />
            </svg>
          </div>
          <div class="stat-number">{{ store.categories.length }}</div>
          <div class="stat-label">比赛类别</div>
        </div>
        <div class="stat-card">
          <div class="stat-icon active">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </div>
          <div class="stat-number">
            {{ judges.filter((item) => item.is_active).length }}
          </div>
          <div class="stat-label">启用评委</div>
        </div>
      </div>

      <div class="section two-column">
        <div class="info-section">
          <h3>
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
            当前活动
          </h3>
          <div class="info-list">
            <div class="info-item">
              <span class="info-label">活动标题</span>
              <span class="info-value">{{ configForm.site_name }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">前端地址</span>
              <span class="info-value">{{ configForm.base_url }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">评分范围</span>
              <span class="info-value"
                >{{ configForm.score_min }} -
                {{ configForm.score_max }} 分</span
              >
            </div>
            <div class="info-item">
              <span class="info-label">统计规则</span>
              <span class="info-value">{{ scoreRuleText }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">评分开关</span>
              <span class="info-value">
                <span
                  class="status-badge"
                  :class="{ active: configForm.allow_scoring }"
                >
                  {{ configForm.allow_scoring ? "开启" : "关闭" }}
                </span>
              </span>
            </div>
          </div>
        </div>
        <div class="qr-card">
          <h3>
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <rect x="3" y="3" width="7" height="7" />
              <rect x="14" y="3" width="7" height="7" />
              <rect x="14" y="14" width="7" height="7" />
              <rect x="3" y="14" width="7" height="7" />
            </svg>
            管理员二维码
          </h3>
          <div class="qr-wrapper">
            <img :src="adminQrUrl" alt="管理员二维码" class="mini-qr" />
          </div>
          <div class="button-row compact">
            <button class="btn btn-outline" @click="showAdminQr">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0z" />
                <path
                  d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                />
              </svg>
              放大查看
            </button>
            <button
              class="btn btn-primary"
              @click="copyLink(configForm.admin_url)"
            >
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                <path
                  d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"
                />
              </svg>
              复制链接
            </button>
          </div>
        </div>
      </div>

      <div class="section">
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
          快捷操作
        </h3>
        <div class="button-row wrap">
          <button class="btn btn-primary" @click="handleExport">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            导出成绩 Excel
          </button>
          <button class="btn btn-outline" @click="downloadTemplate">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path
                d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"
              />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
              <polyline points="10 9 9 9 8 9" />
            </svg>
            下载导入模板
          </button>
          <button class="btn btn-outline" @click="showAdminQr">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <rect x="3" y="3" width="7" height="7" />
              <rect x="14" y="3" width="7" height="7" />
              <rect x="14" y="14" width="7" height="7" />
              <rect x="3" y="14" width="7" height="7" />
            </svg>
            管理员二维码
          </button>
          <button class="btn btn-danger" @click="handleClearScores">
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
            清空评分
          </button>
        </div>
      </div>
    </div>

    <div class="tab-content" v-else-if="activeTab === 'settings'">
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
          <label class="form-field">
            <span>合法打分类型</span>
            <select v-model="configForm.score_value_type" class="input">
              <option value="integer">整数</option>
              <option value="decimal">小数</option>
              <option value="integer_decimal">整数和小数</option>
            </select>
          </label>
          <label class="form-field">
            <span>最低分</span>
            <input
              v-model.number="configForm.score_min"
              class="input"
              type="number"
              :step="configForm.score_value_type === 'integer' ? '1' : '0.01'"
            />
          </label>
          <label class="form-field">
            <span>最高分</span>
            <input
              v-model.number="configForm.score_max"
              class="input"
              type="number"
              :step="configForm.score_value_type === 'integer' ? '1' : '0.01'"
            />
          </label>
        </div>

        <div class="switch-list inline-switch-list">
          <label class="switch-item">
            <div class="switch">
              <input
                v-model="configForm.allow_duplicate_scores"
                type="checkbox"
              />
              <span class="slider"></span>
            </div>
            <span class="switch-label">打分是否允许重复</span>
          </label>
          <label class="switch-item">
            <div class="switch">
              <input v-model="configForm.allow_scoring" type="checkbox" />
              <span class="slider"></span>
            </div>
            <span class="switch-label">允许评委提交评分</span>
          </label>
          <label class="switch-item">
            <div class="switch">
              <input
                v-model="configForm.exclude_extreme_scores"
                type="checkbox"
              />
              <span class="slider"></span>
            </div>
            <span class="switch-label">统计时去掉最高分和最低分</span>
          </label>
        </div>

        <h3>
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

        <h3>
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M4 7h16M4 12h16M4 17h10" />
          </svg>
          导入字段设置（手动输入）
        </h3>
        <div class="form-grid">
          <label class="form-field">
            <span>选手 Sheet 名称</span>
            <input
              v-model="configForm.participant_sheet_name"
              class="input"
              placeholder="选手数据"
            />
          </label>
          <label class="form-field">
            <span>类别字段名</span>
            <input
              v-model="configForm.category_field_name"
              class="input"
              placeholder="类别"
            />
          </label>
          <label class="form-field">
            <span>选手字段名</span>
            <input
              v-model="configForm.participant_field_name"
              class="input"
              placeholder="选手"
            />
          </label>
          <label class="form-field">
            <span>序号字段名</span>
            <input
              v-model="configForm.order_field_name"
              class="input"
              placeholder="序号"
            />
          </label>
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
            v-if="
              saveMessage.includes('成功') || saveMessage.includes('已保存')
            "
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
            @click="saveConfig"
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

    <div class="tab-content" v-else-if="activeTab === 'judges'">
      <div class="section">
        <h3>
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
            <circle cx="8.5" cy="7" r="4" />
            <line x1="20" y1="8" x2="20" y2="14" />
            <line x1="23" y1="11" x2="17" y2="11" />
          </svg>
          创建评委
        </h3>
        <div class="create-form">
          <label class="form-field">
            <span>创建数量</span>
            <input
              v-model.number="newJudgeCount"
              type="number"
              min="1"
              class="input small-input"
            />
          </label>
          <button class="btn btn-primary" @click="handleCreateJudges">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
              <circle cx="8.5" cy="7" r="4" />
              <line x1="20" y1="8" x2="20" y2="14" />
              <line x1="23" y1="11" x2="17" y2="11" />
            </svg>
            创建评委
          </button>
        </div>
      </div>

      <div class="section">
        <h3>
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
            <circle cx="9" cy="7" r="4" />
            <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
            <path d="M16 3.13a4 4 0 0 1 0 7.75" />
          </svg>
          评委列表
        </h3>
        <div class="qr-export-panel">
          <label class="form-field qr-pattern-field">
            <span>二维码命名规则</span>
            <input
              v-model="judgeQrFilenamePattern"
              class="input"
              placeholder="{index}_{judge_display_name}"
            />
            <small class="form-tip"
              >支持
              {index}、{judge_id}、{judge_name}、{judge_display_name}、{site_name}、{token}</small
            >
          </label>
          <button class="btn btn-primary" @click="exportAllJudgeQrcodes">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            一键导出全部二维码
          </button>
        </div>
        <div v-if="loadingJudges" class="loading-state">
          <div class="spinner"></div>
          <p>加载中...</p>
        </div>
        <div v-else-if="!judges.length" class="empty-state">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
            <circle cx="9" cy="7" r="4" />
            <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
            <path d="M16 3.13a4 4 0 0 1 0 7.75" />
          </svg>
          <p>暂无评委</p>
        </div>
        <div v-else class="table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>评委</th>
                <th>状态</th>
                <th>评分链接</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="judge in judges" :key="judge.id">
                <td>
                  <div class="judge-display-cell">
                    <span class="id-badge">{{ judge.id }}</span>
                    <strong>{{ getJudgeDisplayName(judge) }}</strong>
                  </div>
                </td>
                <td>
                  <span
                    class="status-badge"
                    :class="{ active: judge.is_active }"
                  >
                    {{ judge.is_active ? "启用" : "禁用" }}
                  </span>
                </td>
                <td class="ellipsis-cell">{{ judge.scoring_url }}</td>
                <td>
                  <div class="button-row compact">
                    <button
                      class="btn btn-outline mini-btn"
                      @click="showJudgeQr(judge)"
                    >
                      <svg
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                      >
                        <rect x="3" y="3" width="7" height="7" />
                        <rect x="14" y="3" width="7" height="7" />
                        <rect x="14" y="14" width="7" height="7" />
                        <rect x="3" y="14" width="7" height="7" />
                      </svg>
                      二维码
                    </button>
                    <button
                      class="btn btn-outline mini-btn"
                      @click="copyLink(judge.scoring_url)"
                    >
                      <svg
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                      >
                        <rect
                          x="9"
                          y="9"
                          width="13"
                          height="13"
                          rx="2"
                          ry="2"
                        />
                        <path
                          d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"
                        />
                      </svg>
                      复制链接
                    </button>
                    <button
                      class="btn btn-danger mini-btn"
                      @click="confirmDeleteJudge(judge)"
                    >
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
                        <line x1="10" y1="11" x2="10" y2="17" />
                        <line x1="14" y1="11" x2="14" y2="17" />
                      </svg>
                      删除
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div class="tab-content" v-else-if="activeTab === 'scores'">
      <div class="section-actions">
        <button class="btn btn-outline" @click="loadScores">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <polyline points="23 4 23 10 17 10" />
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
          </svg>
          刷新
        </button>
        <button class="btn btn-primary" @click="handleExport">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          导出 Excel
        </button>
      </div>

      <div class="section" v-if="loadingScores">
        <div class="loading-state">
          <div class="spinner"></div>
          <p>正在加载评分数据...</p>
        </div>
      </div>
      <template v-else-if="scoresData">
        <div class="section">
          <h3>
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
            统计规则
          </h3>
          <p class="rule-text">{{ scoresData.calculation_rule }}</p>
        </div>

        <div class="section">
          <h3>
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
              <polyline points="22 4 12 14.01 9 11.01" />
            </svg>
            评委完成情况（按选手）
          </h3>
          <div
            v-for="category in scoresData.categories"
            :key="`progress-${category.id}`"
            class="progress-matrix-section"
          >
            <div class="progress-matrix-header">
              <div>
                <h4>{{ category.name }}</h4>
                <p>显示每位评委对每位选手是否已打分</p>
              </div>
            </div>
            <div class="table-wrap">
              <table class="data-table progress-matrix-table">
                <thead>
                  <tr>
                    <th>评委</th>
                    <th
                      v-for="participant in category.participants"
                      :key="participant.id"
                    >
                      {{ participant.name }}
                    </th>
                    <th>完成度</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="judge in scoresData.judges"
                    :key="`${category.id}-${judge.id}`"
                  >
                    <td>
                      <div class="judge-name-cell">{{ judge.name }}</div>
                    </td>
                    <td
                      v-for="participant in category.participants"
                      :key="`${judge.id}-${participant.id}`"
                    >
                      <span
                        class="status-badge"
                        :class="{
                          active: getJudgeScoreStatus(
                            category.id,
                            judge.id,
                            participant.id,
                          ),
                        }"
                      >
                        {{
                          getJudgeScoreStatus(
                            category.id,
                            judge.id,
                            participant.id,
                          )
                            ? "已打分"
                            : "未打分"
                        }}
                      </span>
                    </td>
                    <td class="progress-summary-cell">
                      <div class="progress-summary-content">
                        <span class="progress-fraction">
                          {{
                            getJudgeCategoryCompletedCount(category, judge.id)
                          }}/{{ category.participants.length }}
                        </span>
                        <div class="progress-bar-wrapper">
                          <div class="progress-bar">
                            <div
                              class="progress-bar-fill"
                              :class="{
                                low:
                                  getJudgeCategoryProgressPercent(
                                    category,
                                    judge.id,
                                  ) < 30,
                                partial:
                                  getJudgeCategoryProgressPercent(
                                    category,
                                    judge.id,
                                  ) >= 30 &&
                                  getJudgeCategoryProgressPercent(
                                    category,
                                    judge.id,
                                  ) < 70,
                              }"
                              :style="{
                                width:
                                  getJudgeCategoryProgressPercent(
                                    category,
                                    judge.id,
                                  ) + '%',
                              }"
                            ></div>
                          </div>
                          <span class="progress-text"
                            >{{
                              getJudgeCategoryProgressPercent(
                                category,
                                judge.id,
                              )
                            }}%</span
                          >
                        </div>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div
          v-for="category in scoresData.categories"
          :key="category.id"
          class="section"
        >
          <h3>
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path
                d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"
              />
            </svg>
            {{ category.name }} 排名
          </h3>
          <div v-if="!category.participants?.length" class="empty-state">
            <p>暂无选手数据</p>
          </div>
          <div v-else class="table-wrap">
            <table class="data-table ranking-table">
              <thead>
                <tr>
                  <th class="col-rank">排名</th>
                  <th class="col-order">序号</th>
                  <th>选手</th>
                  <th class="col-score">统计总分</th>
                  <th class="col-score">统计平均分</th>
                  <th class="col-score">原始总分</th>
                  <th class="col-score">原始平均分</th>
                  <th class="col-count">评委数</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="participant in category.participants"
                  :key="participant.id"
                  :class="{
                    'top-three':
                      (getParticipantRank(category.id, participant.id) || 0) <=
                        3 &&
                      getParticipantRank(category.id, participant.id) !== null,
                  }"
                >
                  <td class="col-rank">
                    <span
                      v-if="getParticipantRank(category.id, participant.id)"
                      class="rank-badge"
                      :class="{
                        gold:
                          getParticipantRank(category.id, participant.id) === 1,
                        silver:
                          getParticipantRank(category.id, participant.id) === 2,
                        bronze:
                          getParticipantRank(category.id, participant.id) === 3,
                      }"
                      >{{
                        getParticipantRank(category.id, participant.id)
                      }}</span
                    >
                    <span v-else class="rank-badge">-</span>
                  </td>
                  <td class="col-order">{{ participant.order || "-" }}</td>
                  <td>
                    <strong>{{ participant.name }}</strong>
                  </td>
                  <td class="col-score">
                    <span
                      v-if="getParticipantStat(category.id, participant.id)"
                      class="score-highlight"
                      >{{
                        getParticipantStat(category.id, participant.id)?.total
                      }}</span
                    >
                    <span v-else>-</span>
                  </td>
                  <td class="col-score">
                    <span
                      v-if="getParticipantStat(category.id, participant.id)"
                      >{{
                        getParticipantStat(category.id, participant.id)?.average
                      }}</span
                    >
                    <span v-else>-</span>
                  </td>
                  <td class="col-score">
                    <span
                      v-if="getParticipantStat(category.id, participant.id)"
                      >{{
                        getParticipantStat(category.id, participant.id)
                          ?.raw_total
                      }}</span
                    >
                    <span v-else>-</span>
                  </td>
                  <td class="col-score">
                    <span
                      v-if="getParticipantStat(category.id, participant.id)"
                      >{{
                        getParticipantStat(category.id, participant.id)
                          ?.raw_average
                      }}</span
                    >
                    <span v-else>-</span>
                  </td>
                  <td class="col-count">
                    <span v-if="getParticipantStat(category.id, participant.id)"
                      >{{
                        getParticipantStat(category.id, participant.id)
                          ?.effective_count
                      }}/{{
                        getParticipantStat(category.id, participant.id)?.count
                      }}</span
                    >
                    <span v-else>-</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </template>
      <div v-else class="section empty-state">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <path d="M12 20V10 M18 20V4 M6 20v-4" />
        </svg>
        <p>点击"刷新"加载统计数据</p>
      </div>
    </div>

    <div class="tab-content" v-else-if="activeTab === 'import'">
      <div class="section">
        <h3>
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path
              d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"
            />
            <polyline points="14 2 14 8 20 8" />
            <line x1="16" y1="13" x2="8" y2="13" />
            <line x1="16" y1="17" x2="8" y2="17" />
            <polyline points="10 9 9 9 8 9" />
          </svg>
          Excel 导入
        </h3>

        <div class="field-settings-panel">
          <div class="field-settings-header">
            <div>
              <h4>字段名手动设置</h4>
            </div>
            <button
              class="btn btn-outline"
              :disabled="savingConfig"
              @click="saveConfig"
            >
              <svg
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
              {{ savingConfig ? "保存中..." : "保存字段设置" }}
            </button>
          </div>
          <div class="form-grid">
            <label class="form-field">
              <span>选手 Sheet 名称</span>
              <input
                v-model="configForm.participant_sheet_name"
                class="input"
                placeholder="选手数据"
              />
            </label>
            <label class="form-field">
              <span>类别字段名</span>
              <input
                v-model="configForm.category_field_name"
                class="input"
                placeholder="类别"
              />
            </label>
            <label class="form-field">
              <span>选手字段名</span>
              <input
                v-model="configForm.participant_field_name"
                class="input"
                placeholder="选手"
              />
            </label>
            <label class="form-field">
              <span>序号字段名</span>
              <input
                v-model="configForm.order_field_name"
                class="input"
                placeholder="序号"
              />
            </label>
          </div>
        </div>

        <div class="import-actions">
          <button class="btn btn-outline" @click="downloadTemplate">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            下载 Excel 模板
          </button>
          <label class="file-input-wrapper btn btn-outline">
            <input
              type="file"
              accept=".xlsx,.xlsm,.xltx,.xltm"
              @change="onImportFileChange"
            />
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
            {{ importFile ? importFile.name : "选择 Excel 文件" }}
          </label>
        </div>

        <div
          v-if="importResult"
          class="message-box"
          :class="{
            success: importResult.includes('成功'),
            error:
              importResult.includes('失败') || importResult.includes('错误'),
          }"
        >
          <svg
            v-if="importResult.includes('成功')"
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
          {{ importResult }}
        </div>

        <div class="button-row">
          <button
            class="btn btn-primary"
            :disabled="importing || !importFile"
            @click="handleImport"
          >
            <span v-if="importing" class="spinner"></span>
            <svg
              v-else
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path
                d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"
              />
              <polyline points="14 2 14 8 20 8" />
              <line x1="12" y1="18" x2="12" y2="12" />
              <line x1="9" y1="15" x2="15" y2="15" />
            </svg>
            {{ importing ? "导入中..." : "开始导入 Excel" }}
          </button>
        </div>
      </div>

      <div class="section">
        <h3>
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path
              d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"
            />
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
          </svg>
          手动录入
        </h3>
        <p class="section-desc">
          直接输入选手数据，每行一个，格式：类别,选手姓名,序号
        </p>

        <div class="manual-import-form">
          <label class="form-field">
            <span>选手数据（每行一个）</span>
            <textarea
              v-model="manualImportData"
              class="textarea manual-input"
              rows="10"
              placeholder="歌唱组,张三,1&#10;歌唱组,李四,2&#10;舞蹈组,王五,1&#10;舞蹈组,赵六"
            />
          </label>
          <div class="form-tip">
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
            支持格式： 类别,选手姓名,序号。序号用于控制同一类别内的展示顺序。
          </div>
        </div>

        <div
          v-if="manualImportResult"
          class="message-box"
          :class="{
            success: manualImportResult.includes('成功'),
            error:
              manualImportResult.includes('失败') ||
              manualImportResult.includes('错误'),
          }"
        >
          <svg
            v-if="manualImportResult.includes('成功')"
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
          {{ manualImportResult }}
        </div>

        <div class="button-row">
          <button
            class="btn btn-primary"
            :disabled="manualImporting || !manualImportData.trim()"
            @click="handleManualImport"
          >
            <span v-if="manualImporting" class="spinner"></span>
            <svg
              v-else
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path
                d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"
              />
              <path
                d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"
              />
            </svg>
            {{ manualImporting ? "导入中..." : "开始手动导入" }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="qrModalVisible" class="modal-overlay" @click.self="closeQrModal">
      <div class="modal-card">
        <button class="modal-close" @click="closeQrModal">
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
        <h3>{{ qrTitle }}</h3>
        <div class="qr-wrapper">
          <img :src="qrImageUrl" alt="二维码" class="qr-image" />
        </div>
        <p class="qr-url">{{ qrTargetUrl }}</p>
        <div class="button-row compact center">
          <button class="btn btn-primary" @click="copyLink(qrTargetUrl)">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
              <path
                d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"
              />
            </svg>
            复制链接
          </button>
          <a :href="qrImageUrl" download class="btn btn-outline">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            下载二维码
          </a>
        </div>
      </div>
    </div>

    <!-- 删除评委确认弹窗 -->
    <div
      v-if="deleteModalVisible"
      class="modal-overlay"
      @click.self="closeDeleteModal"
    >
      <div class="modal-card delete-modal">
        <button class="modal-close" @click="closeDeleteModal">
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
        <div class="delete-modal-header">
          <div class="delete-warning-icon">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path
                d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"
              />
              <line x1="12" y1="9" x2="12" y2="13" />
              <line x1="12" y1="17" x2="12.01" y2="17" />
            </svg>
          </div>
          <h3>确认删除评委</h3>
        </div>
        <div class="delete-modal-content">
          <p class="delete-warning-text">
            您即将删除评委
            <strong>{{
              deleteTargetJudge?.name || `评委${deleteTargetJudge?.id}`
            }}</strong
            >，此操作不可恢复。
          </p>
          <p class="delete-hint-text">
            该评委的所有评分数据将被永久删除，请谨慎操作。
          </p>
          <div class="delete-password-section">
            <label class="form-field">
              <span>请输入确认密码 <code>jndx</code> 以继续</span>
              <input
                v-model="deleteConfirmPassword"
                type="password"
                class="input"
                placeholder="请输入密码"
                @keyup.enter="handleDeleteJudge"
              />
            </label>
          </div>
        </div>
        <div class="button-row compact center delete-actions">
          <button class="btn btn-outline" @click="closeDeleteModal">
            取消
          </button>
          <button
            class="btn btn-danger"
            :disabled="
              deleteLoading || deleteConfirmPassword !== DELETE_CONFIRM_PASSWORD
            "
            @click="handleDeleteJudge"
          >
            <span v-if="deleteLoading" class="spinner"></span>
            <svg
              v-else
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
            {{ deleteLoading ? "删除中..." : "确认删除" }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-dashboard {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
}

.admin-header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  padding: 20px 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: var(--shadow-sm);
  position: sticky;
  top: 0;
  z-index: 10;
}

.header-brand {
  display: flex;
  align-items: center;
  gap: 16px;
}

.brand-icon {
  width: 48px;
  height: 48px;
  background: var(--primary-gradient);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.3);
}

.brand-icon svg {
  width: 24px;
  height: 24px;
}

.brand-text h1 {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 2px;
}

.header-subtitle {
  color: var(--text-secondary);
  font-size: 13px;
}

.logout-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 1px solid #e8e8e8;
  background: #fff;
  border-radius: var(--radius-md);
  padding: 10px 18px;
  cursor: pointer;
  font-size: 14px;
  color: var(--text-secondary);
  transition: all 0.3s;
}

.logout-btn svg {
  width: 18px;
  height: 18px;
}

.logout-btn:hover {
  border-color: var(--error-color);
  color: var(--error-color);
  background: #fff2f0;
}

.tab-nav {
  display: flex;
  gap: 8px;
  padding: 16px 32px;
  background: rgba(255, 255, 255, 0.8);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  overflow-x: auto;
  scrollbar-width: none;
}

.tab-nav::-webkit-scrollbar {
  display: none;
}

.tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  border: none;
  background: transparent;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.3s;
  white-space: nowrap;
}

.tab-btn svg {
  width: 18px;
  height: 18px;
}

.tab-btn:hover {
  background: rgba(24, 144, 255, 0.06);
  color: var(--primary-color);
}

.tab-btn.active {
  background: var(--primary-gradient);
  color: #fff;
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.3);
}

.tab-content {
  padding: 32px;
  max-width: 1400px;
  margin: 0 auto;
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.stat-card {
  background: #fff;
  border-radius: var(--radius-lg);
  padding: 24px;
  box-shadow: var(--shadow-sm);
  transition: all 0.3s;
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--primary-gradient);
  opacity: 0;
  transition: opacity 0.3s;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-md);
}

.stat-card:hover::before {
  opacity: 1;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
}

.stat-icon svg {
  width: 24px;
  height: 24px;
}

.stat-icon.judges {
  background: linear-gradient(135deg, #e6f7ff 0%, #bae7ff 100%);
  color: var(--primary-color);
}

.stat-icon.categories {
  background: linear-gradient(135deg, #f6ffed 0%, #d9f7be 100%);
  color: #52c41a;
}

.stat-icon.active {
  background: linear-gradient(135deg, #f9f0ff 0%, #efdbff 100%);
  color: #722ed1;
}

.stat-number {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: var(--text-secondary);
}

.section {
  background: #fff;
  border-radius: var(--radius-lg);
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: var(--shadow-sm);
}

.section.two-column {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.qr-export-panel {
  display: flex;
  flex-wrap: wrap;
  align-items: end;
  gap: 16px;
  margin-bottom: 20px;
}

.qr-pattern-field {
  flex: 1 1 360px;
}

.form-tip {
  margin-top: 6px;
  color: var(--text-secondary);
  font-size: 12px;
}

.switch-list.inline-switch-list {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
  align-items: center;
  margin-bottom: 24px;
}

.switch-list.inline-switch-list .switch-item {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  margin: 0;
}

.switch-list.inline-switch-list .switch-label {
  white-space: nowrap;
}

.upload-panel {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}

.background-preview-card {
  margin-top: 16px;
}

.background-preview-frame {
  width: 280px;
  height: 160px;
  max-width: 100%;
  border-radius: var(--radius-md);
  border: 1px solid #f0f0f0;
  background: linear-gradient(135deg, #fafafa 0%, #f5f5f5 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.background-preview {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.import-info {
  margin-bottom: 16px;
  color: var(--text-secondary);
  line-height: 1.7;
}

.field-settings-panel {
  margin-bottom: 20px;
  padding: 20px;
  border: 1px solid #f0f0f0;
  border-radius: var(--radius-md);
  background: linear-gradient(180deg, #fcfcfc 0%, #f7f9fc 100%);
}

.field-settings-header {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 16px;
}

.field-settings-header h4 {
  margin: 0 0 6px;
  font-size: 15px;
  color: var(--text-primary);
}

.field-settings-header p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.6;
  font-size: 13px;
}

.import-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
  margin-bottom: 20px;
}

/* 手动导入样式 */
.manual-import-form {
  margin-bottom: 20px;
}

.manual-import-form .form-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.manual-import-form .form-field span {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.manual-input {
  font-family: "Courier New", monospace;
  font-size: 14px;
  line-height: 1.6;
  padding: 16px;
  border: 1px solid #d9d9d9;
  border-radius: var(--radius-md);
  resize: vertical;
  min-height: 200px;
  max-height: 400px;
  overflow-y: auto;
  transition: all 0.3s;
}

.manual-input:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(24, 144, 255, 0.1);
  outline: none;
}

.manual-import-form .form-tip {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px 16px;
  background: #f6ffed;
  border-radius: var(--radius-md);
  border-left: 3px solid #52c41a;
  font-size: 13px;
  color: var(--text-secondary);
}

.manual-import-form .form-tip svg {
  width: 16px;
  height: 16px;
  color: #52c41a;
  flex-shrink: 0;
  margin-top: 2px;
}

.section-desc {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 20px;
  margin-top: -10px;
}

.progress-matrix-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 24px;
}

.progress-matrix-header h4 {
  margin-bottom: 6px;
  font-size: 18px;
  color: var(--text-primary);
}

.progress-matrix-header p {
  color: var(--text-secondary);
  font-size: 14px;
}

.progress-matrix-table th,
.progress-matrix-table td {
  text-align: center;
  white-space: nowrap;
}

.progress-matrix-table td:first-child,
.progress-matrix-table th:first-child {
  text-align: left;
  position: sticky;
  left: 0;
  background: #fff;
  z-index: 1;
}

.progress-summary-cell {
  font-weight: 600;
  color: var(--text-primary);
}

@media (max-width: 768px) {
  .section.two-column {
    grid-template-columns: 1fr;
  }
}

.section h3 {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.section h3 svg {
  width: 20px;
  height: 20px;
  color: var(--primary-color);
}

.info-section {
  background: #fff;
  border-radius: var(--radius-lg);
  padding: 24px;
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f5f5f5;
}

.info-item:last-child {
  border-bottom: none;
}

.info-label {
  font-size: 14px;
  color: var(--text-secondary);
}

.info-value {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.status-badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 14px;
  border-radius: 100px;
  font-size: 13px;
  font-weight: 500;
  background: #f5f5f5;
  color: var(--text-secondary);
}

.status-badge.active {
  background: #f6ffed;
  color: #52c41a;
}

.qr-card {
  background: linear-gradient(135deg, #f6ffed 0%, #fff 100%);
  border-radius: var(--radius-lg);
  padding: 24px;
  border: 1px solid #d9f7be;
}

.qr-card h3 {
  border-bottom-color: #d9f7be;
}

.qr-wrapper {
  display: flex;
  justify-content: center;
  padding: 20px;
}

.mini-qr {
  width: 120px;
  height: 120px;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
}

.button-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.button-row.compact {
  justify-content: center;
}

.button-row.wrap {
  margin-top: 8px;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 20px;
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  border: none;
}

.btn svg {
  width: 16px;
  height: 16px;
}

.btn-primary {
  background: var(--primary-gradient);
  color: #fff;
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.3);
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(24, 144, 255, 0.4);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-outline {
  background: #fff;
  border: 1px solid #d9d9d9;
  color: var(--text-primary);
}

.btn-outline:hover {
  border-color: var(--primary-color);
  color: var(--primary-color);
  background: rgba(24, 144, 255, 0.02);
}

.btn-danger {
  background: #fff;
  border: 1px solid #ff4d4f;
  color: #ff4d4f;
}

.btn-danger:hover {
  background: #fff2f0;
}

.btn-success {
  background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);
  color: #fff;
  box-shadow: 0 4px 12px rgba(82, 196, 26, 0.3);
}

.btn-success:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(82, 196, 26, 0.4);
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group.full-width {
  grid-column: 1 / -1;
}

.form-group label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.form-group label .optional {
  font-weight: 400;
  color: var(--text-hint);
  margin-left: 4px;
}

.form-input,
.form-select,
.form-textarea {
  padding: 10px 14px;
  border: 1px solid #d9d9d9;
  border-radius: var(--radius-md);
  font-size: 14px;
  transition: all 0.3s;
  background: #fff;
}

.form-input:focus,
.form-select:focus,
.form-textarea:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(24, 144, 255, 0.1);
}

.form-textarea {
  min-height: 100px;
  resize: vertical;
  font-family: inherit;
}

.form-hint {
  font-size: 12px;
  color: var(--text-hint);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  padding: 8px 0;
}

.checkbox-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  accent-color: var(--primary-color);
}

.checkbox-text {
  font-size: 14px;
  color: var(--text-primary);
}

.color-picker-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}

.color-picker-wrapper input[type="color"] {
  width: 48px;
  height: 40px;
  border: 1px solid #d9d9d9;
  border-radius: var(--radius-md);
  cursor: pointer;
  padding: 2px;
}

.file-input-wrapper {
  position: relative;
}

.file-input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}

.file-input-text {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: #f5f5f5;
  border: 1px dashed #d9d9d9;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 14px;
  color: var(--text-secondary);
  transition: all 0.3s;
}

.file-input-text svg {
  width: 14px;
  height: 14px;
}

.file-input-text:hover {
  border-color: var(--primary-color);
  color: var(--primary-color);
  background: rgba(24, 144, 255, 0.02);
}

.file-label {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: #f5f5f5;
  border: 1px dashed #d9d9d9;
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 14px;
  color: var(--text-secondary);
  transition: all 0.3s;
}

.file-label:hover {
  border-color: var(--primary-color);
  color: var(--primary-color);
  background: rgba(24, 144, 255, 0.02);
}

.file-label svg {
  width: 16px;
  height: 16px;
}

.preview-image {
  max-width: 200px;
  max-height: 120px;
  border-radius: var(--radius-md);
  margin-top: 12px;
  box-shadow: var(--shadow-sm);
}

.message-box {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-radius: var(--radius-md);
  font-size: 14px;
  margin-top: 16px;
}

.message-box.success {
  background: #f6ffed;
  color: #52c41a;
  border: 1px solid #d9f7be;
}

.message-box.error {
  background: #fff2f0;
  color: #ff4d4f;
  border: 1px solid #ffccc7;
}

.message-box svg {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.judge-table-wrap {
  overflow-x: auto;
  border-radius: var(--radius-md);
  border: 1px solid #f0f0f0;
}

.judge-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.judge-table th,
.judge-table td {
  padding: 14px 16px;
  text-align: left;
  border-bottom: 1px solid #f0f0f0;
}

.judge-table th {
  background: #fafafa;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
}

.judge-table tbody tr:hover {
  background: #fafafa;
}

.judge-table tbody tr:last-child td {
  border-bottom: none;
}

.judge-name {
  font-weight: 500;
  color: var(--text-primary);
}

.judge-token {
  font-family: monospace;
  font-size: 12px;
  color: var(--text-secondary);
  background: #f5f5f5;
  padding: 2px 8px;
  border-radius: 4px;
}

.status-tag {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 100px;
  font-size: 12px;
  font-weight: 500;
}

.status-tag.active {
  background: #f6ffed;
  color: #52c41a;
}

.status-tag.inactive {
  background: #f5f5f5;
  color: var(--text-hint);
}

.action-btns {
  display: flex;
  gap: 8px;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  border-radius: var(--radius-sm);
  cursor: pointer;
  color: var(--text-secondary);
  transition: all 0.3s;
}

.action-btn svg {
  width: 16px;
  height: 16px;
}

.action-btn:hover {
  background: #f5f5f5;
  color: var(--primary-color);
}

.action-btn.qr:hover {
  background: #f6ffed;
  color: #52c41a;
}

.create-mode-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.mode-tab {
  padding: 8px 16px;
  border: 1px solid #d9d9d9;
  background: #fff;
  border-radius: var(--radius-md);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.mode-tab.active {
  background: var(--primary-gradient);
  color: #fff;
  border-color: transparent;
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.3);
}

.scores-table-wrap {
  overflow-x: auto;
  border-radius: var(--radius-md);
  border: 1px solid #f0f0f0;
}

.scores-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.scores-table th,
.scores-table td {
  padding: 12px;
  text-align: center;
  border-bottom: 1px solid #f0f0f0;
  white-space: nowrap;
}

.scores-table th {
  background: linear-gradient(180deg, #fafafa 0%, #f5f5f5 100%);
  font-weight: 600;
  color: var(--text-primary);
  position: sticky;
  top: 0;
}

.scores-table tbody tr:hover {
  background: #fafafa;
}

.scores-table tbody tr:last-child td {
  border-bottom: none;
}

.scores-table .participant-name {
  text-align: left;
  font-weight: 500;
}

.scores-table .final-score {
  font-weight: 700;
  color: var(--primary-color);
  font-size: 14px;
}

.scores-table .rank-1 {
  background: linear-gradient(135deg, #fffbe6 0%, #fff 100%);
}

.scores-table .rank-1 .final-score {
  color: #faad14;
}

.scores-table .rank-2 {
  background: linear-gradient(135deg, #f6ffed 0%, #fff 100%);
}

.scores-table .rank-2 .final-score {
  color: #52c41a;
}

.scores-table .rank-3 {
  background: linear-gradient(135deg, #e6f7ff 0%, #fff 100%);
}

.scores-table .rank-3 .final-score {
  color: var(--primary-color);
}

/* 成绩统计排名样式 */
.ranking-table {
  border-radius: var(--radius-md);
  overflow: hidden;
  min-width: 100%;
}

.ranking-table thead {
  position: sticky;
  top: 0;
  z-index: 2;
}

.ranking-table th {
  background: linear-gradient(180deg, #fafafa 0%, #f5f5f5 100%);
  font-weight: 600;
  color: var(--text-primary);
  padding: 14px 16px;
  text-align: center;
  border-bottom: 2px solid #e8e8e8;
  position: sticky;
  top: 0;
  z-index: 2;
}

.ranking-table td {
  padding: 16px;
  text-align: center;
  border-bottom: 1px solid #f0f0f0;
  transition: all 0.3s;
}

.ranking-table tbody tr {
  transition: all 0.3s;
}

.ranking-table tbody tr:hover {
  background: rgba(24, 144, 255, 0.03);
  transform: scale(1.01);
}

.ranking-table tbody tr.top-three {
  background: linear-gradient(135deg, #fffbe6 0%, #fff 50%, #f6ffed 100%);
}

.ranking-table tbody tr.top-three:hover {
  background: linear-gradient(135deg, #fff7d9 0%, #fff 50%, #e6f7d9 100%);
}

.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  font-weight: 700;
  font-size: 14px;
  background: #f5f5f5;
  color: var(--text-secondary);
  transition: all 0.3s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.rank-badge.gold {
  background: linear-gradient(135deg, #ffd700 0%, #ffb700 100%);
  color: #fff;
  box-shadow: 0 4px 12px rgba(255, 183, 0, 0.4);
  animation: glow-gold 2s ease-in-out infinite alternate;
}

.rank-badge.silver {
  background: linear-gradient(135deg, #c0c0c0 0%, #a0a0a0 100%);
  color: #fff;
  box-shadow: 0 4px 12px rgba(160, 160, 160, 0.4);
}

.rank-badge.bronze {
  background: linear-gradient(135deg, #cd7f32 0%, #b87333 100%);
  color: #fff;
  box-shadow: 0 4px 12px rgba(184, 115, 51, 0.4);
}

@keyframes glow-gold {
  from {
    box-shadow: 0 4px 12px rgba(255, 183, 0, 0.4);
  }
  to {
    box-shadow: 0 6px 20px rgba(255, 183, 0, 0.6);
  }
}

.score-highlight {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 60px;
  padding: 6px 12px;
  background: linear-gradient(135deg, #e6f7ff 0%, #bae7ff 100%);
  color: var(--primary-color);
  font-weight: 700;
  font-size: 15px;
  border-radius: var(--radius-md);
  box-shadow: 0 2px 6px rgba(24, 144, 255, 0.15);
}

.col-rank {
  width: 80px;
}

.col-score {
  width: 100px;
}

.col-count {
  width: 90px;
  color: var(--text-secondary);
  font-size: 13px;
}

/* 评委进度样式优化 */
.progress-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.progress-item:last-child {
  border-bottom: none;
}

.progress-name {
  min-width: 100px;
  font-weight: 500;
  color: var(--text-primary);
}

.progress-bar-wrap {
  flex: 1;
  height: 10px;
  background: #f0f0f0;
  border-radius: 5px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: var(--primary-gradient);
  border-radius: 5px;
  transition: width 0.5s ease;
}

.progress-count {
  min-width: 60px;
  text-align: right;
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
}

/* 统计规则文本样式 */
.rule-text {
  background: linear-gradient(135deg, #f6ffed 0%, #fff 100%);
  padding: 16px 20px;
  border-radius: var(--radius-md);
  border-left: 4px solid #52c41a;
  color: var(--text-primary);
  line-height: 1.8;
  font-size: 14px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-hint);
}

.empty-state svg {
  width: 64px;
  height: 64px;
  margin-bottom: 16px;
  opacity: 0.3;
}

.empty-state p {
  font-size: 14px;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  padding: 20px;
}

.modal-card {
  background: #fff;
  border-radius: var(--radius-lg);
  padding: 32px;
  max-width: 400px;
  width: 100%;
  position: relative;
  animation: modal-in 0.3s ease;
}

@keyframes modal-in {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.modal-close {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 32px;
  height: 32px;
  border: none;
  background: #f5f5f5;
  border-radius: var(--radius-md);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  transition: all 0.3s;
}

.modal-close svg {
  width: 18px;
  height: 18px;
}

.modal-close:hover {
  background: #ff4d4f;
  color: #fff;
}

.modal-card h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 20px;
  text-align: center;
}

.qr-image {
  width: 200px;
  height: 200px;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
}

.qr-url {
  font-size: 12px;
  color: var(--text-secondary);
  word-break: break-all;
  margin-top: 16px;
  padding: 12px;
  background: #f5f5f5;
  border-radius: var(--radius-md);
  text-align: center;
}

@media (max-width: 768px) {
  .admin-header {
    padding: 16px 20px;
  }

  .brand-text h1 {
    font-size: 16px;
  }

  .tab-nav {
    padding: 12px 20px;
  }

  .tab-btn {
    padding: 10px 14px;
    font-size: 13px;
  }

  .tab-content {
    padding: 20px;
  }

  .stat-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }

  .stat-card {
    padding: 16px;
  }

  .stat-icon {
    width: 40px;
    height: 40px;
  }

  .stat-number {
    font-size: 24px;
  }

  .section {
    padding: 16px;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }

  .button-row {
    flex-direction: column;
  }

  .switch-list.inline-switch-list {
    gap: 16px;
    align-items: flex-start;
  }

  .switch-list.inline-switch-list .switch-item {
    width: 100%;
  }

  .import-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .background-preview-frame {
    width: 100%;
    height: 140px;
  }

  .btn {
    width: 100%;
  }
}

/* ==================== 评委列表美化样式 ==================== */
.judge-display-cell {
  display: flex;
  align-items: center;
  gap: 16px;
}

.judge-display-cell strong {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.id-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 32px;
  height: 32px;
  padding: 0 10px;
  background: linear-gradient(135deg, #e6f7ff 0%, #bae7ff 100%);
  color: #1890ff;
  font-size: 13px;
  font-weight: 600;
  border-radius: 8px;
  box-shadow: 0 2px 6px rgba(24, 144, 255, 0.2);
}

/* 评委列表表格优化 */
.data-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}

.data-table thead th {
  padding: 18px 20px;
  font-weight: 600;
  color: var(--text-primary);
  background: linear-gradient(180deg, #fafafa 0%, #f5f5f5 100%);
  border-bottom: 2px solid #e8e8e8;
  font-size: 14px;
  white-space: nowrap;
}

.data-table tbody td {
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
  vertical-align: middle;
}

.data-table tbody tr {
  transition: all 0.25s ease;
}

.data-table tbody tr:hover {
  background: linear-gradient(
    90deg,
    rgba(24, 144, 255, 0.03) 0%,
    rgba(24, 144, 255, 0.06) 100%
  );
  transform: translateX(4px);
}

.data-table tbody tr:last-child td {
  border-bottom: none;
}

.data-table td .status-badge {
  transition: all 0.3s ease;
}

.data-table td .status-badge.active {
  background: linear-gradient(135deg, #f6ffed 0%, #d9f7be 100%);
  color: #52c41a;
  box-shadow: 0 2px 6px rgba(82, 196, 26, 0.2);
}

.data-table td .status-badge:not(.active) {
  background: linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 100%);
  color: #8c8c8c;
}

/* 链接单元格样式 */
.ellipsis-cell {
  max-width: 240px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--text-secondary);
  font-size: 13px;
  font-family: "Courier New", monospace;
  background: #fafafa;
  padding: 10px 14px;
  border-radius: 6px;
  border: 1px dashed #d9d9d9;
}

/* 迷你按钮样式优化 */
.mini-btn {
  padding: 8px 14px;
  font-size: 13px;
  border-radius: 6px;
  transition: all 0.25s ease;
}

.mini-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

/* 按钮行间距优化 */
.button-row.compact {
  gap: 10px;
}

/* ==================== 评委完成情况美化样式 ==================== */
.progress-matrix-section {
  background: linear-gradient(180deg, #fafbfc 0%, #fff 100%);
  border-radius: var(--radius-lg);
  padding: 20px;
  border: 1px solid #e8e8e8;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all 0.3s ease;
}

.progress-matrix-section:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  border-color: #d9d9d9;
}

.progress-matrix-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.progress-matrix-header h4 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-matrix-header h4::before {
  content: "";
  width: 4px;
  height: 18px;
  background: linear-gradient(180deg, #1890ff 0%, #36cfc9 100%);
  border-radius: 2px;
}

.progress-matrix-header p {
  color: var(--text-secondary);
  font-size: 13px;
  margin: 4px 0 0 0;
}

/* 表格容器滚动样式 */
.table-wrap {
  overflow: auto;
  max-height: 500px;
  border-radius: var(--radius-md);
  border: 1px solid #f0f0f0;
}

/* 确保sticky定位在滚动容器中生效 */
.table-wrap table {
  position: relative;
}

/* 进度矩阵表格样式 */
.progress-matrix-table {
  border-collapse: separate;
  border-spacing: 0;
  min-width: 100%;
}

.progress-matrix-table thead {
  background: linear-gradient(180deg, #fafafa 0%, #f5f5f5 100%);
}

.progress-matrix-table th {
  padding: 14px 10px;
  font-weight: 600;
  color: var(--text-primary);
  font-size: 13px;
  border-bottom: 2px solid #e8e8e8;
  text-align: center;
  background: linear-gradient(180deg, #fafafa 0%, #f5f5f5 100%);
  position: sticky;
  top: 0;
  z-index: 10;
}

.progress-matrix-table th:first-child {
  text-align: left;
  padding-left: 16px;
  background: linear-gradient(90deg, #f0f0f0 0%, #e8e8e8 100%);
  left: 0;
  z-index: 11;
}

.progress-matrix-table td {
  padding: 12px 10px;
  border-bottom: 1px solid #f5f5f5;
  text-align: center;
  transition: all 0.2s ease;
  background: #fff;
}

.progress-matrix-table td:first-child {
  text-align: left;
  padding-left: 16px;
  font-weight: 500;
  background: linear-gradient(90deg, #fafafa 0%, #f5f5f5 100%);
  position: sticky;
  left: 0;
  z-index: 5;
  box-shadow: 2px 0 4px rgba(0, 0, 0, 0.05);
}

.progress-matrix-table tbody tr:hover td {
  background: rgba(24, 144, 255, 0.02);
}

.progress-matrix-table tbody tr:hover td:first-child {
  background: linear-gradient(90deg, #e6f7ff 0%, #f0f8ff 100%);
}

/* 状态徽章样式优化 */
.progress-matrix-table .status-badge {
  padding: 4px 10px;
  font-size: 11px;
  font-weight: 500;
  border-radius: 100px;
  transition: all 0.3s ease;
}

.progress-matrix-table .status-badge.active {
  background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);
  color: #fff;
  box-shadow: 0 2px 6px rgba(82, 196, 26, 0.3);
}

.progress-matrix-table .status-badge:not(.active) {
  background: linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 100%);
  color: #8c8c8c;
}

/* 进度汇总单元格 */
.progress-summary-cell {
  font-weight: 600;
  color: var(--text-primary);
  background: linear-gradient(135deg, #fff7e6 0%, #fff 50%, #f6ffed 100%);
  border-left: 2px solid #ffd591;
  min-width: 180px;
}

.progress-summary-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.progress-fraction {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
}

/* 完成度进度条 */
.progress-bar-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-bar {
  flex: 1;
  height: 8px;
  background: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
  position: relative;
}

.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #52c41a 0%, #389e0d 100%);
  border-radius: 4px;
  transition: width 0.5s ease;
  box-shadow: 0 0 8px rgba(82, 196, 26, 0.3);
}

.progress-bar-fill.partial {
  background: linear-gradient(90deg, #faad14 0%, #ffc53d 100%);
  box-shadow: 0 0 8px rgba(250, 173, 20, 0.3);
}

.progress-bar-fill.low {
  background: linear-gradient(90deg, #ff4d4f 0%, #ff7875 100%);
  box-shadow: 0 0 8px rgba(255, 77, 79, 0.3);
}

.progress-text {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  min-width: 40px;
  text-align: right;
}

/* 评委名称样式 */
.judge-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.judge-name-cell::before {
  content: "";
  width: 8px;
  height: 8px;
  background: linear-gradient(135deg, #1890ff 0%, #36cfc9 100%);
  border-radius: 50%;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

/* 选手名称表头样式 */
.progress-matrix-table th:not(:first-child):not(:last-child) {
  background: linear-gradient(180deg, #f0f5ff 0%, #e6f0ff 100%);
  color: #1890ff;
  font-weight: 500;
}

/* ==================== 删除评委弹窗样式 ==================== */
.delete-modal {
  max-width: 420px;
  padding: 32px;
}

.delete-modal-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 24px;
}

.delete-warning-icon {
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, #fff2f0 0%, #ffccc7 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
  box-shadow: 0 4px 12px rgba(255, 77, 79, 0.2);
}

.delete-warning-icon svg {
  width: 32px;
  height: 32px;
  color: #ff4d4f;
}

.delete-modal-header h3 {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
}

.delete-modal-content {
  margin-bottom: 24px;
}

.delete-warning-text {
  font-size: 15px;
  color: var(--text-primary);
  text-align: center;
  margin-bottom: 12px;
  line-height: 1.6;
}

.delete-warning-text strong {
  color: #ff4d4f;
  font-weight: 600;
}

.delete-hint-text {
  font-size: 13px;
  color: var(--text-secondary);
  text-align: center;
  margin-bottom: 24px;
  padding: 12px 16px;
  background: #fafafa;
  border-radius: var(--radius-md);
  border-left: 3px solid #ff4d4f;
}

.delete-password-section {
  margin-top: 20px;
}

.delete-password-section .form-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.delete-password-section .form-field span {
  font-size: 14px;
  color: var(--text-secondary);
}

.delete-password-section .form-field code {
  background: #fff2f0;
  color: #ff4d4f;
  padding: 2px 8px;
  border-radius: 4px;
  font-family: "Courier New", monospace;
  font-weight: 600;
}

.delete-password-section .input {
  padding: 12px 16px;
  border: 1px solid #d9d9d9;
  border-radius: var(--radius-md);
  font-size: 14px;
  transition: all 0.3s;
}

.delete-password-section .input:focus {
  border-color: #ff4d4f;
  box-shadow: 0 0 0 3px rgba(255, 77, 79, 0.1);
  outline: none;
}

.delete-actions {
  gap: 12px;
}

.delete-actions .btn {
  flex: 1;
  padding: 12px 24px;
}

.delete-actions .btn-danger {
  background: linear-gradient(135deg, #ff4d4f 0%, #ff7875 100%);
  box-shadow: 0 4px 12px rgba(255, 77, 79, 0.3);
}

.delete-actions .btn-danger:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(255, 77, 79, 0.4);
}

.delete-actions .btn-danger:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background: #d9d9d9;
}
</style>
