# Learning Space · 个人科研工作台

一个安静的个人科研空间：专注计时、任务四象限、阅读笔记、习惯记录、灵感收集，以及 Google 日历日程安排。奶油白与森林绿界面，适配桌面和手机。

## 功能

- 数据库事务打卡：并发保护、重试幂等、北京时间跨午夜拆分。
- 按真实年月统计，分页读取，不会在 1,000 条后静默截断。
- 阅读笔记独立保存；已完成任务、已读文献可查看、恢复。
- 灵感历史分页展示；Markdown 日报生成后可反复下载到 Obsidian。
- Google 日历：查看全天/重复日程，从任务创建日程，时间冲突提示，重试避免重复创建。
- 标题、格言可修改；登录有效期 12 小时，可主动退出。

这是**单人使用的私有工作台**，不是多租户应用。持有访问密码的人可以操作整个空间及所连接日历。会话内的登录退避不能替代网关限流；多人使用应接入身份认证、user_id 和逐用户 RLS。

## 技术与目录

Python 3.11+ / Streamlit / Supabase PostgreSQL / Pandas / Plotly / Google Calendar REST API。

```text
app.py                      配置、认证、导航与入口
space/domain.py             日期、校验、导出与日程区间
space/repository.py         分页查询、数据写入、打卡 RPC
space/calendar_client.py    Google token 刷新及日历 API
space/views.py              页面模块
space/theme.py              视觉样式
space/demo.py               独立示例预览，不访问真实服务
supabase/migrations/        完整初始化/升级 SQL
scripts/                   本地一次性 Google 授权工具
tests/                     逻辑、界面与 PostgreSQL 集成测试
```

## 新部署

1. 在 Supabase SQL Editor 执行 `supabase/migrations/001_reliable_workspace.sql`。
2. Streamlit Community Cloud 选择仓库、分支和 `app.py`，Python 使用 3.11 或更高版本。
3. 参考 `.streamlit/secrets.toml.example`，填写 Cloud Secrets：

```toml
APP_PASSWORD = "自行生成的长且唯一密码"
SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "服务端 service_role 密钥"
```

密钥仅在 Streamlit 服务端使用。**不要使用 anon key 替代服务端密钥，不要把 service_role 密钥放进网页、截图或 Git 仓库。** SQL 已对全部业务表启用 RLS 并撤销匿名/普通认证角色权限，由服务端代理访问。

4. 可选：[连接 Google 日历](docs/google-calendar.md)。未配置日历时其余功能可正常使用。
5. 启动后用密码进入。已取消 `?key=密码` 免密入口。

## 旧版升级

先阅读 [升级与验收](docs/upgrade.md)。需在维护窗口一起升级 SQL、Secrets 和应用：

- 备份数据库，确认 `daily_routines` 每日期最多一条。
- 配置 `SUPABASE_SERVICE_ROLE_KEY` 和原来的 `APP_PASSWORD`。
- 执行迁移再部署新版本。保留旧表、旧记录和空间名称。
- 日期暂保留 text，避免强制转换造成历史数据丢失。新事务记录由数据库生成规范日期。
- 不自动修正历史跨日日志、删除重复记录或修改真实 Google 日程。

## 本地运行

```sh
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
# 将 .streamlit/secrets.toml.example 复制为 .streamlit/secrets.toml 并填写
streamlit run app.py
```

固定已验证的直接依赖版本，传递依赖由 pip 解析。本地密钥和授权输出已被 `.gitignore` 排除。

只看界面、不连接真实数据（PowerShell）：

```powershell
$env:LEARNING_SPACE_DEMO = "1"
streamlit run app.py
```

macOS/Linux 使用 `LEARNING_SPACE_DEMO=1 streamlit run app.py`。演示模式明确标注示例数据，生产环境不要设置此变量。

## 测试

```sh
pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

没有 `TEST_DATABASE_URL` 时数据库集成测试跳过，其余测试无线上写入。GitHub Actions 使用独立 PostgreSQL 16，验证事务回滚、并发签退、跨日拆分与匿名访问拒绝。数据库测试仅接受本机/CI 的 `*_test` 数据库，并清空其中的测试业务表，不能指向真实数据库。

## 边界

- 跨设备刷新后读取最新状态，尚未实现实时推送。
- 日历授权属于部署应用，不会继承聊天应用里的 Google 连接。
- 按需读取日历，只在用户提交时创建事件；暂不双向同步任务状态、不修改/删除既有事件、不邀请参与者。
- 日历故障不会阻止专注打卡；授权撤销后可重新运行连接工具。
