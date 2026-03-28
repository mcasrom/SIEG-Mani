#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MANI — app.py  v1.1
Media Audit & Narrative Intelligence · M. Castillo 2026
"""

import streamlit as st
import pandas as pd
import json, ast
from datetime import datetime, timezone
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go

DATA_DIR = Path("data")

st.set_page_config(
    page_title="MANI · Media Audit & Narrative Intelligence",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Rajdhani', sans-serif; }
.stApp { background-color: #0a0d14; color: #c9d1d9; }
.mani-header { border-bottom: 1px solid #1e2d45; padding: 0 0 12px 0; margin-bottom: 20px; }
.mani-title  { font-family: 'Share Tech Mono', monospace; font-size: 1.4em; color: #00ff9d; letter-spacing: 3px; }
.mani-sub    { font-family: 'Share Tech Mono', monospace; font-size: 0.75em; color: #5a6a7e; }
.alert-box { background:#1a0a0e; border:1px solid #ff4e6a; border-left:4px solid #ff4e6a;
             padding:10px 16px; border-radius:4px; font-family:'Share Tech Mono',monospace;
             font-size:0.85em; color:#ff4e6a; margin-bottom:16px; }
.ok-box    { background:#0a1a10; border:1px solid #00ff9d; border-left:4px solid #00ff9d;
             padding:8px 16px; border-radius:4px; font-family:'Share Tech Mono',monospace;
             font-size:0.8em; color:#00ff9d; margin-bottom:16px; }
[data-testid="metric-container"] { background:#111827; border:1px solid #1e2d45;
    border-left:3px solid #00ff9d; padding:12px; border-radius:4px; }
[data-testid="metric-container"] label { color:#5a6a7e !important; font-size:0.7em !important; }
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color:#00ff9d !important; font-family:'Share Tech Mono',monospace; }
.stTabs [data-baseweb="tab-list"]  { background:#0a0d14; border-bottom:1px solid #1e2d45; }
.stTabs [data-baseweb="tab"]       { color:#5a6a7e; font-family:'Share Tech Mono',monospace; font-size:0.8em; }
.stTabs [aria-selected="true"]     { color:#00ff9d !important; border-bottom:2px solid #00ff9d !important; }
</style>
""", unsafe_allow_html=True)

# ── Constantes de color ────────────────────────────────────────────────────────
ACCENT = "#00ff9d"
RED    = "#ff4e6a"
YELLOW = "#ffd166"
GRID   = "#1e2d45"
BG_P   = "#111827"
BG_PL  = "#0d1520"

MEDIO_COLORS = {
    "El País":"#4fc3f7","El Mundo":"#ff8a65","ABC":"#ce93d8",
    "Público":"#80cbc4","El Confidencial":"#fff176",
    "BBC World":"#f48fb1","NYT World":"#a5d6a7",
    "Fox News":"#ff5252","RT":"#ef9a9a","France24 ES":"#90caf9",
}

FASE_LABELS = {
    "inoculacion":"🟡 SEM 1 · INOCULACIÓN",
    "saturacion":"🟠 SEM 2 · SATURACIÓN",
    "pivot":"🔴 SEM 3 · PIVOT ⚡",
    "consolidacion":"☠  SEM 4 · CONSOLIDACIÓN",
}

# helper: aplica tema oscuro a cualquier figura
def dark(fig, height=280, **extra):
    fig.update_layout(
        paper_bgcolor=BG_P, plot_bgcolor=BG_PL,
        font=dict(family="Share Tech Mono, monospace", color="#7a8a9a", size=11),
        margin=dict(l=10, r=10, t=30, b=10),
        height=height,
        **extra
    )
    fig.update_xaxes(gridcolor=GRID, linecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, linecolor=GRID)
    return fig

# ── Carga de datos ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=900)
def load_kpis():
    p = DATA_DIR / "kpis.csv"
    if not p.exists(): return pd.DataFrame()
    df = pd.read_csv(p)
    df["fecha"] = pd.to_datetime(df["fecha"])
    return df

