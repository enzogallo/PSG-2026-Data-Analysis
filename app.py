import streamlit as st
from streamlit_extras.stylable_container import stylable_container
from streamlit_extras.app_logo import add_logo
from streamlit_option_menu import option_menu
import pandas as pd
import plotly.express as px
from plotly.io import to_image
import plotly.graph_objects as go
import os
import numpy as np
from datetime import datetime, timedelta
from mplsoccer import Pitch
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
from fpdf import FPDF
import tempfile
import cv2
import easyocr
import base64
import urllib.parse
import time
import re
from streamlit_card import card
 

# ----------------------------
# CONFIGURATION & SETUP
# ----------------------------
st.set_page_config(page_title="PSG Data Center", layout="wide")

def add_bg_from_local(image_file):
    with open(image_file, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{encoded_string}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

add_bg_from_local('images/psg_bg.png')

# ----------------------------
# CHARGEMENT & FORMATAGE DES DONNÉES (toujours avant la navigation)
# ----------------------------
@st.cache_data
def load_data(path):
    return pd.read_csv(path, encoding="ISO-8859-1") if os.path.exists(path) else pd.DataFrame()


def calculate_readiness(row):
    if 'recovery_score' in row and 'distance' in row:
        return round((0.5 * (row['recovery_score'] / 100) + 0.5 * (1 - (row['distance'] / 10000))) * 100, 1)
    return np.nan

# Place la fonction generate_player_report ici pour qu'elle soit accessible partout

def generate_player_report(player_id, filtered_events, color_palette, filtered_event_types=None, fig_timeline=None):
    import unicodedata
    import matplotlib.pyplot as plt
    from mplsoccer import Pitch
    import tempfile
    from plotly.io import to_image
    from fpdf import FPDF
    import numpy as np
    import re
    from datetime import datetime
    fig, ax = plt.subplots(figsize=(10, 7.2))
    filtered_events["timestamp"] = pd.to_datetime(filtered_events["timestamp"], errors="coerce")
    if filtered_event_types:
        timeline_filtered_events = filtered_events[filtered_events["event_type"].isin(filtered_event_types)]
    else:
        timeline_filtered_events = filtered_events.copy()
    stats_summary = timeline_filtered_events["event_type"].value_counts().to_dict()
    total_events = len(timeline_filtered_events)
    most_active_zone = "Left side" if timeline_filtered_events["x"].mean() < 52.5 else "Right side"
    top_activity_minute = timeline_filtered_events["timestamp"].dt.minute.mode().iloc[0] if not timeline_filtered_events.empty else None
    pitch = Pitch(pitch_type='statsbomb', pitch_color='green', line_color='white')
    pitch.draw(ax=ax)
    x_vals = np.random.normal(52.5, 20, 100)
    y_vals = np.random.normal(34, 15, 100)
    pitch.kdeplot(x_vals, y_vals, ax=ax, cmap="Reds", fill=True, levels=100, alpha=0.6)
    fig.subplots_adjust(top=0.85, bottom=0.12)
    norm = plt.Normalize(vmin=0, vmax=1)
    sm = plt.cm.ScalarMappable(cmap="Reds", norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, orientation="horizontal", pad=0.15, fraction=0.05)
    cbar.set_label("Player Activity Density", fontsize=10)
    tick_locs = [0.0, 0.5, 1.0]
    cbar.set_ticks(tick_locs)
    cbar.set_ticklabels(["Low", "Medium", "High"])
    cbar.ax.tick_params(labelsize=9)
    tmp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".png", dir="/tmp")
    fig.savefig(tmp_img.name)
    plt.close(fig)

    fig2, ax2 = plt.subplots(figsize=(8, 6))
    pitch = Pitch(pitch_type='statsbomb', pitch_color='green', line_color='white')
    pitch.draw(ax=ax2)
    fig2.subplots_adjust(bottom=0.25)

    for i, etype in enumerate(filtered_events["event_type"].unique()):
        sub = filtered_events[filtered_events["event_type"] == etype]
        color = color_palette[i % len(color_palette)]
        sub_success = sub[sub["success"] == True]
        sub_fail = sub[sub["success"] == False]
        if not sub_success.empty:
            ax2.scatter(sub_success["x"], sub_success["y"], label=f"{etype} (Success)", c=color, alpha=0.6, edgecolors="black", marker='o')
        if not sub_fail.empty:
            ax2.scatter(sub_fail["x"], sub_fail["y"], label=f"{etype} (Fail)", facecolors='none', edgecolors=color, alpha=0.6, marker='o')

    legend = ax2.legend(loc='upper center', bbox_to_anchor=(0.5, -0.12), ncol=3)
    tmp_img2 = tempfile.NamedTemporaryFile(delete=False, suffix=".png", dir="/tmp")
    fig2.savefig(tmp_img2.name)
    plt.close(fig2)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(0, 67, 112)  # PSG Blue
    pdf.cell(200, 10, unicodedata.normalize("NFKD", f"PSG – Player {player_id} Match Report").encode("ascii", "ignore").decode("ascii"), ln=True, align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", '', 12)
    pdf.cell(200, 10, unicodedata.normalize("NFKD", f"Date: {datetime.now().strftime('%Y-%m-%d')}").encode("ascii", "ignore").decode("ascii"), ln=True, align="C")
    pdf.ln(10)

    summary_text = f"""
        MATCH SUMMARY:
        • Total Events: {total_events}
        • Most Active Zone: {most_active_zone}
        • Peak Activity Minute: {top_activity_minute}th minute

        EVENT BREAKDOWN:
        """ + "\n".join([f"• {evt_type}: {count}" for evt_type, count in stats_summary.items()]) + f"""

        COACH SUMMARY:
        Player had {total_events} key match events with high concentration on the {most_active_zone.lower()}.
        Peak involvement around minute {top_activity_minute}.
        Recommendation: emphasize transition actions in this zone and review decision-making around peak moments.
        """
    summary_text = unicodedata.normalize("NFKD", summary_text).encode("ascii", "ignore").decode("ascii")
    pdf.multi_cell(0, 10, txt=summary_text.strip())

    pdf.add_page()
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(0, 67, 112)  # PSG Blue
    pdf.cell(200, 10, "Heatmap of Player Involvement", ln=True, align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.image(tmp_img.name, x=30, y=20, w=150)
    pdf.ln(100)
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(0, 67, 112)  # PSG Blue
    pdf.cell(200, 10, "Event Map by Type", ln=True, align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.image(tmp_img2.name, x=30, y=130, w=150)

    tmp_img3 = tempfile.NamedTemporaryFile(delete=False, suffix=".png", dir="/tmp")
    img_bytes = to_image(fig_timeline, format="png", width=800, height=400)
    with open(tmp_img3.name, "wb") as f:
        f.write(img_bytes)

    pdf.ln(100)
    pdf.add_page()
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(0, 67, 112)  # PSG Blue
    pdf.cell(200, 10, "Timeline of Match Events", ln=True, align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.image(tmp_img3.name, x=30, y=30, w=150)

    def clean_text_for_pdf(text):
        text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
        text = re.sub(r"[^\x00-\x7F]+", "", text)
        return text

    raw_pdf = pdf.output(dest="S")
    if isinstance(raw_pdf, str):
        raw_pdf = raw_pdf.encode("latin1", errors="replace")
    return raw_pdf


gps_data = load_data("PSG GPS Data.csv")
# Inject mock GPS coordinates if missing
if "x" not in gps_data.columns:
    gps_data["x"] = np.random.uniform(0, 105, len(gps_data))
if "y" not in gps_data.columns:
    gps_data["y"] = np.random.uniform(0, 68, len(gps_data))
recovery_data = load_data("PSG Recovery status Data.csv")
if "date" in recovery_data.columns:
    recovery_data["date"] = pd.to_datetime(recovery_data["date"])
else:
    st.warning("❌ La colonne 'date' est absente de recovery_data.")
if "injury_status" not in recovery_data.columns or recovery_data["injury_status"].nunique() <= 1:
    injury_entries = []
    np.random.seed(42)
    injury_types = ["Hamstring", "Knee", "Ankle", "Fatigue"]
    player_ids = [7, 10, 22]

    for player in player_ids:
        n_injuries = np.random.randint(2, 4)  # max 3 injuries
        injury_dates = pd.date_range(end=datetime.today(), periods=365).to_series().sample(n=n_injuries).sort_values()
        for date in injury_dates:
            injury_entries.append({
                "player_id": player,
                "date": date,
                "injury_status": np.random.choice(injury_types)
            })

    injury_df = pd.DataFrame(injury_entries)
    recovery_data = recovery_data.drop(columns=["injury_status"], errors="ignore")
    recovery_data["date"] = pd.to_datetime(recovery_data["date"])
    injury_df["date"] = pd.to_datetime(injury_df["date"])
    recovery_data["date"] = pd.to_datetime(recovery_data["date"]).dt.date
    injury_df["date"] = pd.to_datetime(injury_df["date"]).dt.date
    recovery_data = pd.merge(recovery_data, injury_df, on=["player_id", "date"], how="left")
    recovery_data["injury_status"] = recovery_data["injury_status"].fillna("None")
if "player_id" not in recovery_data.columns:
    recovery_data["player_id"] = np.random.choice([7, 10, 22], size=len(recovery_data))
if "recovery_score" not in recovery_data.columns:
    if "Subjective_composite" in recovery_data.columns:
        recovery_data.rename(columns={"Subjective_composite": "recovery_score"}, inplace=True)
    else:
        recovery_data["recovery_score"] = np.nan

if recovery_data["recovery_score"].isnull().all():
    np.random.seed(0)
    recovery_data["recovery_score"] = np.random.uniform(50, 95, size=len(recovery_data)).round(1)
priority_data = load_data("PSG Individual Priority Areas.csv")
capability_data = load_data("PSG Physical Capability Data_.csv")
if not capability_data.empty:
    capability_data.columns = (
        capability_data.columns
        .str.strip()
        .str.lower()
        .str.replace("ï»¿", "", regex=False)  # Remove BOM if present
    )
    # Rename misformatted columns
    if "benchmarkpct" in capability_data.columns:
        capability_data.rename(columns={"benchmarkpct": "benchmarkpct"}, inplace=True)
    if "player id" in capability_data.columns:
        capability_data.rename(columns={"player id": "player_id"}, inplace=True)
    if "player_name" in capability_data.columns:
        capability_data.rename(columns={"player_name": "player_id"}, inplace=True)
    if "player_id" not in capability_data.columns:
        capability_data["player_id"] = np.random.choice([7, 10, 22], size=len(capability_data))

# Try to infer player_id if missing (only if capability_data is not empty)
if not capability_data.empty:
    if "player_id" not in capability_data.columns:
        if "player name" in capability_data.columns or "player_name" in capability_data.columns:
            name_col = "player name" if "player name" in capability_data.columns else "player_name"
            name_to_id = {v.lower(): k for k, v in PLAYER_NAMES.items()}
            capability_data["player_id"] = capability_data[name_col].str.lower().map(name_to_id)
required_capability_cols = {"player_id", "movement", "benchmarkpct"}
missing_cols = required_capability_cols - set(capability_data.columns)
if missing_cols:
    st.warning(f"❌ Required columns missing in capability_data: {missing_cols}")

# Format columns
def try_rename(df, old, new):
    if old in df.columns:
        df.rename(columns={old: new}, inplace=True)
for df in [gps_data, recovery_data, capability_data]:
    try_rename(df, "sessionDate", "date")
    try_rename(df, "Subjective_composite", "recovery_score")
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

PLAYER_NAMES = {29: "Bradley Barcola", 17: "Vitinha", 10: "Ousmane Dembélé", 14: "Désiré Doué"}
name_to_id = {v: k for k, v in PLAYER_NAMES.items()}
id_to_name = PLAYER_NAMES

params = st.query_params
if "tab" in params:
    st.session_state.active_tab = params["tab"] if isinstance(params["tab"], str) else params["tab"][0]

if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Home"

module_names = [
    "Match Analysis",
    "Physical fitness",
    "Load Demand",
    "Recovery",
    "Sprint & High Intensity",
    "Physical Development",
    "Injury",
    "External Factors",
    "Biography",
    "Atelier"
]
 
def custom_header():
    with st.container():
        add_logo("https://upload.wikimedia.org/wikipedia/en/3/3b/Paris_Saint-Germain_F.C..svg", height=80)
        with stylable_container("header-button", css_styles="""
            button {
                background-color: #004170;
                color: white;
                font-weight: bold;
                padding: 0.75rem 2.5rem;
                border-radius: 1rem;
                border: 2px solid #e30613;
                font-size: 1.2rem;
                box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.3);
                transition: all 0.3s ease;
            }
            button:hover {
                background-color: #005c9e;
                box-shadow: 0px 6px 14px rgba(0, 0, 0, 0.4);
            }
        """):
            if st.button("⚽ PSG Data Center", key="home_nav_button"):
                st.session_state.active_tab = "Home"
                st.rerun()
        st.caption("© Enzo Gallo 2025")

    selected_tab = option_menu(
        menu_title=None,
        options=module_names,
        icons=["house", "bar-chart", "people", "graph-up", "heart", "lightning", "activity", "exclamation-triangle", "globe", "card-text"],
        orientation="horizontal",
        default_index=module_names.index(st.session_state.active_tab),
        styles={
            "container": {"padding": "0!important", "background-color": "#034694"},
            "icon": {"color": "white", "font-size": "18px"},
            "nav-link": {
                "font-size": "16px",
                "text-align": "center",
                "margin": "0px",
                "color": "white",
                "padding": "10px 15px",
                "font-family": "Poppins, sans-serif",
            },
            "nav-link-selected": {"background-color": "#012d5e"},
        }
    )
    if selected_tab != st.session_state.active_tab:
        show_spinner()
        st.session_state.active_tab = selected_tab
        st.rerun()

def render_home():
    st.markdown("""
    <div style="background-color:#034694; padding:0.1rem 0.5rem; border-radius:1rem; color:white; margin-bottom:2rem;">
        <div style="text-align:center;">
            <div style="display:flex; align-items:center; justify-content:center; gap:1rem;">
                    <img src="https://upload.wikimedia.org/wikipedia/fr/archive/8/86/20231024114602%21Paris_Saint-Germain_Logo.svg" alt="Chelsea Logo" style="height:70px; padding:0.5rem 0.5rem;" />
                    <h1 style="font-family: 'Poppins', sans-serif; margin:0; font-size:1.8rem;">PSG Data Center</h1>
            </div>
            <p style="font-family: 'Poppins', sans-serif; margin-top:0rem; font-size:0.9rem;">
                From data to decisions – a custom-built platform powering PSG's performance strategy
            </p>
            <p style="font-family: 'Poppins', sans-serif; margin-top:-0.7rem; font-size:0.7rem;">
                © Enzo Gallo 2025
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(3, gap="small", vertical_alignment="top")

    cards = [
        {"label": "Match Analysis", "icon": "📊", "tab": "Match Analysis"},
        {"label": "Physical fitness", "icon": "🧠", "tab": "Physical fitness"},
        {"label": "Load Demand", "icon": "📈", "tab": "Load Demand"},
        {"label": "Recovery", "icon": "🛌", "tab": "Recovery"},
        {"label": "Sprint & High Intensity", "icon": "⚡", "tab": "Sprint & High Intensity"},
        {"label": "Physical Development", "icon": "🏋️", "tab": "Physical Development"},
        {"label": "Injury", "icon": "❌", "tab": "Injury"},
        {"label": "External Factors", "icon": "🌍", "tab": "External Factors"},
        {"label": "Biography", "icon": "📇", "tab": "Biography"},
        {"label": "Atelier", "icon": "🎓", "tab": "Atelier"},
    ]

    for i, card_data in enumerate(cards):
        col = cols[i % 3]
        with col:
            image_path = f"images/{card_data['tab'].lower().replace(' ', '_')}.png"
            if os.path.exists(image_path):
                with open(image_path, "rb") as img_file:
                    encoded = base64.b64encode(img_file.read()).decode()
                    image_url = f"data:image/png;base64,{encoded}"
            else:
                image_url = None

            clicked = card(
                title=card_data["label"],
                text="",
                image=image_url,
                styles={
                    "card": {
                        "width": "100%",
                        "height": "180px",
                        "border-radius": "12px",
                        "box-shadow": "0 4px 12px rgba(0,0,0,0.15)",
                        "margin-bottom": "-30px",
                        "margin-top": "-30px",
                        "background-color": "#0a1832",
                        "backdrop-filter": "none",
                        "border": "none",
                        "color": "white",
                        "font-family": "Poppins, sans-serif"
                    },
                    "title": {
                        "font-size": "22px",
                        "font-weight": "bold",
                        "color": "white",
                        "font-family": "Poppins, sans-serif"
                    },
                    "image": {
                        "object-fit": "cover"
                    }
                },
                key=f"card_{card_data['tab']}"
            )

            if clicked:
                show_spinner()
                st.session_state.active_tab = card_data["tab"]
                st.rerun()

def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("styles.css")

def get_season(date):
    """Convert date to season format (e.g., '2024-25')"""
    if isinstance(date, str):
        try:
            date = pd.to_datetime(date)
        except:
            return None
    year = date.year
    return f"{year}/{year+1}" if date.month >= 7 else f"{year-1}/{year}"


def show_spinner():
    spinner_html = """
    <div style="position:fixed; top:0; left:0; width:100%; height:100vh; background-color:rgba(0,0,0,0.9); z-index:9999; display:flex; align-items:center; justify-content:center;">
        <img src="https://upload.wikimedia.org/wikipedia/fr/archive/8/86/20231024114602%21Paris_Saint-Germain_Logo.svg" width="100" style="animation:spin 2s linear infinite;" />
    </div>
    <style>
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    </style>
    """
    st.markdown(spinner_html, unsafe_allow_html=True)
    time.sleep(0.8)

def simulate_realistic_gps_data(n_players=3, days=3, points_per_day=100):
    np.random.seed(42)
    data = []
    player_ids = [29, 17, 10, 14][:n_players]
    start_date = datetime.today() - timedelta(days=days)
 
    for player in player_ids:
        for day in range(days):
            base_time = datetime.combine(start_date + timedelta(days=day), datetime.min.time())
            x, y = np.random.uniform(0, 105), np.random.uniform(0, 68)
            vx, vy = 0, 0
 
            for i in range(points_per_day):
                timestamp = base_time + timedelta(seconds=i)
 
                # Inject some random high acceleration every 20 steps
                if i % 20 == 0:
                    ax = np.random.uniform(-5, 5)  # simulate sudden change
                    ay = np.random.uniform(-5, 5)
                else:
                    ax = np.random.normal(0, 0.5)
                    ay = np.random.normal(0, 0.5)
 
                vx += ax
                vy += ay
 
                # Apply velocity to position
                x += vx * 0.2
                y += vy * 0.2
 
                # Clamp to pitch bounds
                x = np.clip(x, 0, 105)
                y = np.clip(y, 0, 68)
 
                data.append({
                    "player_id": player,
                    "timestamp": timestamp,
                    "x": x,
                    "y": y,
                    "date": timestamp.date()
                })
 
    return pd.DataFrame(data)

if st.session_state.active_tab == "Home":
    render_home()
elif st.session_state.active_tab == "Physical fitness":
    custom_header()
    player_options = sorted(gps_data["player_id"].dropna().unique())
    selected_name = st.selectbox(
        "👤 Select a player",
        options=["All"] + list(id_to_name.values()),
        format_func=lambda x: x,
        key="player_filter_squad"
    )

    selected_player = name_to_id.get(selected_name, "All") if selected_name != "All" else "All"
    if True:
        if selected_player != "All":
            selected_player = int(selected_player)
        gps_data_filtered = gps_data
        recovery_data_filtered = recovery_data
    gps_latest = gps_data_filtered.sort_values("date").groupby(["player_id", "date"]).tail(1)
    rec_latest = recovery_data_filtered.sort_values("date").groupby(["player_id", "date"]).tail(1)
    readiness_df = pd.merge(gps_latest, rec_latest, on=["player_id", "date"])
    readiness_df["readiness_score"] = readiness_df.apply(calculate_readiness, axis=1)
    st.subheader("🧠 Squad Readiness Overview")
    if selected_player != "All":
        st.caption(f"🔍 Showing data for **Player {PLAYER_NAMES.get(selected_player, str(selected_player))}** only.")
    st.caption("""
    This module helps you understand the **team's physical availability and fatigue levels**.
    It provides **daily insights** to help adjust your training load, plan recovery, and reduce injury risks.
    """)
    st.markdown("##### 🧾 What You'll Learn")
    st.caption("- Daily and weekly readiness trend")
    st.caption("- Players at risk of underperformance")
    st.caption("- Relationship with training load and recovery")
 
    if not readiness_df.empty:

        readiness_df["season"] = readiness_df["date"].apply(get_season)
        seasons_available = sorted([s for s in readiness_df["season"].unique() if isinstance(s, str)], reverse=True)
        selected_season = st.selectbox("📆 Select Season", seasons_available, key="season_filter_fitness")
        readiness_df = readiness_df[readiness_df["season"] == selected_season]
 
        # Displaying readiness statistics
        readiness_summary = readiness_df.groupby("date")["readiness_score"].mean().reset_index()
        import plotly.graph_objects as go
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=readiness_summary["date"],
            y=readiness_summary["readiness_score"],
            mode="markers",
            name="Avg Readiness",
            marker=dict(
                size=10,
                color='#034694',  # Chelsea blue
                line=dict(
                    color='white',
                    width=1
                )
            ),
            hovertemplate="Date: %{x}<br>Readiness: %{y:.1f}%<extra></extra>"
        ))

        fig.add_shape(type="rect", xref="x", yref="y", 
                    x0=readiness_summary["date"].min(), 
                    x1=readiness_summary["date"].max(),
                    y0=0, y1=60, fillcolor="red", opacity=0.1, line_width=0)
        fig.add_shape(type="rect", xref="x", yref="y", 
                    x0=readiness_summary["date"].min(), 
                    x1=readiness_summary["date"].max(),
                    y0=60, y1=75, fillcolor="orange", opacity=0.1, line_width=0)
        fig.add_shape(type="rect", xref="x", yref="y", 
                    x0=readiness_summary["date"].min(), 
                    x1=readiness_summary["date"].max(),
                    y0=75, y1=100, fillcolor="green", opacity=0.1, line_width=0)

        fig.update_layout(
            title="📊 Team Readiness Over Time",
            yaxis_title="Readiness Score",
            xaxis_title="Date",
            hovermode="x unified",
            yaxis=dict(range=[0, 100])
        )

        st.plotly_chart(fig, use_container_width=True)

        st.caption("""
        Color zones indicate different readiness levels:
        🟩 Green (75-100%): Optimal readiness
        🟧 Orange (60-75%): Moderate readiness - monitor carefully
        🟥 Red (0-60%): Low readiness - consider load adaptation
        """)
 
        # Résumé par niveau
        low = readiness_df[readiness_df["readiness_score"] < 60].shape[0]
        moderate = readiness_df[(readiness_df["readiness_score"] >= 60) & (readiness_df["readiness_score"] < 75)].shape[0]
        high = readiness_df[readiness_df["readiness_score"] >= 75].shape[0]

        total_days = low + moderate + high
        low_pct = (low / total_days) * 100 if total_days > 0 else 0
        moderate_pct = (moderate / total_days) * 100 if total_days > 0 else 0
        high_pct = (high / total_days) * 100 if total_days > 0 else 0

        st.markdown("#### 🔍 Summary of readiness levels")
        if selected_player == "All":
            st.markdown("#### 🏅 Player Fitness Leaderboard")
            st.caption("This ranking shows which players maintain the highest average readiness levels over the selected season.")
            
            leaderboard_df = readiness_df.groupby("player_id")["readiness_score"].mean().reset_index()
            leaderboard_df["Player Name"] = leaderboard_df["player_id"].map(PLAYER_NAMES)
            leaderboard_df = leaderboard_df.sort_values("readiness_score", ascending=False)


            fig_leaderboard = px.bar(
                leaderboard_df,
                x="readiness_score",
                y="Player Name",
                orientation="h",
                color="readiness_score",
                color_continuous_scale="greens",
                labels={"readiness_score": "Avg Readiness (%)"},
                title="🏅 Average Player Readiness – Season Ranking"
            )
            fig_leaderboard.update_layout(
                xaxis=dict(range=[0, 100]),
                height=400,
                margin=dict(t=60, l=100),
                yaxis_title=None
            )
            st.plotly_chart(fig_leaderboard, use_container_width=True)

        critical_days = readiness_summary[readiness_summary["readiness_score"] < 60]
        if not critical_days.empty:
            st.error(f"⚠️ {len(critical_days)} critical readiness days detected. Last one: {critical_days['date'].max().strftime('%Y-%m-%d')}")
        else:
            st.success("✅ No critical readiness days detected.")

        st.success(f"🟩 High readiness days: {high} days ({high_pct:.1f}%)")
        st.warning(f"🟧 Moderate readiness days: {moderate} days ({moderate_pct:.1f}%)")
        st.error(f"🟥 Low readiness days: {low} days ({low_pct:.1f}%)")
 
        required_cols = ["date", "distance", "recovery_score", "readiness_score"]
        for col in required_cols:
            if col not in readiness_df.columns:
                    readiness_df[col] = np.nan
            styled_df = readiness_df[required_cols].style.applymap(
                lambda v: 'background-color: #b30000; color: white' if isinstance(v, (int, float)) and v < 60 else 'color: white',
                subset=["readiness_score"]
            )
            avg_readiness = readiness_df["readiness_score"].mean()
        st.metric("Average Readiness", f"{avg_readiness:.1f}%")

        st.markdown("#### 📘 Coach Interpretation")
        st.caption("""
        - **Above 75%**: Players are fresh and ready – optimal training intensity possible.
        - **60-75%**: Moderate readiness – be cautious with volume and load.
        - **Below 60%**: Alert! Consider adapting drills or providing recovery.
        
        **Recommendation:** If multiple days are below 60%, consider implementing a team recovery session or reduce intensity temporarily.
        """)
    else:
        st.info("No data available for the moment.")

elif st.session_state.active_tab == "Load Demand":
    custom_header()
    player_list = gps_data["player_id"].dropna().unique()
    selected_name = st.selectbox(
        "Select Player for Individual View",
        options=["All"] + list(id_to_name.values()),
        key="player_filter_load"
    )    
    selected_player = name_to_id[selected_name] if selected_name != "All" else "All"
    if selected_player != "All":
        selected_player = int(selected_player)
        st.caption(f"🔍 Showing data for **Player {PLAYER_NAMES.get(selected_player, str(selected_player))}** only.")
        player_data = gps_data[gps_data["player_id"] == selected_player]
    else:
        player_data = gps_data
    player_data = player_data[player_data["distance"].notnull()]

    st.subheader("📈 Match Load Analysis")

    with st.expander("➕ Add Training Load Entry"):
        with st.form("add_training_load_form"):
            ld_date = st.date_input("📅 Date", value=datetime.today(), key="ld_date")
            ld_player = st.selectbox("👤 Player", options=sorted(gps_data["player_id"].dropna().unique()), format_func=lambda x: id_to_name.get(x, "Player not found"), key="ld_player")
            ld_distance = st.number_input("🏃 Distance (m)", min_value=0, value=5000, step=100, key="ld_distance")
            ld_oppo = st.text_input("🏟️ Opponent (optional)", key="ld_oppo")
            ld_accel = st.number_input("⚡ Accel/Decel (>2.5 m/s²)", min_value=0, step=1, value=12, key="ld_accel")
            submit_ld = st.form_submit_button("Add Load Entry")
            if submit_ld:
                new_entry = {
                    "date": ld_date,
                    "player_id": ld_player,
                    "distance": ld_distance,
                    "opposition_full": ld_oppo,
                    "accel_decel_over_2_5": ld_accel
                }
                gps_path = "PSG GPS Data.csv"
                existing_gps = pd.read_csv(gps_path) if os.path.exists(gps_path) else pd.DataFrame()
                updated_gps = pd.concat([existing_gps, pd.DataFrame([new_entry])], ignore_index=True)
                updated_gps.to_csv(gps_path, index=False)
                st.success("✅ Training load entry added successfully.")
                st.rerun()

    player_data["season"] = player_data["date"].apply(get_season)
    seasons_available = sorted(player_data["season"].unique(), reverse=True)
    selected_season = st.selectbox("📆 Select Season", seasons_available, key="season_filter_load")
    player_data = player_data[player_data["season"] == selected_season]

    # Scatter plot Distance with monthly average and trend
    if "distance" in player_data.columns:
        player_data = player_data[player_data["distance"] != 0]
        player_data_sorted = player_data.sort_values("date")
        avg_distance = player_data_sorted["distance"].mean()
        player_data_sorted["month"] = player_data_sorted["date"].dt.to_period("M").dt.to_timestamp()

        # Average per month
        monthly_avg = player_data_sorted.groupby("month")["distance"].mean().reset_index()

        # Scatter + overall average
        fig_distance = go.Figure()

        fig_distance.add_trace(go.Scatter(
            x=player_data_sorted["date"],
            y=player_data_sorted["distance"],
            mode="markers",
            name="Distance per session",
            marker=dict(size=6, color="skyblue"),
            hovertemplate="Date: %{x}<br>Distance: %{y} m"
        ))

        fig_distance.add_trace(go.Scatter(
            x=monthly_avg["month"],
            y=monthly_avg["distance"],
            mode="lines+markers",
            name="Monthly average",
            line=dict(color="orange", dash="dash"),
            marker=dict(size=8)
        ))

        fig_distance.add_hline(
            y=avg_distance,
            line_dash="dot",
            annotation_text=f"Overall average: {avg_distance:.1f} m",
            line_color="green"
        )

        fig_distance.update_layout(
            hoverlabel=dict(
                bgcolor="#012d5e",
                font_color="#012d5e",
                font_size=13
            )
        )

        fig_distance.update_layout(
        title="📊 Distance per Session with Monthly Trend",
            xaxis_title="Date",
            yaxis_title="Distance (m)",
            height=600,
            hoverlabel=dict(
                bgcolor="#012d5e",
                font_color="white",
                font_size=13
            )
        )

        st.plotly_chart(fig_distance, use_container_width=True)
        st.caption("""
        This scatter plot shows the distance covered in each session over time.
        - Blue dots: Individual session values
        - Orange line: Monthly trend showing load evolution
        - Green line: Overall average serving as a reference point
        """)

    # Acceleration/Deceleration per Session with Mean Line
    st.subheader("⚡ Acceleration/Deceleration Analysis")
    accel_cols = [col for col in player_data.columns if "accel_decel" in col]
    if accel_cols:
        st.caption("""
    ### 📏 Interpreting Acceleration Values
    - **> 2.0 m/s²**: Light acceleration (e.g. jogging bursts)
    - **> 2.5 m/s²**: Moderate acceleration (standard game movements)
    - **> 3.0 m/s²**: High acceleration (explosive efforts, pressing, sprints)
    - **> 3.5 m/s²**: Very high intensity (sprint duels, fast counters)    
    """)
        selected_accel_col = st.radio("⚡ Select acceleration metric", accel_cols, key="accel_selector_load")
        fig_accel = px.line(
            player_data.sort_values("date"),
            x="date",
            y=selected_accel_col,
            title=f"{selected_accel_col.replace('_', ' ').title()} per Session (m/s²)"
        )
        fig_accel.update_layout(height=800, width=1000)
        mean_val = player_data[selected_accel_col].mean()
        fig_accel.add_hline(y=mean_val, line_dash="dot", line_color="orange", annotation_text=f"Average: {mean_val:.1f}")
        st.plotly_chart(fig_accel, use_container_width=True)
        st.caption("""
        Track explosive movements across sessions:
        - Each peak represents high-intensity moments
        - Orange average line helps identify if player maintains expected intensity
        - Useful for monitoring explosive capacity and fatigue
        """)
    # Total Distance vs Peak Speed with Trendline
    if "peak_speed" in player_data.columns:
        player_data = player_data.rename(columns={"peak_speed": "Sprint Max"})
        fig_gps = px.scatter(
                player_data,
                x="distance",
                y="Sprint Max",
                trendline="ols",
                hover_data=["date"],
                title="Total Distance vs Sprint Max",
                labels={"distance": "Distance (m)", "Sprint Max": "Sprint Max (km/h)"}
            )
        fig_gps.update_layout(height=800, width=1000)
        st.plotly_chart(fig_gps, use_container_width=True)
        st.caption("Shows correlation between total distance and Sprint Max — useful to assess efficiency of high-speed efforts.")

        st.caption("### 📘 Coach Interpretation")
        st.caption("""
        - **🔹 Sprint Max** = top speed reached during a session  
        - **🔸 Distance** = total volume of running  

        **🧠 How to read this chart:**  
        - Each dot represents a training or match session  
        - **High Sprint Max with low distance** → explosive player  
        - **High distance with low Sprint Max** → endurance-focused player  
        - The **trendline** shows how sprint ability evolves with workload  

        **💡 Coaching tip:**  
        - Decline in Sprint Max despite high distance may indicate fatigue  
        - Helps optimize balance between volume and intensity based on player roles (e.g. fullbacks)  
        """)
    # Average Distance by Opposition with Annotations
    if "opposition_full" in player_data.columns:
        opposition_summary = player_data.groupby("opposition_full")["distance"].mean().reset_index()
        fig_opposition = px.bar(
                opposition_summary,
                x="opposition_full",
                y="distance",
                title="Average Distance by Opposition"
            )
        fig_opposition.update_layout(height=800, width=1000)
        avg_opp = opposition_summary["distance"].mean()
        fig_opposition.add_hline(y=avg_opp, line_dash="dot", annotation_text=f"Average: {avg_opp:.1f} m", line_color="gray")
        st.plotly_chart(fig_opposition, use_container_width=True)
        st.caption("Highlights the average distance covered against each opponent — helps understand match demands.")
    
elif st.session_state.active_tab == "Recovery":
    custom_header()
    player_options = sorted(recovery_data["player_id"].dropna().unique())
    selected_name = st.selectbox(
        "👤 Select a player",
        options=["All"] + list(id_to_name.values()),
        format_func=lambda x: x,
        key="player_filter_recovery"
    )

    selected_player = name_to_id.get(selected_name, "All") if selected_name != "All" else "All"
    if selected_player != "All":
        selected_player = int(selected_player)
        recovery_data = recovery_data[recovery_data["player_id"] == selected_player]
    
    recovery_data["season"] = recovery_data["date"].apply(get_season)
    seasons_available = sorted(recovery_data["season"].unique(), reverse=True)
    selected_season = st.selectbox("📆 Select Season", seasons_available, key="season_filter_recovery")
    recovery_data = recovery_data[recovery_data["season"] == selected_season]
    
    st.subheader("🛌 Recovery Overview")

    st.caption("🧪 **Recovery Score** – subjective score (0-100) of how recovered a player feels after effort.")

    st.caption("""
    This module helps you assess **player recovery status** and anticipate **readiness risks**.
    It allows you to track recovery trends, spot under-recovered athletes, and adjust training accordingly.
    """)

    # ➕ Add Recovery Entry Form
    with st.expander("➕ Add Recovery Entry"):
        with st.form("add_recovery_entry_form"):
            rec_date = st.date_input("📅 Recovery Date", value=datetime.today(), key="rec_date")
            rec_player = st.selectbox("👤 Player", options=sorted(gps_data["player_id"].dropna().unique()), format_func=lambda x: id_to_name.get(x, "Unknown Player"), key="rec_player")
            rec_score = st.slider("🧪 Recovery Score (0-100)", min_value=0, max_value=100, value=75, key="rec_score")
            rec_note = st.text_area("📝 Optional Notes", key="rec_note")
            submit_recovery = st.form_submit_button("Add Recovery Entry")
            if submit_recovery:
                new_entry = {
                    "date": rec_date,
                    "player_id": rec_player,
                    "recovery_score": rec_score,
                    "note": rec_note
                }
                recovery_path = "PSG Recovery status Data.csv"
                existing_recovery = pd.read_csv(recovery_path) if os.path.exists(recovery_path) else pd.DataFrame()
                updated_recovery = pd.concat([existing_recovery, pd.DataFrame([new_entry])], ignore_index=True)
                updated_recovery.to_csv(recovery_path, index=False)
                st.success(f"✅ Recovery entry added for {PLAYER_NAMES.get(rec_player)} with score {rec_score}")
                st.rerun()

    # ---- Recovery Visuals ----
    if not recovery_data.empty:
        st.markdown("##### 📈 Weekly Average Recovery Trend")
        st.caption("Smooths out daily fluctuations to highlight overall team fatigue or freshness across weeks.")


        recovery_data["week"] = pd.to_datetime(recovery_data["date"]).dt.to_period("W").dt.start_time
        weekly_avg = recovery_data.groupby("week")["recovery_score"].mean().reset_index()

        fig_weekly = px.line(weekly_avg, x="week", y="recovery_score", markers=True,
                            title="Team Recovery Score per Week",
                            labels={"recovery_score": "Avg Recovery (%)", "week": "Week"})
        fig_weekly.update_layout(height=600, width=1000)
        fig_weekly.add_hrect(y0=0, y1=50, fillcolor="red", opacity=0.1, line_width=0)
        fig_weekly.add_hrect(y0=50, y1=70, fillcolor="orange", opacity=0.1, line_width=0)
        fig_weekly.add_hrect(y0=70, y1=100, fillcolor="green", opacity=0.1, line_width=0)
        st.plotly_chart(fig_weekly, use_container_width=True)

        st.caption("""
        Weekly recovery trend interpretation:
        - Upward trend: Improving recovery capacity
        - Downward trend: Potential accumulation of fatigue
        - Colored zones help identify critical periods
        """)

        latest_weekly_score = weekly_avg["recovery_score"].iloc[-1]
        if latest_weekly_score < 50:
            st.error(f"🟥 Latest weekly average recovery is very low ({latest_weekly_score:.1f}%) — prioritize recovery this week.")
        elif latest_weekly_score < 70:
            st.warning(f"🟧 Moderate weekly average recovery ({latest_weekly_score:.1f}%) — consider load adaptation.")
        else:
            st.success(f"🟩 Players are well recovered this week ({latest_weekly_score:.1f}%).")

        st.subheader("📉 Simplified Recovery Trends")
        st.caption("Use this section to follow **player recovery evolution** in a more digestible format.")
        # [Existing simplified trends code remains unchanged]
        smoothed = recovery_data.copy()
 
        smoothed = (
            smoothed
            .groupby(["date", "player_id"])["recovery_score"]
            .mean()
            .reset_index()
        )
 
        available_players = sorted(smoothed["player_id"].unique())
        available_player_names = [id_to_name.get(pid, str(pid)) for pid in available_players]
        selected_player_names = st.multiselect("👤 Players to display", options=available_player_names, default=available_player_names, key="recovery_simplified_multiselect_2")
        selected_players = [pid for pid in available_players if id_to_name.get(pid, str(pid)) in selected_player_names]
 
        smoothed = smoothed[smoothed["player_id"].isin(selected_players)]
        smoothed["player_name"] = smoothed["player_id"].map(id_to_name)
 
        if not smoothed.empty:
            fig_simple = px.line(
                smoothed,
                x="date",
                y="recovery_score",
                color="player_name",
                markers=True,
                title="📈 Recovery Score per Day",
                labels={"recovery_score": "Recovery (%)", "date": "Date", "player_name": "Player"}
            )
            fig_simple.update_layout(height=600, width=1000)
            st.plotly_chart(fig_simple, use_container_width=True, key="recovery_simplified_chart_2")
        else:
            st.info("No recovery data available for the selected period or players.")

        st.subheader("🧍‍♂️ Players With Low Recovery")
        st.caption("Visual summary of average recovery over the last 3 days per player.")
        recent = recovery_data[recovery_data["date"] >= recovery_data["date"].max() - pd.Timedelta(days=3)]
        avg_recovery = recent.groupby("player_id")["recovery_score"].mean().reset_index()

        if not avg_recovery.empty:
            # Calculate the number of columns required
            n_players = len(avg_recovery)
            cols = st.columns(min(n_players, 3))  # Maximum 3 cards per line
            
            # Distribute the cards in the columns
            for idx, row in avg_recovery.iterrows():
                with cols[idx % 3]:  # Use modulo to cycle between columns
                    avg = row["recovery_score"]
                    player = row["player_id"]
                    color = "red" if avg < 60 else "orange" if avg < 75 else "green"
                    card(
                        title=f"{PLAYER_NAMES.get(player, player)}", 
                        text=f"Avg Recovery: {avg:.1f}%", 
                        styles={
                            "card": {
                                "background-color": color,
                                "padding": "0.8rem",
                                "border-radius": "8px",
                                "margin": "0.3rem",
                                "font-family": "Poppins, sans-serif",
                                "min-width": "100%",  # Ensure that the card takes up the full width of the column
                                "height": "auto"
                            },
                            "title": {
                                "font-size": "16px",
                                "font-weight": "bold",
                                "font-family": "Poppins, sans-serif",
                                "margin-bottom": "0.3rem"
                            },
                            "text": {
                                "font-size": "14px"
                            }
                        }
                    )
        else:
            st.success("✅ No recovery data available for the last 3 days.")


    st.subheader("⚖️ Recovery vs Training Load")
    st.caption("""
    This graph helps evaluate whether higher physical loads (distance) negatively impact a player's recovery.
    
    💡 **How to read this:**  
    - Each dot is one training or match day.
    - A **downward trend** = fatigue builds with higher workload (⚠️).
    - A **flat or upward trend** = good recovery capacity (✅).
    """)
    
    merged = pd.merge(gps_data, recovery_data, on=["date", "player_id"])
    
    if selected_player != "All":
        player_data = merged[merged["player_id"] == selected_player]
        title = f"Player {selected_player} – Distance vs Recovery Score"
    else:
        player_data = merged
        title = "All Players – Distance vs Recovery Score"
    
    # Filtrage des données par saison

    player_ids = sorted(merged["player_id"].unique())
    player_display_names = [id_to_name.get(pid, str(pid)) for pid in player_ids]
    player_name_to_id = {id_to_name.get(pid, str(pid)): pid for pid in player_ids}
    selected_names = st.multiselect(
        "👤 Select players for trend view",
        options=player_display_names,
        default=player_display_names[:1],
        key="recovery_trend_multiselect"
    )
    trend_selected_players = [player_name_to_id[name] for name in selected_names]

    merged = merged[merged["player_id"].isin(trend_selected_players)]
    
    if not merged.empty:
        merged["player_name"] = merged["player_id"].map(PLAYER_NAMES)
        fig = px.scatter(
            merged,
            x="distance",
            y="recovery_score",
            color="player_name",
            trendline="ols",
            opacity=0.3,
            title="Distance vs Recovery – Trend by Player",
            labels={"distance": "Distance (m)", "recovery_score": "Recovery (%)", "player_name": "Player"}
        )
        fig.update_traces(selector=dict(mode='lines'), line=dict(width=4))
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

        for pid in trend_selected_players:
            player_subset = merged[merged["player_id"] == pid]
            slope = np.polyfit(player_subset["distance"], player_subset["recovery_score"], 1)[0]
            if slope < -0.005:
                st.error(f"⚠️ {PLAYER_NAMES.get(pid, str(pid))} : Recovery drops significantly with increased load.")
            elif slope > 0.005:
                st.success(f"✅ {PLAYER_NAMES.get(pid, str(pid))} : Good recovery despite high load.")
            else:
                st.warning(f"🟨 {PLAYER_NAMES.get(pid, str(pid))} : Slight or no correlation between distance and recovery.")
    else:
        st.info("No recovery data available for selected players or dates.")
    
elif st.session_state.active_tab == "Physical Development":
    custom_header()
    player_options = sorted(gps_data["player_id"].dropna().unique())
    selected_player = st.selectbox("👤 Select a player", options=["All"] + list(map(str, player_options)), format_func=lambda x: id_to_name.get(int(x), "Player not found") if x != "All" else "All", key="player_filter_physical")
    if selected_player != "All":
        selected_player = int(selected_player)
        capability_data = capability_data[capability_data["player_id"] == selected_player]
    if not capability_data.empty and "testdate" in capability_data.columns:
        capability_data["testdate"] = pd.to_datetime(capability_data["testdate"], errors='coerce')
        valid_dates = capability_data["testdate"].notna()
        capability_data.loc[valid_dates, "season"] = capability_data.loc[valid_dates, "testdate"].apply(get_season)
        seasons_available = sorted([s for s in capability_data["season"].unique() if isinstance(s, str)], reverse=True)
        selected_season = st.selectbox("📆 Select Season", seasons_available, key="season_filter_physical")
        capability_data = capability_data[capability_data["season"] == selected_season]
    st.header("🏋️ Physical Test Results")
    if selected_player != "All":
        st.caption(f"🔍 Showing data for **{PLAYER_NAMES.get(selected_player, str(selected_player))}** only.")

    if not capability_data.empty:
        st.caption("""
        This section helps you **evaluate physical capabilities** of each player through objective testing.
        Tests include sprints, jumps, strength, and mobility benchmarks. 

        👉 These tests help identify:
        - Strengths and development areas
        - Injury risk indicators
        - Progress over time
        """)

        st.markdown("##### 📊 Performance vs Benchmark (by Movement Type)")
        if 'movement' in capability_data.columns and 'benchmarkpct' in capability_data.columns:
            fig_benchmark = px.bar(
                capability_data,
                x='movement',
                y='benchmarkpct',
                color='movement',
                title="💪 Benchmark % Reached per Movement",
                labels={'benchmarkpct': '% Benchmark'},
                text_auto=True
            )
            fig_benchmark.update_layout(yaxis_range=[0, 120])
            st.plotly_chart(fig_benchmark, use_container_width=True)
            fig_benchmark.update_traces(hovertemplate="%{y}%<br>Values above 100% show exceptional performance beyond the set benchmarks.")
            st.caption("""
            Each bar represents the percentage of the benchmark achieved by players for a specific movement, such as sprints or upper body strength. Values over 100% indicate that players exceeded the standard benchmarks, showcasing exceptional performance.
            """)
            
            st.subheader("🌡️ Player vs Movement Heatmap")
            st.caption("Visual comparison of each player's performance per movement — helps identify strengths and weaknesses at a glance.")
            
        if 'player_id' in capability_data.columns and 'movement' in capability_data.columns and 'benchmarkpct' in capability_data.columns:
            heatmap_data = capability_data.pivot_table(index='player_id', columns='movement', values='benchmarkpct')
            heatmap_data.index = heatmap_data.index.map(PLAYER_NAMES.get)
            fig_heatmap, ax = plt.subplots(figsize=(8, 4), facecolor='none')
            ax.set_facecolor('none')
            sns.heatmap(
                heatmap_data,
                cmap="RdYlGn",
                annot=True,
                fmt=".0f",
                ax=ax,
                linewidths=.5,
                cbar_kws={"label": "% Benchmark"}
            )
            for text in ax.texts:
                text.set_color("white")
            ax.tick_params(axis='both', colors='white')
            ax.xaxis.label.set_color('white')
            ax.yaxis.label.set_color('white')
            for label in ax.get_xticklabels():
                label.set_color('white')
            for label in ax.get_yticklabels():
                label.set_color('white')
            cbar = ax.collections[0].colorbar
            cbar.ax.yaxis.label.set_color('white')  # Colorbar label
            cbar.ax.tick_params(colors='white')    # Tick marks
            for t in cbar.ax.get_yticklabels():    # Tick labels
                t.set_color('white')
                t.set_fontsize(10)
            ax.set_xlabel("")
            ax.set_ylabel("")
            st.pyplot(fig_heatmap)
            st.caption("""
            This heatmap highlights the performance of each player across various physical movement categories — agility, sprint, jump, and upper body.
            - Dark green: Performance closer to the benchmark
            - Red: Lower relative performance
            - Use this chart to spot physical strengths or areas needing attention
            """)
        else:
            st.warning("❌ Required columns not found in capability_data.")

        st.markdown("##### 📊 Performance Distribution by Movement Type")
        if {'movement', 'benchmarkpct'}.issubset(capability_data.columns):
            capability_data = capability_data[capability_data['benchmarkpct'] > 1]
            fig_violin = px.violin(
                capability_data,
                x='movement',
                y='benchmarkpct',
                box=True,
                points='all',
                hover_data=['benchmarkpct'],
                title='Enhanced Violin Plot of Performance Distribution by Movement Type',
                labels={'benchmarkpct': 'Benchmark Percentage (%)', 'movement': 'Movement Type'}
            )
            fig_violin.update_layout(height=600, width=1000)
            st.plotly_chart(fig_violin, use_container_width=True)
            st.caption("Violin plot showing distribution of benchmark percentages per movement type, including box plot details.")
            st.markdown("##### Understanding the Graph")
            st.caption("""
            This graph helps the coach understand how players are performing relative to established benchmarks for different physical movements. A performance above 100% means the player has exceeded the expected standards, which could be due to individual improvements or an exceptionally good performance session.
            """)
        else:
            st.warning("Required data ('movement', 'benchmarkpct') not available to display performance distribution.")
            
        st.markdown("##### 📈 Benchmark Progression Over Time")
        required_columns = {"testdate", "benchmarkpct"}
        if required_columns.issubset(capability_data.columns):
            capability_data["testdate"] = pd.to_datetime(capability_data["testdate"], errors='coerce')
            valid_data = capability_data.dropna(subset=["testdate", "benchmarkpct"])
            
            if not valid_data.empty:
                fig_progress = px.scatter(
                            valid_data,
                            x="testdate",
                            y="benchmarkpct",
                            trendline="lowess",
                            title="Progression of player performance relative to benchmark over time",
                            labels={"benchmarkpct": "Percentage of Benchmark Achieved", "testdate": "Test Date"},
                            hover_data=None
                        )
                fig_progress.add_hline(y=100, line_dash="dash", line_color="green",
                                        annotation_text="Target Benchmark (100%)",
                                        annotation_position="bottom right")
                # Update hovertemplate for individual test data points
                fig_progress.update_traces(
                    selector=dict(mode='markers'),
                    hovertemplate="Test Date: %{x}<br>Benchmark Achieved: %{y:.1f}%"
                )
                # Enhance the trendline appearance
                fig_progress.update_traces(
                    selector=dict(mode='lines'),
                    line=dict(color='darkblue', width=4),
                    hovertemplate="Trendline: %{y:.1f}%"
                )
                # Add annotation to explain the trendline
                fig_progress.add_annotation(
                    x=valid_data["testdate"].max(),
                    y=valid_data["benchmarkpct"].mean(),
                    text="Trendline: Overall Performance",
                    showarrow=True,
                    arrowhead=1,
                    ax=-40,
                    ay=-30,
                    font=dict(color="darkblue", size=12)
                )
                fig_progress.update_layout(
                    height=600,
                    width=1000,
                    legend_title="Data Type",
                    legend=dict(itemsizing='constant')
                )
                st.plotly_chart(fig_progress, use_container_width=True)
                st.caption("Scatter plot with lowess trendline showing progression of benchmark percentages over time.")
            else:
                st.warning("No valid data available to display benchmark progression.")
        else:
            st.warning("Missing required data ('testdate', 'benchmarkpct') to display benchmark progression over time.")

        st.markdown("##### 📘 Coach Takeaways")
        st.caption("""
        - Focus on movements **below 80%** – indicates room for physical development
        - Encourage maintenance or further improvement for **players above 100%**
        - Re-test regularly to track progress

        💡 **Tip**: Use this data to adapt training programs based on individual weaknesses (e.g. mobility, strength).
        """)

    else:
        st.warning("No physical development data available.")
    
elif st.session_state.active_tab == "Biography":
    custom_header()
    player_options = sorted(gps_data["player_id"].dropna().unique())
    selected_name = st.selectbox(
        "👤 Select a player",
        options=["All"] + list(id_to_name.values()),
        format_func=lambda x: x,
        key="player_filter_bio"
    )

    selected_player = name_to_id.get(selected_name, "All") if selected_name != "All" else "All"
    if selected_player != "All":
        selected_player = int(selected_player)

    st.subheader("📇 Individual Development Plan (IDP)")

    # Load existing data
    dev_plan_path = "PSG Player Dev Plan.csv"
    if os.path.exists(dev_plan_path):
        dev_data = pd.read_csv(dev_plan_path)
    else:
        dev_data = pd.DataFrame(columns=["player_id", "long_term_goal", "dimensions", "status", "last_update", "coach_notes"])

    st.caption("🎯 This section tracks long-term and short-term player development objectives.")

    player_id = selected_player
    st.subheader(f"🧑‍🎓 Development Plan for {PLAYER_NAMES.get(player_id, player_id)}")
 
    existing = dev_data[dev_data["player_id"] == player_id].sort_values("last_update", ascending=False)
    with st.expander("➕ Add or Update Development Objective"):
        with st.form("add_dev_plan"):
            long_term_goal_val = existing["long_term_goal"].iloc[0] if not existing.empty else ""
            dimensions_val = existing["dimensions"].iloc[0] if not existing.empty else ""
            notes_val = existing["coach_notes"].iloc[0] if not existing.empty else ""

            long_term_goal = st.text_area("🎯 Long-Term Vision", value="" if pd.isna(long_term_goal_val) else long_term_goal_val)
            dimensions = st.text_area("📌 Development Focus Areas (e.g. speed, positioning, leadership)", value="" if pd.isna(dimensions_val) else dimensions_val)
            notes = st.text_area("📝 Coach Notes", value="" if pd.isna(notes_val) else notes_val)

            status = st.selectbox("📈 Progress Status", ["Not Started", "In Progress", "On Hold", "Completed"], index=1)
            submitted = st.form_submit_button("💾 Save Plan")
            if submitted:
                new_entry = {
                    "player_id": player_id,
                    "long_term_goal": long_term_goal,
                    "dimensions": dimensions,
                    "status": status,
                    "coach_notes": notes,
                    "last_update": datetime.now().strftime("%Y-%m-%d %H:%M")
                }
                dev_data = pd.concat([dev_data, pd.DataFrame([new_entry])], ignore_index=True)
                dev_data.to_csv(dev_plan_path, index=False)
                st.success("✅ Development plan updated successfully.")
                st.rerun()

    if not existing.empty:
    
        st.markdown("### 🥧 Overall Objective Completion")
        pie_data = existing["status"].value_counts().reset_index()
        pie_data.columns = ["status", "count"]
        fig_pie = px.pie(
            pie_data,
            names="status",
            values="count",
            title="Distribution of Development Objective Statuses",
            hole=0.3
        )
        fig_pie.update_traces(textinfo="percent+label")
        fig_pie.update_layout(height=600)
        st.plotly_chart(fig_pie, use_container_width=True)
        st.markdown("### 📋 Development Objective History")
        st.caption("Below is a history of all development objectives recorded for this player.")
        table_data = existing[["last_update", "long_term_goal", "dimensions", "status", "coach_notes"]].sort_values("last_update", ascending=False)
        table_data = table_data.rename(columns={
            "last_update": "🕒 Last Update",
            "long_term_goal": "🎯 Long-Term Vision",
            "dimensions": "📌 Focus Areas",
            "status": "📈 Status",
            "coach_notes": "📝 Coach Notes"
        })
        for _, row in table_data.iterrows():
            with st.container():
                st.markdown(f"""
                    <div style="border: 1px solid #ccc; border-radius: 10px; padding: 1rem; margin-bottom: 1rem; background-color: #012d5e;">
                        <h4 style="margin-bottom: 0.5rem;">🎯 {row['🎯 Long-Term Vision']}</h4>
                        <p><strong>📌 Focus Areas:</strong> {row['📌 Focus Areas']}</p>
                        <p><strong>📈 Status:</strong> {row['📈 Status']}</p>
                        <p><strong>📝 Coach Notes:</strong> {row['📝 Coach Notes']}</p>
                        <p style="font-size: 0.8rem; color: gray;"><em>🕒 Last Update: {row['🕒 Last Update']}</em></p>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No development plan recorded yet for this player.")
    
elif st.session_state.active_tab == "Injury":
    custom_header()
    player_options = sorted(gps_data["player_id"].dropna().unique())
    selected_name = st.selectbox(
        "👤 Select a player",
        options=["All"] + list(id_to_name.values()),
        format_func=lambda x: x,
        key="player_filter_injury"
    )

    selected_player = name_to_id.get(selected_name, "All") if selected_name != "All" else "All"
    if selected_player != "All":
        selected_player = int(selected_player)
    st.header("❌ Injury & Medical Overview")
    with st.expander("➕ Add Injury Entry"):
        with st.form("add_injury_entry_form"):
            inj_date = st.date_input("📅 Injury Date", value=datetime.today(), key="inj_date")
            inj_player = st.selectbox(
                "👤 Player", 
                options=sorted(gps_data["player_id"].dropna().unique()), 
                format_func=lambda x: id_to_name.get(x, "Unknown Player"), 
                key="inj_player"
            )
            inj_type = st.selectbox("🩹 Injury Type", ["Hamstring", "Knee", "Ankle", "Fatigue", "Other"])
            inj_note = st.text_area("📝 Notes (optional)", key="inj_note")
 
            submitted_injury = st.form_submit_button("➕ Add Injury Entry")
            if submitted_injury:
                new_injury = {
                    "date": inj_date,
                    "player_id": inj_player,
                    "injury_status": inj_type
                }
 
                recovery_path = "PSG Recovery status Data.csv"
                existing_recovery = pd.read_csv(recovery_path) if os.path.exists(recovery_path) else pd.DataFrame()
                updated_recovery = pd.concat([existing_recovery, pd.DataFrame([new_injury])], ignore_index=True)
                updated_recovery.to_csv(recovery_path, index=False)
                st.success(f"✅ Injury entry added for {PLAYER_NAMES.get(inj_player)} on {inj_date} ({inj_type})")
                st.rerun()
    if selected_player != "All":
        st.caption(f"🔍 Showing data for **{PLAYER_NAMES.get(selected_player, str(selected_player))}** only.")
        recovery_data = recovery_data[recovery_data["player_id"] == selected_player]
    st.caption("Tracking injuries and analyzing availability trends.")

    if not recovery_data.empty:
        if "injury_status" in recovery_data.columns:
            st.subheader("📊 Injury status")
            recovery_data["injury_status"] = recovery_data["injury_status"].fillna("None").astype(str)
            filtered_injuries = recovery_data[
                recovery_data["injury_status"].str.strip().str.lower().ne("none") &
                recovery_data["injury_status"].notna()
            ]
            injury_counts = filtered_injuries["injury_status"].value_counts().reset_index()
            injury_counts.columns = ["injury_status", "count"]
            
            fig_injury = px.histogram(
                injury_counts,
                x="injury_status",
                y="count",
                title="Breakdown of injuries",
                # Trier par fréquence décroissante
                category_orders={"injury_status": injury_counts["injury_status"].tolist()}
            )
            fig_injury.update_layout(
                height=600, 
                width=1000,
                xaxis_title="Injury Type",
                yaxis_title="Number of Occurrences"
            )
            st.plotly_chart(fig_injury, use_container_width=True)

            st.subheader("📅 Injury Timeline")
            injury_timeline = recovery_data[
                recovery_data["injury_status"].str.strip().str.lower().ne("none") &
                recovery_data["injury_status"].notna()
            ]
            if not injury_timeline.empty:
                fig_timeline = px.scatter(
                    injury_timeline,
                    x="date",
                    y="injury_status",
                    color="injury_status",
                    title="",
                    labels={"date": "Date", "injury_status": "Injury Type"}
                )
                fig_timeline.update_traces(marker=dict(size=12))
                fig_timeline.update_layout(
                    height=700,
                    width=1000,
                    xaxis=dict(
                        title="Date",
                        title_font=dict(size=16),
                        tickfont=dict(size=14)
                    ),
                    yaxis=dict(
                        title="Injury Type",
                        title_font=dict(size=16),
                        tickfont=dict(size=16)
                    ),
                    showlegend=True,
                    legend=dict(
                        font=dict(color="white", size=18),
                        title_font=dict(size=18)
                    )
                )
                st.plotly_chart(fig_timeline, use_container_width=True)
            else:
                st.warning("ℹ️ No confirmed injuries found in the dataset.")
        else:
            st.warning("No 'injury_status' column detected. Injury data unavailable.")
    else:
        st.info("No recovery or injury data available.")

elif st.session_state.active_tab == "Sprint & High Intensity":
    custom_header()
    st.header("⚡ Sprint & High Intensity Zones")

    st.markdown("""
    This module summarizes high-intensity efforts per player based on accelerations and decelerations detected by GPS.
    
    - 📈 Helps identify explosive workloads
    - 🧠 Useful for return-to-play or training adaptation
    """)
    st.caption("""
    ### 📏 Interpreting Acceleration Values
    - **> 2.0 m/s²**: Light acceleration (e.g. jogging bursts)
    - **> 2.5 m/s²**: Moderate acceleration (standard game movements)
    - **> 3.0 m/s²**: High acceleration (explosive efforts, pressing, sprints)
    - **> 3.5 m/s²**: Very high intensity (sprint duels, fast counters)    
    """)

    accel_columns = list(sorted(set(
        col for col in gps_data.columns if "accel_decel_over_" in col
    )))

    if not accel_columns:
        st.warning("No acceleration data found in the GPS file.")
    else:
        def format_accel_label(col_name):
            match = re.search(r"over_(\d+)_(\d+)", col_name)
            if match:
                return f"> {match.group(1)}.{match.group(2)} m/s²"
            else:
                return col_name
        
        selected_metric = st.selectbox("📊 Select intensity threshold", options=accel_columns, format_func=format_accel_label)

        display_mode = st.selectbox("🧮 Display as", ["Total", "Average per session"])

        gps_data["season"] = gps_data["date"].apply(get_season)
        seasons_available = sorted(gps_data["season"].unique(), reverse=True)
        selected_season = st.selectbox("📆 Select Season", seasons_available, key="season_filter_sprint")
        gps_data = gps_data[gps_data["season"] == selected_season]

        if display_mode == "Average per session":
            session_level = gps_data.groupby(["player_id", "date"])[selected_metric].sum().reset_index()
            summary = session_level.groupby("player_id")[selected_metric].mean().reset_index()
        else:
            summary = gps_data.groupby("player_id")[selected_metric].sum().reset_index()

        summary["Player"] = summary["player_id"].map(PLAYER_NAMES)
        summary = summary.sort_values(selected_metric, ascending=False)

        fig_summary = px.bar(
            summary,
            x="Player",
            y=selected_metric,
            title=f"{'Average per Session' if display_mode == 'Average per session' else 'Total'} Accelerations/Decelerations Above Threshold",
            labels={selected_metric: "Effort Count"},
            text_auto=True
        )
        fig_summary.update_layout(height=500)
        st.plotly_chart(fig_summary, use_container_width=True)

        st.caption("""
        High-intensity effort comparison:
        - Higher bars indicate more explosive actions
        - Compare players' workload at same intensity threshold
        - Helps identify players who might need specific conditioning
        """)

        st.markdown("### 📘 Coach Insights")
        st.markdown("""
        - Players with higher effort counts were more involved in explosive actions.
        - Use this metric to track conditioning or compare match/training impact.
        - ⚠️ Very low counts might indicate reduced involvement or performance drop.
        """)
    
elif st.session_state.active_tab == "External Factors":
    custom_header()
    player_options = sorted(gps_data["player_id"].dropna().unique())
    selected_name = st.selectbox(
        "👤 Select a player",
        options=["All"] + list(id_to_name.values()),
        format_func=lambda x: x,
        key="player_filter_external"
    )

    selected_player = name_to_id.get(selected_name, "All") if selected_name != "All" else "All"
    if selected_player != "All":
        selected_player = int(selected_player)
    st.header("🌍 External Context")
    if selected_player != "All":
        st.caption(f"🔍 Showing data for **{PLAYER_NAMES.get(selected_player, str(selected_player))}** only.")
    st.markdown("Capture external influences like fatigue, travel, or psychological state that might impact performance.")

    with st.expander("➕ Add External Note"):
        with st.form("external_note_form"):
            note_date = st.date_input("📅 Relevant Date", value=datetime.now())
            player_options = ["Whole Team"] + [str(pid) for pid in sorted(gps_data["player_id"].dropna().unique())]
            selected_player = st.selectbox("👤 Player concerned", options=player_options, format_func=lambda x: x if x=="Whole Team" else id_to_name.get(int(x), "Unknown Player"))
            factor_type = st.selectbox("📌 Type of factor", ["Fatigue", "Travel", "Motivation", "Mental", "Weather", "Other"])
            note_text = st.text_area("📝 Coach's Note")
            submitted = st.form_submit_button("Save Note")

            if submitted and note_text.strip():
                new_note = {
                    "date": note_date,
                    "player": selected_player,
                    "type": factor_type,
                    "note": note_text.strip()
                }

                file_path = "PSG External Factors Data.csv"
                if os.path.exists(file_path):
                    df = pd.read_csv(file_path)
                else:
                    df = pd.DataFrame(columns=["date", "player", "type", "note"])
                df = pd.concat([df, pd.DataFrame([new_note])], ignore_index=True)
                df.to_csv(file_path, index=False)

                st.success("✅ Note saved!")

    # Display External Notes History
    if os.path.exists("PSG External Factors Data.csv"):
        notes_df = pd.read_csv("PSG External Factors Data.csv", parse_dates=["date"])
        if not notes_df.empty:
            notes_df = notes_df.sort_values("date", ascending=False)
            for _, note in notes_df.iterrows():
                with st.container():
                    st.markdown(f"""
                        <div style="border: 1px solid #ccc; border-radius: 10px; padding: 1rem; margin-bottom: 1rem; background-color: #012d5e; color: white;">
                            <h4 style="margin-bottom: 0.5rem;">📅 {note['date'].strftime('%Y-%m-%d')}</h4>
                            <strong>👤 Player:</strong> {note['player'] if note['player']=="Whole Team" else PLAYER_NAMES.get(int(note['player']), note['player'])}
                            <p><strong>📌 Type:</strong> {note['type']}</p>
                            <p><strong>📝 Note:</strong> {note['note']}</p>
                        </div>
                    """, unsafe_allow_html=True)
    else:
        st.info("No external notes recorded yet.")
    
elif st.session_state.active_tab == "Match Analysis":
    custom_header()
    player_options = sorted(gps_data["player_id"].dropna().unique())
    selected_name = st.selectbox(
        "👤 Select a player",
        options=["All"] + list(id_to_name.values()),
        format_func=lambda x: x,
        key="player_filter_analysis"
    )

    selected_player = name_to_id.get(selected_name, "All") if selected_name != "All" else "All"
    if selected_player != "All":
        selected_player = int(selected_player)
    with st.expander("➕ Add Match Event"):
        with st.form("add_match_event_form"):
            match_date = st.date_input("📅 Match Date", value=datetime.today())
            match_time = st.time_input("⏱️ Match Time", value=datetime.now().time())
            event_timestamp = datetime.combine(match_date, match_time)

            player_ids = sorted(gps_data["player_id"].dropna().unique())
            event_player = st.selectbox("👤 Player Involved", options=player_ids, format_func=lambda x: PLAYER_NAMES.get(int(x), "Player not found"))
            event_type = st.selectbox("⚽ Event Type", options=["Pass", "Shot", "Dribble", "Tackle", "Interception", "Foul", "Save", "Clearance", "Cross", "Duel"])
            opponent = st.text_input("🏟️ Opponent (e.g. Arsenal)", key="match_opponent")

            x_coord = st.slider("📍 X Position on Field (0 = Left, 105 = Right)", min_value=0.0, max_value=105.0, value=52.5)
            y_coord = st.slider("📍 Y Position on Field (0 = Bottom, 68 = Top)", min_value=0.0, max_value=68.0, value=34.0)

            tags = st.text_input("🏷️ Tags (comma-separated)", help="Use tags like 'dangerous, counter-attack, assist' for better filtering.")
            notes = st.text_area("📝 Additional Notes", help="Optional context for this event.")

            submitted_event = st.form_submit_button("Add Event to Match Dataset")

            if submitted_event and opponent:
                event_entry = {
                    "timestamp": event_timestamp,
                    "player_id": event_player,
                    "event_type": event_type,
                    "opponent": opponent,
                    "x": round(x_coord, 2),
                    "y": round(y_coord, 2),
                    "tags": tags,
                    "notes": notes
                }
 
                events_path = "PSG Match Events Data.csv"
                existing_events = pd.read_csv(events_path) if os.path.exists(events_path) else pd.DataFrame()
                updated_events = pd.concat([existing_events, pd.DataFrame([event_entry])], ignore_index=True)
                updated_events.to_csv(events_path, index=False)
 
                st.success("✅ Match event successfully added.")
                st.rerun()
            elif submitted_event and not opponent:
                st.warning("⚠️ Please specify the opponent to record the match event.")

    event_data = pd.read_csv("PSG Match Events Data.csv")
    event_data["timestamp"] = pd.to_datetime(event_data["timestamp"], format='mixed', errors='coerce')
    event_data["match_id"] = event_data["opponent"]
    match_ids = sorted(event_data["match_id"].dropna().unique())
    selected_match = st.selectbox("Select Match", options=match_ids, key="match_filter_analysis")
    match_filtered_events = event_data[event_data["match_id"] == selected_match]

    if selected_player != "All":
        st.caption(f"🔍 Showing data for **{PLAYER_NAMES.get(selected_player, str(selected_player))}** only.")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📍 Heatmap of Match Involvement")
        st.caption(f"""
        {'All players' if selected_player == "All" else f'{PLAYER_NAMES.get(int(selected_player), selected_player)}'}'s match involvement
        """)
        
        filtered_events = match_filtered_events[match_filtered_events["player_id"] == selected_player] if selected_player != "All" else match_filtered_events

        fig, ax = plt.subplots(figsize=(5, 3.2), facecolor="none")
        pitch = Pitch(pitch_type='statsbomb', pitch_color='green', line_color='white')
        pitch.draw(ax=ax)
        pitch.kdeplot(filtered_events["x"], filtered_events["y"], ax=ax, cmap="Reds", fill=True, levels=100, alpha=0.6)
        # Enhanced colorbar for better understanding
        norm = plt.Normalize(vmin=0, vmax=1)
        sm = plt.cm.ScalarMappable(cmap="Reds", norm=norm)
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, orientation="horizontal", pad=0.05, fraction=0.05)
        cbar.set_label("Player Activity Density", fontsize=6, color='white', labelpad=10)

        # Add custom tick labels
        tick_locs = [0.0, 0.5, 1.0]
        cbar.set_ticks(tick_locs)
        cbar.set_ticklabels(["Low", "Medium", "High"])

        cbar.ax.tick_params(labelsize=10, colors='white')
        cbar.outline.set_edgecolor('white')
        for t in cbar.ax.get_xticklabels():
            t.set_color('white')
            t.set_fontsize(6)
        st.pyplot(fig, use_container_width=False)

        st.caption("""
        Heatmap interpretation:
        - Darker red areas: Higher concentration of player activity
        - Lighter areas: Less frequent presence
        - Useful for understanding positional tendencies and movement patterns
        """)

    with col2:
        st.markdown("#### 📍 Event Map by Type")

        available_types = filtered_events["event_type"].dropna().unique().tolist()
        default_types = ["shot"] if "shot" in available_types else [available_types[0]] if available_types else []
        selected_types = st.multiselect("Select event types to display", options=available_types, default=default_types, label_visibility="collapsed")        
        filtered_events = filtered_events[filtered_events["event_type"].isin(selected_types)]

        fig2, ax2 = plt.subplots(figsize=(5, 3.2), facecolor="none")
        pitch = Pitch(pitch_type='statsbomb', pitch_color='green', line_color='white')
        pitch.draw(ax=ax2)

        import matplotlib.colors as mcolors
        color_palette = [mcolors.to_hex(tuple(int(x) / 255 for x in c.strip("rgb()").split(","))) for c in px.colors.qualitative.Safe]
        if not color_palette:
            color_palette = ['#1f77b4']

        for i, etype in enumerate(selected_types):
            subset = filtered_events[filtered_events["event_type"] == etype]
            color = color_palette[i % len(color_palette)]

            for success_value in [True, False]:
                sub = subset[subset["success"] == success_value]
                marker = 'o' if success_value else 'X'
                facecolor = color if success_value else 'none'
                edgecolor = color if not success_value else 'black'

                pitch.scatter(
                    sub["x"], sub["y"], ax=ax2,
                    alpha=0.8, s=60,
                    edgecolors=edgecolor,
                    linewidths=1.5,
                    marker=marker,
                    facecolors=facecolor
                )

        from matplotlib.lines import Line2D
        legend_elements = []
        for i, etype in enumerate(selected_types):
            color = color_palette[i % len(color_palette)]
            legend_elements.append(Line2D([0], [0], marker='o', color='w', label=f"{etype} (Success)",
                markerfacecolor=color, markeredgecolor='black', markersize=8))
            legend_elements.append(Line2D([0], [0], marker='X', color='w', label=f"{etype} (Fail)",
                markerfacecolor='none', markeredgecolor=color, markersize=8))
        
        # Create a separate legend figure
        fig_legend, ax_legend = plt.subplots(figsize=(6, 1), facecolor="none")
        ax_legend.axis('off')
        legend = ax_legend.legend(handles=legend_elements, title="Event Type", loc="center", ncol=3, fontsize="x-small", title_fontsize="x-small", frameon=False)
        legend.get_title().set_color("white")
        for text in legend.get_texts():
            text.set_color("white")
        st.pyplot(fig2, use_container_width=True)
        st.pyplot(fig_legend, use_container_width=True)


    st.subheader("🕒 Match Replay Timeline")
    st.caption("Animated replay of key events over time for a selected match and player.")

    event_data = pd.read_csv("PSG Match Events Data.csv")
    event_data["timestamp"] = pd.to_datetime(event_data["timestamp"], format='mixed', errors='coerce')
    event_data["match_id"] = event_data["opponent"]

    if not event_data.empty:
        match_events = event_data[event_data["match_id"] == selected_match]

        # Removed duplicate selectbox for player selection; using selected_player from Match Analysis

        player_events = match_events if selected_player == "All" else match_events[match_events["player_id"] == selected_player]
        player_label = "All Players" if selected_player == "All" else PLAYER_NAMES.get(int(selected_player), selected_player)
        timeline_filtered_events = match_filtered_events[
            match_filtered_events["event_type"].isin(selected_types)
        ]

        if not player_events.empty:
            player_events = player_events.sort_values("timestamp")
            player_events["time"] = player_events["timestamp"].dt.strftime("%H:%M:%S")

            available_event_types = sorted(player_events["event_type"].unique())
            selected_event_types = st.multiselect("Filter by Event Type", available_event_types, default=available_event_types)
            if not selected_event_types:
                st.warning("Please select at least one event type to display the timeline.")
            else:
                # Filter the data accordingly with the selected types
                player_events = player_events[player_events["event_type"].isin(selected_event_types)]

                fig_timeline = px.scatter(
                    player_events,
                    x="timestamp",
                    y="event_type",
                    color="event_type",
                    color_discrete_sequence=color_palette,
                    hover_data=["timestamp", "x", "y"],
                    title=f"📊 Event Timeline – {player_label}",
                    labels={"timestamp": "Time", "event_type": "Event Type"}
                )
                fig_timeline.update_traces(marker=dict(size=12))
                fig_timeline.update_layout(
                    height=700,
                    width=1000,
                    xaxis=dict(title="Timestamp", title_font=dict(size=16), tickfont=dict(size=14)),
                    yaxis=dict(title="Event Type", title_font=dict(size=16), tickfont=dict(size=16)),
                    showlegend=True,
                    legend=dict(font=dict(size=18), title_font=dict(size=18))
                )
                st.plotly_chart(fig_timeline, use_container_width=True)

                # PDF button (optional, keep it here if needed)
                report_bytes = generate_player_report(
                    selected_player,
                    filtered_events,  # pour la heatmap et l'event map
                    color_palette,
                    filtered_event_types=selected_types,  # types sélectionnés pour l'event map
                    fig_timeline=fig_timeline  # timeline = événements + types filtrés dans la timeline
                )
                download_col1, download_col2, download_col3 = st.columns([4, 1, 1])
                with download_col3:
                    st.download_button(
                        label="📄 Download Player Report",
                        data=report_bytes,
                        file_name=f"player_{selected_player}_report.pdf",
                        mime="application/pdf",
                        key="download_player_report"
                    )

elif st.session_state.active_tab == "Atelier":
    custom_header()
    st.header("Atelier : Collecte et Visualisation de Stats")
    st.markdown(
        """
        🎯 **Objectif de l'atelier :** Découvrir comment les développeurs utilisent les données pour analyser les performances des joueurs !

        📝 **Instructions :**
        1. Regardez l'extrait vidéo du match PSG
        2. Notez sur votre feuille :
           - Le nombre de tirs de chaque joueur
           - Le nombre de passes réussies
           - Le nombre de dribbles réussis
        3. Créez un fichier Excel avec ces colonnes :
           - Nom du joueur
           - Tirs
           - Passes
           - Dribbles
        4. Téléversez votre fichier ici pour voir les graphiques !
        """
    )
    # Affichez la vidéo d'extrait
    st.video("https://youtu.be/DzEFJIpvSgw")
    st.markdown("**Téléversez ici votre fichier Excel (.xlsx) :**")
    uploaded_file = st.file_uploader("", type=["xlsx"])
    if uploaded_file is not None:
        try:
            df_user = pd.read_excel(uploaded_file)
        except Exception as e:
            st.error(f"Impossible de lire le fichier : {e}")
            st.stop()
        st.subheader("Vos données collectées")
        st.dataframe(df_user)
        # Graphique : bar chart Tirs vs Passes vs Dribbles
        st.subheader("Visualisation : Comparaison des Stats")
        fig = px.bar(
            df_user,
            x="Name",
            y=["Tirs", "Passes", "Dribbles"],
            barmode="group",
            labels={"value": "Nombre", "variable": "Statistique"},
            title="Comparaison des Statistiques par Joueur"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Radar chart pour chaque joueur
        st.subheader("Radar de Performance par Joueur")
        for _, player in df_user.iterrows():
            fig2 = go.Figure(
                go.Scatterpolar(
                    r=[player["Tirs"], player["Passes"], player["Dribbles"]],
                    theta=["Tirs", "Passes", "Dribbles"],
                    fill="toself",
                    name=player["Name"]
                )
            )
            fig2.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, max(df_user[["Tirs", "Passes", "Dribbles"]].max())]
                    )
                ),
                showlegend=True,
                title=f"Performance de {player['Name']}"
            )
            st.plotly_chart(fig2, use_container_width=True)
            st.plotly_chart(fig2, use_container_width=True)
