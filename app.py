#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MANI — app.py  v1.2
Media Audit & Narrative Intelligence · M. Castillo 2026
Odroid C2/DietPi → GitHub CSV → Streamlit Cloud
"""

import streamlit as st
import pandas as pd
import json, ast
from datetime import datetime, timezone
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px

DATA_DIR = Path("data")

st.set_page_config(
    page_title="MANI · Media Audit & Narrative Intelligence",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@500;600;700&family=Orbitron:wght@700&display=swap');

html, body, [class*="css"] { font-family: 'Rajdhani', sans-serif; }
.stApp { background-color: #080b12; color: #d0dae8; }

/* ── Header ── */
.mani-header { border-bottom: 2px solid #1a2d45; padding: 0 0 14px 0; margin-bottom: 18px; }
.mani-title  { font-family: 'Orbitron', monospace; font-size: 1.3em; color: #00ff9d;
               letter-spacing: 4px; text-shadow: 0 0 20px rgba(0,255,157,0.4); }
.mani-sub    { font-family: 'Share Tech Mono', monospace; font-size: 0.72em; color: #4a6a7e; margin-top:4px; }

/* ── Alertas ── */
.alert-box {
    background: linear-gradient(135deg,#1a0a0e,#200d12);
    border: 1px solid #ff4e6a; border-left: 4px solid #ff4e6a;
    padding: 12px 18px; border-radius: 6px;
    font-family:'Share Tech Mono',monospace; font-size:0.85em; color:#ff4e6a;
    margin-bottom:16px; animation: pulse 2s infinite;
}
.ok-box {
    background: linear-gradient(135deg,#091410,#0b1a14);
    border: 1px solid #00ff9d; border-left: 4px solid #00ff9d;
    padding: 10px 18px; border-radius: 6px;
    font-family:'Share Tech Mono',monospace; font-size:0.78em; color:#00cc7a;
    margin-bottom:16px;
}
@keyframes pulse { 0%,100%{border-color:#ff4e6a} 50%{border-color:#ff8a9a} }

/* ── KPI tiles ── */
[data-testid="metric-container"] {
    background: linear-gradient(135deg,#0f1824,#111e2e) !important;
    border: 1px solid #1e3050 !important;
    border-top: 3px solid #00ff9d !important;
    border-radius: 6px !important;
    padding: 14px 16px !important;
}
[data-testid="metric-container"] label {
    color: #a0b8d0 !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.68em !important;
    text-transform: uppercase;
    letter-spacing: 1px;
}
[data-testid="stMetricValue"] {
    color: #ffffff !important;
    font-family: 'Orbitron', monospace !important;
    font-size: 1.6em !important;
    font-weight: 700 !important;
}
[data-testid="stMetricDelta"] { color: #00ff9d !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #080b12;
    border-bottom: 1px solid #1a2d45;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    color: #4a6a7e !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 0.78em !important;
    padding: 8px 14px !important;
    border-radius: 4px 4px 0 0 !important;
}
.stTabs [aria-selected="true"] {
    color: #00ff9d !important;
    background: #0f1824 !important;
    border-bottom: 2px solid #00ff9d !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] { border: 1px solid #1a2d45; border-radius:4px; }

/* ── Divider ── */
hr { border-color: #1a2d45 !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width:6px; height:6px; }
::-webkit-scrollbar-track { background:#080b12; }
::-webkit-scrollbar-thumb { background:#1e3050; border-radius:3px; }

/* ── Guide cards ── */
.guide-card {
    background: #0f1824; border: 1px solid #1e3050; border-radius:6px;
    padding: 16px 20px; margin-bottom: 12px;
}
.guide-title { color:#00ff9d; font-family:'Share Tech Mono',monospace; font-size:0.85em;
               text-transform:uppercase; letter-spacing:2px; margin-bottom:8px; }
.kpi-def { background:#080b12; border-left:3px solid #00ff9d; padding:8px 12px;
           margin:6px 0; border-radius:0 4px 4px 0; font-size:0.9em; }
</style>
""", unsafe_allow_html=True)

