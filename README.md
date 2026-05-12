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

- **后端**：Django 5.2 + MySQL + django-cors-headers
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

## Docker 镜像部署

推荐使用本仓库 GitHub Action 发布到 DockerHub 的镜像运行，不需要在服务器上安装 Python、Node 或手动配置 Nginx。

镜像包含：

- `frontend/dist` 前端静态文件
- Nginx，监听容器内 `8080`
- Django + Gunicorn 后端，Nginx 反代 `/api/`、`/admin/`、`/media/`
- 启动时自动执行 `collectstatic`，默认执行 `python manage.py migrate --noinput`

将下面示例里的 `yourname/ujn-score:latest` 替换为本仓库发布的 DockerHub 镜像名。若使用默认 workflow，镜像名通常是 `<DOCKERHUB_USERNAME>/ujn-score:latest`。

### 使用本机已部署的 MySQL 数据库

容器内的 `127.0.0.1` 指向容器自己，不是宿主机。连接宿主机上的 MySQL 时：

- Docker Desktop：`MYSQL_HOST=host.docker.internal`
- Linux Docker：额外添加 `--add-host=host.docker.internal:host-gateway`
- 如果数据库是另一个 Docker 容器，把两个容器放进同一 Docker network，并把 `MYSQL_HOST` 设置为数据库服务名

运行示例：

```bash
docker run -d --name ujn-score \
  --add-host=host.docker.internal:host-gateway \
  -p 8080:8080 \
  -e DJANGO_SECRET_KEY=change-me \
  -e DJANGO_DEBUG=False \
  -e DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com \
  -e CORS_ALLOWED_ORIGINS=https://your-domain.com \
  -e USE_MYSQL=1 \
  -e MYSQL_HOST=host.docker.internal \
  -e MYSQL_PORT=3306 \
  -e MYSQL_DATABASE=ujn \
  -e MYSQL_USER=ujn \
  -e MYSQL_PASSWORD=your-db-password \
  -e CLEAR_PASSWORD=jndx \
  -v ujn-score-media:/app/ujn/media \
  yourname/ujn-score:latest
```

本机 MySQL 需要允许 Docker 容器连接：确保 MySQL 监听非 `127.0.0.1` 的地址，并给 `MYSQL_USER` 授权来自 Docker 网段或 `%` 的访问权限。

### docker compose 示例

```yaml
services:
  app:
    image: yourname/ujn-score:latest
    container_name: ujn-score
    ports:
      - "8080:8080"
    extra_hosts:
      - "host.docker.internal:host-gateway"
    environment:
      DJANGO_SECRET_KEY: change-me
      DJANGO_DEBUG: "False"
      DJANGO_ALLOWED_HOSTS: localhost,127.0.0.1,your-domain.com
      CORS_ALLOWED_ORIGINS: https://your-domain.com
      USE_MYSQL: "1"
      MYSQL_HOST: host.docker.internal
      MYSQL_PORT: "3306"
      MYSQL_DATABASE: ujn
      MYSQL_USER: ujn
      MYSQL_PASSWORD: your-db-password
      CLEAR_PASSWORD: jndx
    volumes:
      - ujn-score-media:/app/ujn/media
    restart: unless-stopped

volumes:
  ujn-score-media:
```

### 本地 SQLite 临时运行

不设置 `USE_MYSQL=1` 时会使用容器内 SQLite，适合快速试用，不建议用于生产。容器删除后数据库会丢失，生产请使用外部 MySQL 并备份数据库和 `ujn-score-media` 卷。

```bash
docker run -d --name ujn-score -p 8080:8080 \
  -e DJANGO_SECRET_KEY=change-me \
  -e DJANGO_DEBUG=False \
  -e DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1 \
  -v ujn-score-media:/app/ujn/media \
  yourname/ujn-score:latest
```

### DockerHub 镜像自动发布

`.github/workflows/dockerhub.yml` 会在推送 `main`、推送版本标签或手动触发时构建 Docker 镜像并推送到 DockerHub。

需要在 GitHub 仓库配置：

- Secret `DOCKERHUB_USERNAME`：DockerHub 用户名
- Secret `DOCKERHUB_TOKEN`：DockerHub Access Token
- 可选 Variable `DOCKERHUB_IMAGE`：完整镜像名，例如 `yourname/ujn-score`；未设置时默认使用 `<DOCKERHUB_USERNAME>/ujn-score`

## 其他说明

- **统计规则**：开启极值剔除时，评分数必须大于“去掉最低分数量 + 去掉最高分数量”才会生效
- **清空评分密码**：默认清空密码为 `jndx`，可通过环境变量 `CLEAR_PASSWORD` 修改
- **评委二维码命名规则**：批量导出时支持自定义命名规则，可用占位符包括：
  - `{index}` - 序号
  - `{judge_id}` - 评委 ID
  - `{judge_name}` - 评委姓名
  - `{judge_display_name}` - 评委显示名称（如"评委1"）
  - `{site_name}` - 活动标题
  - `{token}` - 评委令牌
- **Excel 导入**：如果你修改了 Excel 字段名，建议先重新下载模板，再把数据填进去导入
- **数据备份**：生产环境建议定期备份 MySQL 数据库和 Docker 卷 `ujn-score-media`
