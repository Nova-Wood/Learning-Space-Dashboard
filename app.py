"""Single-owner research workspace. Run with: streamlit run app.py."""
import hashlib
import hmac
import os
import time
import streamlit as st
from supabase import create_client
from space.calendar_client import CalendarClient, CalendarError
from space.domain import now
from space.repository import Repository, StorageError
from space.theme import apply_theme
from space.sidebar import render_sidebar
from space import views

st.set_page_config(page_title="Learning Space · 科研日常", page_icon="🌿", layout="wide")
apply_theme()
DEMO = os.environ.get("LEARNING_SPACE_DEMO") == "1"


def authenticate(secrets):
    password = str(secrets.get("APP_PASSWORD", ""))
    if not password:
        st.info("工作台尚未完成配置。请在部署设置中填写 APP_PASSWORD。")
        st.stop()
    if "key" in st.query_params:
        del st.query_params["key"]
    fingerprint = hashlib.sha256(password.encode()).hexdigest()
    session = st.session_state.get("auth", {})
    if session.get("fingerprint") == fingerprint and time.time() < session.get("expires", 0):
        return
    st.markdown('<div class="brand">A LITTLE SPACE TO GROW</div>', unsafe_allow_html=True)
    st.title("欢迎回到你的科研空间")
    st.caption("安静地开始，专注于今天值得做的事。")
    with st.form("login"):
        entered = st.text_input("访问密码", type="password")
        submitted = st.form_submit_button("进入工作台", type="primary")
    if submitted:
        if time.time() < st.session_state.get("retry_after", 0):
            st.warning("尝试过于频繁，请稍后再试。")
        elif hmac.compare_digest(entered.encode(), password.encode()):
            st.session_state["auth"] = {"fingerprint": fingerprint, "expires": time.time() + 12*3600}
            st.session_state["login_failures"] = 0
            st.rerun()
        else:
            failures = st.session_state.get("login_failures", 0) + 1
            st.session_state["login_failures"] = failures
            st.session_state["retry_after"] = time.time() + min(60, 2 ** min(failures, 6))
            st.error("密码不正确，请重新输入。")
    st.markdown("[隐私与日历权限](?page=privacy)")
    st.stop()


@st.cache_resource
def database(url, key):
    try:
        return Repository(create_client(url, key))
    except Exception as exc:
        raise StorageError("数据库连接配置不正确，请检查部署设置。") from exc


@st.cache_resource
def google_calendar(config):
    return CalendarClient(config)


def main():
    if "key" in st.query_params:
        del st.query_params["key"]
    if st.query_params.get("page") == "privacy":
        from space.privacy import show_privacy
        show_privacy()
        return
    if DEMO:
        from space.demo import DemoRepository, DemoCalendar
        repo, calendar = DemoRepository(st.session_state), DemoCalendar(st.session_state)
        st.caption("演示预览 · 示例数据 · 不连接数据库或真实日历")
    else:
        try:
            secrets = st.secrets.to_dict()
        except FileNotFoundError:
            secrets = {}
        authenticate(secrets)
        if not secrets.get("SUPABASE_URL") or not secrets.get("SUPABASE_SERVICE_ROLE_KEY"):
            st.info("请先完成数据库迁移，并在部署设置中填写 SUPABASE_URL 和 SUPABASE_SERVICE_ROLE_KEY。")
            st.stop()
        repo = database(secrets["SUPABASE_URL"], secrets["SUPABASE_SERVICE_ROLE_KEY"])
        config = secrets.get("google_calendar", {})
        calendar = google_calendar(config) if all(config.get(k) for k in ["client_id", "client_secret", "refresh_token"]) else None
    config = repo.singleton("system_config")
    status = repo.singleton("current_status")
    if status.get("is_working"):
        st.session_state["last_focus_session"] = status.get("session_id")
    elif st.session_state.pop("last_focus_session", None):
        # Another device may have finished the last locally started session.
        st.session_state.pop("focus_request", None)
    today = now().date()
    page = render_sidebar(repo, calendar, today, demo=DEMO)
    st.caption(config.get("system_name") or "Learning Space")
    message = st.empty()
    if st.session_state.get("notice"):
        message.success(st.session_state.pop("notice"))
    if page == "今日概览": views.overview(repo, calendar, config, repo.month_data("study_log", today), status, today)
    elif page == "任务与日程": views.planner(repo, calendar, today)
    elif page == "阅读与灵感": views.library(repo, today)
    elif page == "记录与统计": views.history(repo, today)
    else: views.settings(repo, config, calendar)


try:
    main()
except (StorageError, CalendarError, ValueError) as exc:
    st.error(str(exc))
    if st.button("刷新后重试", key="recover"): st.rerun()
