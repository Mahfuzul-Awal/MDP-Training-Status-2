import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
import time

st.set_page_config(page_title="PTC Drilldown V2", layout="wide")

st.markdown("""
<style>
  .stApp { background: #fbfbfd; }
  h1, h2, h3 { letter-spacing: -0.02em; }
  section[data-testid="stFileUploaderDropzone"] {
    border: 1px dashed rgba(0,0,0,0.15);
    border-radius: 14px;
    background: rgba(255,255,255,0.85);
    padding: 16px;
  }
  div.stButton > button {
    border-radius: 999px;
    padding: 0.55rem 0.95rem;
    border: 1px solid rgba(0,0,0,0.08);
    background: white;
  }
  div.stButton > button:hover {
    border: 1px solid rgba(0,0,0,0.18);
    background: rgba(255,255,255,0.95);
  }
  div[data-testid="stDataFrame"] {
    border-radius: 14px;
    overflow: hidden;
    border: 1px solid rgba(0,0,0,0.08);
    background: white;
  }
  .card {
    border: 1px solid rgba(0,0,0,0.08);
    border-radius: 18px;
    background: white;
    padding: 14px 16px;
    box-shadow: 0 6px 24px rgba(0,0,0,0.04);
    margin-bottom: 14px;
  }
  .crumb {
    font-size: 0.95rem;
    color: rgba(0,0,0,0.65);
    margin-top: -6px;
    margin-bottom: 8px;
  }
  .crumb b { color: rgba(0,0,0,0.86); }
  .legend-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 10px;
    font-size: 0.88rem;
  }
  .legend-table th {
    background: #f0f4ff;
    padding: 6px 10px;
    text-align: left;
    border-bottom: 2px solid #d0d8f0;
    font-weight: 600;
    color: #333;
  }
  .legend-table td {
    padding: 5px 10px;
    border-bottom: 1px solid #f0f0f0;
    color: #444;
    vertical-align: top;
  }
  .legend-table tr:hover td {
    background: #f7f9ff;
  }
  .num-badge {
    display: inline-block;
    background: #1f77b4;
    color: white;
    border-radius: 50%;
    width: 22px;
    height: 22px;
    text-align: center;
    line-height: 22px;
    font-size: 0.78rem;
    font-weight: bold;
    margin-right: 4px;
  }
  footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ---------- Helpers ----------
@st.cache_data(show_spinner=False)
def load_data(file_bytes: bytes):
    try:
        org = pd.read_excel(BytesIO(file_bytes), sheet_name="Organized")
        pend = pd.read_excel(BytesIO(file_bytes), sheet_name="Pending")
        return org, pend
    except Exception as e:
        st.error(f"Could not read sheets 'Organized' / 'Pending': {e}")
        st.stop()

def normalize_status(series):
    return series.astype(str).str.strip().str.lower()

def get_selected_x(event):
    if not event:
        return None
    sel = event.get("selection")
    if not sel:
        return None
    pts = sel.get("points")
    if not pts:
        return None
    return pts[0].get("x")

def go(screen, status=None, title=None, dept=None):
    with st.spinner("Loading…"):
        time.sleep(0.18)
    st.session_state.screen = screen
    if status is not None:
        st.session_state.selected_status = status
    if title is not None:
        st.session_state.selected_title = title
    if dept is not None:
        st.session_state.selected_department = dept
    st.rerun()

def reset_to_home():
    st.session_state.screen = "home"
    st.session_state.selected_status = None
    st.session_state.selected_title = None
    st.session_state.selected_department = None

def crumb(text):
    st.markdown(f'<div class="crumb">{text}</div>', unsafe_allow_html=True)

def card_open():
    st.markdown('<div class="card">', unsafe_allow_html=True)

def card_close():
    st.markdown("</div>", unsafe_allow_html=True)

def bar_with_labels(df, xcol, ycol, ytitle, hover_x_name=None, hover_y_name=None, pct_col=None):
    if hover_x_name is None:
        hover_x_name = xcol
    if hover_y_name is None:
        hover_y_name = ytitle

    if pct_col and pct_col in df.columns:
        fig = px.bar(df, x=xcol, y=ycol, text=ycol, custom_data=[pct_col])
        htemplate = f"{hover_x_name}: %{{x}}<br>{hover_y_name}: %{{y}}<br>Percentage: %{{customdata[0]}}<extra></extra>"
    else:
        fig = px.bar(df, x=xcol, y=ycol, text=ycol)
        htemplate = f"{hover_x_name}: %{{x}}<br>{hover_y_name}: %{{y}}<extra></extra>"

    fig.update_traces(textposition="outside", cliponaxis=False, hovertemplate=htemplate)
    fig.update_layout(
        xaxis_title="",
        yaxis_title=ytitle,
        clickmode="event+select",
        margin=dict(l=10, r=10, t=10, b=10),
        uniformtext_minsize=10,
        uniformtext_mode="hide",
        hoverlabel=dict(font_size=16, bgcolor="white", bordercolor="rgba(0,0,0,0.25)"),
    )
    return fig

# ---------- State ----------
for key, default in [
    ("screen", "home"),
    ("selected_status", None),
    ("selected_title", None),
    ("selected_department", None),
    ("page_start", 0),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ---------- Header ----------
left, right = st.columns([0.78, 0.22])
with left:
    st.markdown("## PTC Training Status — V2")
    st.caption("Click charts to drill down • Hover bars to see details")
with right:
    if st.button("🔄 Reset", use_container_width=True):
        reset_to_home()
        st.rerun()

uploaded = st.file_uploader("Upload monthly Excel (.xlsx)", type=["xlsx"])

if not uploaded:
    card_open()
    st.markdown("### Get started")
    st.write("Upload your monthly Excel file containing **Organized** and **Pending** sheets.")
    st.write("Then click the bars to drill down.")
    card_close()
    st.stop()

file_bytes = uploaded.getvalue()
org, pend = load_data(file_bytes)
pend = pend.copy()
pend["_status_norm"] = normalize_status(pend["Status"])

def get_current_df():
    status = st.session_state.selected_status
    if status == "done":
        return org
    elif status in ["offered", "notdone"]:
        return pend[pend["_status_norm"] == status]
    return pd.DataFrame()

def get_status_label():
    return {
        "done": "Done",
        "offered": "Offered",
        "notdone": "Not Done"
    }.get(st.session_state.selected_status, "")

# ================================================
# ---------- HOME --------------------------------
# ================================================
if st.session_state.screen == "home":
    crumb("<b>Home</b>")

    done_count = len(org)
    offered_count = int((pend["_status_norm"] == "offered").sum())
    notdone_count = int((pend["_status_norm"] == "notdone").sum())
    total_count = done_count + offered_count + notdone_count

    df_top = pd.DataFrame({
        "Category": ["Done", "Offered", "Not Done"],
        "Count": [done_count, offered_count, notdone_count]
    })
    df_top["Percentage"] = df_top["Count"].apply(
        lambda x: f"{(x / total_count * 100):.1f}%" if total_count > 0 else "0.0%"
    )

    card_open()
    st.markdown("### Overall Status")
    fig = bar_with_labels(
        df_top, "Category", "Count", "Count",
        hover_x_name="Status", hover_y_name="Count", pct_col="Percentage"
    )
    event = st.plotly_chart(
        fig, key="top_chart", use_container_width=True,
        height=520, on_select="rerun", selection_mode=("points",)
    )
    card_close()

    clicked = get_selected_x(event)
    if clicked == "Done":
        go("titles", status="done")
    elif clicked == "Offered":
        go("titles", status="offered")
    elif clicked == "Not Done":
        go("titles", status="notdone")

# ================================================
# ---------- TITLES ------------------------------
# ================================================
elif st.session_state.screen == "titles":
    label = get_status_label()
    crumb(f'Home → <b>{label}</b> → Training Titles')

    c1, c2 = st.columns([0.15, 0.85])
    with c1:
        if st.button("← Back"):
            go("home")
    with c2:
        st.markdown(f"### Training Title vs {label} Count")

    df_current = get_current_df()
    title_counts = (
        df_current.groupby("Training Title", dropna=False)
        .size().reset_index(name="Count")
        .sort_values("Count", ascending=False)
        .reset_index(drop=True)
    )

    if title_counts.empty:
        st.info("No records found.")
        st.stop()

    total_bars = len(title_counts)

    card_open()

    # Slider + total
    col_slider, col_info = st.columns([0.75, 0.25])
    with col_slider:
        bars_per_page = st.slider(
            "Number of bars to show at once",
            min_value=5,
            max_value=min(30, total_bars),
            value=min(15, total_bars),
            step=1,
            key=f"slider_{st.session_state.selected_status}"
        )
    with col_info:
        st.markdown(f"<br>**Total: {total_bars} titles**", unsafe_allow_html=True)

    # Navigation buttons
    max_start = max(0, total_bars - bars_per_page)
    if st.session_state.page_start > max_start:
        st.session_state.page_start = 0

    b1, b2, b3, b4, b5 = st.columns([0.12, 0.12, 0.44, 0.12, 0.12])
    with b1:
        if st.button("⏮ First"):
            st.session_state.page_start = 0
            st.rerun()
    with b2:
        if st.button("◀ Prev"):
            st.session_state.page_start = max(0, st.session_state.page_start - bars_per_page)
            st.rerun()
    with b3:
        end_idx = min(st.session_state.page_start + bars_per_page, total_bars)
        st.markdown(
            f"<div style='text-align:center; padding-top:6px;'>"
            f"Showing <b>{st.session_state.page_start + 1}</b> – <b>{end_idx}</b> of <b>{total_bars}</b>"
            f"</div>",
            unsafe_allow_html=True
        )
    with b4:
        if st.button("Next ▶"):
            st.session_state.page_start = min(max_start, st.session_state.page_start + bars_per_page)
            st.rerun()
    with b5:
        if st.button("Last ⏭"):
            st.session_state.page_start = max_start
            st.rerun()

    # Slice data
    start = st.session_state.page_start
    title_slice = title_counts.iloc[start: start + bars_per_page].copy()
    title_slice["#"] = range(start + 1, start + len(title_slice) + 1)
    title_slice["Label"] = title_slice["#"].astype(str)

    # Chart — bars labeled with numbers only
    fig2 = px.bar(
        title_slice,
        x="Label",
        y="Count",
        text="Count",
        custom_data=["Training Title", "#"],
    )
    fig2.update_traces(
        textposition="outside",
        cliponaxis=False,
        marker_color="#1f77b4",
        width=0.6,
        hovertemplate="<b>#%{customdata[1]} %{customdata[0]}</b><br>Count: %{y}<extra></extra>",
    )
    fig2.update_layout(
        xaxis=dict(title="", tickfont=dict(size=13, color="#333")),
        yaxis_title="Count",
        bargap=0.25,
        clickmode="event+select",
        margin=dict(l=10, r=10, t=30, b=10),
        hoverlabel=dict(font_size=15, bgcolor="white", bordercolor="rgba(0,0,0,0.25)"),
        uniformtext_minsize=10,
        uniformtext_mode="hide",
    )

    event2 = st.plotly_chart(
        fig2,
        key=f"titles_chart_{st.session_state.selected_status}_{start}_{bars_per_page}",
        use_container_width=True,
        height=500,
        on_select="rerun",
        selection_mode=("points",),
    )

    # Legend table below chart
    st.markdown("**Training Title Legend:**")
    rows_html = ""
    for _, row in title_slice.iterrows():
        rows_html += f"""
        <tr>
          <td><span class="num-badge">{int(row['#'])}</span></td>
          <td>{row['Training Title']}</td>
          <td style="text-align:center;"><b>{int(row['Count'])}</b></td>
        </tr>
        """
    st.markdown(f"""
        <table class="legend-table">
          <thead>
            <tr>
              <th style="width:40px;">#</th>
              <th>Training Title</th>
              <th style="width:60px; text-align:center;">Count</th>
            </tr>
          </thead>
          <tbody>
            {rows_html}
          </tbody>
        </table>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.caption("Click a bar to drill into departments • Hover bar for full title name")

    card_close()

    # Match clicked number label back to title
    clicked_label = get_selected_x(event2)
    if clicked_label is not None:
        matched = title_slice[title_slice["Label"] == str(clicked_label)]
        if not matched.empty:
            go("departments", title=matched.iloc[0]["Training Title"])

# ==============================================
