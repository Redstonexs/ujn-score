import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import API, { resolveAssetUrl } from '@/config/api'

export interface SiteConfig {
  site_name: string
  primary_color: string
  score_min: number
  score_max: number
  score_value_type: 'integer' | 'decimal' | 'integer_decimal'
  allow_duplicate_scores: boolean
  allow_scoring: boolean
  exclude_extreme_scores: boolean
  background_image: string | null
  logo_image: string | null
}

export interface Category {
  id: number
  name: string
  order: number
  description: string
  participant_count: number
}

export interface Participant {
  id: number
  name: string
  category_id: number
  category_name: string
  order: number
  description: string
  photo: string | null
}

export interface JudgeInfo {
  judge_id: number
  judge_name: string
  token: string
  submitted_categories: number[]
  submitted_scores: Record<number, Record<number, number>>
}

export const useScoringStore = defineStore('scoring', () => {
  // 站点配置
  const siteConfig = ref<SiteConfig | null>(null)

  // 评委信息
  const judgeInfo = ref<JudgeInfo | null>(null)

  // 类别列表
  const categories = ref<Category[]>([])

  // 参赛者列表
  const participants = ref<Participant[]>([])

  // 本地评分缓存
  const localScores = ref<Record<number, Record<number, number>>>({}) // {category_id: {participant_id: score}}

  // 已提交的类别（从服务端获取 + 本次会话提交）
  const submittedCategories = ref<number[]>([])

  // 加载状态
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 管理员状态
  const isAdmin = ref(false)
  const adminPassword = ref('')

  // 获取站点配置
  async function fetchSiteConfig() {
    try {
      const res = await fetch(API.config)
      const data = await res.json()
      siteConfig.value = {
        ...data,
        background_image: resolveAssetUrl(data.background_image),
        logo_image: resolveAssetUrl(data.logo_image),
      }
    } catch (e: any) {
      console.error('获取站点配置失败:', e)
    }
  }

  async function syncJudgeState(token: string, restoreScores = true) {
    const res = await fetch(API.judgeAuth(token))
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.error || '认证失败')
    }
    const data = await res.json()
    const submittedScores = normalizeSubmittedScores(data.submitted_scores)
    judgeInfo.value = {
      judge_id: data.judge_id,
      judge_name: data.judge_name,
      token,
      submitted_categories: data.submitted_categories,
      submitted_scores: submittedScores,
    }
    submittedCategories.value = Array.isArray(data.submitted_categories) ? data.submitted_categories : []

    if (restoreScores) {
      restoreLocalScores(token)
      mergeSubmittedScores(submittedScores)
    }
  }

  // 评委认证
  async function authenticateJudge(token: string) {
    loading.value = true
    error.value = null
    try {
      await syncJudgeState(token, true)
    } catch (e: any) {
      error.value = e.message
      judgeInfo.value = null
      throw e
    } finally {
      loading.value = false
    }
  }

  async function refreshJudgeState(token?: string) {
    const judgeToken = token || judgeInfo.value?.token
    if (!judgeToken) return
    try {
      await syncJudgeState(judgeToken, true)
    } catch (e: any) {
      error.value = e.message
      throw e
    }
  }

  // 获取类别列表
  async function fetchCategories() {
    try {
      const res = await fetch(API.categories)
      const data = await res.json()
      categories.value = data.categories
    } catch (e: any) {
      console.error('获取类别失败:', e)
    }
  }

  // 获取参赛者列表
  async function fetchParticipants(categoryId?: number) {
    try {
      let url = API.participants
      if (categoryId) url += `?category_id=${categoryId}`
      const res = await fetch(url)
      const data = await res.json()
      participants.value = (data.participants || []).map((participant: Participant) => ({
        ...participant,
        photo: resolveAssetUrl(participant.photo),
      }))
    } catch (e: any) {
      console.error('获取参赛者失败:', e)
    }
  }

  // 设置评分
  function setScore(categoryId: number, participantId: number, score: number) {
    if (!localScores.value[categoryId]) {
      localScores.value[categoryId] = {}
    }
    localScores.value[categoryId][participantId] = score
    saveLocalScores()
  }

  // 获取某个选手的分数
  function getScore(categoryId: number, participantId: number): number | undefined {
    return localScores.value[categoryId]?.[participantId]
  }

  function clearScore(categoryId: number, participantId: number) {
    if (!localScores.value[categoryId]) return
    delete localScores.value[categoryId][participantId]
    if (Object.keys(localScores.value[categoryId]).length === 0) {
      delete localScores.value[categoryId]
    }
    saveLocalScores()
  }

  // 提交评分
  async function submitScores(categoryId: number) {
    if (!judgeInfo.value) throw new Error('未认证')

    const catScores = localScores.value[categoryId]
    if (!catScores) throw new Error('没有评分数据')

    const scores = Object.entries(catScores).map(([pid, score]) => ({
      participant_id: parseInt(pid),
      score,
    }))

    const res = await fetch(API.submit, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        token: judgeInfo.value.token,
        category_id: categoryId,
        scores,
      }),
    })

    const data = await res.json()
    if (!res.ok) throw new Error(data.error || '提交失败')

    // 更新已提交类别
    if (!submittedCategories.value.includes(categoryId)) {
      submittedCategories.value.push(categoryId)
    }
    saveLocalScores()
    return data
  }

  function normalizeSubmittedScores(raw: unknown): Record<number, Record<number, number>> {
    if (!raw || typeof raw !== 'object') return {}
    const normalized: Record<number, Record<number, number>> = {}

    Object.entries(raw as Record<string, unknown>).forEach(([categoryId, participantMap]) => {
      const categoryKey = Number(categoryId)
      if (!Number.isInteger(categoryKey) || !participantMap || typeof participantMap !== 'object') return

      const categoryScores: Record<number, number> = {}
      Object.entries(participantMap as Record<string, unknown>).forEach(([participantId, score]) => {
        const participantKey = Number(participantId)
        const numericScore = Number(score)
        if (!Number.isInteger(participantKey) || !Number.isFinite(numericScore)) return
        categoryScores[participantKey] = numericScore
      })

      if (Object.keys(categoryScores).length > 0) {
        normalized[categoryKey] = categoryScores
      }
    })

    return normalized
  }

  function mergeSubmittedScores(submittedScores: Record<number, Record<number, number>>) {
    Object.entries(submittedScores).forEach(([categoryId, participantScores]) => {
      const categoryKey = Number(categoryId)
      localScores.value[categoryKey] = {
        ...(localScores.value[categoryKey] || {}),
        ...participantScores,
      }
    })
    saveLocalScores()
  }

  // 本地缓存操作
  function saveLocalScores() {
    if (!judgeInfo.value) return
    const key = `scoring_${judgeInfo.value.token}`
    localStorage.setItem(key, JSON.stringify({
      scores: localScores.value,
    }))
  }

  function restoreLocalScores(token: string) {
    const key = `scoring_${token}`
    const saved = localStorage.getItem(key)
    if (saved) {
      try {
        const data = JSON.parse(saved)
        localScores.value = data.scores || {}
      } catch {
        // ignore
      }
    }
  }

  // 判断类别是否已提交
  function isCategorySubmitted(categoryId: number): boolean {
    return submittedCategories.value.includes(categoryId)
  }

  // 管理员验证
  async function verifyAdmin(password: string) {
    const res = await fetch(API.adminVerify, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password }),
    })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.error || '验证失败')
    }
    isAdmin.value = true
    adminPassword.value = password
    return true
  }

  // 重置
  function reset() {
    judgeInfo.value = null
    localScores.value = {}
    submittedCategories.value = []
    error.value = null
    isAdmin.value = false
    adminPassword.value = ''
  }

  return {
    siteConfig,
    judgeInfo,
    categories,
    participants,
    localScores,
    submittedCategories,
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
    submitScores,
    refreshJudgeState,
    isCategorySubmitted,
    verifyAdmin,
    reset,
  }
})