"""Public, static privacy information. Never loads workspace data or secrets."""
import streamlit as st


def show_privacy():
    st.title("隐私与日历权限")
    st.caption("Novawood Research Space · Privacy notice · 更新于 2026-09-25")
    st.markdown("""
这是空间所有者自用的科研工作台。访问密码保护任务、阅读笔记、习惯和专注记录。
持有工作台密码的人可以访问整个空间及已连接的日历，因此请勿分享访问密码。

### Google 日历
只有在你主动授权后，应用才会连接你的 Google 日历。应用读取日程的标题、时间、
描述、地点和状态，用于展示未来安排、展开重复日程及提示时间冲突。
只有点击提交后，应用才会把你填写的标题、时间、描述和地点写入 Google 日历。
应用不自动修改或删除已有日程，也不添加参与者或发送邀请。

Google 的 `calendar.events` 权限同时包含查看、创建、修改和删除日程的能力。
本应用使用其中的查看和创建功能；该权限不包含 Gmail 邮件、联系人或云端硬盘文件。

### 保存与处理
日历日程按需从 Google 读取，可能在应用服务端内存和当前会话中暂存，
不会复制到本工作台的 Supabase 数据库。新建的日程保存在你的 Google 日历中，
直到你自行删除。Google 授权刷新凭证保存在 Streamlit Cloud 的服务端 Secrets 中，
不会提交到代码仓库或显示在工作台页面。

你在工作台输入的科研记录保存在空间所有者控制的 Supabase 项目中。
部署备份可能保留旧记录；删除数据库记录并不会自动删除已有备份。
Streamlit 提供应用托管，Supabase 提供数据库，Google 提供日历与授权服务；
这些服务按各自的条款处理运行所需的信息。本应用不出售日历数据，
不将其用于广告或训练人工智能模型。

### 撤销授权与删除
你可以在 [Google 账号的第三方连接](https://myaccount.google.com/connections)
撤销本应用的访问权限。空间所有者还可以删除 Streamlit Secrets 中的
`google_calendar` 配置，使工作台停止连接日历。撤销授权不会删除已创建的 Google 日程。
如需删除科研记录及备份，请由空间所有者在 Supabase 中操作。

### 联系
有关此工作台的数据处理问题，可通过
[项目反馈入口](https://github.com/Nova-Wood/Learning-Space-Dashboard/issues)
联系维护者。请勿在公开反馈中粘贴密码、授权凭证或私人日历内容。

---
**English summary.** This is a single-owner research workspace. After explicit Google
authorization, it reads calendar events to show schedules and conflicts, and creates
events only when the user submits a schedule. It does not automatically edit or delete
existing events, add attendees, or send invitations. The `calendar.events` permission
also permits event modification and deletion, which this app does not implement.
Calendar event data is processed in server memory/session and is not copied to Supabase.
Created events remain in Google Calendar until deleted there. Refresh credentials are
stored in server-side Streamlit Secrets. Research records and backups are stored in the
owner's Supabase project. Google, Streamlit, and Supabase process information needed to
provide these services. This app does not sell calendar data or use it for advertising
or AI model training. Revoke access through Google Account connections and remove the
calendar configuration from Streamlit Secrets to disconnect. Contact the maintainer
through the project issue tracker without posting private information.
""")
    if st.button("返回工作台", type="primary"):
        st.query_params.clear()
        st.rerun()
