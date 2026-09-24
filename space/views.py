import hashlib
import uuid
from datetime import date, datetime, time, timedelta
import pandas as pd
import plotly.express as px
import streamlit as st
from .calendar_client import CalendarError
from .domain import (TZ, HABITS, PERIODS, PRIORITIES, now, required_text, safe_html,
                     safe_google_link, event_span, overlapping_events, markdown_report)


def notice(message):
    st.session_state["notice"] = message
    st.rerun()


def section(kicker, title):
    st.markdown(f'<div class="section-kicker">{safe_html(kicker)}</div>', unsafe_allow_html=True)
    st.subheader(title)


def empty(message):
    st.markdown(f'<div class="empty">{safe_html(message)}</div>', unsafe_allow_html=True)


def calendar_events(calendar, start, end):
    if calendar is None: return None
    try:
        return calendar.events(start, end)
    except CalendarError as exc:
        st.warning(str(exc))
        return None


def show_events(events, limit=None):
    if events is None:
        st.info("Google 日历尚未连接或暂时不可用。连接说明在「设置」中。")
        return
    if not events: empty("这段时间还没有安排。留一点空白，也很好。")
    for event in events[:limit] if limit else events:
        start, end, all_day = event_span(event)
        label = f"{start:%m月%d日} · 全天" if all_day else f"{start:%m月%d日 %H:%M} — {end:%m月%d日 %H:%M}"
        st.markdown(f'<div class="agenda-row"><b>{safe_html(event.get("summary") or "未命名日程")}</b>'
                    f'<small>{safe_html(label)} {safe_html(event.get("location", ""))}</small></div>', unsafe_allow_html=True)
        link = safe_google_link(event.get("htmlLink"))
        if link: st.link_button("在 Google 日历查看 ↗", link)


def focus_card(repo, status):
    section("MAKE ROOM FOR DEEP WORK", "此刻，专注一件事")
    with st.container(border=True):
        if status.get("is_working"):
            st.markdown(f'<div class="focus-live">● 正在专注 · {safe_html(status.get("task_type"))}<br>'
                        f'<small>{safe_html(status.get("location"))} · {safe_html(status.get("start_time"))} 开始</small></div>', unsafe_allow_html=True)
            with st.form("finish_focus"):
                details = st.text_area("这次有什么进展？", max_chars=5000, placeholder="记下一点收获，下一次更容易继续。")
                mood = st.select_slider("此刻的心情", ["😫 疲惫", "😐 平静", "😊 开心", "🎉 狂喜"], value="😊 开心")
                if st.form_submit_button("完成这次专注", type="primary", width="stretch"):
                    repo.finish_focus(status["session_id"], details, mood)
                    st.session_state.pop("focus_request", None)
                    notice("专注已保存。辛苦了，休息一下吧。")
        else:
            with st.form("start_focus"):
                task = st.selectbox("今天想推进什么？", ["文献阅读", "论文修改", "组会准备", "地图制作", "自由研究"])
                a, b = st.columns(2)
                location = a.selectbox("所在地点", ["图书馆", "教学楼", "宿舍", "其他"])
                hour = now().hour
                default_period = 0 if hour < 12 else 1 if hour < 18 else 2 if hour < 23 else 3
                period = b.selectbox("时段", PERIODS, index=default_period)
                if st.form_submit_button("开始专注 →", type="primary", width="stretch"):
                    request_id = st.session_state.setdefault("focus_request", str(uuid.uuid4()))
                    repo.start_focus(request_id, location, task, period)
                    notice("计时已开始，按自己的节奏来。")


