# 连接 Google 日历：查看日程 + 安排任务

授权在你电脑的浏览器完成，长期凭证仅存于 Streamlit 服务端 Secrets。不要把凭证发在聊天中或提交到 GitHub。

## 1. 准备 Google 项目

1. 在 [Google Cloud Console](https://console.cloud.google.com/) 选择或新建项目，启用 **Google Calendar API**。
2. 在 **Google Auth Platform** 配置 Branding、Audience、Data Access。个人账号通常选择 External；测试模式将自己添加为测试用户。
3. 添加权限 `https://www.googleapis.com/auth/calendar.events`，仅查看可用 `calendar.events.readonly`。
4. Clients 中创建 **Desktop app** 类型 OAuth 客户端，下载 JSON，文件名保持 `client_secret...json`（已被忽略）。

External 应用处于 Testing 时，包含 Calendar 权限的 refresh token 通常在 7 天后过期。持续使用需按 Google 要求调整发布状态；组织账号可能受管理员策略限制。发布与验证要求以 Google 控制台为准。

## 2. 本地授权

在已安装项目依赖的本地终端运行：

```sh
python scripts/connect_google_calendar.py client_secret_YOUR_CLIENT.json
```

浏览器中选择目标账号并授权。脚本只授权，不创建日程。回调仅监听 `127.0.0.1`，使用随机 state 和 PKCE，五分钟超时。

成功后生成 `.streamlit/google-calendar.secrets.toml`，不会在终端打印 token 或覆盖已有文件。重新授权可指定 `--output .streamlit/reconnect.secrets.toml`。

默认连接 `primary` 主日历。也可创建“科研计划”日历，从 Google 日历设置复制日历 ID，运行：

```sh
python scripts/connect_google_calendar.py client_secret_YOUR_CLIENT.json --calendar-id YOUR_CALENDAR_ID
```

仅查看模式附加 `--readonly`，应用会隐藏创建表单。

## 3. 配置工作台

将生成文件的整个 `[google_calendar]` 段追加到 Streamlit Cloud → App settings → Secrets，或本地 `.streamlit/secrets.toml`：

```toml
[google_calendar]
client_id = "你的客户端 ID"
client_secret = "你的客户端密钥"
refresh_token = "授权工具生成的刷新凭证"
calendar_id = "primary"
readonly = false
```

保存、重启后进入「设置」→「检查日历连接」。然后在「任务与日程」→「Google 日历」选择任务或独立日程，填写起止时间并提交。

## 使用与异常处理

- 按北京时间（UTC+8）显示和安排，支持跨日结束时间。
- 查看窗口为 14 天，首页显示近期 7 天中的前 5 项。重复事件展开；全天事件结束日期按 Google 排他结束规则处理。
- 创建前提示冲突，透明/已取消事件不阻塞。提示并非 Google 端事务锁，其他设备仍可能同时安排。
- 日程 ID 保存在当前应用会话。网络失败后保持页面直接重试可避免重复插入；会话丢失后先检查 Google 日历再重试。
- 不添加参与者、不发送邀请、不自动修改/删除旧事件。
- “已配置连接”表示填了必需字段；“检查连接”成功才表示实时授权可用。
- 无权访问：检查日历编辑权限、scope 和 API 启用状态。
- 授权失效：在 Google 账号撤销本应用权限，重新运行工具并更新 Secrets。

官方参考：[桌面 OAuth](https://developers.google.com/identity/protocols/oauth2/native-app)、[列出事件](https://developers.google.com/workspace/calendar/api/v3/reference/events/list)、[创建事件](https://developers.google.com/workspace/calendar/api/v3/reference/events/insert)、[凭证有效期](https://developers.google.com/identity/protocols/oauth2#expiration)。
