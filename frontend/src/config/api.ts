export const API_BASE_URL = "";
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
};

export default API;
