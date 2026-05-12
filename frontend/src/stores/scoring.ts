import { defineStore } from "pinia";
import { ref, computed } from "vue";
import API, { resolveAssetUrl } from "@/config/api";

export interface SiteConfig {
  site_name: string;
  primary_color: string;
  score_min: number;
  score_max: number;
  score_value_type: "integer" | "decimal" | "integer_decimal";
  allow_duplicate_scores: boolean;
  allow_scoring: boolean;
  exclude_extreme_scores: boolean;
  exclude_lowest_count: number;
  exclude_highest_count: number;
  background_image: string | null;
  logo_image: string | null;
  scoring_mode: "score" | "vote";
  vote_total_count: number;
  vote_select_count: number;
}

export interface Category {
  id: number;
  name: string;
  order: number;
  description: string;
  participant_count: number;
  scoring_mode: "default" | "score" | "vote";
  vote_total_count?: number | null;
  vote_select_count?: number | null;
  score_min?: number | null;
  score_max?: number | null;
  score_value_type?: "integer" | "decimal" | "integer_decimal" | null;
  allow_duplicate_scores?: boolean | null;
  exclude_extreme_scores?: boolean | null;
  exclude_lowest_count?: number | null;
  exclude_highest_count?: number | null;
}

export interface Participant {
  id: number;
  name: string;
  category_id: number;
  category_name: string;
  order: number;
  description: string;
  photo: string | null;
  college?: string;
}

export interface JudgeInfo {
  judge_id: number;
  judge_name: string;
  token: string;
  allowed_category_ids: number[];
  all_categories_allowed: boolean;
  submitted_categories: number[];
  submitted_scores: Record<number, Record<number, number>>;
  submitted_votes: Record<number, number[]>;
}

