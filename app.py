import streamlit as st
import pandas as pd
import datetime
from supabase import create_client, Client
import plotly.express as px

# --- 基础配置 ---
st.set_page_config(page_title="硕博科研工作流", page_icon="🎓", layout="wide")

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
    today_h = df_log[df_log['date'] == str(datetime.date.today())]['duration'].sum() if not df_log.empty else 0
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
                t_type = st.selectbox(f"任务-{p_name}", ["文献阅读", "论文修改", "代码实验", "组会准备"], key=f"t_{p_name}")
                if st.button("开始签到", key=f"in_{p_name}", use_container_width=True):
                    supabase.table("current_status").update({
                        "is_working": True, "start_time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        "location": current_loc, "task_type": t_type, "period": p_name
                    }).eq("id", 1).execute()
                    st.rerun()
            elif cur_stat['period'] == p_name:
                st.info(f"计时中: {cur_stat['start_time'][11:16]}")
                note = st.text_input("进展备注", key=f"n_{p_name}")
                if st.button("停止签退", key=f"out_{p_name}", type="primary", use_container_width=True):
                    start_dt = datetime.datetime.strptime(cur_stat['start_time'], '%Y-%m-%d %H:%M:%S')
                    duration = round((datetime.datetime.now() - start_dt).total_seconds()/3600, 2)
                    supabase.table("study_log").insert({
                        "date": str(datetime.date.today()), "period": p_name, "start_time": cur_stat['start_time'],
                        "end_time": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        "location": cur_stat['location'], "task_type": cur_stat['task_type'],
                        "duration": duration, "details": note, "mood": mood
                    }).execute()
                    supabase.table("current_status").update({"is_working": False}).eq("id", 1).execute()
                    st.rerun()
            else:
                st.button("🔒 锁定", disabled=True, use_container_width=True, key=f"lock_{p_name}")

# ==========================================
# 功能区：任务四象限 & 阅读计划
# ==========================================
col_l, col_r = st.columns(2)
with col_l:
    st.subheader("📋 任务四象限")
    # 此处省略复杂的增删逻辑，参考之前版本的四象限代码渲染...
    st.caption("建议优先处理【重要且紧急】的任务")

with col_r:
    st.subheader("📚 阅读计划")
    # 参考之前的阅读模块代码...

# ==========================================
# 灵感区
# ==========================================
st.subheader("💡 灵感碎片")
# 参考灵感收集箱代码...

# ==========================================
# 导出 Obsidian 模块
# ==========================================
st.divider()
st.subheader("📝 知识沉淀")
if st.button("生成今日科研日报 (Markdown)"):
    # 获取今日所有数据
    today_data = df_log[df_log['date'] == str(datetime.date.today())]
    insps = supabase.table("inspirations").select("*").execute().data
    
    md_content = f"# 科研日报 | {datetime.date.today()}\n\n"
    md_content += f"## 📊 专注统计\n今日总时长：{today_h} 小时\n\n"
    md_content += "## 📝 详细进展\n"
    for _, row in today_data.iterrows():
        md_content += f"- **[{row['period']}]** {row['task_type']} ({row['duration']}h): {row['details']}\n"
    
    md_content += "\n## 💡 灵感捕捉\n"
    for insp in insps:
        if insp['create_time'].startswith(str(datetime.date.today())):
            md_content += f"- [{insp['category']}] {insp['content']}\n"
            
    st.download_button("下载并放入 Obsidian", data=md_content, file_name=f"Research_Log_{datetime.date.today()}.md")
