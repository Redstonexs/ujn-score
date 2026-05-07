<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { useScoringStore } from "@/stores/scoring";
import API, { resolveAssetUrl } from "@/config/api";
import { showAlert, showConfirm, showPrompt } from "@/utils/dialog";
import "./admin-dashboard/admin-dashboard.css";
import OverviewSection from "./admin-dashboard/sections/OverviewSection.vue";
import SettingsSection from "./admin-dashboard/sections/SettingsSection.vue";
import JudgesSection from "./admin-dashboard/sections/JudgesSection.vue";
import ScoresSection from "./admin-dashboard/sections/ScoresSection.vue";
import ParticipantsSection from "./admin-dashboard/sections/ParticipantsSection.vue";
import CategoriesSection from "./admin-dashboard/sections/CategoriesSection.vue";

type TabKey =
  | "overview"
  | "settings"
  | "judges"
  | "scores"
  | "participants"
  | "categories";

interface ParticipantRow {
  id: number;
  name: string;
  category_id: number;
  category_name: string;
  order: number;
  college?: string;
}

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
  college_field_name: string;
  scoring_mode: "score" | "vote";
  vote_total_count: number;
  vote_select_count: number;
}

interface JudgeRow {
  id: number;
  order: number;
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
const participants = ref<ParticipantRow[]>([]);
const scoresData = ref<any>(null);
const loadingConfig = ref(false);
const loadingJudges = ref(false);
const loadingParticipants = ref(false);
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

const createParticipantModalVisible = ref(false);
const createParticipantForm = reactive({
  name: "",
  category_id: 0,
  category_name: "",
  order: 0,
  college: "",
});

const importFile = ref<File | null>(null);
const backgroundFile = ref<File | null>(null);
const backgroundPreview = ref("");
const QR_FILENAME_PATTERN_STORAGE_KEY = "judge_qr_filename_pattern";
const judgeQrFilenamePattern = ref("{index}_{judge_display_name}");

const qrModalVisible = ref(false);
const qrTitle = ref("");
const qrImageUrl = ref("");
const qrTargetUrl = ref("");
const qrCurrentJudge = ref<JudgeRow | null>(null);

// 编辑评委弹窗相关
const editJudgeModalVisible = ref(false);
const editTargetJudge = ref<JudgeRow | null>(null);
const editJudgeForm = reactive({
  order: 1,
  name: "",
});
const editJudgeLoading = ref(false);

// 删除评委弹窗相关
const deleteJudgeModalVisible = ref(false);
const deleteTargetJudge = ref<JudgeRow | null>(null);
const deleteJudgeConfirmPassword = ref("");
const deleteJudgeLoading = ref(false);

// 删除选手弹窗相关
const deleteParticipantModalVisible = ref(false);
const deleteTargetParticipant = ref<ParticipantRow | null>(null);
const deleteParticipantConfirmPassword = ref("");
const deleteParticipantLoading = ref(false);

// 清空选手弹窗相关
const clearParticipantsModalVisible = ref(false);
const clearParticipantsConfirmPassword = ref("");
const clearParticipantsLoading = ref(false);

// 清空评委弹窗相关
const clearJudgesModalVisible = ref(false);
const clearJudgesConfirmPassword = ref("");
const clearJudgesLoading = ref(false);

// 清空类别弹窗相关
const clearCategoriesModalVisible = ref(false);
const clearCategoriesConfirmPassword = ref("");
const clearCategoriesLoading = ref(false);

// 选手编辑弹窗相关
const editParticipantModalVisible = ref(false);
const editTargetParticipant = ref<ParticipantRow | null>(null);
const editParticipantForm = reactive({
  name: "",
  category_id: 0,
  order: 0,
  college: "",
});
const editParticipantLoading = ref(false);
const useNewCategory = ref(false);

// 选手类别筛选
const participantCategoryFilter = ref<number | "">("");

// 选手列表排序相关
type ParticipantSortKey = "order" | null;
type SortOrder = "asc" | "desc";
const participantSortKey = ref<ParticipantSortKey>("order");
const participantSortOrder = ref<SortOrder>("asc");

// 成绩排名排序相关
type SortKey = "score" | "order" | null;
interface SortState {
  [categoryId: number]: {
    key: SortKey;
    order: SortOrder;
  };
}
const sortStates = reactive<SortState>({});

const DELETE_CONFIRM_PASSWORD = "jndx";

// 选手列表排序切换函数
function toggleParticipantSort() {
  if (participantSortKey.value === "order") {
    participantSortOrder.value =
      participantSortOrder.value === "asc" ? "desc" : "asc";
  } else {
    participantSortKey.value = "order";
    participantSortOrder.value = "asc";
  }
}

// 筛选后的选手列表
const filteredParticipants = computed(() => {
  const list =
    participantCategoryFilter.value === ""
      ? participants.value
      : participants.value.filter(
          (p) => p.category_id === participantCategoryFilter.value,
        );

  return [...list].sort((a, b) => {
    if (participantSortKey.value === "order") {
      const orderCompare =
        participantSortOrder.value === "asc"
          ? a.order - b.order
          : b.order - a.order;
      if (orderCompare !== 0) return orderCompare;
    }

    if (a.category_name !== b.category_name) {
      return a.category_name.localeCompare(b.category_name, "zh-CN");
    }
    return a.id - b.id;
  });
});

function getNextJudgeOrder() {
  const maxOrder = judges.value.reduce(
    (max, item) => Math.max(max, item.order || 0),
    0,
  );
  return maxOrder + 1;
}

function getNextCategoryOrder() {
  const maxOrder = store.categories.reduce(
    (max, item) => Math.max(max, Number(item.order) || 0),
    0,
  );
  return maxOrder + 1;
}

function getNextParticipantOrder(categoryId?: number) {
  if (!categoryId) return participants.value.length ? 1 : 1;
  const sameCategory = participants.value.filter(
    (item) => item.category_id === categoryId,
  );
  if (!sameCategory.length) return 1;
  const maxOrder = sameCategory.reduce(
    (max, item) => Math.max(max, item.order || 0),
    0,
  );
  return maxOrder + 1;
}

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
    college_field_name: "学院",
    scoring_mode: "score",
    vote_total_count: 10,
    vote_select_count: 3,
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

watch(
  () => createParticipantForm.category_id,
  (value) => {
    if (!createParticipantModalVisible.value || useNewCategory.value) return;
    createParticipantForm.order = getNextParticipantOrder(value);
  },
);

watch(useNewCategory, (value) => {
  if (!createParticipantModalVisible.value) return;
  createParticipantForm.order = value
    ? 1
    : getNextParticipantOrder(createParticipantForm.category_id);
});

onMounted(async () => {
  loadStoredJudgeQrPattern();
  if (!store.isAdmin) {
    router.push({ name: "adminLogin" });
    return;
  }
  await Promise.all([
    store.fetchCategories(),
    loadConfig(),
    loadJudges(),
    loadParticipants(),
  ]);
  connectSSE();
});

onUnmounted(() => {
  disconnectSSE();
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

async function loadParticipants() {
  loadingParticipants.value = true;
  try {
    const res = await fetch(
      `${API.adminParticipants}?password=${encodeURIComponent(store.adminPassword)}`,
    );
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "加载选手失败");
    participants.value = data.participants || [];
  } catch (error) {
    console.error(error);
  } finally {
    loadingParticipants.value = false;
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

// ==================== SSE 实时评分更新 ====================

type SSEStatus = "disconnected" | "connecting" | "connected";
const sseStatus = ref<SSEStatus>("disconnected");
let sseSource: EventSource | null = null;

function connectSSE() {
  disconnectSSE();
  sseStatus.value = "connecting";
  loadingScores.value = true;

  const url = `${API.adminScoresStream}?password=${encodeURIComponent(store.adminPassword)}`;
  const es = new EventSource(url);
  sseSource = es;

  es.addEventListener("init", (e: MessageEvent) => {
    try {
      scoresData.value = JSON.parse(e.data);
      sseStatus.value = "connected";
    } catch (err) {
      console.error("SSE init 解析失败:", err);
    } finally {
      loadingScores.value = false;
    }
  });

  es.addEventListener("update", (e: MessageEvent) => {
    try {
      scoresData.value = JSON.parse(e.data);
    } catch (err) {
      console.error("SSE update 解析失败:", err);
    }
  });

  es.addEventListener("error", (e: MessageEvent) => {
    try {
      const data = JSON.parse(e.data);
      console.error("SSE 服务端错误:", data.message);
    } catch {
      // non-JSON error event
    }
  });

  es.onerror = () => {
    // EventSource 会自动尝试重连
    if (es.readyState === EventSource.CLOSED) {
      sseStatus.value = "disconnected";
      loadingScores.value = false;
    } else {
      sseStatus.value = "connecting";
    }
  };
}

function disconnectSSE() {
  if (sseSource) {
    sseSource.close();
    sseSource = null;
  }
  sseStatus.value = "disconnected";
}

async function saveConfig() {
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
    formData.append("college_field_name", configForm.college_field_name);
    formData.append("scoring_mode", configForm.scoring_mode);
    formData.append("vote_total_count", String(configForm.vote_total_count));
    formData.append("vote_select_count", String(configForm.vote_select_count));
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
      await showAlert("请输入有效数量");
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
    await showAlert(`成功创建 ${data.count} 名评委`);
    await loadJudges();
  } catch (error: any) {
    await showAlert(error.message || "创建失败");
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
    college?: string;
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
    const college = parts[3] || undefined;

    if (!category || !name) {
      errors.push(`第 ${index + 1} 行类别或姓名为空`);
      return;
    }

    participants.push({ category, name, order, college });
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
  if (!(await showConfirm("确定要清空所有评分记录吗？此操作不可恢复。")))
    return;

  const clearPassword = await showPrompt("请输入清空评分密码：");
  if (clearPassword === null) return;
  if (!clearPassword.trim()) {
    await showAlert("请输入清空评分密码");
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
    await showAlert(data.message || data.error || "操作完成");
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

function handleExportScoreDetails() {
  window.open(
    `${API.adminExportDetails}?password=${encodeURIComponent(store.adminPassword)}`,
    "_blank",
  );
}

function handleExportParticipants() {
  window.open(
    `${API.adminExportParticipants}?password=${encodeURIComponent(store.adminPassword)}`,
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
  judge: JudgeRow | { id: number; name?: string; display_name?: string },
) {
  return judge.name || judge.display_name || `评委${judge.id}`;
}

function openQrModal(
  title: string,
  imageUrl: string,
  targetUrl: string,
  judge?: JudgeRow,
) {
  qrTitle.value = title;
  qrImageUrl.value = imageUrl;
  qrTargetUrl.value = targetUrl;
  qrCurrentJudge.value = judge || null;
  qrModalVisible.value = true;
}

function showJudgeQr(judge: JudgeRow) {
  openQrModal(
    `${judge.order}号 - ${getJudgeDisplayName(judge)} - 评委二维码`,
    API.judgeQrcode(judge.token),
    judge.scoring_url,
    judge,
  );
}

function showAdminQr() {
  openQrModal("管理员入口二维码", adminQrUrl.value, configForm.admin_url);
}

function closeQrModal() {
  qrModalVisible.value = false;
  qrCurrentJudge.value = null;
}

function formatQRFileName(pattern: string, index: number, name: string) {
  let fileName = pattern;
  fileName = fileName.replace(/{index}/g, String(index));
  fileName = fileName.replace(/{judge_name}/g, name);
  fileName = fileName.replace(/{judge_display_name}/g, name);
  fileName = fileName.replace(
    /{site_name}/g,
    configForm.site_name || "评分系统",
  );
  return fileName.endsWith(".png") ? fileName : `${fileName}.png`;
}

async function downloadCurrentQRCode() {
  try {
    let fileName = "二维码.png";

    if (qrCurrentJudge.value) {
      const index =
        qrCurrentJudge.value.order ||
        judges.value.indexOf(qrCurrentJudge.value) + 1;
      fileName = formatQRFileName(
        judgeQrFilenamePattern.value,
        index,
        qrCurrentJudge.value.name,
      );
    } else if (qrTitle.value === "管理员入口二维码") {
      fileName = "管理员二维码.png";
    }

    const link = document.createElement("a");
    link.href = qrImageUrl.value;
    link.download = fileName;
    link.click();

    await showAlert("下载成功");
  } catch {
    await showAlert("下载失败");
  }
}

function openEditJudgeModal(judge: JudgeRow) {
  editTargetJudge.value = judge;
  editJudgeForm.order = judge.order;
  editJudgeForm.name = judge.name;
  editJudgeModalVisible.value = true;
}

function closeEditJudgeModal() {
  editJudgeModalVisible.value = false;
  editTargetJudge.value = null;
  editJudgeForm.order = 1;
  editJudgeForm.name = "";
}

async function handleEditJudge() {
  if (!editTargetJudge.value) return;

  if (editJudgeForm.order <= 0) {
    await showAlert("请输入大于 0 的评委序号");
    return;
  }

  if (!editJudgeForm.name.trim()) {
    await showAlert("请输入评委名称");
    return;
  }

  editJudgeLoading.value = true;
  try {
    const res = await fetch(
      `${API.adminJudgeUpdate(editTargetJudge.value.id)}?password=${encodeURIComponent(store.adminPassword)}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          order: editJudgeForm.order,
          name: editJudgeForm.name.trim(),
        }),
      },
    );

    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "更新失败");

    await showAlert(data.message || "评委信息已更新");
    closeEditJudgeModal();
    await loadJudges();
  } catch (err: any) {
    await showAlert(err.message || "更新评委失败");
  } finally {
    editJudgeLoading.value = false;
  }
}

// 删除评委相关函数
function confirmDeleteJudge(judge: JudgeRow) {
  deleteTargetJudge.value = judge;
  deleteJudgeConfirmPassword.value = "";
  deleteJudgeModalVisible.value = true;
}

function closeDeleteJudgeModal() {
  deleteJudgeModalVisible.value = false;
  deleteTargetJudge.value = null;
  deleteJudgeConfirmPassword.value = "";
}

async function handleDeleteJudge() {
  if (!deleteTargetJudge.value) return;

  if (deleteJudgeConfirmPassword.value !== DELETE_CONFIRM_PASSWORD) {
    await showAlert("密码错误，请输入正确的确认密码");
    return;
  }

  deleteJudgeLoading.value = true;
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

    await showAlert("评委删除成功");
    closeDeleteJudgeModal();
    await loadJudges();
  } catch (err: any) {
    await showAlert(err.message || "删除评委失败");
  } finally {
    deleteJudgeLoading.value = false;
  }
}

// 删除选手相关函数
function confirmDeleteParticipant(participant: ParticipantRow) {
  deleteTargetParticipant.value = participant;
  deleteParticipantConfirmPassword.value = "";
  deleteParticipantModalVisible.value = true;
}

function closeDeleteParticipantModal() {
  deleteParticipantModalVisible.value = false;
  deleteTargetParticipant.value = null;
  deleteParticipantConfirmPassword.value = "";
}

async function handleDeleteParticipant() {
  if (!deleteTargetParticipant.value) return;

  if (deleteParticipantConfirmPassword.value !== DELETE_CONFIRM_PASSWORD) {
    await showAlert("密码错误，请输入正确的确认密码");
    return;
  }

  deleteParticipantLoading.value = true;
  try {
    const res = await fetch(
      `${API.adminParticipantDelete(deleteTargetParticipant.value.id)}?password=${encodeURIComponent(store.adminPassword)}`,
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

    await showAlert("选手删除成功");
    closeDeleteParticipantModal();
    await loadParticipants();
    await store.fetchCategories();
  } catch (err: any) {
    await showAlert(err.message || "删除选手失败");
  } finally {
    deleteParticipantLoading.value = false;
  }
}

// 清空选手相关函数
function confirmClearParticipants() {
  clearParticipantsConfirmPassword.value = "";
  clearParticipantsModalVisible.value = true;
}

function closeClearParticipantsModal() {
  clearParticipantsModalVisible.value = false;
  clearParticipantsConfirmPassword.value = "";
}

async function handleClearParticipants() {
  if (clearParticipantsConfirmPassword.value !== DELETE_CONFIRM_PASSWORD) {
    await showAlert("密码错误，请输入正确的确认密码");
    return;
  }

  clearParticipantsLoading.value = true;
  try {
    const res = await fetch(API.adminClearParticipants, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        password: store.adminPassword,
        clear_password: clearParticipantsConfirmPassword.value,
      }),
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "清空失败");

    await showAlert(data.message || "选手清空成功");
    closeClearParticipantsModal();
    await loadParticipants();
    await store.fetchCategories();
  } catch (err: any) {
    await showAlert(err.message || "清空选手失败");
  } finally {
    clearParticipantsLoading.value = false;
  }
}

// 清空评委相关函数
function confirmClearJudges() {
  clearJudgesConfirmPassword.value = "";
  clearJudgesModalVisible.value = true;
}

function closeClearJudgesModal() {
  clearJudgesModalVisible.value = false;
  clearJudgesConfirmPassword.value = "";
}

async function handleClearJudges() {
  if (clearJudgesConfirmPassword.value !== DELETE_CONFIRM_PASSWORD) {
    await showAlert("密码错误，请输入正确的确认密码");
    return;
  }

  clearJudgesLoading.value = true;
  try {
    const res = await fetch(API.adminClearJudges, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        password: store.adminPassword,
        clear_password: clearJudgesConfirmPassword.value,
      }),
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "清空失败");

    await showAlert(data.message || "评委清空成功");
    closeClearJudgesModal();
    await loadJudges();
  } catch (err: any) {
    await showAlert(err.message || "清空评委失败");
  } finally {
    clearJudgesLoading.value = false;
  }
}

// 清空类别相关函数
function confirmClearCategories() {
  clearCategoriesConfirmPassword.value = "";
  clearCategoriesModalVisible.value = true;
}

function closeClearCategoriesModal() {
  clearCategoriesModalVisible.value = false;
  clearCategoriesConfirmPassword.value = "";
}

async function handleClearCategories() {
  if (clearCategoriesConfirmPassword.value !== DELETE_CONFIRM_PASSWORD) {
    await showAlert("密码错误，请输入正确的确认密码");
    return;
  }

  clearCategoriesLoading.value = true;
  try {
    const res = await fetch(API.adminClearCategories, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        password: store.adminPassword,
        clear_password: clearCategoriesConfirmPassword.value,
      }),
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "清空失败");

    await showAlert(data.message || "类别清空成功");
    closeClearCategoriesModal();
    await store.fetchCategories();
  } catch (err: any) {
    await showAlert(err.message || "清空类别失败");
  } finally {
    clearCategoriesLoading.value = false;
  }
}

// 编辑选手相关函数
function openEditParticipantModal(participant: ParticipantRow) {
  editTargetParticipant.value = participant;
  editParticipantForm.name = participant.name;
  editParticipantForm.category_id = participant.category_id;
  editParticipantForm.order = participant.order;
  editParticipantForm.college = participant.college || "";
  editParticipantModalVisible.value = true;
}

function closeEditParticipantModal() {
  editParticipantModalVisible.value = false;
  editTargetParticipant.value = null;
  editParticipantForm.college = "";
  editParticipantForm.name = "";
  editParticipantForm.category_id = 0;
  editParticipantForm.order = 0;
}

async function handleEditParticipant() {
  if (!editTargetParticipant.value) return;

  if (!editParticipantForm.name.trim()) {
    await showAlert("请输入选手姓名");
    return;
  }

  editParticipantLoading.value = true;
  try {
    const res = await fetch(
      `${API.adminParticipantUpdate(editTargetParticipant.value.id)}?password=${encodeURIComponent(store.adminPassword)}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: editParticipantForm.name.trim(),
          category_id: editParticipantForm.category_id,
          order: editParticipantForm.order,
          college: editParticipantForm.college.trim(),
        }),
      },
    );

    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.error || "更新失败");
    }

    await showAlert("选手信息更新成功");
    closeEditParticipantModal();
    await loadParticipants();
    await store.fetchCategories();
  } catch (err: any) {
    await showAlert(err.message || "更新选手失败");
  } finally {
    editParticipantLoading.value = false;
  }
}

function copyLink(url: string) {
  navigator.clipboard
    .writeText(url)
    .then(() => {
      void showAlert("链接已复制");
    })
    .catch(() => {
      void showPrompt("请手动复制链接：", url);
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

function getJudgeVoteStatus(categoryId: number, judgeId: number) {
  // 投票模式：检查评委是否已完成投票
  const votes = scoresData.value?.votes?.[categoryId]?.[judgeId] || [];
  return votes.length > 0;
}

function getJudgeVoteCount(categoryId: number, judgeId: number) {
  // 获取评委在投票模式下的投票数量
  const votes = scoresData.value?.votes?.[categoryId]?.[judgeId] || [];
  return votes.length;
}

function getJudgeCategoryCompletedCount(category: any, judgeId: number) {
  // 投票模式
  if (category.mode === "vote") {
    return getJudgeVoteStatus(category.id, judgeId) ? 1 : 0;
  }
  // 打分模式
  const participants = category?.participants || [];
  return participants.filter((participant: any) =>
    getJudgeScoreStatus(category.id, judgeId, participant.id),
  ).length;
}

function getJudgeCategoryProgressPercent(category: any, judgeId: number) {
  // 投票模式：评委要么已完成（100%），要么未完成（0%）
  if (category.mode === "vote") {
    return getJudgeVoteStatus(category.id, judgeId) ? 100 : 0;
  }
  // 打分模式
  const total = category?.participants?.length || 0;
  if (!total) return 0;
  return Math.round(
    (getJudgeCategoryCompletedCount(category, judgeId) / total) * 100,
  );
}

function switchTab(tab: TabKey) {
  activeTab.value = tab;
  if (tab === "scores" && !scoresData.value && sseStatus.value !== "connected") {
    loadScores();
  }
  if (tab === "participants") {
    loadParticipants();
  }
}

function logout() {
  store.reset();
  router.push({ name: "adminLogin" });
}

// 类别管理相关
const editCategoryModalVisible = ref(false);
const editTargetCategory = ref<any>(null);
const editCategoryForm = reactive({
  name: "",
  order: 0,
  description: "",
});
const editCategoryLoading = ref(false);

const deleteCategoryModalVisible = ref(false);
const deleteTargetCategory = ref<any>(null);
const deleteCategoryConfirmPassword = ref("");
const deleteCategoryLoading = ref(false);

const createParticipantLoading = ref(false);

function openCreateParticipantModal() {
  createParticipantForm.name = "";
  createParticipantForm.category_id =
    store.categories.length > 0 && store.categories[0]
      ? store.categories[0].id
      : 0;
  createParticipantForm.category_name = "";
  createParticipantForm.order = getNextParticipantOrder(
    createParticipantForm.category_id,
  );
  createParticipantForm.college = "";
  useNewCategory.value = false;
  createParticipantModalVisible.value = true;
}

function closeCreateParticipantModal() {
  createParticipantModalVisible.value = false;
}

async function handleCreateParticipant() {
  if (!createParticipantForm.name.trim()) {
    await showAlert("请输入选手姓名");
    return;
  }

  if (useNewCategory.value && !createParticipantForm.category_name.trim()) {
    await showAlert("请输入新类别名称");
    return;
  }

  if (!useNewCategory.value && !createParticipantForm.category_id) {
    await showAlert("请选择类别");
    return;
  }

  createParticipantLoading.value = true;
  try {
    const body: any = {
      name: createParticipantForm.name.trim(),
      order: createParticipantForm.order,
      college: createParticipantForm.college.trim(),
    };

    if (useNewCategory.value) {
      body.category_name = createParticipantForm.category_name.trim();
    } else {
      body.category_id = createParticipantForm.category_id;
    }

    const res = await fetch(
      `${API.adminParticipantCreate}?password=${encodeURIComponent(store.adminPassword)}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      },
    );

    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.error || "创建失败");
    }

    await showAlert("选手创建成功");
    closeCreateParticipantModal();
    await loadParticipants();
    await store.fetchCategories();
  } catch (err: any) {
    await showAlert(err.message || "创建选手失败");
  } finally {
    createParticipantLoading.value = false;
  }
}

function openEditCategoryModal(category: any) {
  editTargetCategory.value = category;
  editCategoryForm.name = category.name;
  editCategoryForm.order = category.order;
  editCategoryForm.description = category.description || "";
  editCategoryModalVisible.value = true;
}

function closeEditCategoryModal() {
  editCategoryModalVisible.value = false;
  editTargetCategory.value = null;
  editCategoryForm.name = "";
  editCategoryForm.order = 0;
  editCategoryForm.description = "";
}

async function handleEditCategory() {
  if (!editTargetCategory.value) return;

  if (!editCategoryForm.name.trim()) {
    await showAlert("请输入类别名称");
    return;
  }

  editCategoryLoading.value = true;
  try {
    const res = await fetch(
      `${API.adminCategoryUpdate(editTargetCategory.value.id)}?password=${encodeURIComponent(store.adminPassword)}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: editCategoryForm.name.trim(),
          order: editCategoryForm.order,
          description: editCategoryForm.description.trim(),
        }),
      },
    );

    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.error || "更新失败");
    }

    await showAlert("类别信息更新成功");
    closeEditCategoryModal();
    await store.fetchCategories();
  } catch (err: any) {
    await showAlert(err.message || "更新类别失败");
  } finally {
    editCategoryLoading.value = false;
  }
}