# ── Colores ────────────────────────────────────────────────────────────────────
ACCENT = "#00ff9d"
RED    = "#ff4e6a"
YELLOW = "#ffd166"
BLUE   = "#4fc3f7"
GRID   = "#1a2d45"
BG_P   = "#0f1824"
BG_PL  = "#080e18"

MEDIO_COLORS = {
    "El País":"#4fc3f7","El Mundo":"#ff8a65","ABC":"#ce93d8",
    "Público":"#80cbc4","El Confidencial":"#fff176",
    "BBC World":"#f48fb1","NYT World":"#a5d6a7",
    "Fox News":"#ff5252","RT":"#ef9a9a","France24 ES":"#90caf9",
}
FASE_LABELS = {
    "inoculacion":"🟡 SEM 1 · INOCULACIÓN",
    "saturacion": "🟠 SEM 2 · SATURACIÓN",
    "pivot":       "🔴 SEM 3 · PIVOT ⚡",
    "consolidacion":"☠  SEM 4 · CONSOLIDACIÓN",
}

def dark(fig, height=280, **extra):
    fig.update_layout(
        paper_bgcolor=BG_P, plot_bgcolor=BG_PL,
        font=dict(family="Share Tech Mono, monospace", color="#8090a8", size=11),
        margin=dict(l=10, r=10, t=35, b=10),
        height=height, **extra
    )
    fig.update_xaxes(gridcolor=GRID, linecolor=GRID, zerolinecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, linecolor=GRID, zerolinecolor=GRID)
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
    if pd.isna(val) or str(val).strip() in ("", "{}"): return {}
    try: return json.loads(val)
    except Exception:
        try: return ast.literal_eval(val)
        except Exception: return {}

# ── HEADER ─────────────────────────────────────────────────────────────────────
now_utc = datetime.now(timezone.utc)
col_h1, col_h2 = st.columns([3,1])
with col_h1:
    st.markdown("""
    <div class="mani-header">
      <div class="mani-title">◈ M.A.N.I · MEDIA AUDIT & NARRATIVE INTELLIGENCE</div>
      <div class="mani-sub">Sistema autónomo de vigilancia editorial y análisis de narrativas · M. Castillo - Privacy Tools · 2026</div>
    </div>""", unsafe_allow_html=True)
with col_h2:
    st.markdown(f"""
    <div style="text-align:right;font-family:'Share Tech Mono',monospace;font-size:0.7em;color:#4a6a7e;padding-top:8px">
    🕐 {now_utc.strftime('%Y-%m-%d %H:%M UTC')}<br>
    🔄 Refresco cada 15 min<br>
    📡 10 fuentes · 5 países
    </div>""", unsafe_allow_html=True)

# ── Datos ──────────────────────────────────────────────────────────────────────
kpis_df  = load_kpis()
arts_df  = load_articulos()
camps_df = load_campanas()

if kpis_df.empty:
    st.warning("⏳ Sin datos. El pipeline del Odroid aún no ha completado el primer ciclo.")
    st.stop()

# ── Campaña activa ─────────────────────────────────────────────────────────────
active_camp = None
if not camps_df.empty:
    act = camps_df[camps_df["fin"].astype(str) == "EN CURSO"]
    if not act.empty:
        active_camp = act.iloc[0]

if active_camp is not None:
    fl = FASE_LABELS.get(str(active_camp["fase"]), str(active_camp["fase"]).upper())
    st.markdown(f'<div class="alert-box">⚠️ CAMPAÑA DE INFLUENCIA DETECTADA &nbsp;|&nbsp; {fl} &nbsp;|&nbsp; Inicio: {active_camp["inicio"]}</div>',
                unsafe_allow_html=True)
else:
    sync_max = float(kpis_df["sync_index"].max()) if "sync_index" in kpis_df.columns else 0
    st.markdown(f'<div class="ok-box">✓ SISTEMA NOMINAL · Sin campaña activa · Sync máximo registrado: <strong>{sync_max:.4f}</strong> (umbral alerta: 0.650)</div>',
                unsafe_allow_html=True)

