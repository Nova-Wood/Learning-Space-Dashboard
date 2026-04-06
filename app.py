import streamlit as st
import pandas as pd
import datetime
import calendar
from supabase import create_client, Client
import plotly.express as px

# --- 基础配置 ---
st.set_page_config(page_title="硕博科研工作流", page_icon="🌿", layout="wide")

# ==========================================
# 🎨 注入淡绿色系主题 CSS
# ==========================================
st.markdown("""
<style>
    .stApp { background-color: #F2FBF5; }
    [data-testid="stSidebar"] { background-color: #E8F5E9 !important; }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF;
        border: 1px solid #C8E6C9 !important;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(165, 214, 167, 0.15);
    }
    .stCheckbox { color: #2E7D32; }
</style>
""", unsafe_allow_html=True)

def module_header(title, bg_color, border_color):
    st.markdown(f"""
    <div style="background-color: {bg_color}; padding: 12px 15px; border-radius: 10px; margin-bottom: 15px; border-left: 6px solid {border_color};">
        <h3 style="margin: 0; color: #2E7D32; font-size: 18px;">{title}</h3>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# 🔒 核心安全防盗门
# ==========================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<h2 style='text-align: center; margin-top: 100px; color: #388E3C;'>🌿 专属科研空间</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        pwd = st.text_input("请输入访问密码", type="password")
        if st.button("🗝️ 开锁进入", use_container_width=True):
            if pwd == st.secrets["APP_PASSWORD"]:
                st.session_state.authenticated = True
                st.rerun() 
            else:
                st.error("❌ 密码错误")
    st.stop() 

# --- 强制设置时区 ---
TZ = datetime.timezone(datetime.timedelta(hours=8))
def get_now(): return datetime.datetime.now(TZ)
def get_today_str(): return get_now().date().strftime('%Y-%m-%d')

# --- Supabase 连接 ---
@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
supabase: Client = init_connection()

# --- 数据加载 ---
def load_all_data():
    conf = supabase.table("system_config").select("*").eq("id", 1).execute().data[0]
    stat = supabase.table("current_status").select("*").eq("id", 1).execute().data[0]
    logs = supabase.table("study_log").select("*").execute().data
    
    # 加载所有习惯数据，用于计算月度统计
    routines_data = supabase.table("daily_routines").select("*").execute().data
    df_routines = pd.DataFrame(routines_data)
    
    # 提取今天的习惯，如果没有则新建
    today_rout = None
    if not df_routines.empty:
        today_match = df_routines[df_routines['date'] == get_today_str()]
        if not today_match.empty:
            today_rout = today_match.iloc[0].to_dict()
            
    if not today_rout:
        supabase.table("daily_routines").insert({"date": get_today_str()}).execute()
        today_rout = {"breakfast":False, "lunch":False, "dinner":False, "early_sleep":False, "early_wake":False}
        
    return conf, stat, pd.DataFrame(logs), df_routines, today_rout

user_config, cur_stat, df_log, df_routines, today_rout = load_all_data()

# ==========================================
# 侧边栏：日历 + 习惯 + 统计图表
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='color: #2E7D32;'>🌿 个人中心</h2>", unsafe_allow_html=True)
    
    # 1. 动态日历
    today_dt = get_now()
    cal = calendar.monthcalendar(today_dt.year, today_dt.month)
    checked_days = df_log[pd.to_datetime(df_log['date']).dt.month == today_dt.month]['date'].apply(lambda x: int(x[-2:])).unique() if not df_log.empty else []
    
    cal_html = f"<div style='background-color:white; padding:10px; border-radius:10px; border:1px solid #C8E6C9; margin-bottom: 15px;'>"
    cal_html += f"<h4 style='text-align:center; color:#388E3C; font-size:14px; margin:0;'>📅 {today_dt.year}年{today_dt.month}月</h4><table style='width:100%; text-align:center; font-size:12px;'>"
    for week in cal:
        cal_html += "<tr>"
        for day in week:
            if day == 0: cal_html += "<td></td>"
            elif day in checked_days: cal_html += f"<td><div style='background-color:#81C784; color:white; border-radius:50%; width:22px; height:22px; line-height:22px; margin:auto;'>{day}</div></td>"
            elif day == today_dt.day: cal_html += f"<td><div style='border:1px solid #81C784; color:#388E3C; border-radius:50%; width:22px; height:22px; line-height:20px; margin:auto;'>{day}</div></td>"
            else: cal_html += f"<td style='color:#9E9E9E;'>{day}</td>"
        cal_html += "</tr>"
    cal_html += "</table></div>"
    st.markdown(cal_html, unsafe_allow_html=True)

    # 2. 三餐作息打卡 (生活复利)
    with st.container(border=True):
        st.markdown("<p style='color:#2E7D32; font-weight:bold; margin-bottom:5px;'>🥗 今日习惯打卡</p>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            b = st.checkbox("🍳 早餐", value=today_rout['breakfast'])
            l = st.checkbox("🍱 午餐", value=today_rout['lunch'])
            d = st.checkbox("🥗 晚餐", value=today_rout['dinner'])
        with c2:
            es = st.checkbox("🌙 早睡", value=today_rout['early_sleep'])
            ew = st.checkbox("☀️ 早起", value=today_rout['early_wake'])
        
        if st.button("更新习惯", use_container_width=True):
            supabase.table("daily_routines").update({
                "breakfast": b, "lunch": l, "dinner": d, "early_sleep": es, "early_wake": ew
            }).eq("date", get_today_str()).execute()
            st.rerun() # 改为 rerun 强制刷新页面，让下方的数据统计立刻变化

    # 3. 每月专注分布图
    st.write("")
    if not df_log.empty:
        df_log['date_obj'] = pd.to_datetime(df_log['date'])
        curr_month_df = df_log[df_log['date_obj'].dt.month == today_dt.month]
        
        if not curr_month_df.empty:
            st.markdown("<p style='color:#2E7D32; font-weight:bold; margin-bottom:0;'>📊 月度专注洞察</p>", unsafe_allow_html=True)
            
            # 趋势图
            daily_stats = curr_month_df.groupby(curr_month_df['date_obj'].dt.day)['duration'].sum().reset_index()
            fig_trend = px.area(daily_stats, x='date_obj', y='duration', 
                               labels={'date_obj':'日期','duration':'小时'},
                               color_discrete_sequence=['#81C784'])
            fig_trend.update_layout(height=150, margin=dict(l=0,r=0,t=10,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})
            
            # 时段占比饼图
            period_stats = curr_month_df.groupby('period')['duration'].sum().reset_index()
            fig_pie = px.pie(period_stats, values='duration', names='period', 
                             color_discrete_sequence=['#C8E6C9','#A5D6A7','#81C784','#66BB6A'])
            fig_pie.update_layout(height=180, margin=dict(l=0,r=0,t=0,b=0), showlegend=False)
            fig_pie.update_traces(textinfo='label+percent')
            st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})

    # 4. 本月习惯养成统计 (新增模块)
    if not df_routines.empty:
        df_routines['date_obj'] = pd.to_datetime(df_routines['date'])
        curr_routines = df_routines[df_routines['date_obj'].dt.month == today_dt.month]
        
        if not curr_routines.empty:
            st.markdown("<p style='color:#2E7D32; font-weight:bold; margin-top:10px; margin-bottom:5px;'>🏆 本月习惯达成</p>", unsafe_allow_html=True)
            
            # 统计布尔值为 True 的数量
            b_count = curr_routines['breakfast'].sum()
            l_count = curr_routines['lunch'].sum()
            d_count = curr_routines['dinner'].sum()
            es_count = curr_routines['early_sleep'].sum()
            ew_count = curr_routines['early_wake'].sum()
            
            with st.container(border=True):
                rc1, rc2 = st.columns(2)
                with rc1:
                    st.markdown(f"<div style='font-size:13px; color:#4CAF50; margin-bottom:4px;'>🍳 早餐: <b>{b_count}</b> 天</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='font-size:13px; color:#4CAF50; margin-bottom:4px;'>🍱 午餐: <b>{l_count}</b> 天</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='font-size:13px; color:#4CAF50;'>🥗 晚餐: <b>{d_count}</b> 天</div>", unsafe_allow_html=True)
                with rc2:
                    st.markdown(f"<div style='font-size:13px; color:#4CAF50; margin-bottom:4px;'>🌙 早睡: <b>{es_count}</b> 天</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='font-size:13px; color:#4CAF50;'>☀️ 早起: <b>{ew_count}</b> 天</div>", unsafe_allow_html=True)

# ==========================================
# 主页面：保持之前的抹茶绿布局
# ==========================================
st.markdown(f"<h1 style='text-align: center; color: #2E7D32;'>{user_config['system_name']}</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #66BB6A;'>{user_config['daily_motto']}</p>", unsafe_allow_html=True)

# --- 模块1：打卡中心 ---
module_header("🕒 实时打卡中心", bg_color="#E8F5E9", border_color="#81C784")
mood = st.radio("当前状态", ["😫 疲惫", "😐 平静", "😊 开心", "🎉 狂喜"], horizontal=True, label_visibility="collapsed")
current_loc = st.radio("所在地", ["工位", "图书馆", "宿舍", "其他"], horizontal=True)

periods = [("上午", "🌅"), ("下午", "☀️"), ("晚上", "🌙"), ("深夜", "🦉")]
p_cols = st.columns(4)
for i, (p_name, p_icon) in enumerate(periods):
    with p_cols[i]:
        with st.container(border=True):
            st.markdown(f"<h4 style='color:#388E3C; margin:0;'>{p_icon} {p_name}</h4>", unsafe_allow_html=True)
            if not cur_stat['is_working']:
                t_type = st.selectbox(f"任务-{p_name}", ["文献阅读", "论文修改", "语言学习", "组会准备"], key=f"t_{p_name}", label_visibility="collapsed")
                if st.button("▶️ 开始", key=f"in_{p_name}", use_container_width=True):
                    supabase.table("current_status").update({"is_working": True, "start_time": get_now().strftime('%Y-%m-%d %H:%M:%S'), "location": current_loc, "task_type": t_type, "period": p_name}).eq("id", 1).execute()
                    st.rerun()
            elif cur_stat['period'] == p_name:
                st.info(f"计时中: {cur_stat['start_time'][11:16]}")
                note = st.text_input("备注", key=f"n_{p_name}", label_visibility="collapsed")
                if st.button("⏹️ 签退", key=f"out_{p_name}", type="primary", use_container_width=True):
                    start_dt = datetime.datetime.strptime(cur_stat['start_time'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=TZ)
                    duration = round((get_now() - start_dt).total_seconds()/3600, 2)
                    supabase.table("study_log").insert({"date": get_today_str(), "period": p_name, "start_time": cur_stat['start_time'], "end_time": get_now().strftime('%Y-%m-%d %H:%M:%S'), "location": cur_stat['location'], "task_type": cur_stat['task_type'], "duration": duration, "details": note, "mood": mood}).execute()
                    supabase.table("current_status").update({"is_working": False}).eq("id", 1).execute()
                    st.rerun()
            else:
                st.button("🔒", disabled=True, use_container_width=True, key=f"lock_{p_name}")

# --- 模块2：任务与阅读 ---
c_left, c_right = st.columns([1.2, 1])
with c_left:
    module_header("🎯 任务四象限", bg_color="#E0F2F1", border_color="#4DB6AC")
    with st.expander("➕ 新增任务"):
        with st.form("add_t", clear_on_submit=True):
            tn = st.text_input("任务名")
            td = st.date_input("DDL", get_now().date())
            tp = st.selectbox("优先级", ["🚀 重要且紧急", "📅 重要不紧急", "⚡ 紧急不重要", "☁️ 不重要不紧急"])
            if st.form_submit_button("添加"):
                supabase.table("tasks").insert({"task_name":tn, "status":"待办", "create_date":get_today_str(), "deadline":str(td), "priority":tp}).execute()
                st.rerun()
    tasks = supabase.table("tasks").select("*").eq("status", "待办").execute().data
    if tasks:
        df_t = pd.DataFrame(tasks)
        for p in ["🚀 重要且紧急", "📅 重要不紧急", "⚡ 紧急不重要", "☁️ 不重要不紧急"]:
            st.caption(p)
            sub = df_t[df_t['priority'] == p]
            for _, r in sub.iterrows():
                if st.checkbox(r['task_name'], key=f"tk_{r['id']}"):
                    supabase.table("tasks").update({"status":"已完成"}).eq("id", r['id']).execute()
                    st.rerun()

with c_right:
    module_header("📚 阅读计划", bg_color="#F1F8E9", border_color="#AED581")
    with st.form("add_r", clear_on_submit=True):
        bn = st.text_input("文献/书名", placeholder="输入书名...", label_visibility="collapsed")
        pc = st.text_input("计划", placeholder="精读方法论部分...", label_visibility="collapsed")
        if st.form_submit_button("添加"):
            supabase.table("reading_plan").insert({"create_date":get_today_str(), "book_name":bn, "plan_content":pc, "status":"阅读中"}).execute()
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

st.write("")

# --- 模块3：灵感碎片 ---
module_header("💡 灵感碎片收集箱", bg_color="#DCEDC8", border_color="#9CCC65")
ci1, ci2 = st.columns([1, 2])
with ci1:
    with st.form("insp", clear_on_submit=True):
        ic = st.text_area("记录想法...", placeholder="例如：损失函数加个正则化项...", height=100, label_visibility="collapsed")
        it = st.selectbox("分类", ["🧠 科研Idea", "📝 写作思路", "🐛 代码解法", "💭 随想/吐槽"], label_visibility="collapsed")
        if st.form_submit_button("✨ 存入"):
            supabase.table("inspirations").insert({"create_time":get_now().strftime('%Y-%m-%d %H:%M'), "content":ic, "category":it}).execute()
            st.rerun()

with ci2:
    insp_res = supabase.table("inspirations").select("*").order("id", desc=True).limit(6).execute()
    df_insp = pd.DataFrame(insp_res.data)
    if not df_insp.empty:
        c1, c2 = st.columns(2)
        for i, row in df_insp.iterrows():
            with (c1 if i % 2 == 0 else c2):
                with st.container(border=True):
                    st.markdown(f"**{row['category']}** <span style='color:gray;font-size:12px;float:right;'>{row['create_time'][5:]}</span>", unsafe_allow_html=True)
                    st.write(row['content'])
                    if st.button("🗑️", key=f"del_insp_{row['id']}", help="删除"):
                        supabase.table("inspirations").delete().eq("id", row['id']).execute()
                        st.rerun()
    else:
        st.info("暂无灵感，随时准备捕捉你的思维火花！")

# ==========================================
# 模块4：知识沉淀导出 
# ==========================================
st.divider()
if st.button("📝 生成今日科研日报 (导出至 Obsidian)"):
    today_str = get_today_str()
    today_data = df_log[df_log['date'] == today_str] if not df_log.empty else pd.DataFrame()
    insps = supabase.table("inspirations").select("*").execute().data
    
    # 获取今天习惯数据
    today_rout_export = df_routines[df_routines['date'] == today_str].iloc[0] if not df_routines[df_routines['date'] == today_str].empty else None
    
    md_content = f"# 科研日报 | {today_str}\n\n"
    
    md_content += "## 🥗 习惯打卡\n"
    if today_rout_export is not None:
        md_content += f"- 早餐: {'✅' if today_rout_export['breakfast'] else '❌'} | "
        md_content += f"午餐: {'✅' if today_rout_export['lunch'] else '❌'} | "
        md_content += f"晚餐: {'✅' if today_rout_export['dinner'] else '❌'}\n"
        md_content += f"- 早睡: {'✅' if today_rout_export['early_sleep'] else '❌'} | "
        md_content += f"早起: {'✅' if today_rout_export['early_wake'] else '❌'}\n\n"

    today_h = today_data['duration'].sum() if not today_data.empty else 0
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