def overview(repo, calendar, config, logs, status, today):
    greeting = "早上好" if now().hour < 12 else "下午好" if now().hour < 18 else "晚上好"
    st.markdown(f'<div class="hero"><div class="eyebrow">YOUR QUIET CORNER · {today:%Y / %m / %d}</div>'
                f'<h2>{greeting}，让研究慢慢生长。</h2><p>{safe_html(config.get("daily_motto"))}</p></div>', unsafe_allow_html=True)
    tasks = repo.rows("tasks", [("eq", "status", "待办")])
    today_hours = sum(float(r.get("duration") or 0) for r in logs if r["date"] == str(today))
    month_hours = sum(float(r.get("duration") or 0) for r in logs)
    a, b, c = st.columns(3)
    a.metric("今日已完成专注", f"{today_hours:.1f} h")
    b.metric("本月累计", f"{month_hours:.1f} h")
    c.metric("等待推进的任务", f"{len(tasks):02d}")
    left, right = st.columns([1.15, 1], gap="large")
    with left:
        focus_card(repo, status)
        section("ONE STEP AT A TIME", "接下来，慢慢推进")
        for row in sorted(tasks, key=lambda r: r.get("deadline") or "9999")[:3]:
            with st.container(border=True):
                st.write(row["task_name"])
                st.caption(f"{row.get('priority', '')} · 截止 {row.get('deadline') or '未设置'}")
        if not tasks: empty("待办已经清空。给自己一点掌声。")
    with right:
        section("YOUR NEXT SEVEN DAYS", "近期日程")
        start = datetime.combine(today, time.min, TZ)
        events = calendar_events(calendar, start, start + timedelta(days=7))
        show_events(events, limit=5)
        if events and len(events) > 5: st.caption("更多日程请到「任务与日程」查看。")
        section("SMALL THOUGHTS, BIG POSSIBILITIES", "最近的灵感")
        ideas = repo.rows("inspirations", desc=True, page=0)
        if ideas:
            with st.container(border=True):
                st.caption(ideas[0].get("category", "灵感"))
                st.write(ideas[0]["content"])
        else: empty("随手记下一个想法，让它有机会发芽。")


def planner(repo, calendar, today):
    section("PLAN WITH INTENTION", "把重要的事，留在日程里")
    tasks = repo.rows("tasks", [("eq", "status", "待办")])
    with st.expander("＋ 添加任务"):
        with st.form("new_task", clear_on_submit=True):
            title = st.text_input("任务名称", max_chars=200)
            deadline = st.date_input("截止日期", today)
            priority = st.selectbox("优先级", PRIORITIES)
            if st.form_submit_button("保存任务", type="primary"):
                repo.insert("tasks", {"task_name": required_text(title, "任务名称", 200), "deadline": str(deadline),
                                      "priority": priority, "status": "待办", "create_date": str(today)})
                notice("任务已加入清单。")
    task_tab, schedule_tab, archive_tab = st.tabs(["任务四象限", "Google 日历", "已完成"])
    with task_tab:
        columns = st.columns(2)
        for i, priority in enumerate(PRIORITIES):
            with columns[i % 2]:
                with st.container(border=True):
                    st.markdown(f"**{priority}**")
                    group = [r for r in tasks if r.get("priority") == priority]
                    if not group: st.caption("暂时没有任务")
                    for row in sorted(group, key=lambda r: r.get("deadline") or "9999"):
                        st.write(row["task_name"])
                        try:
                            days = (date.fromisoformat(row["deadline"]) - today).days
                            st.caption(f"逾期 {-days} 天" if days < 0 else "今天到期" if days == 0 else f"还有 {days} 天")
                        except (TypeError, ValueError, KeyError): st.caption("截止日期未设置或格式需修正")
                        if st.button("完成", key=f"done_{row['id']}"):
                            repo.update("tasks", row["id"], {"status": "已完成"})
                            notice("又推进了一步。")
        unknown = [r for r in tasks if r.get("priority") not in PRIORITIES]
        if unknown:
            st.warning("有历史任务的优先级无法识别，请在数据库中修正后归入四象限。")
            st.dataframe(unknown, hide_index=True)
    with archive_tab:
        completed = repo.rows("tasks", [("eq", "status", "已完成")], desc=True)
        for row in completed:
            a, b = st.columns([5, 1])
            a.write(row["task_name"])
            if b.button("恢复", key=f"restore_task_{row['id']}"):
                repo.update("tasks", row["id"], {"status": "待办"})
                notice("任务已恢复。")
        if not completed: empty("完成的任务会保留在这里。")
    with schedule_tab:
        if calendar is None:
            st.info("连接后可查看日程，也可以把任务安排到 Google 日历。请先到「设置」完成连接。")
            return
        from_day = st.date_input("查看从哪一天开始的日程", today)
        start = datetime.combine(from_day, time.min, TZ)
        events = calendar_events(calendar, start, start + timedelta(days=14))
        st.caption("显示未来 14 天 · 北京时间 · 包含重复日程与全天日程")
        show_events(events)
        if calendar.readonly:
            st.caption("当前为只读连接。")
            return
        st.divider()
        st.markdown("**安排一段专注时间**")
        chosen = st.selectbox("从任务安排，或创建独立日程", [None] + tasks,
                              format_func=lambda r: "独立日程" if r is None else r["task_name"])
        suffix = str(chosen["id"]) if chosen else "custom"
        with st.form("new_calendar_event"):
            title = st.text_input("日程标题", value=chosen["task_name"] if chosen else "", max_chars=200, key=f"event_title_{suffix}")
            a, b = st.columns(2)
            day_start = a.date_input("开始日期", today)
            time_start = a.time_input("开始时间", time(9, 0))
            day_end = b.date_input("结束日期", today)
            time_end = b.time_input("结束时间", time(10, 0))
            description = st.text_area("日程备注", max_chars=5000)
            allow_overlap = st.checkbox("如有时间冲突，仍按这个时间安排")
            submitted = st.form_submit_button("添加到 Google 日历", type="primary")
        if submitted:
            title = required_text(title, "日程标题", 200)
            begin = datetime.combine(day_start, time_start, TZ)
            end = datetime.combine(day_end, time_end, TZ)
            if end <= begin: raise ValueError("结束时间必须晚于开始时间。")
            conflicts = overlapping_events(calendar.events(begin, end), begin, end)
            if conflicts and not allow_overlap:
                st.warning("这个时段已有安排。请调整时间，或勾选允许冲突后再次提交。")
                for item in conflicts: st.write(item.get("summary", "已有日程"))
            else:
                payload = f"{title}|{begin.isoformat()}|{end.isoformat()}|{description}"
                digest = hashlib.sha256(payload.encode()).hexdigest()
                ids = st.session_state.setdefault("calendar_request_ids", {})
                event_id = ids.setdefault(digest, uuid.uuid4().hex)
                calendar.create_event(event_id, title, begin, end, description)
                notice("已安排到 Google 日历。任务完成状态保持独立。")


