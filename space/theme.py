import streamlit as st


def apply_theme():
    st.markdown("""<style>
    :root { --forest:#23483E; --sage:#728D75; --ink:#263E36; }
    .stApp { background:#F7F8F3; color:var(--ink); }
    [data-testid="stSidebar"] { background:#EEF1E8; border-right:1px solid #DFE6D9; }
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
