import streamlit as st
import pandas as pd
import datetime
import os
import plotly.express as px
import json

# --- 页面基础设置 (必须放在最前面) ---
st.set_page_config(page_title="专属科研管理系统", page_icon="🎓", layout="wide")

# --- 数据文件路径 ---
LOG_FILE = "study_log.csv"
TASK_FILE = "tasks.csv"
READ_FILE = "reading_plan.csv"
CONFIG_FILE = "config.json"

# --- 初始化数据文件 ---
if not os.path.exists(LOG_FILE):
    pd.DataFrame(columns=["日期", "时段", "开始时间", "结束时间", "地点", "任务类型", "时长(小时)", "具体内容", "心情"]).to_csv(LOG_FILE, index=False)
if not os.path.exists(TASK_FILE):
    pd.DataFrame(columns=["任务名称", "状态", "创建日期"]).to_csv(TASK_FILE, index=False)
if not os.path.exists(READ_FILE):
    pd.DataFrame(columns=["创建日期", "文献/书名", "计划内容", "实际完成", "状态"]).to_csv(READ_FILE, index=False)

# --- 初始化或读取配置文件 ---
if not os.path.exists(CONFIG_FILE):
    default_config = {
        "system_name": "Novawood's Learning Space",
        "daily_motto": "今日目标: 不生气、不摸鱼、写论文一切顺利。"
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(default_config, f, ensure_ascii=False)

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    user_config = json.load(f)

# --- 初始化 Session State ---
if 'is_working' not in st.session_state:
    st.session_state.is_working = False
if 'start_time' not in st.session_state:
    st.session_state.start_time = None
if 'current_loc' not in st.session_state:
    st.session_state.current_loc = ""
if 'current_type' not in st.session_state:
    st.session_state.current_type = ""
if 'current_period' not in st.session_state:
    st.session_state.current_period = ""

# ==========================================
# 左侧边栏 (个性化设置 & 今日状态)
# ==========================================
with st.sidebar:
    st.title("🎓 控制面板")
    
    with st.expander("⚙️ 个性化参数设置", expanded=False):
        with st.form("config_form"):
            new_name = st.text_input("系统名称", value=user_config["system_name"])
            new_motto = st.text_input("今日目标", value=user_config["daily_motto"])
            if st.form_submit_button("保存设置"):
                user_config["system_name"] = new_name
                user_config["daily_motto"] = new_motto
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(user_config, f, ensure_ascii=False)
                st.success("✅ 设置已保存！")
                st.rerun()

    st.markdown("---")
    
    st.subheader("💡 今日状态")
    today_str = str(datetime.date.today())
    try:
        df_log = pd.read_csv(LOG_FILE)
        today_logs = df_log[df_log["日期"] == today_str] if not df_log.empty else pd.DataFrame()
        today_hours = today_logs["时长(小时)"].sum() if not today_logs.empty else 0
        total_hours = df_log["时长(小时)"].sum() if not df_log.empty else 0
    except:
        today_hours = 0
        total_hours = 0

    st.metric("今日打卡时长", f"{round(today_hours, 1)} 小时")
    st.metric("累计总时长", f"{round(total_hours, 1)} 小时")
    
    st.markdown("**当前状态:**")
    if st.session_state.is_working:
        st.info(f"🟢 进行中: {st.session_state.current_type}")
        st.caption(f"📍 {st.session_state.current_loc} | 🕒 {st.session_state.current_period}")
    else:
        st.write("⚪ 摸鱼中 (未签到)")


# ==========================================
# 主工作区：顶部横幅
# ==========================================
st.markdown(f"<h1 style='text-align: center; color: #4A90E2;'>{user_config['system_name']}</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>🐱 点击: 0次 &nbsp;&nbsp;&nbsp; 🐶 点击: 0次</p>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: #4A90E2;'>{user_config['daily_motto']}</p>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: gray;'>{datetime.datetime.now().strftime('%Y年%m月%d日 %A %H:%M')}</p>", unsafe_allow_html=True)
st.divider()

# ==========================================
# 主工作区：专属打卡中心
# ==========================================
st.markdown("### 💙 今日心情打卡")
mood = st.radio("心情选择:", ["😊 充实/开心", "😐 平静/正常", "😫 疲惫/头秃", "😤 烦躁/卡壳", "🎉 狂喜/突破"], horizontal=True, label_visibility="collapsed")
st.write("") # 留点空隙

st.markdown("### 🕒 专注打卡记录")

# 第一部分：上方点击打卡地点
st.markdown("**📍 选择当前所在地:**")
current_location = st.radio("地点选择:", ["工位", "图书馆", "宿舍", "假期"], horizontal=True, label_visibility="collapsed")
st.write("") # 留点空隙

# 第二部分：下方分时段四大模块
periods_data = [
    {"name": "上午", "icon": "🌅", "time": "06:00 - 12:00"},
    {"name": "下午", "icon": "☀️", "time": "12:00 - 18:00"},
    {"name": "晚上", "icon": "🌙", "time": "18:00 - 24:00"},
    {"name": "深夜", "icon": "🦉", "time": "00:00 - 06:00"}
]

cols = st.columns(4)

for i, p_info in enumerate(periods_data):
    p_name = p_info["name"]
    with cols[i]:
        # 使用 border=True 创造卡片效果
        with st.container(border=True):
            st.markdown(f"<h4 style='text-align: center; margin-bottom: 0;'>{p_info['icon']} {p_name}</h4>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center; color: gray; font-size: 13px;'>{p_info['time']}</p>", unsafe_allow_html=True)
            
            # 状态判定逻辑
            if not st.session_state.is_working:
                # 未签到状态：显示任务选择和签到按钮
                task_type = st.selectbox(f"任务类型 ({p_name})", ["文献阅读", "论文撰写/修改", "实验/跑代码", "课程学习", "组会/汇报", "其他"], key=f"task_{p_name}", label_visibility="collapsed")
                if st.button("▶️ 签到", key=f"in_{p_name}", use_container_width=True):
                    st.session_state.is_working = True
                    st.session_state.start_time = datetime.datetime.now()
                    st.session_state.current_loc = current_location
                    st.session_state.current_type = task_type
                    st.session_state.current_period = p_name
                    st.rerun()
            
            else:
                # 已签到状态：判断是否是当前正在工作的卡片
                if st.session_state.current_period == p_name:
                    start_str = st.session_state.start_time.strftime('%H:%M:%S')
                    st.success(f"专注中...\n\n开始于 {start_str}")
                    
                    details = st.text_input("记录进展", key=f"detail_{p_name}", placeholder="简述进展...", label_visibility="collapsed")
                    
                    if st.button("⏹️ 签退", key=f"out_{p_name}", type="primary", use_container_width=True):
                        end_time = datetime.datetime.now()
                        duration = round((end_time - st.session_state.start_time).total_seconds() / 3600, 2)
                        
                        new_log = pd.DataFrame({
                            "日期": [st.session_state.start_time.date()],
                            "时段": [p_name],
                            "开始时间": [st.session_state.start_time.strftime('%Y-%m-%d %H:%M:%S')],
                            "结束时间": [end_time.strftime('%Y-%m-%d %H:%M:%S')],
                            "地点": [st.session_state.current_loc],
                            "任务类型": [st.session_state.current_type],
                            "时长(小时)": [duration],
                            "具体内容": [details],
                            "心情": [mood] # 抓取顶部的心情
                        })
                        new_log.to_csv(LOG_FILE, mode="a", header=False, index=False)
                        
                        st.session_state.is_working = False
                        st.session_state.start_time = None
                        st.success(f"✅ 打卡成功！共 {duration} 小时")
                        st.rerun()
                else:
                    # 其他非工作卡片：显示锁定状态
                    st.info("锁定中")
                    st.caption("其他时段正在专注")
                    st.button("🔒", key=f"lock_{p_name}", disabled=True, use_container_width=True)

st.divider()

# ==========================================
# 主工作区：中部双列布局 (阅读 vs 任务)
# ==========================================
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📚 阅读计划")
    with st.form("add_read_form", clear_on_submit=True):
        book_name = st.text_input("文献/书名", placeholder="输入书名...")
        plan_content = st.text_input("计划内容", placeholder="精读方法论部分...")
        if st.form_submit_button("添加计划") and book_name:
            read_df = pd.DataFrame({"创建日期": [datetime.date.today()], "文献/书名": [book_name], "计划内容": [plan_content], "实际完成": [""], "状态": ["阅读中"]})
            read_df.to_csv(READ_FILE, mode="a", header=False, index=False)
            st.rerun()

    try:
        reads = pd.read_csv(READ_FILE)
        if not reads.empty:
            reading_now = reads[reads["状态"] == "阅读中"]
            read_done = reads[reads["状态"] == "已读完"]
            
            for index, row in reading_now.iterrows():
                with st.expander(f"📌 {row['文献/书名']}", expanded=False):
                    st.write(f"**计划:** {row['计划内容']}")
                    actual_done = st.text_input("笔记摘要", key=f"actual_{index}")
                    c1, c2 = st.columns(2)
                    if c1.button("✅ 标为已读", key=f"done_{index}"):
                        reads.at[index, "状态"] = "已读完"
                        reads.at[index, "实际完成"] = actual_done
                        reads.to_csv(READ_FILE, index=False)
                        st.rerun()
                    if c2.button("💾 存笔记", key=f"save_{index}"):
                        reads.at[index, "实际完成"] = actual_done
                        reads.to_csv(READ_FILE, index=False)
                        st.toast("笔记保存成功！")
            
            if not read_done.empty:
                st.markdown("**🏆 已读完**")
                st.dataframe(read_done[["文献/书名", "实际完成"]], use_container_width=True, height=150)
    except Exception as e:
        pass

with col_right:
    st.subheader("📋 任务管理")
    with st.form("add_task_form", clear_on_submit=True):
        new_task = st.text_input("新增零碎任务", placeholder="整理组会PPT...")
        if st.form_submit_button("添加任务") and new_task:
            task_df = pd.DataFrame({"任务名称": [new_task], "状态": ["待办"], "创建日期": [datetime.date.today()]})
            task_df.to_csv(TASK_FILE, mode="a", header=False, index=False)
            st.rerun()

    try:
        tasks = pd.read_csv(TASK_FILE)
        if not tasks.empty:
            pending_tasks = tasks[tasks["状态"] == "待办"]
            done_tasks = tasks[tasks["状态"] == "已完成"]
            
            st.write("🔴 **待办**")
            for index, row in pending_tasks.iterrows():
                if st.checkbox(row["任务名称"], key=f"task_{index}"):
                    tasks.at[index, "状态"] = "已完成"
                    tasks.to_csv(TASK_FILE, index=False)
                    st.rerun()
                    
            st.write("🟢 **完成**")
            for index, row in done_tasks.iterrows():
                st.write(f"~~{row['任务名称']}~~")
    except Exception as e:
        pass

st.divider()

# ==========================================
# 主工作区：底部统计
# ==========================================
st.subheader("📊 总体数据统计")
try:
    df_log = pd.read_csv(LOG_FILE)
    if not df_log.empty:
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            daily_trend = df_log.groupby("日期")["时长(小时)"].sum().reset_index()
            fig_bar = px.bar(daily_trend, x="日期", y="时长(小时)", title="📅 每日学习时长", text_auto=True)
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with col_chart2:
            type_dist = df_log.groupby("任务类型")["时长(小时)"].sum().reset_index()
            fig_pie1 = px.pie(type_dist, values="时长(小时)", names="任务类型", title="🧩 精力分布", hole=0.3)
            st.plotly_chart(fig_pie1, use_container_width=True)
        
        with st.expander("📝 展开查看详细打卡流水", expanded=False):
            st.dataframe(df_log.sort_values(by="开始时间", ascending=False), use_container_width=True)
    else:
        st.info("暂无打卡数据，图表将在完成第一次打卡后生成。")
except Exception as e:
    st.error(f"读取统计数据失败: {e}")