def library(repo, today):
    section("COLLECT, CONNECT, CREATE", "阅读与灵感")
    reading_tab, idea_tab = st.tabs(["阅读书架", "灵感收集箱"])
    with reading_tab:
        with st.expander("＋ 添加阅读计划"):
            with st.form("new_reading", clear_on_submit=True):
                title = st.text_input("文献 / 书名", max_chars=300)
                plan = st.text_input("阅读目标", max_chars=1000)
                if st.form_submit_button("加入书架", type="primary"):
                    repo.insert("reading_plan", {"book_name": required_text(title, "文献或书名", 300),
                        "plan_content": plan.strip(), "actual_done": "", "create_date": str(today), "status": "阅读中"})
                    notice("新的阅读计划已保存。")
        state = st.radio("阅读状态", ["阅读中", "已读完"], horizontal=True)
        rows = repo.rows("reading_plan", [("eq", "status", state)], desc=True)
        if not rows: empty("在这里积累你的阅读与思考。")
        for row in rows:
            with st.expander(row["book_name"], expanded=len(rows) == 1):
                st.caption(row.get("plan_content") or "还没有填写阅读目标")
                with st.form(f"reading_{row['id']}"):
                    note = st.text_area("阅读笔记", value=row.get("actual_done") or "", height=160, max_chars=20000)
                    a, b = st.columns(2)
                    save = a.form_submit_button("保存笔记", width="stretch")
                    finish = b.form_submit_button("标记读完" if state == "阅读中" else "继续阅读", width="stretch")
                    if save or finish:
                        new_state = ("已读完" if state == "阅读中" else "阅读中") if finish else state
                        repo.update("reading_plan", row["id"], {"actual_done": note, "status": new_state})
                        notice("笔记已保存。")
    with idea_tab:
        with st.form("new_idea", clear_on_submit=True):
            content = st.text_area("有什么新的想法？", placeholder="一个问题、一句话、一个还没想明白的方向……", max_chars=5000)
            category = st.selectbox("分类", ["🧠 科研Idea", "📝 写作思路", "🐛 代码解法", "💭 随想/吐槽"])
            if st.form_submit_button("收好这个想法", type="primary"):
                repo.insert("inspirations", {"content": required_text(content, "灵感内容", 5000), "category": category,
                                            "create_time": now().strftime('%Y-%m-%d %H:%M')})
                notice("灵感已收好。")
        ideas = repo.rows("inspirations", desc=True)
        pages = max(1, (len(ideas) + 9) // 10)
        page = st.number_input("灵感页码", min_value=1, max_value=pages, value=1)
        if not ideas: empty("小小的想法，也值得被记住。")
        for row in ideas[(page-1)*10:page*10]:
            with st.container(border=True):
                st.caption(f"{row.get('category', '')} · {row.get('create_time', '')}")
                st.write(row["content"])
                with st.popover("删除"):
                    st.caption("删除后无法在应用内恢复。")
                    if st.button("确认删除", key=f"delete_idea_{row['id']}"):
                        repo.delete("inspirations", row["id"])
                        notice("灵感已删除。")


def history(repo, today):
    section("LOOK BACK, MOVE FORWARD", "看见每一点积累")
    chosen = st.date_input("选择统计月份（任选当月一天）", today)
    logs = repo.month_data("study_log", chosen)
    routines = repo.month_data("daily_routines", chosen)
    if logs:
        df = pd.DataFrame(logs)
        df["duration"] = pd.to_numeric(df["duration"], errors="coerce").fillna(0)
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        first = chosen.replace(day=1)
        last = (first + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        series = df.groupby("date")["duration"].sum().reindex(pd.date_range(first, last), fill_value=0)
        chart = series.rename_axis("日期").reset_index(name="小时")
        figure = px.area(chart, x="日期", y="小时", color_discrete_sequence=["#728D75"])
        figure.update_layout(height=260, margin=dict(l=10, r=10, t=15, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(figure, width="stretch", config={"displayModeBar": False})
        st.metric("该月专注时长", f"{df['duration'].sum():.2f} h")
        for label, amount in df.groupby("period")["duration"].sum().items(): st.caption(f"{label} · {amount:.1f} 小时")
        columns = [c for c in ["date", "task_type", "period", "duration", "details", "mood"] if c in df]
        st.dataframe(df[columns].sort_values("date", ascending=False), hide_index=True, width="stretch")
    else: empty("这个月还没有完成的专注记录。")
    st.markdown("**习惯积累**")
    st.write(" · ".join(f"{label} {sum(bool(r.get(key)) for r in routines)} 天" for key, label in HABITS.items()))
    st.divider()
    export_day = st.date_input("导出哪一天的科研日报？", today)
    if st.button("生成 Markdown 日报"):
        logs = repo.rows("study_log", [("eq", "date", str(export_day))])
        habits = repo.rows("daily_routines", [("eq", "date", str(export_day))])
        st.session_state["report"] = (str(export_day), markdown_report(str(export_day), logs, habits, repo.day_ideas(export_day)))
    report = st.session_state.get("report")
    if report:
        st.download_button(f"下载 {report[0]} 日报", report[1], file_name=f"Research_Log_{report[0]}.md", mime="text/markdown", on_click="ignore")
        st.caption("下载后放入 Obsidian，继续连接你的知识。")


def settings(repo, config, calendar):
    section("MAKE IT YOURS", "你的空间，你的节奏")
    with st.form("workspace_settings"):
        name = st.text_input("空间名称", config.get("system_name") or "Learning Space", max_chars=100)
        motto = st.text_input("给今天的一句话", config.get("daily_motto") or "", max_chars=300)
        if st.form_submit_button("保存设置", type="primary"):
            repo.update("system_config", 1, {"system_name": required_text(name, "空间名称", 100), "daily_motto": motto.strip()})
            notice("空间设置已更新。")
    st.markdown("**Google 日历**")
    st.caption("已配置连接" if calendar else "尚未配置连接")
    if calendar and st.button("检查日历连接"):
        calendar.events(now(), now() + timedelta(days=1))
        st.success("日历连接正常。")
    st.write("首次使用需要为这个应用单独授权。按仓库里的日历连接指南操作一次，即可查看日程与安排任务。")
    st.link_button("打开连接指南 ↗", "https://github.com/Nova-Wood/Learning-Space-Dashboard/blob/main/docs/google-calendar.md")
    st.caption("日程按北京时间显示；只在你提交安排时写入 Google，不会自动改动或删除现有日程。")
