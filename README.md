# 🎓 Novawood's Learning Space | 硕博科研全平台工作流

![Python](https://img.shields.io/badge/Python-3.12-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B) ![Supabase](https://img.shields.io/badge/Supabase-Database-3ECF8E)

告别碎片化的纸质手账与笨重的效率软件。这是一个基于 Python + Streamlit + Supabase 打造的**全平台、云同步、高定制度**的科研日常管理看板。

它不仅是一个打卡器，更是一个融合了**「时间追踪 + 艾森豪矩阵 + 知识沉淀 (Obsidian联动)」**的专属科研操作系统。

---

## ✨ 核心亮点 (Core Features)

* **☁️ 跨设备状态漫游**：基于 Supabase 云端数据库，彻底打破设备壁垒。在实验室电脑点击“签到”，回宿舍路上用手机浏览器直接“签退”，数据无缝实时同步。
* **🎯 四象限任务池 (Eisenhower Matrix)**：支持为待办事项设定 DDL（截止日期）与优先级。系统自动计算倒计时，逾期自动标红警告，专治 DDL 拖延症。
* **💡 灵感碎片收集箱**：瀑布流卡片设计，随时捕捉“Eureka Moment（顿悟时刻）”。科研 Idea、写作思路、代码解法分类存储。
* **📚 文献阅读管理**：专属的论文精读跟踪库，支持记录阶段性笔记，一键标记“已读完”。
* **📊 自动化数据洞察**：根据打卡记录，自动生成每日专注时长柱状图与精力分布饼图。
* **🔗 完美接入 Obsidian**：一键生成标准 Markdown 格式的「今日科研日报」，直接拖入 Obsidian 构建你的第二大脑知识图谱。

---

## 🚀 极速云端部署指南 (无需懂代码)

想要拥有一个属于你自己的专属链接？只需简单三步，5 分钟即可免费上线！

### Step 1: 建立 Supabase 云端大脑
1. 注册/登录 [Supabase](https://supabase.com/)，新建一个 Project。
2. 进入项目左侧导航栏的 **SQL Editor**，新建 Query，复制并运行以下 SQL 脚本以初始化数据库：
<details>
<summary>👉 点击展开查看 SQL 初始化脚本</summary>

```sql
create table study_log (
  id bigint primary key generated always as identity,
  date text, period text, start_time text, end_time text, location text, task_type text, duration float, details text, mood text
);
create table reading_plan (
  id bigint primary key generated always as identity,
  create_date text, book_name text, plan_content text, actual_done text, status text
);
create table tasks (
  id bigint primary key generated always as identity,
  task_name text, status text, create_date text, deadline text, priority text
);
create table system_config (
  id integer primary key, system_name text, daily_motto text
);
insert into system_config (id, system_name, daily_motto) values (1, '我的科研基地', '今日目标: 拒绝内耗，按时干饭！');
create table current_status (
  id integer primary key, is_working boolean, start_time text, location text, task_type text, period text
);
insert into current_status (id, is_working) values (1, false);
create table inspirations (
  id bigint primary key generated always as identity,
  create_time text, content text, category text
);</details>
 ```
3. 运行成功后，进入 Project Settings -> API，复制你的 Project URL 和 anon public key 保存备用。

### Step 2: 部署前端网页
1. Fork 本仓库到你的 GitHub 账号下。

2. 登录 Streamlit Community Cloud，点击 New app。

3. 选择你 Fork 的仓库，主文件路径填写 app.py。

4. ⚠️ 最重要的一步：点击页面底部的 Advanced settings...，在 Secrets 文本框中按以下格式填入你刚才保存的数据库秘钥：
```
Ini, TOML
SUPABASE_URL = "https://你的Project_URL.supabase.co"
SUPABASE_KEY = "你的那一长串anon_public_key"
```
5. 点击 Deploy! 气球飘落后，你的专属系统即刻上线。

### 💻 进阶：本地开发与运行指南
如果你希望在本地修改代码、增加新功能，请遵循以下环境隔离规范（避免因 C++ 编译工具缺失导致的本地报错）：

1. 推荐环境：强烈建议使用 Python 3.11 或 3.12 稳定版本。

2. 建立虚拟环境：

Bash
python -m venv .venv
# Windows 激活:
.venv\Scripts\activate
# Mac/Linux 激活:
source .venv/bin/activate
3. 安装依赖包：

Bash
pip install -r requirements.txt
4. 配置本地秘钥：
在项目根目录下新建 .streamlit 文件夹，在其中创建 secrets.toml 文件，并写入与云端相同的 SUPABASE_URL 和 SUPABASE_KEY。
(注意：请确保 .streamlit 文件夹已加入 .gitignore，切勿将秘钥推送到公开仓库！)

5. 启动系统：

Bash
streamlit run app.py
Powered by Python & Streamlit | 祝各位硕博士：Paper 顺利，永不延毕！🎓
