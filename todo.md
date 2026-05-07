# 仓库审查问题清单

## 安全问题

### 1. 数据库凭据硬编码在代码中
**文件**: `ujn/scoring_system/settings.py:87-99`
**严重程度**: 高
MySQL 数据库的用户名 `ujn`、密码 `ujn2026` 直接硬编码在 settings.py 中并提交到 Git 仓库。应使用环境变量或 `.env` 文件管理敏感配置。

### 2. Django SECRET_KEY 硬编码
**文件**: `ujn/scoring_system/settings.py:23`
**严重程度**: 高
`SECRET_KEY` 直接写死在代码中且已提交到版本库。生产环境应通过环境变量注入。

### 3. DEBUG = True 在 settings 中
**文件**: `ujn/scoring_system/settings.py:26,147`
**严重程度**: 高
DEBUG 模式开启且被重复设置（第26行和第147行）。生产环境必须关闭，否则会暴露敏感调试信息。

### 4. ALLOWED_HOSTS = ['*']
**文件**: `ujn/scoring_system/settings.py:28`
**严重程度**: 高
允许任意主机访问，存在 Host Header 攻击风险。生产环境应限制为实际域名。

### 5. CORS_ALLOW_ALL_ORIGINS = True
**文件**: `ujn/scoring_system/settings.py:30,146`
**严重程度**: 中
CORS 允许所有来源，且被重复设置（第30行和第146行）。生产环境应限制为前端域名。

### 6. 清空密码硬编码
**文件**: `ujn/scoring/views.py:20`
**严重程度**: 中
`CLEAR_SCORES_PASSWORD = 'jndx'` 硬编码在代码中。应存储在数据库或环境变量中。

### 7. 管理员密码明文存储
**文件**: `ujn/scoring/models.py:18`
**严重程度**: 中
`admin_password` 使用 CharField 明文存储，未做哈希处理。应使用 Django 的密码哈希机制。

### 8. 管理员密码通过 URL 参数传递
**文件**: `ujn/scoring/views.py:193,205`
**严重程度**: 中
`_verify_admin` 和 `get_admin_password_from_request` 从 GET 参数读取密码，密码会出现在 URL 和服务器日志中。应统一通过 POST body 或 Header 传递。

---

## 代码质量问题

### 9. settings.py 配置重复定义
**文件**: `ujn/scoring_system/settings.py:30,146` 和 `settings.py:26,147`
**严重程度**: 低
`CORS_ALLOW_ALL_ORIGINS` 和 `DEBUG` 各被定义了两次。

### 10. README 与实际配置不一致
**文件**: `README.md`
**严重程度**: 中
- README 声称使用 SQLite，但 settings.py 实际配置为 MySQL
- README 中部署路径写的是 `backend/`，但实际后端目录为 `ujn/`
- README 中 `docker-compose.yml` 引用 `./backend`，与实际目录结构不符

### 11. 后端目录存在无用的 package-lock.json
**文件**: `ujn/package-lock.json`
**严重程度**: 低
后端 Python 项目中存在一个空的 `package-lock.json` 文件，无任何用途，应删除。

### 12. get_admin_password_from_request 函数未使用
**文件**: `ujn/scoring/views.py:204-205`
**严重程度**: 低
`get_admin_password_from_request` 函数定义了但从未被调用，属于死代码。

### 13. 前端管理面板页面过于庞大
**文件**: `frontend/src/views/AdminDashboardView.vue`
**严重程度**: 中
单个 Vue 文件超过 5600 行，包含全部管理功能，难以维护。应拆分为多个子组件。

### 14. tests.py 为空
**文件**: `ujn/scoring/tests.py`
**严重程度**: 中
没有任何测试用例，无法保证代码质量和回归测试。

---

## 功能/设计问题

### 15. 删除评委/选手时未检查关联数据
**文件**: `ujn/scoring/views.py:696-712,1017-1033`
**严重程度**: 中
`delete_judge` 和 `delete_participant` 直接删除记录，未检查是否有关联的评分数据。删除后评分记录会因 CASCADE 被级联删除，可能导致数据丢失。

### 16. clear_participants 和 clear_judges 复用清空评分密码
**文件**: `ujn/scoring/views.py:1055,1082`
**严重程度**: 低
清空选手和清空评委都使用 `CLEAR_SCORES_PASSWORD`（评分清空密码），语义不清晰，应使用独立密码或统一为一个管理密码。

### 17. uwsgi.ini 中虚拟环境路径硬编码
**文件**: `ujn/uwsgi.ini:12`
**严重程度**: 低
`home = /root/miniconda3/envs/web` 硬编码了特定服务器的路径，不便于其他环境部署。

### 18. 评分提交缺少频率限制
**文件**: `ujn/scoring/views.py:352-435`
**严重程度**: 中
`submit_scores` 接口没有速率限制（rate limiting），可能被恶意频繁调用。

### 19. 生产环境媒体文件通过 Django serve 提供
**文件**: `ujn/scoring_system/urls.py:34-37`
**严重程度**: 中
非 DEBUG 模式下仍通过 Django 视图提供媒体文件，性能差。生产环境应由 Nginx 等 Web 服务器直接提供。

### 20. API 接口缺少 CSRF 保护
**文件**: `ujn/scoring/views.py`
**严重程度**: 中
多个 POST 接口使用 `@csrf_exempt` 装饰器禁用了 CSRF 保护。虽然前后端分离场景常见，但应确保有其他安全措施（如 Token 认证）替代。

### 21. 缺少 .env.example 或环境变量文档
**严重程度**: 中
项目没有提供 `.env.example` 文件说明需要哪些环境变量，增加了部署配置的难度。
