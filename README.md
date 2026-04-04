# 评分系统

基于 Django + Vue 3 的在线评分系统，支持管理员后台配置、Excel 导入、二维码生成与可配置统计规则。

## 本次新增能力

- 管理员可在前端管理界面直接修改：
  - 活动标题
  - 背景图和 Logo 图
  - 评分范围（支持整数和小数）
  - 是否允许评分
  - 是否允许重复打分
  - 统计时是否去掉最高分和最低分
  - 管理密码
- Excel 导入更友好：
  - 支持直接上传 `.xlsx` 导入选手数据
  - 支持一键下载 Excel 模板
  - 支持自定义 Sheet 名称与字段名
- 二维码增强：
  - 生成管理员入口二维码
  - 生成评委专属评分二维码
  - 支持批量导出所有评委二维码（可自定义命名规则）
- 评委管理增强：
  - 支持按姓名列表批量创建评委
  - 支持按数量批量创建评委
- 成绩统计增强：
  - 支持按配置决定是否去掉最高分和最低分
  - 导出 Excel 时同时导出统计总分、原始总分、有效评委数等信息
- 安全增强：
  - 清空评分需要额外的清空密码验证

## 核心功能

- 🎨 **管理员配置**：通过 Django Admin 或前端管理面板设置活动标题、背景图、Logo 图、主题色、评分规则
- 👥 **评委管理**：动态创建评委，支持按姓名列表或数量批量创建，每个评委拥有唯一链接和二维码
- 📱 **二维码生成**：自动生成管理员入口二维码和评委专属二维码，支持批量导出评委二维码（可自定义命名规则）
- 📊 **Excel 导入**：支持上传 Excel 文件导入类别和选手数据
- 🧩 **字段映射可配**：Excel 模板中的 Sheet 名称、类别字段、选手字段、序号字段等可在后台修改
- 📈 **评分统计**：查看评分进度、排名统计、导出 Excel 报表
- 🔒 **权限控制**：评委只能通过专属链接评分，管理员需密码验证，清空评分需额外密码

## 技术栈

- **后端**：Django 5.2 + SQLite + django-cors-headers
- **前端**：Vue 3 + TypeScript + Pinia + Vue Router + Vite
- **Excel**：openpyxl
- **二维码**：qrcode + Pillow

## 快速开始

### 1. 后端

```bash
cd ujn
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### 2. 前端

```bash
cd frontend
npm install
npm run dev
```

### 3. 访问

- **前端首页**：http://localhost:5173
- **Django 管理后台**：http://localhost:8000/admin/
- **前端管理面板**：http://localhost:5173/manage

## Excel 导入说明

默认生成一个 Sheet：

1. `选手数据`

默认字段如下：

### 选手数据 Sheet

| 类别   | 选手  | 序号 |
| ------ | ----- | ---- |
| 才艺组 | 选手A | 1    |
| 才艺组 | 选手B | 2    |
| 演讲组 | 选手C | 1    |

> 以上 Sheet 名称和字段名都可以在管理员界面中修改，修改后再下载模板即可。

**注意**：Excel 导入仅支持导入选手数据，评委需要通过管理界面的「评委管理」功能创建。

## API 接口

| 接口                                | 方法 | 说明                                     |
| ----------------------------------- | ---- | ---------------------------------------- |
| `/api/config/`                      | GET  | 获取站点公开配置                         |
| `/api/categories/`                  | GET  | 获取比赛类别                             |
| `/api/participants/`                | GET  | 获取参赛选手                             |
| `/api/judge/<token>/auth/`          | GET  | 评委认证                                 |
| `/api/judge/<token>/qrcode/`        | GET  | 获取评委二维码                           |
| `/api/submit/`                      | POST | 提交评分                                 |
| `/api/admin/verify/`                | POST | 管理员验证                               |
| `/api/admin/config/`                | GET  | 获取管理员配置                           |
| `/api/admin/config/update/`         | POST | 更新管理员配置                           |
| `/api/admin/qrcode/`                | GET  | 获取管理员二维码                         |
| `/api/admin/template/`              | GET  | 下载 Excel 导入模板                      |
| `/api/admin/import/`                | POST | 上传 Excel 导入数据                      |
| `/api/admin/scores/`                | GET  | 获取所有评分和统计                       |
| `/api/admin/export/`                | GET  | 导出 Excel 统计报表                      |
| `/api/admin/clear/`                 | POST | 清空评分（需清空密码）                   |
| `/api/admin/judges/`                | GET  | 获取评委列表                             |
| `/api/admin/judges/batch/`          | POST | 批量创建评委                             |
| `/api/admin/judges/qrcodes/export/` | GET  | 批量导出评委二维码（支持自定义命名规则） |

## 默认管理员密码

- 前端管理面板默认密码：`admin123`
- Django Admin 密码：初始化 `createsuperuser` 时设置

## 生产环境部署

### 部署前准备

1. **服务器要求**：
   - Python 3.10+
   - Node.js 18+
   - Nginx（推荐）或其他 Web 服务器
   - 域名（可选，用于生成二维码链接）

2. **修改配置**：
   - 后端：`backend/scoring_system/settings.py` 中修改 `ALLOWED_HOSTS`
   - 前端：创建 `frontend/.env.production` 文件，设置生产环境 API 地址

### 部署步骤

#### 1. 后端部署

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 收集静态文件
python manage.py collectstatic --noinput

# 执行数据库迁移
python manage.py migrate

# 创建管理员账号（如未创建）
python manage.py createsuperuser

# 使用 Gunicorn 启动（生产环境推荐）
pip install gunicorn
gunicorn scoring_system.wsgi:application -b 127.0.0.1:8000
```