export const useScoringStore = defineStore("scoring", () => {
  // 站点配置
  const siteConfig = ref<SiteConfig | null>(null);

  // 评委信息
  const judgeInfo = ref<JudgeInfo | null>(null);

  // 类别列表
  const categories = ref<Category[]>([]);

  // 参赛者列表
  const participants = ref<Participant[]>([]);

  // 本地评分缓存
  const localScores = ref<Record<number, Record<number, number>>>({}); // {category_id: {participant_id: score}}

  // 本地投票缓存
  const localVotes = ref<Record<number, number[]>>({}); // {category_id: [participant_id_1, participant_id_2, ...]}

  // 已提交的类别（从服务端获取 + 本次会话提交）
  const submittedCategories = ref<number[]>([]);

  // 服务端已提交记录，切换设备后以此为准
  const submittedScoreRecords = ref<Record<number, Record<number, number>>>({});
  const submittedVoteRecords = ref<Record<number, number[]>>({});

  // 加载状态
  const loading = ref(false);
  const error = ref<string | null>(null);

  // 管理员状态
  const isAdmin = ref(false);
  const adminPassword = ref("");

  // 获取站点配置
  async function fetchSiteConfig() {
    try {
      const res = await fetch(API.config);
      const data = await res.json();
      siteConfig.value = {
        ...data,
        background_image: resolveAssetUrl(data.background_image),
        logo_image: resolveAssetUrl(data.logo_image),
      };
    } catch (e: any) {
      console.error("获取站点配置失败:", e);
    }
  }

  async function syncJudgeState(token: string, restoreScores = true) {
    const res = await fetch(API.judgeAuth(token));
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || "认证失败");
    }
    const data = await res.json();
    const submittedScores = normalizeSubmittedScores(data.submitted_scores);
    const submittedVotes = normalizeSubmittedVotes(data.submitted_votes);
    const submittedCategoryIds = normalizeCategoryIds(data.submitted_categories);
    judgeInfo.value = {
      judge_id: data.judge_id,
      judge_name: data.judge_name,
      token,
      allowed_category_ids: normalizeCategoryIds(data.allowed_category_ids),
      all_categories_allowed: Boolean(data.all_categories_allowed),
      submitted_categories: submittedCategoryIds,
      submitted_scores: submittedScores,
      submitted_votes: submittedVotes,
    };
    submittedCategories.value = submittedCategoryIds;
    submittedScoreRecords.value = submittedScores;
    submittedVoteRecords.value = submittedVotes;

    if (restoreScores) {
      restoreLocalScores(token);
      mergeSubmittedScores(submittedScores);
      mergeSubmittedVotes(submittedVotes);
    }
  }

  // 评委认证
  async function authenticateJudge(token: string) {
    loading.value = true;
    error.value = null;
    try {
      await syncJudgeState(token, true);
    } catch (e: any) {
      error.value = e.message;
      judgeInfo.value = null;
      throw e;
    } finally {
      loading.value = false;
    }
  }

  async function refreshJudgeState(token?: string) {
    const judgeToken = token || judgeInfo.value?.token;
    if (!judgeToken) return;
    try {
      await syncJudgeState(judgeToken, true);
    } catch (e: any) {
      error.value = e.message;
      throw e;
    }
  }

  // 获取类别列表
  async function fetchCategories(token?: string) {
    try {
      const url = token
        ? `${API.categories}?token=${encodeURIComponent(token)}`
        : API.categories;
      const res = await fetch(url);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "获取类别失败");
      categories.value = data.categories;
    } catch (e: any) {
      console.error("获取类别失败:", e);
      throw e;
    }
  }

  // 获取参赛者列表
  async function fetchParticipants(categoryId?: number, token?: string) {
    try {
      const params = new URLSearchParams();
      if (categoryId) params.set("category_id", String(categoryId));
      if (token) params.set("token", token);
      const query = params.toString();
      const url = query ? `${API.participants}?${query}` : API.participants;
      const res = await fetch(url);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "获取参赛者失败");
      participants.value = (data.participants || []).map(
        (participant: Participant) => ({
          ...participant,
          photo: resolveAssetUrl(participant.photo),
        }),
      );
    } catch (e: any) {
      console.error("获取参赛者失败:", e);
      throw e;
    }
  }

  // 设置评分
  function setScore(categoryId: number, participantId: number, score: number) {
    if (!localScores.value[categoryId]) {
      localScores.value[categoryId] = {};
    }
    localScores.value[categoryId][participantId] = score;
    saveLocalScores();
  }

  // 获取某个选手的分数
  function getScore(
    categoryId: number,
    participantId: number,
  ): number | undefined {
    return localScores.value[categoryId]?.[participantId];
  }

  function clearScore(categoryId: number, participantId: number) {
    if (!localScores.value[categoryId]) return;
    delete localScores.value[categoryId][participantId];
    if (Object.keys(localScores.value[categoryId]).length === 0) {
      delete localScores.value[categoryId];
    }
    saveLocalScores();
  }

  // 投票相关
  function getVotes(categoryId: number): number[] {
    return localVotes.value[categoryId] || [];
  }

  function isVoted(categoryId: number, participantId: number): boolean {
    return getVotes(categoryId).includes(participantId);
  }

  function toggleVote(categoryId: number, participantId: number) {
    if (!localVotes.value[categoryId]) {
      localVotes.value[categoryId] = [];
    }

    const index = localVotes.value[categoryId].indexOf(participantId);
    if (index === -1) {
      localVotes.value[categoryId].push(participantId);
    } else {
      localVotes.value[categoryId].splice(index, 1);
    }
    saveLocalScores();
  }

  function setVotes(categoryId: number, participantIds: number[]) {
    localVotes.value[categoryId] = [...participantIds];
    saveLocalScores();
  }

  function clearVotes(categoryId: number) {
    delete localVotes.value[categoryId];
    saveLocalScores();
  }

  // 提交投票
  async function submitVotes(categoryId: number) {
    if (!judgeInfo.value) throw new Error("未认证");

    const votes = localVotes.value[categoryId];
    if (!votes || votes.length === 0) throw new Error("没有投票数据");

    const res = await fetch(API.submitVote, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        token: judgeInfo.value.token,
        category_id: categoryId,
        votes: votes.map((pid, idx) => ({
          participant_id: pid,
          vote_order: idx,
        })),
      }),
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "提交失败");

    applySubmittedState(data);
    // 更新已提交类别
    if (!submittedCategories.value.includes(categoryId)) {
      submittedCategories.value.push(categoryId);
    }
    saveLocalScores();
    return data;
  }

  // 提交评分
  async function submitScores(categoryId: number) {
    if (!judgeInfo.value) throw new Error("未认证");

    const catScores = localScores.value[categoryId];
    if (!catScores) throw new Error("没有评分数据");

    const scores = Object.entries(catScores).map(([pid, score]) => ({
      participant_id: parseInt(pid),
      score,
    }));

    const res = await fetch(API.submit, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        token: judgeInfo.value.token,
        category_id: categoryId,
        scores,
      }),
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "提交失败");

    applySubmittedState(data);
    // 更新已提交类别
    if (!submittedCategories.value.includes(categoryId)) {
      submittedCategories.value.push(categoryId);
    }
    saveLocalScores();
    return data;
  }

  function normalizeCategoryIds(raw: unknown): number[] {
    if (!Array.isArray(raw)) return [];
    return raw
      .map((categoryId) => Number(categoryId))
      .filter((categoryId) => Number.isInteger(categoryId));
  }

  function normalizeSubmittedScores(
    raw: unknown,
  ): Record<number, Record<number, number>> {
    if (!raw || typeof raw !== "object") return {};
    const normalized: Record<number, Record<number, number>> = {};

    Object.entries(raw as Record<string, unknown>).forEach(
      ([categoryId, participantMap]) => {
        const categoryKey = Number(categoryId);
        if (
          !Number.isInteger(categoryKey) ||
          !participantMap ||
          typeof participantMap !== "object"
        )
          return;

        const categoryScores: Record<number, number> = {};
        Object.entries(participantMap as Record<string, unknown>).forEach(
          ([participantId, score]) => {
            const participantKey = Number(participantId);
            const numericScore = Number(score);
            if (
              !Number.isInteger(participantKey) ||
              !Number.isFinite(numericScore)
            )
              return;
            categoryScores[participantKey] = numericScore;
          },
        );

        if (Object.keys(categoryScores).length > 0) {
          normalized[categoryKey] = categoryScores;
        }
      },
    );

    return normalized;
  }

  function normalizeSubmittedVotes(raw: unknown): Record<number, number[]> {
    if (!raw || typeof raw !== "object") return {};
    const normalized: Record<number, number[]> = {};

    Object.entries(raw as Record<string, unknown>).forEach(
      ([categoryId, votes]) => {
        const categoryKey = Number(categoryId);
        if (!Number.isInteger(categoryKey) || !Array.isArray(votes)) return;

        const voteItems = votes
          .map((vote, index) => {
            if (vote && typeof vote === "object") {
              const entry = vote as Record<string, unknown>;
              return {
                participantId: Number(entry.participant_id),
                order: Number(entry.vote_order ?? index),
              };
            }
            return { participantId: Number(vote), order: index };
          })
          .filter((vote) => Number.isInteger(vote.participantId))
          .sort((a, b) => a.order - b.order);

        if (voteItems.length > 0) {
          normalized[categoryKey] = voteItems.map((vote) => vote.participantId);
        }
      },
    );

    return normalized;
  }

  function mergeScoreRecords(
    current: Record<number, Record<number, number>>,
    incoming: Record<number, Record<number, number>>,
  ) {
    const merged: Record<number, Record<number, number>> = { ...current };
    Object.entries(incoming).forEach(([categoryId, participantScores]) => {
      const categoryKey = Number(categoryId);
      merged[categoryKey] = {
        ...(merged[categoryKey] || {}),
        ...participantScores,
      };
    });
    return merged;
  }

  function applySubmittedState(data: Record<string, unknown>) {
    const categoryIds = normalizeCategoryIds(data.submitted_categories);
    const serverScores = normalizeSubmittedScores(data.submitted_scores);
    const serverVotes = normalizeSubmittedVotes(data.submitted_votes);

    if (categoryIds.length > 0) {
      submittedCategories.value = categoryIds;
    }

    if (Object.keys(serverScores).length > 0) {
      submittedScoreRecords.value = mergeScoreRecords(
        submittedScoreRecords.value,
        serverScores,
      );
      if (judgeInfo.value) {
        judgeInfo.value.submitted_scores = submittedScoreRecords.value;
      }
      mergeSubmittedScores(serverScores);
    }

    if (Object.keys(serverVotes).length > 0) {
      submittedVoteRecords.value = {
        ...submittedVoteRecords.value,
        ...serverVotes,
      };
      if (judgeInfo.value) {
        judgeInfo.value.submitted_votes = submittedVoteRecords.value;
      }
      mergeSubmittedVotes(serverVotes);
    }
  }

  function mergeSubmittedScores(
    submittedScores: Record<number, Record<number, number>>,
  ) {
    Object.entries(submittedScores).forEach(
      ([categoryId, participantScores]) => {
        const categoryKey = Number(categoryId);
        localScores.value[categoryKey] = {
          ...(localScores.value[categoryKey] || {}),
          ...participantScores,
        };
      },
    );
    saveLocalScores();
  }

  function mergeSubmittedVotes(submittedVotes: Record<number, number[]>) {
    Object.entries(submittedVotes).forEach(([categoryId, participantIds]) => {
      const categoryKey = Number(categoryId);
      localVotes.value[categoryKey] = [...participantIds];
    });
    saveLocalScores();
  }

  // 本地缓存操作
  function saveLocalScores() {
    if (!judgeInfo.value) return;
    const key = `scoring_${judgeInfo.value.token}`;
    localStorage.setItem(
      key,
      JSON.stringify({
        scores: localScores.value,
        votes: localVotes.value,
      }),
    );
  }

  function restoreLocalScores(token: string) {
    const key = `scoring_${token}`;
    const saved = localStorage.getItem(key);
    if (saved) {
      try {
        const data = JSON.parse(saved);
        localScores.value = data.scores || {};
        localVotes.value = data.votes || {};
      } catch {
        // ignore
      }
    }
  }

  // 判断类别是否已提交
  function isCategorySubmitted(categoryId: number): boolean {
    return submittedCategories.value.includes(categoryId);
  }

  function getSubmittedScore(
    categoryId: number,
    participantId: number,
  ): number | undefined {
    return submittedScoreRecords.value[categoryId]?.[participantId];
  }

  function isSubmittedVote(categoryId: number, participantId: number): boolean {
    return (
      submittedVoteRecords.value[categoryId]?.includes(participantId) ?? false
    );
  }

  // 管理员验证
  async function verifyAdmin(password: string) {
    const res = await fetch(API.adminVerify, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password }),
    });
    if (!res.ok) {
      // 尝试解析 JSON 错误，如果失败则使用状态文本
      let errorMessage = "验证失败";
      try {
        const contentType = res.headers.get("content-type");
        if (contentType && contentType.includes("application/json")) {
          const err = await res.json();
          errorMessage = err.error || err.message || "验证失败";
        } else {
          errorMessage = res.statusText || `请求失败 (${res.status})`;
        }
      } catch {
        errorMessage = res.statusText || `请求失败 (${res.status})`;
      }
      throw new Error(errorMessage);
    }
    isAdmin.value = true;
    adminPassword.value = password;
    return true;
  }

  // 重置
  function reset() {
    judgeInfo.value = null;
    localScores.value = {};
    localVotes.value = {};
    submittedCategories.value = [];
    submittedScoreRecords.value = {};
    submittedVoteRecords.value = {};
    error.value = null;
    isAdmin.value = false;
    adminPassword.value = "";
  }

  return {
    siteConfig,
    judgeInfo,
    categories,
    participants,
    localScores,
    localVotes,
    submittedCategories,
    submittedScoreRecords,
    submittedVoteRecords,
    loading,
    error,
    isAdmin,
    adminPassword,
    fetchSiteConfig,
    authenticateJudge,
    fetchCategories,
    fetchParticipants,
    setScore,
    getScore,
    clearScore,
    getVotes,
    isVoted,
    toggleVote,
    setVotes,
    clearVotes,
    submitScores,
    submitVotes,
    refreshJudgeState,
    isCategorySubmitted,
    getSubmittedScore,
    isSubmittedVote,
    verifyAdmin,
    reset,
  };
});
