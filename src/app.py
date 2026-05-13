import streamlit as st
import plotly.graph_objects as go
from data import fetch_soxl_data
import datetime
import pandas as pd
from streamlit_autorefresh import st_autorefresh

# --- Page Config ---
st.set_page_config(
    page_title="SOXL Tracker",
    page_icon="📈",
    layout="wide"
)

# モバイル向け強制横並びCSSと余白調整 (Task 4.1++)
st.markdown("""
    <style>
    /* カラムの強制横並び */
    [data-testid="column"] {
        flex: 1 1 0% !important;
        min-width: 0px !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.3rem !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.7rem !important;
    }
    div.stButton > button {
        height: 2.2em;
    }
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }
    /* モバイルでのピンチ操作を妨げないための設定 */
    .element-container iframe {
        touch-action: auto !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Auto Refresh ---
st_autorefresh(interval=60 * 1000, key="data_refresh")

# 期間設定の定義
period_map = {
    "1日": {"p": "1d", "i": "1m"},
    "5日": {"p": "5d", "i": "5m"},
    "10日": {"p": "10d", "i": "5m"},
    "1月": {"p": "1mo", "i": "30m"},
    "3月": {"p": "3mo", "i": "60m"}
}

if 'selected_period' not in st.session_state:
    st.session_state.selected_period = "5日"

# --- Fetch Data ---
@st.cache_data(ttl=60)
def load_data(period, interval):
    return fetch_soxl_data(period=period, interval=interval)

p_conf = period_map[st.session_state.selected_period]
with st.spinner(""):
    df = load_data(p_conf["p"], p_conf["i"])

if df.empty:
    st.error("Data error")
    st.stop()

# --- Metrics ---
latest_data = df.iloc[-1]
current_price = latest_data['Close']
current_session = latest_data['Session']
last_update = latest_data.name.strftime("%H:%M")

regular_only = df[df['Session'] == 'Regular']
if not regular_only.empty:
    latest_date = df.index[-1].date()
    prev_regular = regular_only[regular_only.index.date < latest_date]
    if not prev_regular.empty:
        prev_close = prev_regular['Close'].iloc[-1]
    else:
        prev_close = df['Close'].iloc[0]
else:
    prev_close = df['Close'].iloc[0]

change_pct = ((current_price - prev_close) / prev_close) * 100

session_icons = {
    'Pre-market': '🌅Pre',
    'Regular': '☀️Reg',
    'After-market': '🌙Aft',
    'Overnight': '🌌Ovn',
    'Unknown': '❓?'
}
display_session = session_icons.get(current_session, current_session)

# 強制横並びカラム
m1, m2, m3 = st.columns(3)
m1.metric("SOXL", f"${current_price:.2f}", f"{change_pct:+.2f}%")
m2.metric("Market", display_session)
m3.metric("Time", last_update)

# --- Chart ---
fig = go.Figure()
colors = {'Pre-market': '#FFA500', 'Regular': '#1E90FF', 'After-market': '#8A2BE2', 'Overnight': '#2E8B57'}

for session_name in ['Pre-market', 'Regular', 'After-market', 'Overnight']:
    session_data = df[df['Session'] == session_name].copy()
    if session_data.empty: continue
    plot_df_list = []
    session_data['diff'] = session_data.index.to_series().diff()
    gap_threshold = datetime.timedelta(hours=4)
    current_start = 0
    for i in range(1, len(session_data)):
        if session_data['diff'].iloc[i] > gap_threshold:
            plot_df_list.append(session_data.iloc[current_start:i])
            plot_df_list.append(pd.DataFrame(index=[session_data.index[i-1] + datetime.timedelta(seconds=1)]))
            current_start = i
    plot_df_list.append(session_data.iloc[current_start:])
    plot_df = pd.concat(plot_df_list)
    fig.add_trace(go.Scatter(
        x=plot_df.index, y=plot_df['Close'], mode='lines', name=session_name,
        line=dict(color=colors.get(session_name, 'gray'), width=2.5), connectgaps=False
    ))

fig.update_layout(
    xaxis_title="", yaxis_title="", hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=10)),
    margin=dict(l=0, r=0, t=30, b=0), height=420,
    dragmode='pan' # タッチ操作での移動を優先（ピンチズームしやすくする）
)
# ピンチ操作とスクロールズームを有効化
st.plotly_chart(fig, use_container_width=True, config={
    'scrollZoom': True, 
    'displayModeBar': False,
    'showAxisDragHandles': True
})

# --- Controls (Bottom) ---
st.session_state.selected_period = st.radio(
    "Period", options=list(period_map.keys()), 
    index=list(period_map.keys()).index(st.session_state.selected_period), 
    horizontal=True, label_visibility="collapsed"
)

if st.button("🔄 Refresh", use_container_width=True):
    st.cache_data.clear()
    st.rerun()