#### 2. 前端构建

```bash
cd frontend

# 安装依赖
npm install

# 构建生产版本
npm run build

# 构建后的文件在 dist/ 目录，可部署到 Nginx 或静态文件服务器
```

#### 3. Nginx 配置示例

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 媒体文件（上传的背景图、Logo 等）
    location /media/ {
        alias /path/to/backend/media/;
    }

    # 静态文件（Django admin 等）
    location /static/ {
        alias /path/to/backend/static/;
    }
}
```

#### 4. 使用 Systemd 管理后端服务

创建 `/etc/systemd/system/scoring-backend.service`：

```ini
[Unit]
Description=Scoring System Backend
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/backend
ExecStart=/path/to/venv/bin/gunicorn scoring_system.wsgi:application -b 127.0.0.1:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable scoring-backend
sudo systemctl start scoring-backend
```

#### 5. 配置前端基础 URL

部署完成后，访问管理后台 `/manage`，在「基础设置」中修改：

- **前端基础 URL**：设置为你的实际域名，如 `https://your-domain.com`
- **活动标题**：修改为实际活动名称
- **背景图/Logo**：上传活动相关图片

### 使用 Docker 部署（可选）

项目支持 Docker 部署，可参考以下 `docker-compose.yml`：

```yaml
version: "3.8"

services:
  backend:
    build: ./backend
    volumes:
      - ./backend/db.sqlite3:/app/db.sqlite3
      - ./backend/media:/app/media
    environment:
      - DEBUG=False
      - ALLOWED_HOSTS=your-domain.com

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
```

## 其他说明

- **统计规则**："去掉最高分和最低分"只有在某个选手收到 **至少 3 个评委评分** 时才会生效
- **清空评分密码**：默认清空密码为 `jndx`，可在后端代码中修改
- **评委二维码命名规则**：批量导出时支持自定义命名规则，可用占位符包括：
  - `{index}` - 序号
  - `{judge_id}` - 评委 ID
  - `{judge_name}` - 评委姓名
  - `{judge_display_name}` - 评委显示名称（如"评委1"）
  - `{site_name}` - 活动标题
  - `{token}` - 评委令牌
- **Excel 导入**：如果你修改了 Excel 字段名，建议先重新下载模板，再把数据填进去导入
- **数据备份**：生产环境建议定期备份 `backend/db.sqlite3` 和 `backend/media/` 目录
