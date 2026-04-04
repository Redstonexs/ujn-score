# 路由路径对照表

## 前端路由

| 路径 | 页面 | 说明 |
|------|------|------|
| `/` | LandingView | 首页，显示系统名称和管理员入口 |
| `/judge/:token` | JudgeHomeView | 评委首页，显示类别列表和评分进度 |
| `/judge/:token/score/:categoryId` | ScoringView | 评分页面，为选手打分 |
| `/manage` | AdminLoginView | 管理员登录页 |
| `/manage/dashboard` | AdminDashboardView | 管理后台仪表盘 |
| `/*` | InvalidRouteView | 404页面 |

## 后端API路由

| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/config/` | GET | 获取站点公开配置 |
| `/api/categories/` | GET | 获取所有比赛类别 |
| `/api/participants/` | GET | 获取参赛选手列表 |
| `/api/judge/<token>/auth/` | GET | 评委身份认证 |
| `/api/judge/<token>/qrcode/` | GET | 获取评委二维码图片 |
| `/api/submit/` | POST | 提交评分 |
| `/api/admin/verify/` | POST | 管理员密码验证 |
| `/api/admin/scores/` | GET | 获取全部评分数据 |
| `/api/admin/export/` | GET | 导出Excel报表 |
| `/api/admin/clear/` | POST | 清空所有评分 |
| `/api/admin/judges/` | GET | 获取评委列表 |
| `/api/admin/judges/batch/` | POST | 批量创建评委 |
| `/api/admin/import/` | POST | 导入数据（JSON格式） |
| `/admin/` | Web | Django管理后台 |

## 评委链接格式

每个评委拥有唯一的UUID令牌，链接格式为：
```
{base_url}/judge/{uuid-token}
```
例如：`https://score.example.com/judge/d6c98e3e-c5e9-4802-b0fa-b2839eed6cfe`

评委链接和二维码可在：
1. Django Admin后台 → 评委管理 中查看
2. 前端管理面板 → 评委管理 中查看和下载