const createCategoryModalVisible = ref(false);
const createCategoryForm = reactive({
  name: "",
  order: 0,
  description: "",
});
const createCategoryLoading = ref(false);

function openCreateCategoryModal() {
  createCategoryForm.name = "";
  createCategoryForm.order = getNextCategoryOrder();
  createCategoryForm.description = "";
  createCategoryModalVisible.value = true;
}

function closeCreateCategoryModal() {
  createCategoryModalVisible.value = false;
}

async function handleCreateCategory() {
  if (!createCategoryForm.name.trim()) {
    await showAlert("请输入类别名称");
    return;
  }

  createCategoryLoading.value = true;
  try {
    const res = await fetch(
      `${API.adminCategoryCreate}?password=${encodeURIComponent(store.adminPassword)}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: createCategoryForm.name.trim(),
          order: createCategoryForm.order,
          description: createCategoryForm.description.trim(),
        }),
      },
    );

    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.error || "创建失败");
    }

    await showAlert("类别创建成功");
    closeCreateCategoryModal();
    await store.fetchCategories();
  } catch (err: any) {
    await showAlert(err.message || "创建类别失败");
  } finally {
    createCategoryLoading.value = false;
  }
}

function confirmDeleteCategory(category: any) {
  deleteTargetCategory.value = category;
  deleteCategoryConfirmPassword.value = "";
  deleteCategoryModalVisible.value = true;
}

function closeDeleteCategoryModal() {
  deleteCategoryModalVisible.value = false;
  deleteTargetCategory.value = null;
  deleteCategoryConfirmPassword.value = "";
}

async function handleDeleteCategory() {
  if (!deleteTargetCategory.value) return;

  if (deleteCategoryConfirmPassword.value !== DELETE_CONFIRM_PASSWORD) {
    await showAlert("密码错误，请输入正确的确认密码");
    return;
  }

  deleteCategoryLoading.value = true;
  try {
    const res = await fetch(
      `${API.adminCategoryDelete(deleteTargetCategory.value.id)}?password=${encodeURIComponent(store.adminPassword)}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      },
    );

    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.error || "删除失败");
    }

    await showAlert("类别删除成功");
    closeDeleteCategoryModal();
    await store.fetchCategories();
    await loadParticipants();
  } catch (err: any) {
    await showAlert(err.message || "删除类别失败");
  } finally {
    deleteCategoryLoading.value = false;
  }
}

