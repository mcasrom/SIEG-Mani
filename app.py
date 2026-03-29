#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MANI — app.py v1.3
Media Audit & Narrative Intelligence · M. Castillo 2026
16 fuentes · Telegram/Email alertas · Timestamp pipeline · SIEG integrado
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
    page_icon="🔍", layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Rajdhani:wght@500;600;700&family=Orbitron:wght@700;900&display=swap');

*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] { font-family: 'Rajdhani', sans-serif; }
.stApp { background-color: #080b12; color: #d0dae8; }

/* Header */
.mani-title { font-family:'Orbitron',monospace; font-size:1.25em; color:#00ff9d;
              letter-spacing:4px; text-shadow:0 0 24px rgba(0,255,157,0.5); }
.mani-sub   { font-family:'Share Tech Mono',monospace; font-size:0.7em; color:#3d5a6e; margin-top:3px; }
.header-bar { border-bottom:1px solid #1a2d45; padding-bottom:12px; margin-bottom:16px; }

/* Timestamp badge */
.ts-badge {
    background:#0c1520; border:1px solid #1a2d45; border-radius:6px;
    padding:8px 12px; font-family:'Share Tech Mono',monospace; font-size:0.68em;
    color:#4a7a6e; text-align:right; line-height:1.8;
}
.ts-badge strong { color:#00cc7a; }

/* Alertas */
.alert-box {
    background:linear-gradient(135deg,#1a0a0e,#200d12);
    border:1px solid #ff4e6a; border-left:4px solid #ff4e6a;
    padding:12px 18px; border-radius:6px;
    font-family:'Share Tech Mono',monospace; font-size:0.82em; color:#ff6a7e;
    margin-bottom:14px;
}
.ok-box {
    background:linear-gradient(135deg,#091410,#0b1a14);
    border:1px solid #1a4a38; border-left:4px solid #00ff9d;
    padding:10px 18px; border-radius:6px;
    font-family:'Share Tech Mono',monospace; font-size:0.75em; color:#00cc7a;
    margin-bottom:14px;
}

/* KPI tiles */
[data-testid="metric-container"] {
    background:linear-gradient(160deg,#0f1824,#111e2e) !important;
    border:1px solid #1a3050 !important; border-top:3px solid #00ff9d !important;
    border-radius:8px !important; padding:14px 16px !important;
}
[data-testid="metric-container"] label {
    color:#8aacbe !important; font-family:'Share Tech Mono',monospace !important;
    font-size:0.65em !important; text-transform:uppercase; letter-spacing:1.5px;
}
[data-testid="stMetricValue"] {
    color:#ffffff !important; font-family:'Orbitron',monospace !important;
    font-size:1.55em !important; font-weight:900 !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] { background:#080b12; border-bottom:1px solid #1a2d45; }
.stTabs [data-baseweb="tab"] {
    color:#3d5a6e !important; font-family:'Share Tech Mono',monospace !important;
    font-size:0.75em !important; padding:8px 14px !important;
}
.stTabs [aria-selected="true"] {
    color:#00ff9d !important; background:#0f1824 !important;
    border-bottom:2px solid #00ff9d !important;
}

/* SIEG link cards */
.sieg-card {
    background:#0f1824; border:1px solid #1a3050; border-radius:8px;
    padding:14px 18px; margin:6px 0; transition:border-color 0.2s;
    text-decoration:none; display:block;
}
.sieg-card:hover { border-color:#00ff9d; }
.sieg-card-title { color:#00ff9d; font-family:'Share Tech Mono',monospace;
                   font-size:0.82em; letter-spacing:1px; }
.sieg-card-desc  { color:#5a7a8e; font-size:0.85em; margin-top:3px; }

/* Guide */
.guide-card { background:#0f1824; border:1px solid #1a3050; border-radius:8px;
              padding:16px 20px; margin-bottom:12px; }
.guide-title { color:#00ff9d; font-family:'Share Tech Mono',monospace;
               font-size:0.8em; text-transform:uppercase; letter-spacing:2px; margin-bottom:8px; }
.kpi-def { background:#080b12; border-left:3px solid #00ff9d; padding:8px 12px;
           margin:5px 0; border-radius:0 4px 4px 0; font-size:0.88em; }

hr { border-color:#1a2d45 !important; }
::-webkit-scrollbar { width:5px; height:5px; }
::-webkit-scrollbar-track { background:#080b12; }
::-webkit-scrollbar-thumb { background:#1e3050; border-radius:3px; }
</style>
""", unsafe_allow_html=True)

# ── Colores ────────────────────────────────────────────────────────────────────
ACCENT = "#00ff9d"; RED = "#ff4e6a"; YELLOW = "#ffd166"; GRID = "#1a2d45"
BG_P = "#0f1824"; BG_PL = "#080e18"

MEDIO_COLORS = {
    "El País":"#4fc3f7","El Mundo":"#ff8a65","ABC":"#ce93d8","Público":"#80cbc4",
    "El Confidencial":"#fff176","El Diario":"#a8d8a8","La Vanguardia":"#ffb347",
    "RTVE":"#87ceeb","BBC World":"#f48fb1","The Guardian":"#98fb98",
    "NYT World":"#a5d6a7","Fox News":"#ff5252","RT":"#ef9a9a",
    "France24 ES":"#90caf9","Al Jazeera":"#ffd700","EFE via ABC":"#d3d3d3",
}
FASE_LABELS = {
    "inoculacion":"🟡 SEM 1 · INOCULACIÓN","saturacion":"🟠 SEM 2 · SATURACIÓN",
    "pivot":"🔴 SEM 3 · PIVOT ⚡","consolidacion":"☠  SEM 4 · CONSOLIDACIÓN",
}

def dark(fig, height=280, **extra):
    fig.update_layout(
        paper_bgcolor=BG_P, plot_bgcolor=BG_PL,
        font=dict(family="Share Tech Mono, monospace", color="#7090a8", size=11),
        margin=dict(l=10,r=10,t=35,b=10), height=height, **extra
    )
    fig.update_xaxes(gridcolor=GRID, linecolor=GRID, zerolinecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, linecolor=GRID, zerolinecolor=GRID)
    return fig

# ── Carga de datos ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=900)
def load_kpis():
    p = DATA_DIR/"kpis.csv"
    if not p.exists(): return pd.DataFrame()
    df = pd.read_csv(p); df["fecha"] = pd.to_datetime(df["fecha"]); return df

@st.cache_data(ttl=900)
def load_articulos():
    p = DATA_DIR/"articulos.csv"
    if not p.exists(): return pd.DataFrame()
    df = pd.read_csv(p)
    df["publicado"] = pd.to_datetime(df["publicado"], utc=True, errors="coerce")
    return df

@st.cache_data(ttl=900)
def load_campanas():
    p = DATA_DIR/"campanas.csv"
    if not p.exists(): return pd.DataFrame()
    return pd.read_csv(p)

@st.cache_data(ttl=900)
def load_timestamp() -> dict:
    p = DATA_DIR/"last_update.json"
    if not p.exists(): return {}
    try: return json.loads(p.read_text(encoding="utf-8"))
    except: return {}

def parse_json_col(val):
    if pd.isna(val) or str(val).strip() in ("","{}",""): return {}
    try: return json.loads(val)
    except:
        try: return ast.literal_eval(val)
        except: return {}

# ── Cargar datos ───────────────────────────────────────────────────────────────
kpis_df  = load_kpis()
arts_df  = load_articulos()
camps_df = load_campanas()
ts       = load_timestamp()
now_utc  = datetime.now(timezone.utc)

# ── HEADER ─────────────────────────────────────────────────────────────────────
col_h1, col_h2 = st.columns([4, 1])
with col_h1:
    st.markdown("""
    <div class="header-bar">
      <div class="mani-title">◈ M.A.N.I · MEDIA AUDIT & NARRATIVE INTELLIGENCE</div>
      <div class="mani-sub">Sistema autónomo de vigilancia editorial · M. Castillo - Privacy Tools · 2026 · 16 fuentes · 6 países</div>
    </div>""", unsafe_allow_html=True)
with col_h2:
    # Timestamp de último pipeline
    pipeline_time = ts.get("scraper_time","—")
    pipeline_date = ts.get("scraper_date","—")
    n_arts_ts     = ts.get("articulos_72h","—")
    nuevos_ts     = ts.get("nuevos_ciclo","—")
    st.markdown(f"""
    <div class="ts-badge">
    📡 Pipeline: <strong>{pipeline_date}</strong><br>
    🕐 Último push: <strong>{pipeline_time}</strong><br>
    📰 Arts 72h: <strong>{n_arts_ts}</strong><br>
    🆕 Nuevos ciclo: <strong>{nuevos_ts}</strong>
    </div>""", unsafe_allow_html=True)

# ── Alerta campaña ─────────────────────────────────────────────────────────────
active_camp = None
if not kpis_df.empty and not camps_df.empty:
    act = camps_df[camps_df["fin"].astype(str)=="EN CURSO"]
    if not act.empty: active_camp = act.iloc[0]

if active_camp is not None:
    fl = FASE_LABELS.get(str(active_camp["fase"]),str(active_camp["fase"]).upper())
    st.markdown(f'<div class="alert-box">⚠️ CAMPAÑA DETECTADA &nbsp;|&nbsp; {fl} &nbsp;|&nbsp; Inicio: {active_camp["inicio"]}</div>',
                unsafe_allow_html=True)
elif not kpis_df.empty:
    sync_max = float(kpis_df["sync_index"].max())
    st.markdown(f'<div class="ok-box">✓ SISTEMA NOMINAL · Sin campaña activa · Sync máximo: <strong>{sync_max:.4f}</strong> (umbral: 0.650)</div>',
                unsafe_allow_html=True)

# ── KPI tiles ──────────────────────────────────────────────────────────────────
if not kpis_df.empty:
    last_sync  = float(kpis_df.sort_values("fecha")["sync_index"].iloc[-1])
    last_pivot = float(kpis_df["pivot_score"].max()) if "pivot_score" in kpis_df.columns else 0
    n_medios   = kpis_df["medio"].nunique()
    n_camps    = len(camps_df) if not camps_df.empty else 0
    n_arts     = len(arts_df) if not arts_df.empty else 0

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.metric("📰 Artículos 72h",   f"{n_arts:,}",        help="Artículos ingestados en las últimas 72h")
    c2.metric("📡 Fuentes activas", f"{n_medios}/16",      help="Medios con artículos procesados en el último ciclo")
    c3.metric("🔄 Sync Index",      f"{last_sync:.4f}",    help="Similitud coseno entre medios. ≥0.65 = campaña coordinada")
    c4.metric("📊 Pivot max",       f"{last_pivot:.4f}",   help="Máximo cambio editorial en 24h. >0.5 = giro significativo")
    c5.metric("🚨 Campañas",        f"{n_camps}",          help="Campañas de influencia detectadas en histórico")
    c6.metric("🕐 Push",            pipeline_time,         help="Hora UTC del último git push al repositorio")

st.divider()

# ── TABS ───────────────────────────────────────────────────────────────────────
if kpis_df.empty:
    st.warning("⏳ Sin datos. Ejecuta primero el pipeline en el Odroid.")
    st.stop()

tab1,tab2,tab3,tab4,tab5,tab6,tab7,tab8 = st.tabs([
    "📡 Sync & Pivot","🧭 Sentiment","💉 Keywords",
    "📰 Artículos","🚨 Campañas","🔗 SIEG","📋 Sistema","📖 Guía",
])

# ═══ TAB 1: SYNC & PIVOT ══════════════════════════════════════════════════════
with tab1:
    st.caption("**Sync Index** ≥0.65 indica coordinación narrativa entre medios de distintas líneas editoriales. **Pivot Score** alto indica un giro brusco en la agenda editorial de un medio en 24h.")
    col_a, col_b = st.columns([1,2])
    with col_a:
        st.markdown("#### 🔄 Media Sync Index")
        sync_ts = kpis_df.groupby("fecha")["sync_index"].mean().reset_index()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=sync_ts["fecha"],y=sync_ts["sync_index"],
            mode="lines+markers",line=dict(color=ACCENT,width=2.5),
            fill="tozeroy",fillcolor="rgba(0,255,157,0.07)",name="Sync",
            hovertemplate="<b>%{x|%d/%m}</b><br>Sync: %{y:.4f}<extra></extra>"))
        fig.add_hline(y=0.65,line_dash="dash",line_color=RED,line_width=1.5,
                      annotation_text="umbral 0.65",annotation_font_color=RED,annotation_font_size=10)
        fig.add_hrect(y0=0.65,y1=1,fillcolor="rgba(255,78,106,0.05)",line_width=0)
        dark(fig,300,yaxis=dict(range=[0,1],gridcolor=GRID,tickformat=".3f"))
        st.plotly_chart(fig,width="stretch")
    with col_b:
        st.markdown("#### 📊 Pivot Score por Medio")
        fig2 = go.Figure()
        for m in sorted(kpis_df["medio"].unique()):
            sub = kpis_df[kpis_df["medio"]==m].sort_values("fecha")
            fig2.add_trace(go.Scatter(x=sub["fecha"],y=sub["pivot_score"],
                mode="lines+markers",name=m,
                line=dict(color=MEDIO_COLORS.get(m,"#aaa"),width=1.8),marker=dict(size=4),
                hovertemplate=f"<b>{m}</b><br>%{{x|%d/%m}}<br>Pivot: %{{y:.4f}}<extra></extra>"))
        dark(fig2,300,yaxis=dict(range=[0,1],gridcolor=GRID,tickformat=".3f"),
             legend=dict(orientation="h",y=-0.35,font=dict(size=9),bgcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig2,width="stretch")
    # Tabla
    last_kpis = kpis_df.sort_values("fecha").groupby("medio").last().reset_index()
    disp = last_kpis[["medio","fecha","pivot_score","sync_index","num_articulos","alerta_campana"]].copy()
    disp.columns = ["Medio","Fecha","Pivot","Sync","Arts","⚠"]
    disp["⚠"] = disp["⚠"].map({0:"✓ OK",1:"⚠ ALERTA"})
    st.dataframe(disp,width="stretch",hide_index=True)

# ═══ TAB 2: SENTIMENT ═════════════════════════════════════════════════════════
with tab2:
    st.caption("Score VADER: **+1** = cobertura favorable · **–1** = hostil. Revela la agenda real detrás del lenguaje diplomático.")
    sent_rows = []
    for _,row in kpis_df.iterrows():
        for actor,score in parse_json_col(row.get("sentiment_bias","{}")).items():
            sent_rows.append({"fecha":row["fecha"],"medio":row["medio"],"actor":actor,"score":float(score)})
    if sent_rows:
        sdf = pd.DataFrame(sent_rows); sdf["fecha"]=pd.to_datetime(sdf["fecha"])
        col1,col2 = st.columns(2)
        with col1:
            st.markdown("#### 🌍 Bias global por actor")
            aa = sdf.groupby("actor")["score"].mean().reset_index().sort_values("score")
            fig3 = go.Figure(go.Bar(x=aa["score"],y=aa["actor"],orientation="h",
                marker_color=[ACCENT if s>=0 else RED for s in aa["score"]],
                text=[f"{v:+.3f}" for v in aa["score"]],textposition="outside",
                textfont=dict(color="#d0dae8",size=11),
                hovertemplate="<b>%{y}</b>: %{x:+.4f}<extra></extra>"))
            dark(fig3,320,xaxis=dict(range=[-1,1],gridcolor=GRID,zeroline=True,
                 zerolinecolor="#334455",zerolinewidth=1.5))
            st.plotly_chart(fig3,width="stretch")
        with col2:
            st.markdown("#### 📈 Evolución temporal")
            sel = st.selectbox("Actor",sorted(sdf["actor"].unique()))
            sub2 = sdf[sdf["actor"]==sel].groupby("fecha")["score"].mean().reset_index()
            fig4 = go.Figure(go.Scatter(x=sub2["fecha"],y=sub2["score"],
                mode="lines+markers",line=dict(color=YELLOW,width=2.5),
                fill="tozeroy",fillcolor="rgba(255,209,102,0.07)",
                hovertemplate="%{x|%d/%m}: %{y:+.4f}<extra></extra>"))
            fig4.add_hline(y=0,line_dash="dot",line_color="#334455")
            dark(fig4,320,yaxis=dict(range=[-1,1],gridcolor=GRID))
            st.plotly_chart(fig4,width="stretch")
        st.markdown("#### 🗺 Mapa de calor Medio × Actor")
        ph = sdf.groupby(["medio","actor"])["score"].mean().unstack(fill_value=0)
        fig5 = px.imshow(ph,color_continuous_scale=[[0,RED],[0.5,"#0f1824"],[1,ACCENT]],
                         zmin=-1,zmax=1,aspect="auto",text_auto=".2f")
        fig5.update_traces(textfont=dict(size=10,color="white"))
        dark(fig5,400)
        st.plotly_chart(fig5,width="stretch")
    else:
        st.info("Sin datos de sentiment aún.")

# ═══ TAB 3: KEYWORDS ══════════════════════════════════════════════════════════
with tab3:
    st.caption("**Keyword Injection**: términos exógenos de agencias PR, think tanks o coordinación narrativa. Presencia simultánea en medios de líneas opuestas = campaña en curso.")
    kw_rows = []
    for _,row in kpis_df.iterrows():
        for kw,cnt in parse_json_col(row.get("keyword_inj","{}")).items():
            kw_rows.append({"fecha":row["fecha"],"medio":row["medio"],"keyword":kw,"freq":int(cnt)})
    if kw_rows:
        kdf = pd.DataFrame(kw_rows); kdf["fecha"]=pd.to_datetime(kdf["fecha"])
        col1,col2 = st.columns(2)
        with col1:
            top = kdf.groupby("keyword")["freq"].sum().reset_index().sort_values("freq").tail(15)
            fig6 = go.Figure(go.Bar(x=top["freq"],y=top["keyword"],orientation="h",
                marker=dict(color=top["freq"],colorscale=[[0,GRID],[1,YELLOW]]),
                hovertemplate="<b>%{y}</b>: %{x}<extra></extra>"))
            dark(fig6,420,title="Top keywords acumuladas")
            st.plotly_chart(fig6,width="stretch")
        with col2:
            km = kdf.groupby(["medio","keyword"])["freq"].sum().reset_index()
            fig7 = px.bar(km,x="medio",y="freq",color="keyword",barmode="stack",
                          color_discrete_sequence=px.colors.qualitative.Dark24)
            dark(fig7,420,title="Por medio",xaxis=dict(tickangle=-35))
            st.plotly_chart(fig7,width="stretch")
        sel_kw = st.selectbox("Evolución de keyword",sorted(kdf["keyword"].unique()))
        kts = kdf[kdf["keyword"]==sel_kw].groupby("fecha")["freq"].sum().reset_index()
        fig8 = go.Figure(go.Bar(x=kts["fecha"],y=kts["freq"],marker_color=YELLOW,
                                hovertemplate="%{x|%d/%m}: %{y}<extra></extra>"))
        dark(fig8,200,title=f'Frecuencia diaria · "{sel_kw}"')
        st.plotly_chart(fig8,width="stretch")
    else:
        st.info("Sin keywords detectadas.")

# ═══ TAB 4: ARTÍCULOS ═════════════════════════════════════════════════════════
with tab4:
    st.caption("Últimas 72h de las 16 fuentes monitoreadas. Filtra por medio o línea editorial.")
    if not arts_df.empty:
        col1,col2 = st.columns([1,3])
        with col1:
            ms = st.multiselect("Medio",sorted(arts_df["medio"].unique()),
                                default=sorted(arts_df["medio"].unique()))
            ls = st.multiselect("Línea",sorted(arts_df["linea"].unique()),
                                default=sorted(arts_df["linea"].unique()))
        with col2:
            filt = arts_df[arts_df["medio"].isin(ms)&arts_df["linea"].isin(ls)]\
                       .sort_values("publicado",ascending=False)
            cnt = filt["medio"].value_counts().reset_index(); cnt.columns=["medio","n"]
            fig9 = go.Figure(go.Pie(labels=cnt["medio"],values=cnt["n"],hole=0.55,
                marker=dict(colors=[MEDIO_COLORS.get(m,"#aaa") for m in cnt["medio"]],
                            line=dict(color="#080b12",width=2)),
                textinfo="label+percent",textfont=dict(size=9),
                hovertemplate="<b>%{label}</b>: %{value} (%{percent})<extra></extra>"))
            fig9.add_annotation(text=f"{len(filt)}",x=0.5,y=0.5,showarrow=False,
                font=dict(size=18,color="#fff",family="Orbitron"))
            dark(fig9,210,showlegend=True,legend=dict(orientation="h",y=-0.2,font=dict(size=9)))
            st.plotly_chart(fig9,width="stretch")
        show=[c for c in ["publicado","medio","linea","titulo","url"] if c in filt.columns]
        st.dataframe(filt[show].head(300),width="stretch",hide_index=True,
            column_config={
                "url":st.column_config.LinkColumn("🔗"),
                "publicado":st.column_config.DatetimeColumn("📅",format="DD/MM HH:mm"),
                "medio":st.column_config.TextColumn("📰 Medio"),
                "linea":st.column_config.TextColumn("🏷"),
                "titulo":st.column_config.TextColumn("📝 Titular",width="large"),
            })
    else:
        st.info("Sin artículos.")

# ═══ TAB 5: CAMPAÑAS ══════════════════════════════════════════════════════════
with tab5:
    st.caption("Campaña activa cuando Sync Index ≥ 0.65 durante días consecutivos.")
    col1,col2 = st.columns([1,1])
    with col1:
        st.markdown("""
<div class="guide-card">
<div class="guide-title">Modelo de detección 4 semanas</div>
<div class="kpi-def">🟡 <b>Sem 1 · Inoculación</b> — Día Cero. Nueva terminología emocional/técnica en titulares.</div>
<div class="kpi-def">🟠 <b>Sem 2 · Saturación</b> — Unanimidad en medios de líneas opuestas. Alerta activada.</div>
<div class="kpi-def">🔴 <b>Sem 3 · Pivot</b> — El medio modifica postura para justificar acción política.</div>
<div class="kpi-def">☠ <b>Sem 4 · Consolidación</b> — El tema pasa de noticia a dogma aceptado.</div>
</div>""", unsafe_allow_html=True)
    with col2:
        if "alerta_campana" in kpis_df.columns:
            at = kpis_df.groupby("fecha")["alerta_campana"].max().reset_index()
            fig10 = go.Figure(go.Bar(x=at["fecha"],y=at["alerta_campana"],
                marker_color=[RED if v else "rgba(0,255,157,0.12)" for v in at["alerta_campana"]],
                hovertemplate="%{x|%d/%m}: %{y}<extra></extra>"))
            dark(fig10,200,title="Días con Sync ≥ 0.65",
                 yaxis=dict(tickvals=[0,1],ticktext=["✓ OK","⚠ ALERTA"],gridcolor=GRID))
            st.plotly_chart(fig10,width="stretch")
    if not camps_df.empty:
        st.dataframe(camps_df,width="stretch",hide_index=True)
    else:
        st.success("✓ Sin campañas en el histórico.")

# ═══ TAB 6: SIEG ECOSYSTEM ════════════════════════════════════════════════════
with tab6:
    st.markdown("#### 🔗 Ecosistema SIEG · Sistema de Inteligencia y Evaluación Geopolítica")
    st.caption("MANI forma parte del ecosistema SIEG desplegado en Odroid C2/DietPi. Todos los módulos comparten la misma arquitectura: pipeline local → GitHub CSV → Streamlit Cloud.")

    col1,col2 = st.columns(2)
    with col1:
        st.markdown("""
<a class="sieg-card" href="https://mcasrom.github.io/sieg-osint/" target="_blank">
<div class="sieg-card-title">◈ SIEG Portal · Hub Principal</div>
<div class="sieg-card-desc">Portal de entrada al ecosistema SIEG con métricas globales y acceso a todos los módulos.</div>
</a>
<a class="sieg-card" href="https://fake-news-narrative.streamlit.app" target="_blank">
<div class="sieg-card-title">◈ Narrative Radar</div>
<div class="sieg-card-desc">Análisis de narrativas y desinformación. Detector de hate speech, bulos y sesgo ideológico. 34+ fuentes, 26 personas.</div>
</a>
<a class="sieg-card" href="https://sieg-monitor-boe.streamlit.app" target="_blank">
<div class="sieg-card-title">◈ Monitor BOE</div>
<div class="sieg-card-desc">Vigilancia automática del Boletín Oficial del Estado. Alertas sobre normativa relevante.</div>
</a>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
<a class="sieg-card" href="https://sieg-energia.streamlit.app" target="_blank">
<div class="sieg-card-title">◈ Monitor Energético</div>
<div class="sieg-card-desc">Seguimiento de precios PVPC, REE y análisis de tendencias energéticas con regresión lineal.</div>
</a>
<a class="sieg-card" href="https://sieg-ipc.streamlit.app" target="_blank">
<div class="sieg-card-title">◈ Monitor IPC / Inflación</div>
<div class="sieg-card-desc">Datos INE + cross-validación Eurostat HICP. Divergencias sistemáticas entre metodologías.</div>
</a>
<a class="sieg-card" href="https://sieg-mani.streamlit.app" target="_blank">
<div class="sieg-card-title">◈ MANI · Este módulo</div>
<div class="sieg-card-desc">Media Audit & Narrative Intelligence. 16 fuentes · Sync Index · Sentiment · Campañas.</div>
</a>
        """, unsafe_allow_html=True)

    st.divider()
    st.markdown("**Arquitectura común del ecosistema:**")
    st.code("""
Odroid C2 (DietPi · 192.168.1.147)
├── ~/SIEG-mani/          ← MANI (este módulo)
├── ~/narrative-radar/    ← Narrative Radar
├── ~/sieg-monitor-boe/   ← Monitor BOE
├── ~/sieg-energia/       ← Monitor Energético
└── ~/sieg-ipc/           ← Monitor IPC

Pipeline universal: cron → Python → SQLite → CSV → git push → GitHub → Streamlit Cloud
Sin APIs externas · Sin NAT · Sin servidor · Privacidad total
    """, language="bash")

# ═══ TAB 7: SISTEMA ═══════════════════════════════════════════════════════════
with tab7:
    st.markdown("#### 📋 Estado del sistema y pipeline")
    col1,col2 = st.columns(2)
    with col1:
        st.markdown("**📊 KPIs disponibles**")
        if not kpis_df.empty:
            for k,v in {
                "Primer dato":str(kpis_df["fecha"].min().date()),
                "Último dato":str(kpis_df["fecha"].max().date()),
                "Días con datos":kpis_df["fecha"].nunique(),
                "Medios activos":kpis_df["medio"].nunique(),
                "Registros KPI":len(kpis_df),
                "Sync máx":f"{kpis_df['sync_index'].max():.4f}",
                "Sync promedio":f"{kpis_df['sync_index'].mean():.4f}",
                "Alertas activadas":int(kpis_df["alerta_campana"].sum()),
            }.items():
                st.markdown(f"- **{k}**: `{v}`")
        st.markdown("**📰 Artículos**")
        if not arts_df.empty:
            for k,v in {
                "Total 72h":len(arts_df),
                "Medios":arts_df["medio"].nunique(),
                "Más reciente":str(arts_df["publicado"].max()),
            }.items():
                st.markdown(f"- **{k}**: `{v}`")
    with col2:
        st.markdown("**⏱ Último pipeline**")
        if ts:
            for k,v in ts.items():
                st.markdown(f"- **{k}**: `{v}`")
        st.markdown("**⚙️ Cron /etc/cron.d/mani**")
        st.code("""# Franja :10/:25/:40 — sin conflicto con 30 crons SIEG
10 */3 * * * dietpi ~/SIEG-mani/src/mani_run.sh scrape
25 */3 * * * dietpi ~/SIEG-mani/src/mani_run.sh process
35 */3 * * * dietpi ~/SIEG-mani/src/mani_run.sh alertas
40 */3 * * * dietpi ~/SIEG-mani/src/mani_run.sh push
00 8  * * * dietpi ~/SIEG-mani/src/mani_run.sh resumen
55 4  * * * dietpi ~/SIEG-mani/src/mani_run.sh logrotate""", language="cron")

        st.markdown("**📦 Stack técnico**")
        st.code("""Hardware:  Odroid C2 · ARM Cortex-A53 · DietPi
DB:        SQLite WAL (solo local, nunca sube a GitHub)
NLP:       VADER sentiment (sin GPU, sin modelos)
ML:        TF-IDF Python puro (sin NumPy, ARM-safe)
Alertas:   Telegram Bot API + Gmail SMTP
Fuentes:   16 RSS · ES/UK/US/RU/FR/QA
Transporte: GitHub CSV → Streamlit Cloud (free tier)""", language="text")

# ═══ TAB 8: GUÍA ══════════════════════════════════════════════════════════════
with tab8:
    st.markdown("## 📖 Guía de uso · MANI v1.3")
    col1,col2 = st.columns(2)
    with col1:
        st.markdown("""
<div class="guide-card">
<div class="guide-title">🎯 Tres fenómenos detectados</div>
<div class="kpi-def">📌 <b>Narrative Shifting</b> — Giro brusco en la línea editorial de un medio en 24h. → Pivot Score</div>
<div class="kpi-def">📌 <b>Sincronización Mediática</b> — Múltiples medios adoptando el mismo guion simultáneamente. → Media Sync Index</div>
<div class="kpi-def">📌 <b>Sesgo Geopolítico</b> — Postura real de cada medio frente a actores internacionales. → Sentiment Bias</div>
</div>

<div class="guide-card">
<div class="guide-title">📐 Definición técnica de KPIs</div>
<div class="kpi-def"><b>Pivot Score</b> [0–1] — Distancia euclidiana TF-IDF entre corpus de hoy y ayer. >0.5 = giro editorial significativo.</div>
<div class="kpi-def"><b>Media Sync Index</b> [0–1] — Coseno promedio entre todos los pares de medios. ≥0.65 = alerta de coordinación.</div>
<div class="kpi-def"><b>Sentiment Bias</b> [–1,+1] — VADER compound. <–0.3 hostil · –0.3/+0.3 neutro · >+0.3 favorable.</div>
<div class="kpi-def"><b>Keyword Injection</b> — Frecuencia de 30 términos exógenos de PR/agencias/OTAN monitoreados.</div>
</div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
<div class="guide-card">
<div class="guide-title">⚠️ Cómo interpretar una alerta</div>
<div class="kpi-def">1. Sync Index ≥ 0.65 → revisar Tab Campañas para ver la fase (sem 1-4)</div>
<div class="kpi-def">2. Identificar el actor geopolítico con mayor variación en Sentiment</div>
<div class="kpi-def">3. Buscar keywords inyectadas predominantes en ese periodo</div>
<div class="kpi-def">4. Cruzar con Tab Artículos filtrando por fechas de la campaña</div>
<div class="kpi-def">5. La alerta Telegram llega automáticamente si el bot está configurado</div>
</div>

<div class="guide-card">
<div class="guide-title">🔔 Sistema de alertas</div>
<div class="kpi-def">📱 <b>Telegram</b>: alerta inmediata cuando Sync ≥ 0.65, Pivot > 0.5 o spike de keywords</div>
<div class="kpi-def">📧 <b>Email</b>: mismo evento + resumen diario a las 08:00</div>
<div class="kpi-def">⚙️ Config: <code>~/SIEG-mani/config/alertas.json</code></div>
</div>

<div class="guide-card">
<div class="guide-title">🔄 Ciclo pipeline (cada 3h)</div>
<div class="kpi-def">:10 scraper — 16 fuentes RSS → SQLite → articulos.csv</div>
<div class="kpi-def">:25 processor — VADER + TF-IDF → kpis.csv</div>
<div class="kpi-def">:35 alertas — check Telegram/Email si hay evento</div>
<div class="kpi-def">:40 push — git commit + push → GitHub → Streamlit</div>
<div class="kpi-def">08:00 resumen — digest diario Telegram + Email</div>
</div>
        """, unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    f'<div style="font-family:\'Share Tech Mono\',monospace;font-size:0.65em;color:#2a4a5e;text-align:center;padding:4px">'
    f'MANI v1.3 · © 2026 M. Castillo · Privacy Tools · mybloggingnotes@gmail.com · '
    f'Odroid C2/DietPi → GitHub → Streamlit Cloud · VADER + TF-IDF puro · Sin APIs externas · '
    f'Último pipeline: {ts.get("scraper_date","—")} {ts.get("scraper_time","—")}'
    f'</div>',
    unsafe_allow_html=True)
