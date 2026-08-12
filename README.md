# 🚀 VPS 实时库存与降价监控平台 (VPS Panel Stock Monitor)

参考 `https://panel.yins.win/stock` 深度打造的现代化全网 VPS 实时库存与价格监控平台，内置主流海外/亚太 40+ 厂商热门方案监控，支持**【特定产品加关注】**、**【补货即时提醒】**、**【价格下调提醒】**及**【免密跨设备同步】**。

---

## 🌟 核心特性

- 🌸 **多主题系统**：像素级还原 `panel.yins.win` 经典的 **🌸 樱花粉（Sakura）**、**☀️ 浅色**、**🌙 深色**、**💻 跟随系统** 四种模式。
- 📊 **双视图模式**：紧凑表格视图（Table）与网格卡片视图（Grid）一键切换。
- 🔔 **加关注与邮件通知（核心）**：
  - ⚡ **缺货补货提醒**（Back in Stock Alert）：产品有货时第一时间邮件通知。
  - 📉 **降价优惠提醒**（Price Drop Alert）：产品调价或促销时自动邮件送达。
  - 🎯 **期望价格阈值**：支持自定义设定低于多少价格才发信。
- 🔑 **三重免密管理**：
  - 浏览器本地持久化（`localStorage` 自动记忆关注列表）。
  - 邮件专属 Magic Link 安全密钥。
  - 邮箱一键跨设备拉取与同步。
- ⚙️ **自动轮询与差分爬虫**：
  - APScheduler 定时轮询，自动对比状态与价格，记录 `PriceHistory` 走势。
- 📧 **Web UI SMTP 面板**：
  - 支持在网页端直接配置 QQ 邮箱、163 网易邮箱、Gmail、阿里云企业邮。
  - 在线发送测试邮件，实时检验配置可用性。
- 🔍 **全局即时搜索**：支持键盘 `⌘K` 或 `/` 随时唤起全局快速查找。

---

## 🛠️ 技术栈

* **前端**：Vue 3 + Vite + Tailwind CSS + Pinia + Vue Router + Lucide Icons
* **后端**：Python 3.12 + FastAPI + SQLAlchemy (Async) + aiosqlite (SQLite) + APScheduler + smtplib / Jinja2
* **容器化**：Docker / Docker Compose

---

## 🚀 本地快速启动

### 方式一：源码直接运行
```bash
# 1. 启动后端 (Python 3.12)
cd backend
pip install -r requirements.txt
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 2. 启动前端 (Node.js)
cd ../frontend
npm install
npm run dev
```
打开浏览器访问：`http://localhost:5173`

---

### 方式二：Docker Compose 一键启动
```bash
docker-compose up -d
```