@st.cache_data(ttl=900)
def load_articulos():
    p = DATA_DIR / "articulos.csv"
    if not p.exists(): return pd.DataFrame()
    df = pd.read_csv(p)
    df["publicado"] = pd.to_datetime(df["publicado"], utc=True, errors="coerce")
    return df

@st.cache_data(ttl=900)
def load_campanas():
    p = DATA_DIR / "campanas.csv"
    if not p.exists(): return pd.DataFrame()
    return pd.read_csv(p)

def parse_json_col(val):
    if pd.isna(val) or val == "": return {}
    try: return json.loads(val)
    except Exception:
        try: return ast.literal_eval(val)
        except Exception: return {}

# ── HEADER ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="mani-header">
  <div class="mani-title">M.A.N.I // MEDIA AUDIT &amp; NARRATIVE INTELLIGENCE</div>
  <div class="mani-sub">Sistema de vigilancia editorial · M. Castillo - Privacy Tools · 2026</div>
</div>
""", unsafe_allow_html=True)

kpis_df  = load_kpis()
arts_df  = load_articulos()
camps_df = load_campanas()

if kpis_df.empty:
    st.warning("⏳ Sin datos aún. El pipeline del Odroid aún no ha generado el primer ciclo.")
    st.stop()

# ── Campaña activa ─────────────────────────────────────────────────────────────
active_camp = None
if not camps_df.empty:
    act = camps_df[camps_df["fin"] == "EN CURSO"]
    if not act.empty:
        active_camp = act.iloc[0]

if active_camp is not None:
    fase_label = FASE_LABELS.get(active_camp["fase"], active_camp["fase"].upper())
    st.markdown(f'<div class="alert-box">⚠️ CAMPAÑA DETECTADA &nbsp;|&nbsp; {fase_label} &nbsp;|&nbsp; Inicio: {active_camp["inicio"]}</div>',
                unsafe_allow_html=True)
else:
    sync_max = kpis_df["sync_index"].max() if "sync_index" in kpis_df.columns else 0
    st.markdown(f'<div class="ok-box">✓ Sin campaña activa · Sync máximo: {sync_max:.3f}</div>',
                unsafe_allow_html=True)

# ── Métricas ───────────────────────────────────────────────────────────────────
c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("Artículos (72h)",       f"{len(arts_df):,}" if not arts_df.empty else "—")
c2.metric("Medios monitoreados",   kpis_df["medio"].nunique())
last_sync = float(kpis_df.sort_values("fecha")["sync_index"].iloc[-1]) if not kpis_df.empty else 0
c3.metric("Sync Index (último)",   f"{last_sync:.3f}")
c4.metric("Campañas registradas",  len(camps_df) if not camps_df.empty else 0)
c5.metric("Última actualización",  datetime.now(timezone.utc).strftime("%H:%M UTC"))

st.divider()

tab1,tab2,tab3,tab4,tab5 = st.tabs([
    "📡 Sync & Pivot","🧭 Sentiment Bias","💉 Keyword Injection","📰 Artículos","🗂 Campañas"
])

# ═══════════ TAB 1 ═══════════════════════════════════════════════════════════
with tab1:
    col_a, col_b = st.columns([1, 2])

    with col_a:
        st.markdown("#### Media Sync Index")
        st.caption("Similitud coseno entre medios. ≥0.65 = alerta campaña.")
        sync_ts = kpis_df.groupby("fecha")["sync_index"].mean().reset_index()
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=sync_ts["fecha"], y=sync_ts["sync_index"],
            mode="lines+markers", line=dict(color=ACCENT, width=2),
            fill="tozeroy", fillcolor="rgba(0,255,157,0.09)", name="Sync",
        ))
        fig.add_hline(y=0.65, line_dash="dash", line_color=RED,
                      annotation_text="umbral", annotation_font_color=RED)
        dark(fig, height=280, yaxis=dict(range=[0,1], gridcolor=GRID))
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.markdown("#### Pivot Score por Medio")
        st.caption("Distancia euclidiana TF-IDF respecto al día anterior.")
        fig2 = go.Figure()
        for medio in kpis_df["medio"].unique():
            sub = kpis_df[kpis_df["medio"]==medio].sort_values("fecha")
            fig2.add_trace(go.Scatter(
                x=sub["fecha"], y=sub["pivot_score"],
                mode="lines+markers", name=medio,
                line=dict(color=MEDIO_COLORS.get(medio,"#aaa"), width=1.5),
                marker=dict(size=4),
            ))
        dark(fig2, height=280,
             yaxis=dict(range=[0,1], gridcolor=GRID),
             legend=dict(orientation="h", y=-0.25, font=dict(size=9)))
        st.plotly_chart(fig2, use_container_width=True)

# ═══════════ TAB 2 ═══════════════════════════════════════════════════════════
with tab2:
    st.markdown("#### Sentiment Bias · Actores Geopolíticos")
    st.caption("Score VADER promedio. Positivo = favorable. Negativo = hostil.")

    sent_rows = []
    for _, row in kpis_df.iterrows():
        for actor, score in parse_json_col(row.get("sentiment_bias","{}")).items():
            sent_rows.append({"fecha":row["fecha"],"medio":row["medio"],"actor":actor,"score":score})

    if sent_rows:
        sent_df = pd.DataFrame(sent_rows)
        sent_df["fecha"] = pd.to_datetime(sent_df["fecha"])
        col1, col2 = st.columns(2)

        with col1:
            actor_avg = sent_df.groupby("actor")["score"].mean().reset_index().sort_values("score")
            colors_bar = [ACCENT if s>=0 else RED for s in actor_avg["score"]]
            fig3 = go.Figure(go.Bar(
                x=actor_avg["score"], y=actor_avg["actor"], orientation="h",
                marker_color=colors_bar,
                text=[f"{v:+.3f}" for v in actor_avg["score"]], textposition="outside",
            ))
            dark(fig3, height=300, title="Promedio global",
                 xaxis=dict(range=[-1,1], gridcolor=GRID))
            st.plotly_chart(fig3, use_container_width=True)

        with col2:
            sel = st.selectbox("Actor", sorted(sent_df["actor"].unique()))
            sub2 = sent_df[sent_df["actor"]==sel].groupby("fecha")["score"].mean().reset_index()
            fig4 = go.Figure(go.Scatter(
                x=sub2["fecha"], y=sub2["score"],
                mode="lines+markers", line=dict(color=YELLOW, width=2),
            ))
            fig4.add_hline(y=0, line_dash="dot", line_color="#5a6a7e")
            dark(fig4, height=300, title=f"Evolución · {sel}",
                 yaxis=dict(range=[-1,1], gridcolor=GRID))
            st.plotly_chart(fig4, use_container_width=True)

        st.markdown("##### Mapa de calor: Medio × Actor")
        pivot_heat = sent_df.groupby(["medio","actor"])["score"].mean().unstack(fill_value=0)
        fig5 = px.imshow(pivot_heat,
                         color_continuous_scale=[[0,RED],[0.5,"#111827"],[1,ACCENT]],
                         zmin=-1, zmax=1, aspect="auto")
        dark(fig5, height=350)
        st.plotly_chart(fig5, use_container_width=True)
    else:
        st.info("Sin datos de sentiment aún.")

# ═══════════ TAB 3 ═══════════════════════════════════════════════════════════
with tab3:
    st.markdown("#### Keyword Injection")
    st.caption("Términos exógenos (PR, agencias, narrativas coordinadas) en titulares.")

    kw_rows = []
    for _, row in kpis_df.iterrows():
        for kw, cnt in parse_json_col(row.get("keyword_inj","{}")).items():
            kw_rows.append({"fecha":row["fecha"],"medio":row["medio"],"keyword":kw,"freq":cnt})

    if kw_rows:
        kw_df = pd.DataFrame(kw_rows)
        col1, col2 = st.columns(2)
        with col1:
            top = kw_df.groupby("keyword")["freq"].sum().reset_index().sort_values("freq").tail(15)
            fig6 = go.Figure(go.Bar(x=top["freq"], y=top["keyword"],
                                    orientation="h", marker_color=YELLOW))
            dark(fig6, height=400, title="Top keywords acumuladas")
            st.plotly_chart(fig6, use_container_width=True)
        with col2:
            kw_med = kw_df.groupby(["medio","keyword"])["freq"].sum().reset_index()
            fig7 = px.bar(kw_med, x="medio", y="freq", color="keyword",
                          color_discrete_sequence=px.colors.qualitative.Dark24)
            dark(fig7, height=400, title="Por medio", xaxis_tickangle=-30)
            st.plotly_chart(fig7, use_container_width=True)
    else:
        st.info("Sin keywords detectadas aún.")

# ═══════════ TAB 4 ═══════════════════════════════════════════════════════════
with tab4:
    st.markdown("#### Últimas 72h · Artículos ingestados")
    if not arts_df.empty:
        col1, col2 = st.columns([1,3])
        with col1:
            medios_sel = st.multiselect("Medio", sorted(arts_df["medio"].unique()),
                                        default=sorted(arts_df["medio"].unique()))
            lineas_sel = st.multiselect("Línea", sorted(arts_df["linea"].unique()),
                                        default=sorted(arts_df["linea"].unique()))
        with col2:
            filt = arts_df[arts_df["medio"].isin(medios_sel) & arts_df["linea"].isin(lineas_sel)]\
                       .sort_values("publicado", ascending=False)
            cnt = filt["medio"].value_counts().reset_index()
            cnt.columns = ["medio","n"]
            fig8 = go.Figure(go.Pie(
                labels=cnt["medio"], values=cnt["n"],
                marker=dict(colors=[MEDIO_COLORS.get(m,"#aaa") for m in cnt["medio"]]),
                hole=0.5,
            ))
            dark(fig8, height=230, showlegend=True, legend=dict(font=dict(size=9)))
            st.plotly_chart(fig8, use_container_width=True)

        show = [c for c in ["publicado","medio","linea","titulo","url"] if c in filt.columns]
        st.dataframe(filt[show].head(200), use_container_width=True, hide_index=True,
                     column_config={
                         "url": st.column_config.LinkColumn("url"),
                         "publicado": st.column_config.DatetimeColumn("publicado", format="DD/MM HH:mm"),
                     })
    else:
        st.info("Sin artículos.")

# ═══════════ TAB 5 ═══════════════════════════════════════════════════════════
with tab5:
    st.markdown("#### Historial de Campañas Detectadas")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
| Fase | Días | Descripción |
|------|------|-------------|
| 🟡 Inoculación | 1–7 | Día Cero · nuevos términos |
| 🟠 Saturación | 8–14 | Unanimidad editorial |
| 🔴 Pivot | 15–21 | Cambio de postura |
| ☠ Consolidación | 22+ | El tema se convierte en dogma |
        """)
    with col2:
        if "alerta_campana" in kpis_df.columns:
            alert_ts = kpis_df.groupby("fecha")["alerta_campana"].max().reset_index()
            fig9 = go.Figure(go.Bar(
                x=alert_ts["fecha"], y=alert_ts["alerta_campana"],
                marker_color=[RED if v else "rgba(0,255,157,0.2)" for v in alert_ts["alerta_campana"]],
            ))
            dark(fig9, height=180, title="Alertas activas",
                 yaxis=dict(tickvals=[0,1], ticktext=["OK","ALERTA"], gridcolor=GRID))
            st.plotly_chart(fig9, use_container_width=True)

    if not camps_df.empty:
        st.dataframe(camps_df, use_container_width=True, hide_index=True)
    else:
        st.success("✓ Sin campañas en el histórico.")

st.divider()
st.markdown(
    '<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.7em;color:#5a6a7e;text-align:center">'
    'MANI v1.1 · © 2026 M. Castillo · Privacy Tools · mybloggingnotes@gmail.com · '
    'Odroid C2/DietPi → GitHub → Streamlit Cloud · Sin APIs de terceros'
    '</div>', unsafe_allow_html=True)