# ── KPI tiles ──────────────────────────────────────────────────────────────────
last_sync  = float(kpis_df.sort_values("fecha")["sync_index"].iloc[-1]) if not kpis_df.empty else 0
last_pivot = float(kpis_df.sort_values("fecha")["pivot_score"].max()) if "pivot_score" in kpis_df.columns else 0
n_arts     = len(arts_df) if not arts_df.empty else 0
n_medios   = kpis_df["medio"].nunique() if not kpis_df.empty else 0
n_camps    = len(camps_df) if not camps_df.empty else 0

c1,c2,c3,c4,c5,c6 = st.columns(6)
c1.metric("📰 Artículos (72h)",     f"{n_arts:,}",         help="Artículos ingestados en las últimas 72h")
c2.metric("📡 Medios activos",      f"{n_medios}",         help="Medios distintos con artículos procesados")
c3.metric("🔄 Sync Index",          f"{last_sync:.4f}",    help="Similitud coseno entre medios. ≥0.65 = campaña coordinada")
c4.metric("📊 Pivot Score max",     f"{last_pivot:.4f}",   help="Máximo cambio editorial detectado. >0.5 = giro significativo")
c5.metric("🚨 Campañas",            f"{n_camps}",          help="Campañas de influencia detectadas históricamente")
c6.metric("🕐 Actualización",       now_utc.strftime("%H:%M"), help="Hora UTC de esta carga. Datos se actualizan cada 3h")

st.divider()

# ── TABS ───────────────────────────────────────────────────────────────────────
tab1,tab2,tab3,tab4,tab5,tab6,tab7 = st.tabs([
    "📡 Sync & Pivot",
    "🧭 Sentiment",
    "💉 Keywords",
    "📰 Artículos",
    "🚨 Campañas",
    "📋 Logs",
    "📖 Guía",
])

