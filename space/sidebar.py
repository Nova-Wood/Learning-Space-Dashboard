"""Compact navigation and daily check-in for the personal workspace."""
import streamlit as st
from .domain import HABITS
from .views import notice


def render_sidebar(repo, calendar, today, demo=False):
    with st.sidebar, st.container(key="sidebar_shell"):
        st.markdown('''<div class="space-identity">
            <div class="space-monogram" aria-hidden="true">n<span>·</span></div>
            <div><div class="space-wordmark">NOVAWOOD</div><div class="space-title">科研工作台</div></div>
            </div><p class="space-motto">为专注，留一处空白。</p>''', unsafe_allow_html=True)
        with st.container(key="workspace_nav"):
            st.markdown('<div class="sidebar-label">工作空间</div>', unsafe_allow_html=True)
            page = st.radio("工作台导航", ["今日概览", "任务与日程", "阅读与灵感", "记录与统计", "设置"],
                            label_visibility="collapsed", key="workspace_page", width="stretch")

        rows = repo.rows("daily_routines", [("eq", "date", str(today))])
        current = rows[0] if rows else {}
        completed = sum(bool(current.get(key)) for key in HABITS)
        with st.container(key="daily_care"):
            st.markdown(f'''<div class="care-heading"><span>今日的小习惯</span>
                <span class="care-count">{completed}<span> / {len(HABITS)}</span></span></div>''',
                unsafe_allow_html=True)
            st.progress(completed / len(HABITS))
            with st.expander("照顾好自己", expanded=False):
                st.caption(f"{today:%m 月 %d 日} · 一点点，也算进步")
                with st.form(f"habits_{today}"):
                    habits = {key: st.checkbox(label, value=bool(current.get(key)), key=f"{today}_{key}")
                              for key, label in HABITS.items()}
                    if st.form_submit_button("保存今日习惯", width="stretch", type="primary"):
                        repo.save_habits(str(today), habits)
                        notice("今日习惯已保存。")

        with st.container(key="sidebar_footer"):
            state = "connected" if calendar else "disconnected"
            label = "日历预览" if demo else ("Google 日历已连接" if calendar else "Google 日历未连接")
            st.markdown(f'''<div class="sidebar-connection {state}"><span aria-hidden="true"></span>{label}</div>
                <div class="sidebar-timezone">北京时间 · UTC+8</div>''', unsafe_allow_html=True)
            refresh, logout = st.columns(2, gap="small")
            if refresh.button("刷新", icon=":material/refresh:", key="refresh_workspace", width="stretch"):
                st.rerun()
            if not demo and logout.button("退出", icon=":material/logout:", key="logout_workspace", width="stretch"):
                st.session_state.clear()
                st.rerun()
    return page
