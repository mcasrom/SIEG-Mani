#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MANI — app.py
Media Audit & Narrative Intelligence
M. Castillo - Privacy Tools | 2026

Dashboard público en Streamlit Cloud.
Lee CSVs del repo GitHub (data/kpis.csv, data/articulos.csv, data/campanas.csv)
Sin servidor local. Sin nginx. Sin NAT. Sin tokens de terceros.
"""

import streamlit as st
import pandas as pd
import json
import ast
from datetime import datetime, timezone, timedelta
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go

# ── Streamlit Cloud lee los CSVs del propio repo (rutas relativas) ─────────────
DATA_DIR = Path("data")

st.set_page_config(
    page_title="MANI · Media Audit & Narrative Intelligence",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS: estética terminal verde oscuro, coherente con SIEG ────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Rajdhani', sans-serif; }
.stApp { background-color: #0a0d14; color: #c9d1d9; }

/* Header */
.mani-header {
    border-bottom: 1px solid #1e2d45;
    padding: 0 0 12px 0;
    margin-bottom: 20px;
}
.mani-title {
    font-family: 'Share Tech Mono', monospace;
    font-size: 1.4em;
    color: #00ff9d;
    letter-spacing: 3px;
}
.mani-sub {
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.75em;
    color: #5a6a7e;
}

/* Alerta campaña */
.alert-box {
    background: #1a0a0e;
    border: 1px solid #ff4e6a;
    border-left: 4px solid #ff4e6a;
    padding: 10px 16px;
    border-radius: 4px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.85em;
    color: #ff4e6a;
    margin-bottom: 16px;
}
.ok-box {
    background: #0a1a10;
    border: 1px solid #00ff9d;
    border-left: 4px solid #00ff9d;
    padding: 8px 16px;
    border-radius: 4px;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.8em;
    color: #00ff9d;
    margin-bottom: 16px;
}

/* Métricas */
[data-testid="metric-container"] {
    background: #111827;
    border: 1px solid #1e2d45;
    border-left: 3px solid #00ff9d;
    padding: 12px;
    border-radius: 4px;
}
[data-testid="metric-container"] label { color: #5a6a7e !important; font-size: 0.7em !important; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #00ff9d !important; font-family: 'Share Tech Mono', monospace; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { background: #0a0d14; border-bottom: 1px solid #1e2d45; }
.stTabs [data-baseweb="tab"] { color: #5a6a7e; font-family: 'Share Tech Mono', monospace; font-size: 0.8em; }
.stTabs [aria-selected="true"] { color: #00ff9d !important; border-bottom: 2px solid #00ff9d !important; }

/* Dataframe */
[data-testid="stDataFrame"] { border: 1px solid #1e2d45; }

/* Sidebar */
[data-testid="stSidebar"] { background: #0d1117; }
</style>
""", unsafe_allow_html=True)

# ── Plotly theme base ──────────────────────────────────────────────────────────
PLOT_LAYOUT = dict(
    paper_bgcolor="#111827",
    plot_bgcolor="#0d1520",
    font=dict(family="Share Tech Mono, monospace", color="#7a8a9a", size=11),
    margin=dict(l=10, r=10, t=30, b=10),
    xaxis=dict(gridcolor="#1e2d45", linecolor="#1e2d45"),
    yaxis=dict(gridcolor="#1e2d45", linecolor="#1e2d45"),
)
ACCENT  = "#00ff9d"
RED     = "#ff4e6a"
YELLOW  = "#ffd166"

MEDIO_COLORS = {
    "El País": "#4fc3f7", "El Mundo": "#ff8a65", "ABC": "#ce93d8",
    "Público": "#80cbc4", "El Confidencial": "#fff176",
    "BBC World": "#f48fb1", "NYT World": "#a5d6a7",
    "Fox News": "#ff5252", "RT": "#ef9a9a", "France24 ES": "#90caf9",
}

FASE_LABELS = {
    "inoculacion":   "🟡 SEM 1 · INOCULACIÓN",
    "saturacion":    "🟠 SEM 2 · SATURACIÓN",
    "pivot":         "🔴 SEM 3 · PIVOT ⚡",
    "consolidacion": "☠  SEM 4 · CONSOLIDACIÓN",
}


# ── Carga de datos ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=900)   # refresca cada 15 min
def load_kpis() -> pd.DataFrame:
    p = DATA_DIR / "kpis.csv"
    if not p.exists():
        return pd.DataFrame()
    df = pd.read_csv(p)
    df["fecha"] = pd.to_datetime(df["fecha"])
    return df


