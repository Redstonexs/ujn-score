// 根据环境自动选择 API 基础 URL
// 生产环境：使用相对路径（前后端同域部署）
// 开发环境：使用空字符串，通过 Vite 代理转发到后端
export const API_BASE_URL = import.meta.env.PROD ? "" : "";
export function resolveAssetUrl(url?: string | null) {
  if (!url) return null;
  if (/^https?:\/\//i.test(url)) return url;
  if (url.startsWith("//")) return `${window.location.protocol}${url}`;
  if (url.startsWith("/")) return `${API_BASE_URL}${url}`;
  return `${API_BASE_URL}/${url.replace(/^\/+/, "")}`;
}

export const API = {
  // 公开接口
  config: `${API_BASE_URL}/api/config/`,
  categories: `${API_BASE_URL}/api/categories/`,
  participants: `${API_BASE_URL}/api/participants/`,

  // 评委接口
  judgeAuth: (token: string) => `${API_BASE_URL}/api/judge/${token}/auth/`,
  judgeQrcode: (token: string) => `${API_BASE_URL}/api/judge/${token}/qrcode/`,
  submit: `${API_BASE_URL}/api/submit/`,

  // 管理员接口
  adminVerify: `${API_BASE_URL}/api/admin/verify/`,
  adminConfig: `${API_BASE_URL}/api/admin/config/`,
  adminConfigUpdate: `${API_BASE_URL}/api/admin/config/update/`,
  adminQrcode: `${API_BASE_URL}/api/admin/qrcode/`,
  adminTemplate: `${API_BASE_URL}/api/admin/template/`,
  adminScores: `${API_BASE_URL}/api/admin/scores/`,
  adminExport: `${API_BASE_URL}/api/admin/export/`,
  adminClear: `${API_BASE_URL}/api/admin/clear/`,
  adminJudges: `${API_BASE_URL}/api/admin/judges/`,
  adminJudgesBatch: `${API_BASE_URL}/api/admin/judges/batch/`,
  adminJudgeQrcodesExport: `${API_BASE_URL}/api/admin/judges/qrcodes/export/`,
  adminImport: `${API_BASE_URL}/api/admin/import/`,
  adminJudgeDelete: (id: number) =>
    `${API_BASE_URL}/api/admin/judges/${id}/delete/`,
  // 选手管理接口
  adminParticipants: `${API_BASE_URL}/api/admin/participants/`,
  adminParticipantCreate: `${API_BASE_URL}/api/admin/participants/create/`,
  adminParticipantDelete: (id: number) =>
    `${API_BASE_URL}/api/admin/participants/${id}/delete/`,
  adminParticipantUpdate: (id: number) =>
    `${API_BASE_URL}/api/admin/participants/${id}/update/`,
  adminClearParticipants: `${API_BASE_URL}/api/admin/participants/clear/`,
  adminClearJudges: `${API_BASE_URL}/api/admin/judges/clear/`,
  // 类别管理接口
  adminCategoryCreate: `${API_BASE_URL}/api/admin/categories/create/`,
  adminCategoryUpdate: (id: number) =>
    `${API_BASE_URL}/api/admin/categories/${id}/update/`,
  adminCategoryDelete: (id: number) =>
    `${API_BASE_URL}/api/admin/categories/${id}/delete/`,
};

export default API;
