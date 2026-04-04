import streamlit as st
import pandas as pd
import datetime
from supabase import create_client, Client
import plotly.express as px

# --- 基础配置 ---
st.set_page_config(page_title="硕博科研工作流", page_icon="🎓", layout="wide")

# ==========================================
# 🔒 核心安全防盗门
# ==========================================
# 1. 检查当前设备是否已经登录过
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# 2. 如果没登录，显示密码输入框并拦截后续代码
if not st.session_state.authenticated:
    st.markdown("<h2 style='text-align: center; margin-top: 100px;'>🔒 私人科研空间，闲人免进</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        pwd = st.text_input("请输入访问密码", type="password", placeholder="输入密码后按回车或点击下方按钮")
        if st.button("🗝️ 开锁进入", use_container_width=True):
            if pwd == st.secrets["APP_PASSWORD"]:
                st.session_state.authenticated = True
                st.toast("✅ 密码正确，欢迎回来！")
                st.rerun() 
            else:
                st.error("❌ 密码错误，你是不是导师派来的卧底？")
    
    # 关键：阻断程序，只要没登录，下面的打卡代码绝对不会执行！
    st.stop() 

# --- 强制设置时区 (东八区 UTC+8) ---
TZ = datetime.timezone(datetime.timedelta(hours=8))

def get_now():
    """获取东八区当前精准时间"""
    return datetime.datetime.now(TZ)

def get_today_str():
    """获取东八区今天的日期字符串 (YYYY-MM-DD)"""
    return get_now().date().strftime('%Y-%m-%d')

# --- Supabase 连接 ---
@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase: Client = init_connection()

# --- 数据加载函数 ---
def load_base_info():
    conf = supabase.table("system_config").select("*").eq("id", 1).execute().data[0]
    stat = supabase.table("current_status").select("*").eq("id", 1).execute().data[0]
    return conf, stat

user_config, cur_stat = load_base_info()

# ==========================================
# 侧边栏：状态与设置
# ==========================================
with st.sidebar:
    st.title("🎓 仪表盘")
    with st.expander("⚙️ 系统个性化"):
        with st.form("conf_f"):
            n_name = st.text_input("系统名", user_config['system_name'])
            n_motto = st.text_input("今日目标", user_config['daily_motto'])
            if st.form_submit_button("更新"):
                supabase.table("system_config").update({"system_name": n_name, "daily_motto": n_motto}).eq("id", 1).execute()
                st.rerun()
    
    st.divider()
    # 统计今日时长
    logs_res = supabase.table("study_log").select("*").execute()
    df_log = pd.DataFrame(logs_res.data)
    today_h = df_log[df_log['date'] == get_today_str()]['duration'].sum() if not df_log.empty else 0
    st.metric("今日专注", f"{round(today_h, 1)} 小时")
    
    if cur_stat['is_working']:
        st.success(f"正在进行: {cur_stat['task_type']}")
    else:
        st.write("⚪ 当前空闲")

# ==========================================
# 顶部：欢迎语
# ==========================================
st.markdown(f"<h1 style='text-align: center;'>{user_config['system_name']}</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #4A90E2;'>{user_config['daily_motto']}</p>", unsafe_allow_html=True)
st.divider()

# ==========================================
# 核心区：打卡与计时 (四模块布局)
# ==========================================
st.markdown("### 🕒 实时打卡中心")
mood = st.select_slider("当前心情状态", options=["😫", "😐", "😊", "🎉"], value="😊")
current_loc = st.radio("所在地", ["工位", "图书馆", "宿舍", "其他"], horizontal=True)

periods = [("上午", "🌅"), ("下午", "☀️"), ("晚上", "🌙"), ("深夜", "🦉")]
p_cols = st.columns(4)

for i, (p_name, p_icon) in enumerate(periods):
    with p_cols[i]:
        with st.container(border=True):
            st.markdown(f"#### {p_icon} {p_name}")
            if not cur_stat['is_working']:
                t_type = st.selectbox(f"任务-{p_name}", ["文献阅读", "论文修改", "语言学习", "组会准备","自媒体输出"], key=f"t_{p_name}")
                if st.button("开始签到", key=f"in_{p_name}", use_container_width=True):
                    supabase.table("current_status").update({
                        "is_working": True, 
                        "start_time": get_now().strftime('%Y-%m-%d %H:%M:%S'),
                        "location": current_loc, 
                        "task_type": t_type, 
                        "period": p_name
                    }).eq("id", 1).execute()
                    st.rerun()
            elif cur_stat['period'] == p_name:
                st.info(f"计时中: {cur_stat['start_time'][11:16]}")
                note = st.text_input("进展备注", key=f"n_{p_name}")
                if st.button("停止签退", key=f"out_{p_name}", type="primary", use_container_width=True):
                    start_dt = datetime.datetime.strptime(cur_stat['start_time'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=TZ)
                    duration = round((get_now() - start_dt).total_seconds()/3600, 2)
                    
                    supabase.table("study_log").insert({
                        "date": get_today_str(), 
                        "period": p_name, 
                        "start_time": cur_stat['start_time'],
                        "end_time": get_now().strftime('%Y-%m-%d %H:%M:%S'),
                        "location": cur_stat['location'], 
                        "task_type": cur_stat['task_type'],
                        "duration": duration, 
                        "details": note, 
                        "mood": mood
                    }).execute()
                    supabase.table("current_status").update({"is_working": False}).eq("id", 1).execute()
                    st.rerun()
            else:
                st.button("🔒 锁定", disabled=True, use_container_width=True, key=f"lock_{p_name}")

st.divider()

# ==========================================
# 功能区：任务四象限 & 阅读计划
# ==========================================
col_l, col_r = st.columns([1.2, 1]) 

with col_l:
    st.subheader("🎯 任务管理 (四象限)")
    with st.expander("➕ 新增待办任务"):
        with st.form("add_task_form", clear_on_submit=True):
            t_name = st.text_input("任务名称", placeholder="例如：修改第三章实验数据")
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                t_ddl = st.date_input("截止日期 (DDL)", get_now().date())
            with col_t2:
                t_priority = st.selectbox("优先级", ["🚀 重要且紧急", "📅 重要不紧急", "⚡ 紧急不重要", "☁️ 不重要不紧急"])
            
            if st.form_submit_button("添加至任务池"):
                if t_name:
                    supabase.table("tasks").insert({
                        "task_name": t_name, 
                        "status": "待办", 
                        "create_date": get_today_str(),
                        "deadline": str(t_ddl), 
                        "priority": t_priority
                    }).execute()
                    st.rerun()

    task_res = supabase.table("tasks").select("*").execute()
    df_task = pd.DataFrame(task_res.data)

    if not df_task.empty:
        pending_tasks = df_task[df_task["status"] == "待办"]
        quadrants = {"🚀 重要且紧急": "red", "📅 重要不紧急": "orange", "⚡ 紧急不重要": "blue", "☁️ 不重要不紧急": "gray"}
        
        q_cols = st.columns(2)
        for i, (q_name, q_color) in enumerate(quadrants.items()):
            with q_cols[i % 2]:
                st.markdown(f"**{q_name}**")
                q_tasks = pending_tasks[pending_tasks["priority"] == q_name]
                
                with st.container(border=True):
                    if q_tasks.empty:
                        st.caption("暂无任务")
                    else:
                        for _, row in q_tasks.iterrows():
                            try:
                                ddl_date = datetime.datetime.strptime(row['deadline'], '%Y-%m-%d').date()
                                days_left = (ddl_date - get_now().date()).days
                            except:
                                days_left = 999 
                            
                            if st.checkbox(f"{row['task_name']}", key=f"t_{row['id']}"):
                                supabase.table("tasks").update({"status": "已完成"}).eq("id", row['id']).execute()
                                st.rerun()
                            
                            if days_left < 0:
                                st.markdown(f"<span style='color:red;font-size:12px;'>⚠️ 逾期 {abs(days_left)} 天</span>", unsafe_allow_html=True)
                            elif days_left <= 3:
                                st.markdown(f"<span style='color:orange;font-size:12px;'>⏳ 剩 {days_left} 天</span>", unsafe_allow_html=True)
                            elif days_left != 999:
                                st.markdown(f"<span style='color:gray;font-size:12px;'>📅 剩 {days_left} 天</span>", unsafe_allow_html=True)

        with st.expander("✅ 查看已完成任务"):
            done_tasks = df_task[df_task["status"] == "已完成"]
            for _, row in done_tasks.iterrows():
                st.write(f"~~{row['task_name']}~~")
    else:
        st.info("任务池空空如也，点上面添加一个吧！")


with col_r:
    st.subheader("📚 阅读计划")
    with st.form("add_read_form", clear_on_submit=True):
        book_name = st.text_input("文献/书名", placeholder="输入书名...")
        plan_content = st.text_input("计划内容", placeholder="精读方法论部分...")
        if st.form_submit_button("添加计划") and book_name:
            supabase.table("reading_plan").insert({
                "create_date": get_today_str(), 
                "book_name": book_name, 
                "plan_content": plan_content, 
                "actual_done": "", 
                "status": "阅读中"
            }).execute()
            st.rerun()

    read_res = supabase.table("reading_plan").select("*").execute()
    df_read = pd.DataFrame(read_res.data)
    
    if not df_read.empty:
        reading_now = df_read[df_read["status"] == "阅读中"]
        read_done = df_read[df_read["status"] == "已读完"]
        
        for index, row in reading_now.iterrows():
            with st.expander(f"📌 {row['book_name']}", expanded=False):
                st.write(f"**计划:** {row['plan_content']}")
                actual_done = st.text_input("笔记摘要", key=f"actual_{row['id']}", value=row['actual_done'])
                c1, c2 = st.columns(2)
                if c1.button("✅ 标为已读", key=f"done_{row['id']}"):
                    supabase.table("reading_plan").update({"status": "已读完", "actual_done": actual_done}).eq("id", row['id']).execute()
                    st.rerun()
                if c2.button("💾 存笔记", key=f"save_{row['id']}"):
                    supabase.table("reading_plan").update({"actual_done": actual_done}).eq("id", row['id']).execute()
                    st.toast("笔记已同步云端！")
        
        if not read_done.empty:
            st.markdown("**🏆 已读完**")
            st.dataframe(read_done[["book_name", "actual_done"]].rename(columns={"book_name": "书名", "actual_done": "笔记"}), use_container_width=True, height=150)

st.divider()

# ==========================================
# 灵感区
# ==========================================
st.subheader("💡 灵感碎片收集箱")
col_insp_in, col_insp_out = st.columns([1, 2])

with col_insp_in:
    st.caption("随时捕捉你的 Eureka Moment！")
    with st.form("add_insp_form", clear_on_submit=True):
        insp_content = st.text_area("记录瞬间的想法...", placeholder="例如：可以把第三章的损失函数加上一个正则化项...", height=100)
        col_c1, col_c2 = st.columns([2, 1])
        with col_c1:
            insp_category = st.selectbox("灵感分类", ["🧠 科研Idea", "📝 写作思路", "🐛 代码解法", "💭 随想/吐槽"], label_visibility="collapsed")
        with col_c2:
            submitted_insp = st.form_submit_button("✨ 存入")
            
        if submitted_insp and insp_content:
            supabase.table("inspirations").insert({
                "create_time": get_now().strftime('%Y-%m-%d %H:%M'),
                "content": insp_content,
                "category": insp_category
            }).execute()
            st.rerun()

with col_insp_out:
    insp_res = supabase.table("inspirations").select("*").order("id", desc=True).limit(6).execute()
    df_insp = pd.DataFrame(insp_res.data)
    
    if not df_insp.empty:
        c1, c2 = st.columns(2)
        for i, row in df_insp.iterrows():
            with (c1 if i % 2 == 0 else c2):
                with st.container(border=True):
                    st.markdown(f"**{row['category']}** <span style='color:gray;font-size:12px;float:right;'>{row['create_time'][5:]}</span>", unsafe_allow_html=True)
                    st.write(row['content'])
                    if st.button("🗑️", key=f"del_insp_{row['id']}", help="删除这条灵感"):
                        supabase.table("inspirations").delete().eq("id", row['id']).execute()
                        st.rerun()
    else:
        st.info("暂无灵感，随时准备捕捉你的思维火花！")

# ==========================================
# 导出 Obsidian 模块
# ==========================================
st.divider()
st.subheader("📝 知识沉淀")
if st.button("生成今日科研日报 (Markdown)"):
    today_str = get_today_str()
    today_data = df_log[df_log['date'] == today_str] if not df_log.empty else pd.DataFrame()
    insps = supabase.table("inspirations").select("*").execute().data
    
    md_content = f"# 科研日报 | {today_str}\n\n"
    md_content += f"## 📊 专注统计\n今日总时长：{today_h} 小时\n\n"
    md_content += "## 📝 详细进展\n"
    
    if not today_data.empty:
        for _, row in today_data.iterrows():
            md_content += f"- **[{row['period']}]** {row['task_type']} ({row['duration']}h): {row['details']}\n"
    else:
        md_content += "- 今日暂无打卡记录\n"
    
    md_content += "\n## 💡 灵感捕捉\n"
    has_insp = False
    for insp in insps:
        if insp['create_time'].startswith(today_str):
            md_content += f"- [{insp['category']}] {insp['content']}\n"
            has_insp = True
    if not has_insp:
        md_content += "- 今日暂无灵感记录\n"
            
    st.download_button("下载并放入 Obsidian", data=md_content, file_name=f"Research_Log_{today_str}.md")
