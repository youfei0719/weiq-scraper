# 📊 WEIQ 商业数据调度舱 (WEIQ Scraper Pro)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io/)
[![Playwright](https://img.shields.io/badge/engine-Playwright-green.svg)](https://playwright.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


**专为 MCN 机构打造的“社交媒体资产自动化监控与商业价值评估系统”。**

本项目基于 `Playwright` 构建了高可用的底层防风控爬虫引擎，并结合 `Streamlit` + `Plotly` 打造了 0 前端 Bug、极具商业质感的 SaaS 级交互式数据监控大盘。

---

## 🔗 保持联系 (Connect)
如果您对本项目有任何建议，或者需要定制化的商业数据解决方案，欢迎联系：
* **GitHub**: [youfei0719](https://github.com/youfei0719)

---

## 🆕 更新日志 (Changelog)

### 🚀 v3.0 商业级 BI 大盘与引擎重构 (最新)
**更新时间：2026-03-16**
* **可视化大盘彻底重构 (`main.py`)**：引入“主从联动交互 (Master-Detail)”范式，彻底杜绝 500+ 账号下的图表拉伸崩溃。
* **金融级热力树图 (Treemap)**：区块面积代表粉丝体量，红绿灯色带实时映射 CPM 成本高低，解决高密度展示痛点。
* **微观对比防崩溃机制**：内置 Top-N 智能截断，自动提取各项指标 Top 20 生成对比图。
* **高管级数据清洗**：重写智能单位换算器，所有标签强制转换为“1.2亿”、“4.5万”等中文格式。
* **爬虫引擎重构 (`scraper.py`)**：引入 `playwright-stealth` 深度抹除自动化特征。
* **双轨制落盘方案**：SQLite 数据库并发容灾 + 内存映射 Excel 导出，确保数据安全。

### 🚀 v2.0 史诗级更新
**更新时间：2026-03-09**
* **全量 15 项指标扩容**：支持粉丝数、直发 CPM、阅读中位数、最近 20 篇博文趋势等。
* **Viewport 懒加载击穿**：注入平滑深度滚动算法，强制唤醒底部数据请求。
* **父级区块逆向解析**：无视 DOM 多层嵌套与 CSS 混淆，精准提取核心数值。

---

## 📖 详尽使用教程 (Mac & Win 双端保姆级)

### 第一步：环境初始化

#### 🍏  MacBook (M1/M2/M3/M4) 用户：
1. **进入目录**：`cd ~/Documents/weiq-scraper-main` (请替换为你的实际路径)
2. **安装依赖**：
   ```bash
   uv pip install streamlit pandas plotly openpyxl playwright playwright-stealth
   ```
3. **下载 Mac 专用内核**：
   ```bash
   uv run playwright install chromium
   ```

#### 🪟 Windows 用户：
1. **进入目录**：`cd /d E:\exe\cpm\weiq-scraper-main` (请替换为你的实际路径)
2. **安装依赖与内核**：
   ```cmd
   uv pip install streamlit pandas plotly openpyxl playwright playwright-stealth
   uv run playwright install chromium
   ```

### 第二步：准备监控名单 (本地安全保护)
1. 在项目根目录下创建 `accounts.xlsx`。
2. 必须包含两列表头：`账号ID`（博主名）和 `uid`（WEIQ平台唯一ID）。
3. 🔒 **绝对隐私安全**：该文件已被 `.gitignore` 排除，**监控名单与凭证绝不会上传至云端**。

### 第三步：启动底层爬虫引擎
**执行命令**：`uv run python scraper.py`
1. **首次登录**：程序会弹出浏览器窗口，请手动扫码登录。
2. **权限捕获**：成功进入 WEIQ 后台后，**请务必回到终端按下【回车键】**。
3. **静默运行**：系统会自动保存 `state.json`，以后运行将全自动静默采集，无需再次扫码。

### 第四步：启动商业大盘 (可视化决策)
**执行命令**：`streamlit run main.py`

#### 💡 深度解惑：如果我不小心关闭了看板页面？
* **场景 A：终端窗口还在运行**
  只需在浏览器地址栏重新输入 `http://localhost:8501` 即可找回页面。
* **场景 B：终端窗口也被关了**
  **不需要重新爬取数据！** 只需再次输入 `streamlit run main.py`，系统会瞬间从本地数据库加载历史数据，耗时不到 2 秒。
* **场景 C：采集时看板一直开着**
  直接运行 `scraper.py`。爬完后，看板右上角会提示 `Source file changed`，点击 **Rerun** 即可刷新。

---

## 📑 核心函数日志 (Function Log)

**爬虫引擎模块 (`scraper.py`)**
* `init_browser(p)`: 隐身浏览器初始化。随机视口尺寸，注入 stealth 抹除指纹，挂载 state.json。
* `extract_metrics(page)`: 逆向视觉树提取。基于 TreeWalker 绕过复杂 DOM 精准提取 15 项数值。
* `check_anti_spider(page)`: 风控熔断器。实时扫描重定向与验证码，命中则触发终端响铃并暂停。
* `append_to_storage(...)`: 双轨落盘机制。同步写入 SQLite DB 和 Excel，解决文件锁宕机问题。

**商业大盘模块 (`main.py`)**
* `format_chinese_unit(num)`: 商业语义转化。将庞大数字智能转换为“亿”、“万”等极简文本。
* `load_data()`: 数据缓存装载。带有 `@st.cache_data` 装饰器，进行深度清洗与 0 值过滤。
* `create_clean_bar_chart(...)`: 微观对比渲染。极简条形图，内置 Top-N 截断保护。

---

## 🏗️ 项目架构设计 (Architecture)

1. **采集引擎层 (`scraper.py`)**：负责突破反爬协议、执行模拟滚动、提取数据并安全落盘。
2. **数据落盘层 (高容错)**：SQLite (`weiq_data.db`) 负责并发容灾，Excel (`weiq_results.xlsx`) 负责交付查阅。
3. **决策可视化层 (`main.py`)**：纯读取状态，零交互干扰。通过 Streamlit + Plotly 实现热力树图资产洞察。

---

## ⚖️ 免责声明 (Disclaimer)

1. **技术交流专用**：本项目仅供技术研究与学习参考，严禁用于任何非法商业采集或侵害他人的行为。
2. **法律合规**：使用者应遵守相关法律法规及平台服务协议（ToS）。因不当使用导致的账号封禁或法律责任，由使用者自行承担，开发者不承担任何直接或间接责任。
3. **数据隐私**：本项目为本地运行脚本，不具备任何上传、共享用户凭证或监控名单的功能。

---

## 🛡️ 跨平台推送指南 (Git Guide)

### 1. 终端进入项目
* **🍏 Mac**: `cd ~/Documents/weiq-scraper-main`
* **🪟 Win**: `cd /d E:\exe\cpm\weiq-scraper-main`

### 2. 执行安全推送
```bash
git add .
git commit -m "feat: 升级专业化README，添加社交链接、Mac支持与免责声明"
git push origin main -f
```
