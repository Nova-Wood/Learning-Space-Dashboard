import streamlit as st
from urllib.parse import quote


def apply_theme():
    st.markdown("""<style>
    :root { --forest:#23483E; --sage:#728D75; --ink:#263E36; }
    .stApp { background:#F7F8F3; color:var(--ink); }
    [data-testid="stSidebar"] { background:#F0F3ED; border-right:1px solid #DFE6D9; }
    [data-testid="stSidebarUserContent"] { padding:0 0 20px; }
    .st-key-sidebar_shell { min-height:calc(100dvh - 100px); gap:0; }
    .space-identity { display:flex; gap:12px; align-items:center; padding:4px 8px 0; }
    .space-monogram { width:42px; height:42px; flex-shrink:0; border-radius:14px; background:#244D40;
      color:#F5F6EE; display:flex; align-items:center; justify-content:center; font:italic 32px Georgia,serif; }
    .space-monogram span { color:#B7CEA1; }
    .space-wordmark { color:#6E8174; font-size:10px; letter-spacing:.18em; font-weight:600; line-height:1.8; }
    .space-title { color:#29483A; font-size:18px; font-weight:650; letter-spacing:.05em; line-height:1.5; }
    [data-testid="stSidebar"] .space-motto { margin:18px 8px 28px; color:#78857B; font-size:12px; letter-spacing:.04em; }
    .sidebar-label { color:#879287; font-size:10px; letter-spacing:.15em; font-weight:600; margin:0 12px 7px; }
    .st-key-workspace_nav { gap:0; }
    .st-key-workspace_nav [role="radiogroup"] { gap:6px; width:100%; margin-top:10px; }
    .st-key-workspace_nav [data-baseweb="radio"] { margin:0; padding:12px 15px; gap:12px; min-height:46px;
      box-sizing:border-box; border:1px solid transparent; border-radius:12px; transition:background .15s,color .15s;
      color:#5F7265; align-items:center; width:100%; }
    .st-key-workspace_nav [data-baseweb="radio"] > div:first-child { display:none; }
    .st-key-workspace_nav [data-baseweb="radio"] > div:last-child { padding:0; }
    .st-key-workspace_nav [data-baseweb="radio"] p { font-size:14px; line-height:20px; font-weight:500; color:#5F7265; }
    .st-key-workspace_nav [data-baseweb="radio"]::before { content:""; display:block; width:19px; height:19px;
      flex-shrink:0; background:currentColor; mask:var(--nav-icon) center/contain no-repeat; }
    .st-key-workspace_nav [data-baseweb="radio"]:hover { background:#E4EBDF; color:#244D40; }
    .st-key-workspace_nav [data-baseweb="radio"]:has(input:checked) { background:#244D40; color:#FFF;
      border-color:#244D40; box-shadow:0 3px 8px #244D4012; }
    .st-key-workspace_nav [data-baseweb="radio"]:has(input:checked) p { color:#FFF; font-weight:600; }
    .st-key-workspace_nav [data-baseweb="radio"]:has(input:focus-visible) { outline:2px solid #6B936D; outline-offset:3px; }
    .st-key-workspace_nav [data-baseweb="radio"]:last-child { margin-top:10px; }
    .st-key-daily_care { background:#FAFBF7; border:1px solid #DDE5D8; border-radius:15px;
      padding:16px 15px 5px; margin-top:28px; gap:9px; box-shadow:0 2px 4px #244D4003; }
    .care-heading { display:flex; align-items:center; justify-content:space-between; color:#405C49; font-size:13px; font-weight:600; }
    .care-count { color:#345C42; font-size:14px; font-variant-numeric:tabular-nums; }
    .care-count span { color:#99A494; font-size:11px; font-weight:400; }
    .st-key-daily_care [data-testid="stProgress"] > div { height:4px; }
    .st-key-daily_care [data-testid="stProgress"] [role="progressbar"] { height:4px; }
    .st-key-daily_care [data-testid="stExpander"] details { border:0; background:transparent; }
    .st-key-daily_care [data-testid="stExpander"] summary { padding:6px 0; min-height:34px; color:#7A877B; }
    .st-key-daily_care [data-testid="stExpander"] summary p { font-size:12px; }
    .st-key-daily_care [data-testid="stExpanderDetails"] { padding:8px 0 10px; }
    .st-key-daily_care [data-testid="stForm"] { border:0; padding:0; }
    .st-key-daily_care [data-testid="stCheckbox"] p { font-size:13px; }
    .st-key-sidebar_shell > [data-testid="stLayoutWrapper"]:has(> .st-key-sidebar_footer) { margin-top:auto; }
    .st-key-sidebar_footer { padding:26px 6px 0; gap:12px; }
    .sidebar-connection { color:#64786B; display:flex; align-items:center; gap:7px; font-size:11px; }
    .sidebar-connection > span { width:6px; height:6px; border-radius:50%; background:#789871; }
    .sidebar-connection.disconnected > span { background:#A2AAA0; }
    .sidebar-timezone { color:#8D988E; font-size:10px; margin-top:5px; padding-left:13px; }
    .st-key-sidebar_footer button { background:transparent; border-color:transparent; min-height:34px;
      color:#6B7D6E; font-size:12px; }
    .st-key-sidebar_footer button p { font-size:12px; }
    .st-key-sidebar_footer button:hover { background:#E2EADD; border-color:transparent; }
    .st-key-sidebar_footer [data-testid="stHorizontalBlock"] { flex-direction:row; gap:8px; }
    .st-key-sidebar_footer [data-testid="stColumn"] { min-width:0; flex:1; }
    .block-container { padding-top:2.4rem; padding-bottom:3rem; max-width:1360px; }
    h1,h2,h3 { color:var(--forest); letter-spacing:-.025em; }
    h1 { font-family:Georgia,'Noto Serif SC',serif; }
    [data-testid="stMetric"] { background:white; border:1px solid #E3E8DD; border-radius:16px; padding:18px 22px; }
    [data-testid="stMetricLabel"] { color:#708078; font-size:13px; }
    [data-testid="stMetricValue"] { color:var(--forest); font-family:Georgia,serif; font-size:32px; }
    [data-testid="stVerticalBlockBorderWrapper"] { border-radius:16px; }
    .stButton > button, .stDownloadButton > button, .stLinkButton > a { border-radius:10px; min-height:42px; }
    .stButton > button[kind="primary"] { background:#315D48; border-color:#315D48; }
    .brand { font-size:11px; letter-spacing:.20em; color:#69806C; font-weight:600; }
    .brand-name { font-family:Georgia,serif; font-size:29px; color:#23483E; margin:6px 0; }
    .subtle { color:#738177; font-size:13px; line-height:1.7; }
    .hero { padding:30px 34px; border-radius:22px; margin:10px 0 24px;
      background:linear-gradient(115deg,#23483E 0%,#355D48 72%,#64816A 100%); color:#FFF; }
    .hero .eyebrow { font-size:11px; letter-spacing:.2em; color:#CCDBCA; }
    .hero h2 { color:#FFF; font-weight:500; font-size:30px; margin:10px 0; }
    .hero p { color:#E0E9DA; font-size:14px; margin:0; line-height:1.8; }
    .section-kicker { color:#6A826F; font-size:11px; letter-spacing:.18em; margin:26px 0 4px; }
    .agenda-row { border-left:3px solid #93AA84; padding:10px 15px; margin:8px 0 13px;
      background:#F0F4EA; border-radius:0 10px 10px 0; }
    .agenda-row b { color:#294D3C; font-size:14px; }
    .agenda-row small { color:#687D6B; display:block; margin-top:3px; }
    .focus-live { background:#EDF4E8; border-radius:12px; padding:16px 20px; color:#315D48; margin-bottom:14px; }
    .empty { padding:25px 18px; background:#F0F3EB; border-radius:12px; color:#708078; line-height:1.8; }
    [data-testid="stForm"] { border-color:#E0E6D9; border-radius:14px; }
    @media (max-width:700px) {
      .block-container { padding:1rem; } .hero { padding:22px; } .hero h2 { font-size:24px; }
      [data-testid="stMetric"] { padding:12px; }
    }
    </style>""", unsafe_allow_html=True)
    # Static vector masks keep navigation icons consistent without external assets.
    icons = [
        '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
        '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 11h18M8 15h2m4 0h2m-8 3h2"/>',
        '<path d="M12 5C9 3 5 3 3 4v16c3-1 6-1 9 1 3-2 6-2 9-1V4c-2-1-6-1-9 1Zm0 0v16"/>',
        '<path d="M4 3v17h17M8 15v-4m5 4V7m5 8V4"/>',
        '<path d="M4 7h16M4 17h16"/><circle cx="9" cy="7" r="3" fill="white"/><circle cx="15" cy="17" r="3" fill="white"/>',
    ]
    rules = []
    for index, paths in enumerate(icons):
        svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="black" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round">' + paths + '</svg>'
        rules.append('.st-key-workspace_nav label:has(input[value="' + str(index) + '"]) { --nav-icon:url("data:image/svg+xml,' + quote(svg, safe='') + '"); }')
    st.markdown('<style>' + ''.join(rules) + '</style>', unsafe_allow_html=True)
