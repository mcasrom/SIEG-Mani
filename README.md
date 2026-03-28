# ◈ MANI · Media Audit & Narrative Intelligence

> Sistema autónomo de vigilancia editorial y OSINT para detección de campañas de influencia mediática, sincronización entre medios y sesgo geopolítico.

**🔗 Dashboard público:** https://sieg-mani.streamlit.app

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://sieg-mani.streamlit.app)

---

## Arquitectura

```
Odroid C2 (DietPi)          GitHub              Streamlit Cloud
─────────────────────        ──────────          ───────────────
scraper.py                   
  └─ RSS × 10 fuentes  ──→  data/               app.py
  └─ SQLite local             ├── articulos.csv  ├── Tab Sync & Pivot
                              ├── kpis.csv       ├── Tab Sentiment
processor.py                  └── campanas.csv   ├── Tab Keywords
  └─ VADER sentiment                             ├── Tab Artículos
  └─ TF-IDF puro (sin numpy)                     ├── Tab Campañas
  └─ KPI calculation                             ├── Tab Logs
                                                 └── Tab Guía
mani_run.sh push
  └─ git commit + push  ──────────────────────→ (auto-redeploy ~1min)
```

**Sin nginx. Sin NAT. Sin puertos abiertos. Sin APIs de terceros.**

---

## KPIs calculados

| KPI | Definición | Rango | Alerta |
|-----|-----------|-------|--------|
| **Pivot Score** | Distancia euclidiana TF-IDF entre corpus de hoy vs. ayer | [0, 1] | >0.5 |
| **Media Sync Index** | Similitud coseno promedio entre todos los pares de medios | [0, 1] | ≥0.65 |
| **Sentiment Bias** | Score VADER compound por actor geopolítico | [–1, +1] | <–0.3 o >+0.3 |
| **Keyword Injection** | Frecuencia de 30 términos exógenos de PR/agencias | entero | >5/día |

## Fuentes monitoreadas (10)

| Medio | País | Línea editorial |
|-------|------|-----------------|
| El País | 🇪🇸 ES | centroizquierda |
| El Mundo | 🇪🇸 ES | centroderecha |
| ABC | 🇪🇸 ES | derecha |
| Público | 🇪🇸 ES | izquierda |
| El Confidencial | 🇪🇸 ES | liberal |
| BBC World | 🇬🇧 UK | centrist |
| NYT World | 🇺🇸 US | centroliberal |
| Fox News | 🇺🇸 US | conservador |
| RT | 🇷🇺 RU | estatal-ru |
| France24 ES | 🇫🇷 FR | centrist |

## Fases de campaña

El sistema detecta días consecutivos con Sync Index ≥ 0.65:

| Días | Fase | Descripción |
|------|------|-------------|
| 1–7 | 🟡 Inoculación | Día Cero. Nuevos términos emocionales/técnicos |
| 8–14 | 🟠 Saturación | Unanimidad entre líneas editoriales opuestas |
| 15–21 | 🔴 Pivot | Cambio de postura para justificar acción política |
| 22+ | ☠ Consolidación | El tema pasa de noticia a dogma aceptado |

## Instalación en Odroid C2 / DietPi

```bash
# 1. Clonar o transferir ficheros
mkdir -p ~/SIEG-mani/src ~/SIEG-mani/db ~/SIEG-mani/logs ~/SIEG-mani/repo/data

# 2. SCP desde Lubuntu
scp scraper.py processor.py mani_run.sh  dietpi@192.168.1.147:~/SIEG-mani/src/
scp install.sh                            dietpi@192.168.1.147:~/SIEG-mani/
scp app.py requirements.txt README.md    dietpi@192.168.1.147:~/SIEG-mani/repo/

# 3. Instalar (sin sudo)
bash ~/SIEG-mani/install.sh

# 4. Test manual
bash ~/SIEG-mani/src/mani_run.sh all
```

## Cron (aislado en /etc/cron.d/mani)

```cron
# Franja :10/:25/:40 — sin conflicto con los 30 crons SIEG existentes
10 */3  * * *  dietpi  ~/SIEG-mani/src/mani_run.sh scrape
25 */3  * * *  dietpi  ~/SIEG-mani/src/mani_run.sh process
40 */3  * * *  dietpi  ~/SIEG-mani/src/mani_run.sh push
55 4    * * *  dietpi  ~/SIEG-mani/src/mani_run.sh logrotate
```

## Stack técnico

- **Hardware**: Odroid C2 (ARM Cortex-A53) / DietPi
- **Backend**: Python 3.x + feedparser + vaderSentiment + scikit-learn
- **DB**: SQLite (WAL mode, escritura local)
- **Transporte**: GitHub (solo CSVs, nunca la DB)
- **Frontend**: Streamlit Cloud (gratis, auto-deploy)
- **NLP**: VADER sentiment (sin GPU, sin modelos descargados)
- **ML**: TF-IDF implementado en Python puro (sin NumPy, optimizado para ARM)

## Privacidad

Este sistema opera en entorno de **caja negra local**. No utiliza:
- APIs de OpenAI, Anthropic, Google Cloud, Azure
- Servicios de NLP en la nube
- Telemetría o analítica externa

Todo el procesamiento ocurre en el Odroid C2. Los datos procesados (SQLite) nunca salen del dispositivo. Solo los CSVs de resultados se publican en GitHub.

---

© 2026 M. Castillo · Privacy Tools · mybloggingnotes@gmail.com
