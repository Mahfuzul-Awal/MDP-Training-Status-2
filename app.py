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
  footer { visibility: hidden; }
  .scroll-wrap {
    overflow-x: scroll;
    width: 100%;
    scroll-behavior: smooth;
    scrollbar-width: auto;
    scrollbar-color: #555 #e0e0e0;
  }
  .scroll-wrap::-webkit-scrollbar {
    height: 14px;
  }
  .scroll-wrap::-webkit-scrollbar-track {
    background: #e0e0e0;
    border-radius: 8px;
  }
  .scroll-wrap::-webkit-scrollbar-thumb {
    background-color: #555;
    border-radius: 8px;
    border: 2px solid #e0e0e0;
  }
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

    card_open()

    total_bars = len(title_counts)

    # Slider to control visible window width
    bars_per_page = st.slider(
        "Number of bars to show at once",
        min_value=5,
        max_value=min(30, total_bars),
        value=min(15, total_bars),
        step=1,
        key=f"slider_{st.session_state.selected_status}"
    )

    # Full chart rendered at total width, windowed by CSS
    chart_width = max(900, total_bars * 80)
    visible_width = bars_per_page * 80

    fig2 = bar_with_labels(
        title_counts, "Training Title", "Count", "Count",
        hover_x_name="Training Title", hover_y_name=f"{label} Count"
    )
    fig2.update_xaxes(showticklabels=False)
    fig2.update_traces(width=0.6)
    fig2.update_layout(
        bargap=0.25,
        width=chart_width,
        height=520,
    )

    # Top scrollbar mirror div
    st.markdown(f"""
        <div style="overflow-x:scroll; width:{visible_width}px; height:14px; scroll-behavior:smooth;"
             id="top-scroll"
             onscroll="document.getElementById('chart-scroll').scrollLeft=this.scrollLeft">
            <div style="width:{chart_width}px; height:1px;"></div>
        </div>
    """, unsafe_allow_html=True)

    # Main scrollable chart div
    st.markdown(f"""
        <div class="scroll-wrap"
             id="chart-scroll"
             style="max-width:{visible_width}px;"
             onscroll="document.getElementById('top-scroll').scrollLeft=this.scrollLeft">
    """, unsafe_allow_html=True)

    event2 = st.plotly_chart(
        fig2,
        key=f"titles_chart_{st.session_state.selected_status}_{bars_per_page}",
        use_container_width=False,
        height=520,
        on_select="rerun",
        selection_mode=("points",),
    )

    st.markdown("</div>", unsafe_allow_html=True)

    st.caption(
        f"Total: {total_bars} training titles • "
        f"Showing {bars_per_page} at a time • "
        f"Scroll to explore all • Hover a bar for its name"
    )

    card_close()

    clicked = get_selected_x(event2)
    if clicked is not None:
        go("departments", title=clicked)

# ================================================
# ---------- DEPARTMENTS -------------------------
# ================================================
elif st.session_state.screen == "departments":
    label = get_status_label()
    title = st.session_state.selected_title
    crumb(f'Home → {label} → <b>{title}</b> → Departments')

    c1, c2 = st.columns([0.15, 0.85])
    with c1:
        if st.button("← Back"):
            go("titles")
    with c2:
        st.markdown(f"### Department vs {label} Count")

    df_current = get_current_df()
    df_filtered = df_current[df_current["Training Title"].astype(str) == str(title)]
    dept_counts = (
        df_filtered.groupby("Department", dropna=False)
        .size().reset_index(name="Count")
        .sort_values("Count", ascending=False)
    )

    if dept_counts.empty:
        st.info("No records found.")
        st.stop()

    card_open()
    fig3 = bar_with_labels(
        dept_counts, "Department", "Count", "Count",
        hover_x_name="Department", hover_y_name=f"{label} Count"
    )
    event3 = st.plotly_chart(
        fig3,
        key=f"dept_chart_{st.session_state.selected_status}",
        use_container_width=True,
        height=520,
        on_select="rerun",
        selection_mode=("points",),
    )
    card_close()

    clicked = get_selected_x(event3)
    if clicked is not None:
        go("employees", dept=clicked)

# ================================================
# ---------- EMPLOYEES ---------------------------
# ================================================
elif st.session_state.screen == "employees":
    label = get_status_label()
    title = st.session_state.selected_title
    dept = st.session_state.selected_department
    crumb(f'Home → {label} → {title} → <b>{dept}</b> → Employees')

    c1, c2 = st.columns([0.15, 0.85])
    with c1:
        if st.button("← Back"):
            go("departments")
    with c2:
        st.markdown(f"### Employee Information ({label})")

    df_current = get_current_df()
    df_emp = df_current[
        (df_current["Training Title"].astype(str) == str(title)) &
        (df_current["Department"].astype(str) == str(dept))
    ].copy()

    show_cols = [
        "Staff ID", "Employee Name", "Desg Name",
        "Department", "Training Type", "Training Title", "Status"
    ]
    existing_cols = [c for c in show_cols if c in df_emp.columns]

    if df_emp.empty:
        st.info("No employee records found.")
        st.stop()

    card_open()
    st.dataframe(df_emp[existing_cols], use_container_width=True, hide_index=True)
    st.download_button(
        label="⬇️ Download as CSV",
        data=df_emp[existing_cols].to_csv(index=False),
        file_name=f"{dept}_{title}_employees.csv",
        mime="text/csv"
    )
    card_close()