@st.cache_data(ttl=900)
def load_articulos() -> pd.DataFrame:
    p = DATA_DIR / "articulos.csv"
    if not p.exists():
        return pd.DataFrame()
    df = pd.read_csv(p)
    df["publicado"] = pd.to_datetime(df["publicado"], utc=True, errors="coerce")
    return df


@st.cache_data(ttl=900)
def load_campanas() -> pd.DataFrame:
    p = DATA_DIR / "campanas.csv"
    if not p.exists():
        return pd.DataFrame()
    return pd.read_csv(p)


def parse_json_col(val):
    if pd.isna(val) or val == "":
        return {}
    try:
        return json.loads(val)
    except Exception:
        try:
            return ast.literal_eval(val)
        except Exception:
            return {}


# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="mani-header">
  <div class="mani-title">M.A.N.I // MEDIA AUDIT &amp; NARRATIVE INTELLIGENCE</div>
  <div class="mani-sub">Sistema de vigilancia editorial · M. Castillo - Privacy Tools · 2026</div>
</div>
""", unsafe_allow_html=True)

# ── Cargar datos ──────────────────────────────────────────────────────────────
kpis_df    = load_kpis()
arts_df    = load_articulos()
camps_df   = load_campanas()

now_utc = datetime.now(timezone.utc)

if kpis_df.empty:
    st.warning("⏳ Sin datos aún. El pipeline del Odroid aún no ha generado el primer ciclo.")
    st.stop()

# ── Detectar campaña activa ───────────────────────────────────────────────────
active_camp = None
if not camps_df.empty:
    active = camps_df[camps_df["fin"] == "EN CURSO"]
    if not active.empty:
        active_camp = active.iloc[0]

if active_camp is not None:
    fase_label = FASE_LABELS.get(active_camp["fase"], active_camp["fase"].upper())
    st.markdown(f"""
    <div class="alert-box">
    ⚠️ CAMPAÑA DE INFLUENCIA DETECTADA &nbsp;|&nbsp; {fase_label}
    &nbsp;|&nbsp; Inicio: {active_camp['inicio']}
    </div>""", unsafe_allow_html=True)
else:
    sync_max = kpis_df["sync_index"].max() if "sync_index" in kpis_df.columns else 0
    st.markdown(f'<div class="ok-box">✓ Sin campaña activa · Sync máximo últimos datos: {sync_max:.3f}</div>',
                unsafe_allow_html=True)

# ── KPI tiles ─────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.metric("Artículos (72h)", f"{len(arts_df):,}" if not arts_df.empty else "—")
with c2:
    st.metric("Medios monitoreados", kpis_df["medio"].nunique() if not kpis_df.empty else 0)
with c3:
    last_sync = kpis_df.sort_values("fecha")["sync_index"].iloc[-1] if not kpis_df.empty else 0
    st.metric("Sync Index (último)", f"{last_sync:.3f}", help="≥0.65 = alerta campaña")
with c4:
    camp_n = len(camps_df) if not camps_df.empty else 0
    st.metric("Campañas registradas", camp_n)
with c5:
    st.metric("Última actualización",
              now_utc.strftime("%H:%M UTC"),
              help="Refresca cada 15 min")

st.divider()

# ── TABS ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📡 Sync & Pivot",
    "🧭 Sentiment Bias",
    "💉 Keyword Injection",
    "📰 Artículos",
    "🗂 Campañas",
])

# ═══════════════ TAB 1: Sync & Pivot ══════════════════════════════════════════
with tab1:
    col_a, col_b = st.columns([1, 2])

    with col_a:
        st.markdown("#### Media Sync Index")
        st.caption("Similitud coseno promedio entre todos los medios. ≥0.65 = alerta campaña.")

        # Sync timeseries por fecha (valor único por día = mismo para todos los medios)
        sync_ts = kpis_df.groupby("fecha")["sync_index"].mean().reset_index()
        fig_sync = go.Figure()
        fig_sync.add_trace(go.Scatter(
            x=sync_ts["fecha"], y=sync_ts["sync_index"],
            mode="lines+markers", line=dict(color=ACCENT, width=2),
            fill="tozeroy", fillcolor="rgba(0,255,157,0.09)",
            name="Sync Index",
        ))
        fig_sync.add_hline(y=0.65, line_dash="dash", line_color=RED,
                           annotation_text="umbral campaña", annotation_font_color=RED)
        fig_sync.update_layout(**PLOT_LAYOUT, height=280,
                               yaxis=dict(range=[0, 1], gridcolor="#1e2d45"))
        st.plotly_chart(fig_sync, use_container_width=True)

    with col_b:
        st.markdown("#### Pivot Score por Medio")
        st.caption("Distancia euclidiana TF-IDF respecto al día anterior. Alto = cambio brusco de línea editorial.")
        fig_pivot = go.Figure()
        for medio in kpis_df["medio"].unique():
            sub = kpis_df[kpis_df["medio"] == medio].sort_values("fecha")
            fig_pivot.add_trace(go.Scatter(
                x=sub["fecha"], y=sub["pivot_score"],
                mode="lines+markers", name=medio,
                line=dict(color=MEDIO_COLORS.get(medio, "#aaa"), width=1.5),
                marker=dict(size=4),
            ))
        fig_pivot.update_layout(**PLOT_LAYOUT, height=280,
                                yaxis=dict(range=[0, 1], gridcolor="#1e2d45"),
                                legend=dict(orientation="h", y=-0.2, font=dict(size=9)))
        st.plotly_chart(fig_pivot, use_container_width=True)

# ═══════════════ TAB 2: Sentiment Bias ════════════════════════════════════════
with tab2:
    st.markdown("#### Sentiment Bias · Actores Geopolíticos")
    st.caption("Score VADER promedio por actor. Positivo = cobertura favorable. Negativo = hostil.")

    # Desplegar sentiment_bias JSON a filas
    sent_rows = []
    for _, row in kpis_df.iterrows():
        sb = parse_json_col(row.get("sentiment_bias", "{}"))
        for actor, score in sb.items():
            sent_rows.append({"fecha": row["fecha"], "medio": row["medio"],
                               "actor": actor, "score": score})

    if sent_rows:
        sent_df = pd.DataFrame(sent_rows)
        sent_df["fecha"] = pd.to_datetime(sent_df["fecha"])

        col1, col2 = st.columns(2)
        with col1:
            # Promedio global por actor
            actor_avg = sent_df.groupby("actor")["score"].mean().reset_index()
            actor_avg = actor_avg.sort_values("score")
            colors = [ACCENT if s >= 0 else RED for s in actor_avg["score"]]
            fig_act = go.Figure(go.Bar(
                x=actor_avg["score"], y=actor_avg["actor"],
                orientation="h", marker_color=colors,
                text=[f"{v:+.3f}" for v in actor_avg["score"]],
                textposition="outside",
            ))
            fig_act.update_layout(**PLOT_LAYOUT, height=300,
                                  title="Promedio global por actor",
                                  xaxis=dict(range=[-1, 1], gridcolor="#1e2d45"))
            st.plotly_chart(fig_act, use_container_width=True)

        with col2:
            # Evolución temporal por actor (selector)
            actors_avail = sorted(sent_df["actor"].unique())
            sel_actor = st.selectbox("Actor geopolítico", actors_avail)
            sub_act = sent_df[sent_df["actor"] == sel_actor].groupby("fecha")["score"].mean().reset_index()
            fig_evo = px.line(sub_act, x="fecha", y="score",
                              color_discrete_sequence=[YELLOW])
            fig_evo.add_hline(y=0, line_dash="dot", line_color="#5a6a7e")
            fig_evo.update_layout(**PLOT_LAYOUT, height=300,
                                  title=f"Evolución temporal · {sel_actor}",
                                  yaxis=dict(range=[-1, 1]))
            st.plotly_chart(fig_evo, use_container_width=True)

        # Heatmap medio × actor
        st.markdown("##### Mapa de calor: Medio × Actor")
        pivot_heat = sent_df.groupby(["medio","actor"])["score"].mean().unstack(fill_value=0)
        fig_heat = px.imshow(
            pivot_heat,
            color_continuous_scale=[[0, RED], [0.5, "#111827"], [1, ACCENT]],
            zmin=-1, zmax=1,
            aspect="auto",
        )
        fig_heat.update_layout(**PLOT_LAYOUT, height=350)
        st.plotly_chart(fig_heat, use_container_width=True)
    else:
        st.info("Sin datos de sentiment aún.")

# ═══════════════ TAB 3: Keyword Injection ═════════════════════════════════════
with tab3:
    st.markdown("#### Keyword Injection")
    st.caption("Términos exógenos (PR, agencias, narrativas coordinadas) detectados en titulares.")

    kw_rows = []
    for _, row in kpis_df.iterrows():
        kj = parse_json_col(row.get("keyword_inj", "{}"))
        for kw, cnt in kj.items():
            kw_rows.append({"fecha": row["fecha"], "medio": row["medio"],
                             "keyword": kw, "freq": cnt})

    if kw_rows:
        kw_df = pd.DataFrame(kw_rows)
        kw_df["fecha"] = pd.to_datetime(kw_df["fecha"])

        col1, col2 = st.columns([1, 1])
        with col1:
            top = kw_df.groupby("keyword")["freq"].sum().reset_index().sort_values("freq", ascending=True).tail(15)
            fig_kw = go.Figure(go.Bar(
                x=top["freq"], y=top["keyword"],
                orientation="h",
                marker_color=YELLOW,
            ))
            fig_kw.update_layout(**PLOT_LAYOUT, height=400, title="Top keywords acumuladas")
            st.plotly_chart(fig_kw, use_container_width=True)

        with col2:
            # Keyword por medio (stacked)
            kw_med = kw_df.groupby(["medio","keyword"])["freq"].sum().reset_index()
            fig_stk = px.bar(kw_med, x="medio", y="freq", color="keyword",
                             color_discrete_sequence=px.colors.qualitative.Dark24)
            fig_stk.update_layout(**PLOT_LAYOUT, height=400,
                                  title="Distribución por medio",
                                  xaxis_tickangle=-30)
            st.plotly_chart(fig_stk, use_container_width=True)
    else:
        st.info("Sin keywords detectadas aún.")

# ═══════════════ TAB 4: Artículos ═════════════════════════════════════════════
with tab4:
    st.markdown("#### Últimas 72h · Artículos ingestados")
    if not arts_df.empty:
        col1, col2 = st.columns([1, 3])
        with col1:
            medios_sel = st.multiselect("Filtrar medio",
                                        sorted(arts_df["medio"].unique()),
                                        default=sorted(arts_df["medio"].unique()))
            lineas_sel = st.multiselect("Línea editorial",
                                        sorted(arts_df["linea"].unique()),
                                        default=sorted(arts_df["linea"].unique()))
        with col2:
            filt = arts_df[
                arts_df["medio"].isin(medios_sel) &
                arts_df["linea"].isin(lineas_sel)
            ].sort_values("publicado", ascending=False)

            # Donut artículos por medio
            cnt = filt["medio"].value_counts().reset_index()
            cnt.columns = ["medio", "n"]
            colors_pie = [MEDIO_COLORS.get(m, "#aaa") for m in cnt["medio"]]
            fig_pie = go.Figure(go.Pie(
                labels=cnt["medio"], values=cnt["n"],
                marker=dict(colors=colors_pie),
                hole=0.5,
            ))
            fig_pie.update_layout(**PLOT_LAYOUT, height=250,
                                  showlegend=True,
                                  legend=dict(font=dict(size=9)))
            st.plotly_chart(fig_pie, use_container_width=True)

        # Tabla artículos
        show_cols = ["publicado","medio","linea","titulo","url"]
        show_cols = [c for c in show_cols if c in filt.columns]
        st.dataframe(
            filt[show_cols].head(200),
            use_container_width=True,
            hide_index=True,
            column_config={
                "url": st.column_config.LinkColumn("url"),
                "publicado": st.column_config.DatetimeColumn("publicado", format="DD/MM HH:mm"),
            }
        )
    else:
        st.info("Sin artículos cargados aún.")

# ═══════════════ TAB 5: Campañas ══════════════════════════════════════════════
with tab5:
    st.markdown("#### Historial de Campañas Detectadas")
    st.caption("Una campaña se activa cuando Media Sync Index ≥ 0.65 durante días consecutivos.")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
| Fase | Días | Descripción |
|------|------|-------------|
| 🟡 Inoculación | 1–7 | Día Cero · nuevos términos emocionales |
| 🟠 Saturación | 8–14 | Unanimidad entre líneas editoriales opuestas |
| 🔴 Pivot | 15–21 | Cambio de postura para justificar acción política |
| ☠ Consolidación | 22+ | El tema pasa a ser dogma aceptado |
        """)
    with col2:
        if not kpis_df.empty and "alerta_campana" in kpis_df.columns:
            alert_ts = kpis_df.groupby("fecha")["alerta_campana"].max().reset_index()
            fig_al = go.Figure(go.Bar(
                x=alert_ts["fecha"],
                y=alert_ts["alerta_campana"],
                marker_color=[RED if v else "rgba(0,255,157,0.27)" for v in alert_ts["alerta_campana"]],
            ))
            fig_al.update_layout(**PLOT_LAYOUT, height=180,
                                 title="Días con alerta activa",
                                 yaxis=dict(tickvals=[0,1], ticktext=["OK","ALERTA"]))
            st.plotly_chart(fig_al, use_container_width=True)

    if not camps_df.empty:
        st.dataframe(camps_df, use_container_width=True, hide_index=True)
    else:
        st.success("✓ Sin campañas registradas en el histórico.")

# ── Footer ─────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    '<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.7em;color:#5a6a7e;text-align:center">'
    'MANI v1.0 · © 2026 M. Castillo · Privacy Tools · mybloggingnotes@gmail.com · '
    'Odroid C2/DietPi → GitHub → Streamlit Cloud · Sin APIs de terceros'
    '</div>',
    unsafe_allow_html=True,
)