# ═══════════════════ TAB 1: SYNC & PIVOT ══════════════════════════════════════
with tab1:
    st.caption("**Media Sync Index**: similitud coseno promedio entre todos los medios monitoreados. Valores ≥0.65 indican que medios de distintas líneas editoriales están usando el mismo vocabulario — señal de campaña coordinada. **Pivot Score**: distancia euclidiana TF-IDF entre el corpus de hoy y el de ayer para cada medio. Valores altos indican un cambio brusco en la agenda editorial.")

    col_a, col_b = st.columns([1, 2])
    with col_a:
        st.markdown("#### 🔄 Media Sync Index")
        sync_ts = kpis_df.groupby("fecha")["sync_index"].mean().reset_index()
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=sync_ts["fecha"], y=sync_ts["sync_index"],
            mode="lines+markers",
            line=dict(color=ACCENT, width=2.5),
            fill="tozeroy", fillcolor="rgba(0,255,157,0.07)",
            name="Sync Index",
            hovertemplate="<b>%{x|%d/%m}</b><br>Sync: %{y:.4f}<extra></extra>",
        ))
        fig.add_hline(y=0.65, line_dash="dash", line_color=RED, line_width=1.5,
                      annotation_text="umbral campaña 0.65",
                      annotation_font_color=RED, annotation_font_size=10)
        fig.add_hrect(y0=0.65, y1=1, fillcolor="rgba(255,78,106,0.05)", line_width=0)
        dark(fig, height=300, yaxis=dict(range=[0,1], gridcolor=GRID, tickformat=".3f"))
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.markdown("#### 📊 Pivot Score por Medio")
        fig2 = go.Figure()
        for medio in sorted(kpis_df["medio"].unique()):
            sub = kpis_df[kpis_df["medio"]==medio].sort_values("fecha")
            fig2.add_trace(go.Scatter(
                x=sub["fecha"], y=sub["pivot_score"],
                mode="lines+markers", name=medio,
                line=dict(color=MEDIO_COLORS.get(medio,"#aaa"), width=1.8),
                marker=dict(size=5),
                hovertemplate=f"<b>{medio}</b><br>%{{x|%d/%m}}<br>Pivot: %{{y:.4f}}<extra></extra>",
            ))
        dark(fig2, height=300,
             yaxis=dict(range=[0,1], gridcolor=GRID, tickformat=".3f"),
             legend=dict(orientation="h", y=-0.3, font=dict(size=9),
                         bgcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig2, use_container_width=True)

    # Tabla resumen KPIs
    st.markdown("#### 📋 Últimos KPIs por medio")
    last_kpis = kpis_df.sort_values("fecha").groupby("medio").last().reset_index()
    last_kpis = last_kpis[["medio","fecha","pivot_score","sync_index","num_articulos","alerta_campana"]].copy()
    last_kpis.columns = ["Medio","Fecha","Pivot Score","Sync Index","N° Artículos","⚠ Alerta"]
    last_kpis["⚠ Alerta"] = last_kpis["⚠ Alerta"].map({0:"✓ OK",1:"⚠ CAMPAÑA"})
    st.dataframe(last_kpis, use_container_width=True, hide_index=True)

# ═══════════════════ TAB 2: SENTIMENT ═════════════════════════════════════════
with tab2:
    st.caption("**Sentiment Bias**: score VADER promedio por actor geopolítico. +1.0 = cobertura totalmente positiva/favorable. -1.0 = cobertura hostil. Los valores revelan la agenda real detrás del lenguaje aparentemente neutral. El **mapa de calor** cruza medios × actores para detectar patrones sistemáticos.")

    sent_rows = []
    for _, row in kpis_df.iterrows():
        for actor, score in parse_json_col(row.get("sentiment_bias","{}")).items():
            sent_rows.append({"fecha":row["fecha"],"medio":row["medio"],"actor":actor,"score":float(score)})

    if sent_rows:
        sent_df = pd.DataFrame(sent_rows)
        sent_df["fecha"] = pd.to_datetime(sent_df["fecha"])
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 🌍 Bias global por actor")
            actor_avg = sent_df.groupby("actor")["score"].mean().reset_index().sort_values("score")
            colors_bar = [ACCENT if s>=0 else RED for s in actor_avg["score"]]
            fig3 = go.Figure(go.Bar(
                x=actor_avg["score"], y=actor_avg["actor"], orientation="h",
                marker_color=colors_bar,
                text=[f"{v:+.3f}" for v in actor_avg["score"]],
                textposition="outside",
                textfont=dict(color="#d0dae8", size=11),
                hovertemplate="<b>%{y}</b><br>Score: %{x:+.4f}<extra></extra>",
            ))
            dark(fig3, height=320, title="Score VADER promedio (–1 hostil / +1 favorable)",
                 xaxis=dict(range=[-1,1], gridcolor=GRID, tickformat=".2f",
                            zeroline=True, zerolinecolor="#334455", zerolinewidth=1.5))
            st.plotly_chart(fig3, use_container_width=True)

        with col2:
            st.markdown("#### 📈 Evolución temporal")
            sel = st.selectbox("Actor geopolítico", sorted(sent_df["actor"].unique()))
            sub2 = sent_df[sent_df["actor"]==sel].groupby("fecha")["score"].mean().reset_index()
            fig4 = go.Figure()
            fig4.add_trace(go.Scatter(
                x=sub2["fecha"], y=sub2["score"],
                mode="lines+markers",
                line=dict(color=YELLOW, width=2.5),
                fill="tozeroy",
                fillcolor="rgba(255,209,102,0.07)",
                hovertemplate="%{x|%d/%m}: %{y:+.4f}<extra></extra>",
            ))
            fig4.add_hline(y=0, line_dash="dot", line_color="#334455", line_width=1)
            dark(fig4, height=320, title=f"Evolución bias hacia {sel}",
                 yaxis=dict(range=[-1,1], gridcolor=GRID, tickformat=".2f"))
            st.plotly_chart(fig4, use_container_width=True)

        st.markdown("#### 🗺 Mapa de calor: Medio × Actor")
        st.caption("Verde = cobertura favorable · Rojo = cobertura hostil · Negro = neutro o sin datos")
        pivot_heat = sent_df.groupby(["medio","actor"])["score"].mean().unstack(fill_value=0)
        fig5 = px.imshow(pivot_heat,
                         color_continuous_scale=[[0,RED],[0.5,"#0f1824"],[1,ACCENT]],
                         zmin=-1, zmax=1, aspect="auto",
                         text_auto=".2f")
        fig5.update_traces(textfont=dict(size=10, color="white"))
        dark(fig5, height=380)
        st.plotly_chart(fig5, use_container_width=True)
    else:
        st.info("Sin datos de sentiment aún. El processor necesita artículos con referencias a actores geopolíticos.")

# ═══════════════════ TAB 3: KEYWORDS ══════════════════════════════════════════
with tab3:
    st.caption("**Keyword Injection**: frecuencia de términos exógenos procedentes de agencias PR, think tanks o coordinación de narrativas. La aparición simultánea de estos términos en medios de distintas líneas editoriales es un indicador de campaña de influencia en curso.")

    kw_rows = []
    for _, row in kpis_df.iterrows():
        for kw, cnt in parse_json_col(row.get("keyword_inj","{}")).items():
            kw_rows.append({"fecha":row["fecha"],"medio":row["medio"],"keyword":kw,"freq":int(cnt)})

    if kw_rows:
        kw_df = pd.DataFrame(kw_rows)
        kw_df["fecha"] = pd.to_datetime(kw_df["fecha"])
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 💉 Top keywords detectadas")
            top = kw_df.groupby("keyword")["freq"].sum().reset_index().sort_values("freq").tail(15)
            fig6 = go.Figure(go.Bar(
                x=top["freq"], y=top["keyword"], orientation="h",
                marker=dict(color=top["freq"], colorscale=[[0,GRID],[1,YELLOW]]),
                hovertemplate="<b>%{y}</b><br>Frecuencia: %{x}<extra></extra>",
            ))
            dark(fig6, height=420, title="Frecuencia acumulada (todos los medios)")
            st.plotly_chart(fig6, use_container_width=True)

        with col2:
            st.markdown("#### 📊 Distribución por medio")
            kw_med = kw_df.groupby(["medio","keyword"])["freq"].sum().reset_index()
            fig7 = px.bar(kw_med, x="medio", y="freq", color="keyword",
                          color_discrete_sequence=px.colors.qualitative.Dark24,
                          barmode="stack")
            dark(fig7, height=420, title="Keywords por medio (stacked)",
                 xaxis=dict(tickangle=-35))
            st.plotly_chart(fig7, use_container_width=True)

        # Evolución temporal de keyword
        st.markdown("#### 📈 Evolución temporal de keyword")
        all_kws = sorted(kw_df["keyword"].unique())
        sel_kw = st.selectbox("Keyword a trazar", all_kws)
        kw_ts = kw_df[kw_df["keyword"]==sel_kw].groupby("fecha")["freq"].sum().reset_index()
        fig8 = go.Figure(go.Bar(
            x=kw_ts["fecha"], y=kw_ts["freq"],
            marker_color=YELLOW,
            hovertemplate="%{x|%d/%m}: %{y} menciones<extra></extra>",
        ))
        dark(fig8, height=220, title=f'Frecuencia diaria · "{sel_kw}"')
        st.plotly_chart(fig8, use_container_width=True)
    else:
        st.info("Sin keywords inyectadas detectadas aún.")

# ═══════════════════ TAB 4: ARTÍCULOS ═════════════════════════════════════════
with tab4:
    st.caption("Artículos ingestados en las **últimas 72 horas** desde las 10 fuentes RSS monitoreadas. Usa los filtros para segmentar por medio o línea editorial. Los enlaces abren el artículo original.")

    if not arts_df.empty:
        col1, col2 = st.columns([1,3])
        with col1:
            medios_sel = st.multiselect("Medio", sorted(arts_df["medio"].unique()),
                                        default=sorted(arts_df["medio"].unique()),
                                        key="art_medios")
            lineas_sel = st.multiselect("Línea editorial", sorted(arts_df["linea"].unique()),
                                        default=sorted(arts_df["linea"].unique()),
                                        key="art_lineas")
            st.markdown("---")
            st.markdown(f"**Mostrando:** {len(arts_df):,} artículos totales")

        with col2:
            filt = arts_df[
                arts_df["medio"].isin(medios_sel) &
                arts_df["linea"].isin(lineas_sel)
            ].sort_values("publicado", ascending=False)

            cnt = filt["medio"].value_counts().reset_index()
            cnt.columns = ["medio","n"]
            fig9 = go.Figure(go.Pie(
                labels=cnt["medio"], values=cnt["n"],
                marker=dict(colors=[MEDIO_COLORS.get(m,"#aaa") for m in cnt["medio"]],
                            line=dict(color="#080b12", width=2)),
                hole=0.55,
                textinfo="label+percent",
                textfont=dict(size=10),
                hovertemplate="<b>%{label}</b><br>%{value} artículos (%{percent})<extra></extra>",
            ))
            fig9.add_annotation(text=f"{len(filt)}<br>arts", x=0.5, y=0.5,
                                font=dict(size=16, color="#ffffff", family="Orbitron"),
                                showarrow=False)
            dark(fig9, height=220, showlegend=True,
                 legend=dict(orientation="h", y=-0.15, font=dict(size=9)))
            st.plotly_chart(fig9, use_container_width=True)

        show = [c for c in ["publicado","medio","linea","titulo","url"] if c in filt.columns]
        st.dataframe(
            filt[show].head(300),
            use_container_width=True, hide_index=True,
            column_config={
                "url": st.column_config.LinkColumn("🔗 Enlace"),
                "publicado": st.column_config.DatetimeColumn("📅 Publicado", format="DD/MM HH:mm"),
                "medio": st.column_config.TextColumn("📰 Medio"),
                "linea": st.column_config.TextColumn("🏷 Línea"),
                "titulo": st.column_config.TextColumn("📝 Titular", width="large"),
            }
        )
    else:
        st.info("Sin artículos disponibles.")

# ═══════════════════ TAB 5: CAMPAÑAS ══════════════════════════════════════════
with tab5:
    st.caption("Una **campaña de influencia** se detecta cuando el Media Sync Index supera 0.65 durante días consecutivos, indicando que medios de distintas líneas editoriales adoptan el mismo vocabulario y encuadre narrativo de forma simultánea.")

    col1, col2 = st.columns([1,1])
    with col1:
        st.markdown("#### 🗓 Fases de campaña (modelo 4 semanas)")
        st.markdown("""
<div class="guide-card">
<div class="kpi-def">🟡 <strong>Semana 1 · INOCULACIÓN</strong> — Día Cero. Aparición de terminología nueva (emocional o técnica) que empieza a repetirse en titulares. El algoritmo marca el inicio de la ventana de análisis.</div>
<div class="kpi-def">🟠 <strong>Semana 2 · SATURACIÓN</strong> — El ML mide coordinación. Si el sentimiento es unánime en medios de distintas líneas editoriales, el sistema activa la alerta de "Campaña en Curso".</div>
<div class="kpi-def">🔴 <strong>Semana 3 · PIVOT / EL GIRO</strong> — Análisis comparativo. El medio modifica su postura inicial para justificar una nueva acción política o militar. Pivot Score elevado.</div>
<div class="kpi-def">☠ <strong>Semana 4 · CONSOLIDACIÓN</strong> — El tema deja de ser noticia para convertirse en dogma aceptado. El sistema archiva la firma semántica para futuras comparaciones.</div>
</div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("#### 📊 Histórico de alertas")
        if "alerta_campana" in kpis_df.columns:
            alert_ts = kpis_df.groupby("fecha")["alerta_campana"].max().reset_index()
            fig10 = go.Figure(go.Bar(
                x=alert_ts["fecha"], y=alert_ts["alerta_campana"],
                marker_color=[RED if v else "rgba(0,255,157,0.15)"
                              for v in alert_ts["alerta_campana"]],
                hovertemplate="%{x|%d/%m}: %{y}<extra></extra>",
            ))
            dark(fig10, height=200, title="Días con Sync ≥ 0.65",
                 yaxis=dict(tickvals=[0,1], ticktext=["✓ OK","⚠ ALERTA"],
                            gridcolor=GRID))
            st.plotly_chart(fig10, use_container_width=True)
        else:
            st.info("Sin histórico de alertas.")

    st.markdown("#### 📋 Registro de campañas detectadas")
    if not camps_df.empty:
        st.dataframe(camps_df, use_container_width=True, hide_index=True,
                     column_config={
                         "inicio": st.column_config.TextColumn("📅 Inicio"),
                         "fin":    st.column_config.TextColumn("📅 Fin"),
                         "fase":   st.column_config.TextColumn("⚡ Fase"),
                         "descripcion": st.column_config.TextColumn("📝 Descripción", width="large"),
                     })
    else:
        st.success("✓ Sin campañas registradas en el histórico.")

# ═══════════════════ TAB 6: LOGS ══════════════════════════════════════════════
with tab6:
    st.markdown("#### 📋 Estado del pipeline (basado en datos disponibles)")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**📊 Estadísticas de ingestión**")
        if not kpis_df.empty:
            stats = {
                "Primer dato registrado": str(kpis_df["fecha"].min().date()),
                "Último dato registrado": str(kpis_df["fecha"].max().date()),
                "Días con datos": kpis_df["fecha"].nunique(),
                "Medios activos": kpis_df["medio"].nunique(),
                "Total registros KPI": len(kpis_df),
                "Sync Index máximo": f"{kpis_df['sync_index'].max():.4f}",
                "Sync Index mínimo": f"{kpis_df['sync_index'].min():.4f}",
                "Sync Index promedio": f"{kpis_df['sync_index'].mean():.4f}",
                "Alertas activadas": int(kpis_df["alerta_campana"].sum()),
            }
            for k,v in stats.items():
                st.markdown(f"- **{k}**: `{v}`")
        else:
            st.info("Sin datos de KPI.")

    with col2:
        st.markdown("**📰 Estadísticas de artículos**")
        if not arts_df.empty:
            stats2 = {
                "Total artículos (72h)": len(arts_df),
                "Medios con artículos": arts_df["medio"].nunique(),
                "Artículo más reciente": str(arts_df["publicado"].max()),
                "Artículo más antiguo": str(arts_df["publicado"].min()),
                "Líneas editoriales": arts_df["linea"].nunique(),
            }
            for k,v in stats2.items():
                st.markdown(f"- **{k}**: `{v}`")
            st.markdown("**Artículos por medio:**")
            for m, n in arts_df["medio"].value_counts().items():
                pct = 100*n/len(arts_df)
                st.markdown(f"  - {m}: `{n}` ({pct:.1f}%)")
        else:
            st.info("Sin artículos.")

    st.markdown("**⚙️ Configuración del pipeline**")
    st.code("""
# Odroid C2 · DietPi · ~/SIEG-mani/
# Cron /etc/cron.d/mani — sin conflicto con otros 30 crons SIEG

:10 */3  → scraper.py   (RSS → SQLite → articulos.csv)
:25 */3  → processor.py (SQLite → KPIs → kpis.csv + campanas.csv)
:40 */3  → mani_run.sh push (git commit + push → GitHub → Streamlit)
:55 04   → logrotate (diario)

# Arquitectura: sin nginx, sin NAT, sin tokens de terceros
# Odroid → GitHub CSV → Streamlit Cloud (público)
    """, language="bash")

# ═══════════════════ TAB 7: GUÍA ══════════════════════════════════════════════
with tab7:
    st.markdown("## 📖 Guía de uso · MANI v1.2")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
<div class="guide-card">
<div class="guide-title">🎯 Objetivo del sistema</div>
MANI detecta mediante métricas matemáticas tres fenómenos de influencia mediática:
<div class="kpi-def">📌 <strong>Narrative Shifting</strong> — Cambios bruscos en la línea editorial de un medio en periodos cortos. Detectado via Pivot Score (distancia TF-IDF entre corpus diarios).</div>
<div class="kpi-def">📌 <strong>Sincronización Mediática</strong> — Múltiples medios adoptando el mismo "guion" de forma simultánea. Detectado via Media Sync Index (coseno entre vectores de medios).</div>
<div class="kpi-def">📌 <strong>Análisis de Sesgo Geopolítico</strong> — Postura real de cada medio frente a actores internacionales. Detectado via Sentiment Bias (VADER por actor).</div>
</div>

<div class="guide-card">
<div class="guide-title">📐 KPIs: definición técnica</div>
<div class="kpi-def"><strong>Pivot Score</strong> [0–1] — Distancia euclidiana normalizada entre vectores TF-IDF del corpus de hoy vs. ayer. >0.5 indica un giro editorial significativo en 24h.</div>
<div class="kpi-def"><strong>Media Sync Index</strong> [0–1] — Similitud coseno promedio entre todos los pares de medios. <0.3 = divergencia normal. 0.3–0.65 = convergencia moderada. ≥0.65 = alerta de campaña coordinada.</div>
<div class="kpi-def"><strong>Sentiment Bias</strong> [–1,+1] — Score VADER compound promedio en artículos que mencionan al actor. <–0.3 = hostil. –0.3/+0.3 = neutro. >+0.3 = favorable.</div>
<div class="kpi-def"><strong>Keyword Injection</strong> [entero] — Frecuencia de términos exógenos de agencias PR, think tanks o coordinación narrativa. Lista de 30 términos vigilados.</div>
</div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
<div class="guide-card">
<div class="guide-title">📡 Fuentes monitoreadas</div>
<div class="kpi-def">🇪🇸 <strong>El País</strong> — centroizquierda</div>
<div class="kpi-def">🇪🇸 <strong>El Mundo</strong> — centroderecha</div>
<div class="kpi-def">🇪🇸 <strong>ABC</strong> — derecha</div>
<div class="kpi-def">🇪🇸 <strong>Público</strong> — izquierda</div>
<div class="kpi-def">🇪🇸 <strong>El Confidencial</strong> — liberal</div>
<div class="kpi-def">🇬🇧 <strong>BBC World</strong> — centrist</div>
<div class="kpi-def">🇺🇸 <strong>NYT World</strong> — centroliberal</div>
<div class="kpi-def">🇺🇸 <strong>Fox News</strong> — conservador</div>
<div class="kpi-def">🇷🇺 <strong>RT</strong> — estatal ruso</div>
<div class="kpi-def">🇫🇷 <strong>France24 ES</strong> — centrist</div>
</div>

<div class="guide-card">
<div class="guide-title">🔄 Ciclo de actualización</div>
<div class="kpi-def">⏱ El pipeline completo se ejecuta cada <strong>3 horas</strong> en el Odroid C2 (DietPi).</div>
<div class="kpi-def">📥 <strong>:10</strong> — Scraper: descarga y parsea RSS, detecta actores geopolíticos, guarda en SQLite.</div>
<div class="kpi-def">⚙️ <strong>:25</strong> — Processor: calcula KPIs con VADER + TF-IDF sin NumPy (optimizado para ARM).</div>
<div class="kpi-def">☁️ <strong>:40</strong> — Push: git commit + push a GitHub. Streamlit Cloud redespliega en ~1 min.</div>
<div class="kpi-def">🔒 <strong>Privacidad total</strong>: sin APIs de terceros (OpenAI, Google, etc.). Todo procesado localmente.</div>
</div>

<div class="guide-card">
<div class="guide-title">⚠️ Cómo interpretar una alerta</div>
<div class="kpi-def">1. Sync Index ≥ 0.65 → revisar Tab Campañas para ver la fase</div>
<div class="kpi-def">2. Identificar el actor geopolítico con mayor variación en Sentiment</div>
<div class="kpi-def">3. Buscar las keywords inyectadas predominantes en ese periodo</div>
<div class="kpi-def">4. Cruzar con Tab Artículos filtrando por fechas de la campaña</div>
</div>
        """, unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    '<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.68em;color:#3a5a6e;text-align:center;padding:4px">'
    'MANI v1.2 · © 2026 M. Castillo · Privacy Tools · mybloggingnotes@gmail.com · '
    'Odroid C2/DietPi → GitHub → Streamlit Cloud · Motor: VADER + TF-IDF puro · Sin APIs externas'
    '</div>',
    unsafe_allow_html=True)