async function updateCategoryVoteSelectCount(
  categoryId: number,
  voteSelectCount: number | null,
) {
  try {
    const res = await fetch(
      `${API.adminCategoryUpdate(categoryId)}?password=${encodeURIComponent(store.adminPassword)}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ vote_select_count: voteSelectCount }),
      },
    );

    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.error || "更新失败");
    }

    await store.fetchCategories();
  } catch (err: any) {
    await showAlert(err.message || "更新类别选择人数失败");
  }
}

function openEditParticipantModalWithNewCategory(participant: ParticipantRow) {
  editTargetParticipant.value = participant;
  editParticipantForm.name = participant.name;
  editParticipantForm.category_id = participant.category_id;
  editParticipantForm.order = participant.order;
  editParticipantForm.college = participant.college || "";
  editParticipantModalVisible.value = true;
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

// 获取选手的得票率（投票模式）
function getParticipantVoteRate(categoryId: number, participantId: number) {
  const stats = scoresData.value?.statistics?.[categoryId] || [];
  const stat = stats.find((s: any) => s.participant_id === participantId);
  if (!stat) return "-";
  const totalVotes = stats.reduce(
    (sum: number, s: any) => sum + (s.vote_count || 0),
    0,
  );
  if (totalVotes === 0) return "0.00%";
  const rate = ((stat.vote_count || 0) / totalVotes) * 100;
  return `${rate.toFixed(2)}%`;
}

// 排序相关函数
function getSortState(categoryId: number) {
  return sortStates[categoryId] || { key: null, order: "desc" };
}

function toggleSort(categoryId: number, key: SortKey) {
  const current = getSortState(categoryId);
  if (current.key === key) {
    sortStates[categoryId] = {
      key,
      order: current.order === "asc" ? "desc" : "asc",
    };
  } else {
    sortStates[categoryId] = { key, order: key === "score" ? "desc" : "asc" };
  }
}

function getSortedParticipants(category: any) {
  const participants = category.participants || [];
  const sortState = getSortState(category.id);

  if (!sortState.key) return participants;

  return [...participants].sort((a, b) => {
    if (sortState.key === "order") {
      const orderA = a.order || 0;
      const orderB = b.order || 0;
      return sortState.order === "asc" ? orderA - orderB : orderB - orderA;
    }

    if (sortState.key === "score") {
      const statA = getParticipantStat(category.id, a.id);
      const statB = getParticipantStat(category.id, b.id);
      // 投票模式按票数排序，打分模式按总分排序
      const scoreA =
        category.mode === "vote"
          ? (statA?.vote_count ?? -Infinity)
          : (statA?.total ?? -Infinity);
      const scoreB =
        category.mode === "vote"
          ? (statB?.vote_count ?? -Infinity)
          : (statB?.total ?? -Infinity);
      return sortState.order === "asc" ? scoreA - scoreB : scoreB - scoreA;
    }

    return 0;
  });
}

const sectionCtx = {
  API,
  DELETE_CONFIRM_PASSWORD,
  QR_FILENAME_PATTERN_STORAGE_KEY,
  activeTab,
  adminQrUrl,
  backgroundFile,
  backgroundPreview,
  clearBackground,
  clearBackgroundRequested,
  clearCategoriesConfirmPassword,
  clearCategoriesLoading,
  clearCategoriesModalVisible,
  clearJudgesConfirmPassword,
  clearJudgesLoading,
  clearJudgesModalVisible,
  clearParticipantsConfirmPassword,
  clearParticipantsLoading,
  clearParticipantsModalVisible,
  closeClearCategoriesModal,
  closeClearJudgesModal,
  closeClearParticipantsModal,
  closeCreateCategoryModal,
  closeCreateParticipantModal,
  closeDeleteCategoryModal,
  closeDeleteJudgeModal,
  closeDeleteParticipantModal,
  closeEditCategoryModal,
  closeEditJudgeModal,
  closeEditParticipantModal,
  closeQrModal,
  configForm,
  confirmClearCategories,
  confirmClearJudges,
  confirmClearParticipants,
  confirmDeleteCategory,
  confirmDeleteJudge,
  confirmDeleteParticipant,
  copyLink,
  createCategoryForm,
  createCategoryLoading,
  createCategoryModalVisible,
  createDefaultConfig,
  createParticipantForm,
  createParticipantLoading,
  createParticipantModalVisible,
  deleteCategoryConfirmPassword,
  deleteCategoryLoading,
  deleteCategoryModalVisible,
  deleteJudgeConfirmPassword,
  deleteJudgeLoading,
  deleteJudgeModalVisible,
  deleteParticipantConfirmPassword,
  deleteParticipantLoading,
  deleteParticipantModalVisible,
  deleteTargetCategory,
  deleteTargetJudge,
  deleteTargetParticipant,
  downloadCurrentQRCode,
  downloadTemplate,
  editCategoryForm,
  editCategoryLoading,
  editCategoryModalVisible,
  editJudgeForm,
  editJudgeLoading,
  editJudgeModalVisible,
  editParticipantForm,
  editParticipantLoading,
  editParticipantModalVisible,
  editTargetCategory,
  editTargetJudge,
  editTargetParticipant,
  exportAllJudgeQrcodes,
  filteredParticipants,
  formatQRFileName,
  getJudgeCategoryCompletedCount,
  getJudgeCategoryProgressPercent,
  getJudgeDisplayName,
  getJudgeScoreStatus,
  getJudgeVoteCount,
  getJudgeVoteStatus,
  getNextCategoryOrder,
  getNextJudgeOrder,
  getNextParticipantOrder,
  getParticipantRank,
  getParticipantStat,
  getParticipantVoteRate,
  getSortState,
  getSortedParticipants,
  handleClearCategories,
  handleClearJudges,
  handleClearParticipants,
  handleClearScores,
  handleCreateCategory,
  handleCreateJudges,
  handleCreateParticipant,
  handleDeleteCategory,
  handleDeleteJudge,
  handleDeleteParticipant,
  handleEditCategory,
  handleEditJudge,
  handleEditParticipant,
  handleExport,
  handleExportParticipants,
  handleExportScoreDetails,
  handleImport,
  handleManualImport,
  importFile,
  importResult,
  importing,
  judgeQrFilenamePattern,
  judges,
  loadConfig,
  loadJudges,
  loadParticipants,
  loadScores,
  connectSSE,
  disconnectSSE,
  sseStatus,
  loadStoredJudgeQrPattern,
  loadingConfig,
  loadingJudges,
  loadingParticipants,
  loadingScores,
  logout,
  manualImportData,
  manualImportResult,
  manualImporting,
  newJudgeCount,
  onBackgroundChange,
  onImportFileChange,
  openCreateCategoryModal,
  openCreateParticipantModal,
  openEditCategoryModal,
  openEditJudgeModal,
  openEditParticipantModal,
  openEditParticipantModalWithNewCategory,
  openQrModal,
  participantCategoryFilter,
  participantSortKey,
  participantSortOrder,
  participants,
  qrCurrentJudge,
  qrImageUrl,
  qrModalVisible,
  qrTargetUrl,
  qrTitle,
  resolveAssetUrl,
  router,
  saveConfig,
  saveMessage,
  savingConfig,
  scoreRuleText,
  scoresData,
  showAdminQr,
  showAlert,
  showConfirm,
  showJudgeQr,
  showPrompt,
  sortStates,
  store,
  switchTab,
  toggleParticipantSort,
  toggleSort,
  updateCategoryVoteSelectCount,
  useNewCategory,
};
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
            key: 'participants',
            label: '选手管理',
            icon: 'M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2 M9 7a4 4 0 1 0 0-8 4 4 0 0 0 0 8z M23 21v-2a4 4 0 0 0-3-3.87 M16 3.13a4 4 0 0 1 0 7.75',
          },
          {
            key: 'categories',
            label: '类别管理',
            icon: 'M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5',
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

    <OverviewSection v-if="activeTab === 'overview'" :ctx="sectionCtx" />

    <SettingsSection v-if="activeTab === 'settings'" :ctx="sectionCtx" />

    <JudgesSection v-if="activeTab === 'judges'" :ctx="sectionCtx" />

    <ScoresSection v-if="activeTab === 'scores'" :ctx="sectionCtx" />

    <ParticipantsSection
      v-if="activeTab === 'participants'"
      :ctx="sectionCtx"
    />

    <CategoriesSection v-if="activeTab === 'categories'" :ctx="sectionCtx" />
  </div>
</template>
