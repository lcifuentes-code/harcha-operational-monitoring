"""
app.py  —  Dashboard ejecutivo de monitoreo operacional
=========================================================
Streamlit · Harcha Maquinaria

Ejecutar:
    streamlit run app.py

Solo este archivo cambió respecto a la versión anterior.
Los scripts de procesamiento (scripts/) no se modificaron.
"""

import streamlit as st
import pandas as pd
import numpy as np
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from scripts.load_data  import cargar_datos
from scripts.clean_data import limpiar_datos
from scripts.transform  import calcular_metricas
from scripts.alerts     import generar_alertas
from config.settings    import ESTADOS_ACTIVOS

# ── Configuración de página ───────────────────────────────────────────────────
st.set_page_config(
    page_title="Harcha · Monitor Operacional",
    page_icon="🚜",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS global del dashboard ──────────────────────────────────────────────────
st.markdown("""
<style>
:root {
    --azul:        #3B82F6;
    --azul-oscuro: #1D4ED8;
    --azul-claro:  #EFF6FF;
    --rojo:        #EF4444;
    --rojo-claro:  #FEF2F2;
    --verde:       #10B981;
    --verde-claro: #ECFDF5;
    --ambar:       #F59E0B;
    --ambar-claro: #FFFBEB;
    --gris-bg:     #F8FAFC;
    --gris-borde:  #E2E8F0;
    --texto-1:     #0F172A;
    --texto-2:     #475569;
    --texto-3:     #94A3B8;
    --blanco:      #FFFFFF;
    --radio:       12px;
    --sombra:      0 1px 3px rgba(0,0,0,.08), 0 1px 2px rgba(0,0,0,.04);
    --sombra-md:   0 4px 12px rgba(0,0,0,.08);
}
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 2rem 2rem !important; max-width: 1400px !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px; background: var(--gris-bg); padding: 5px;
    border-radius: 10px; border: 1px solid var(--gris-borde);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important; padding: 8px 20px !important;
    font-size: 14px; font-weight: 500; color: var(--texto-2);
    background: transparent; border: none !important;
}
.stTabs [aria-selected="true"] {
    background: var(--blanco) !important; color: var(--azul) !important;
    box-shadow: var(--sombra) !important;
}
.stTabs [data-baseweb="tab-border"] { display: none; }
.stTabs [data-baseweb="tab-panel"] { padding-top: 1.25rem !important; }

/* Ocultar colapso del sidebar */
div[data-testid="stSidebarCollapsedControl"] button { display: none; }

/* KPI Grid */
.kpi-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 14px; margin-bottom: 20px; }
.kpi-card {
    background: var(--blanco); border: 1px solid var(--gris-borde);
    border-radius: var(--radio); padding: 18px 20px 16px;
    box-shadow: var(--sombra); position: relative; overflow: hidden;
    transition: box-shadow .15s, transform .15s;
}
.kpi-card:hover { box-shadow: var(--sombra-md); transform: translateY(-1px); }
.kpi-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0;
    height: 3px; background: var(--kpi-color, var(--azul));
    border-radius: var(--radio) var(--radio) 0 0;
}
.kpi-icon  { font-size: 20px; margin-bottom: 8px; display: block; }
.kpi-label { font-size: 11px; font-weight: 700; letter-spacing: .07em;
             text-transform: uppercase; color: var(--texto-3); margin-bottom: 5px; }
.kpi-value { font-size: 28px; font-weight: 800; color: var(--texto-1);
             line-height: 1; margin-bottom: 4px; }
.kpi-sub   { font-size: 11.5px; color: var(--texto-2); }
.kpi-alerta { --kpi-color: var(--rojo); }
.kpi-verde  { --kpi-color: var(--verde); }
.kpi-ambar  { --kpi-color: var(--ambar); }

/* Sección / card interna */
.seccion {
    background: var(--blanco); border: 1px solid var(--gris-borde);
    border-radius: var(--radio); padding: 18px 20px;
    box-shadow: var(--sombra); margin-bottom: 16px;
}
.seccion-titulo {
    font-size: 13.5px; font-weight: 700; color: var(--texto-1);
    margin: 0 0 14px; display: flex; align-items: center; gap: 6px;
}

/* Badge */
.badge {
    display: inline-block; padding: 2px 9px; border-radius: 20px;
    font-size: 10.5px; font-weight: 700; letter-spacing: .05em;
}
.badge-azul  { background: var(--azul-claro);  color: var(--azul-oscuro); }
.badge-rojo  { background: var(--rojo-claro);  color: #B91C1C; }
.badge-verde { background: var(--verde-claro); color: #065F46; }
.badge-ambar { background: var(--ambar-claro); color: #92400E; }

/* Alerta item */
.alerta-item {
    display: flex; align-items: flex-start; gap: 10px;
    padding: 11px 13px; border-radius: 8px; margin-bottom: 8px; border: 1px solid;
}
.alerta-rojo  { background: var(--rojo-claro);  border-color: #FECACA; }
.alerta-ambar { background: var(--ambar-claro); border-color: #FDE68A; }
.alerta-dot   { width: 7px; height: 7px; border-radius: 50%;
                flex-shrink: 0; margin-top: 5px; }
.alerta-dot-r { background: var(--rojo); }
.alerta-dot-a { background: var(--ambar); }
.alerta-maq   { font-size: 13px; font-weight: 600; color: var(--texto-1); margin-bottom: 2px; }
.alerta-desc  { font-size: 11.5px; color: var(--texto-2); }

/* Ranking */
.rank-row {
    display: flex; align-items: center; padding: 9px 0;
    border-bottom: 1px solid var(--gris-borde); gap: 10px;
}
.rank-row:last-child { border-bottom: none; }
.rank-pos    { font-size: 13px; font-weight: 700; color: var(--texto-3); width: 22px; text-align: center; }
.rank-nombre { font-size: 13px; font-weight: 600; color: var(--texto-1); flex: 1; }
.rank-valor  { font-size: 13px; font-weight: 700; color: var(--azul); }
.rank-sub    { font-size: 11px; color: var(--texto-3); }

/* Barra de progreso */
.prog-wrap   { margin-bottom: 11px; }
.prog-header { display: flex; justify-content: space-between;
               font-size: 12px; margin-bottom: 4px; }
.prog-label  { font-weight: 600; color: var(--texto-1); }
.prog-val    { color: var(--texto-2); }
.prog-bar-bg { height: 5px; background: var(--gris-borde);
               border-radius: 4px; overflow: hidden; }
.prog-bar-fill { height: 100%; border-radius: 4px; }

/* Upload zone */
.upload-zone {
    background: var(--azul-claro); border: 2px dashed #93C5FD;
    border-radius: var(--radio); padding: 32px; text-align: center; margin: 20px 0;
}
.upload-title { font-size: 18px; font-weight: 700; color: var(--azul-oscuro); margin-bottom: 6px; }
.upload-sub   { font-size: 13px; color: var(--texto-2); }

/* Tablas */
div[data-testid="stDataFrame"] > div {
    border-radius: 8px !important; border: 1px solid var(--gris-borde) !important;
}
</style>
""", unsafe_allow_html=True)


# ── Helpers de render ─────────────────────────────────────────────────────────
def kpi_card(icono, label, valor, sub="", color=""):
    clase = f"kpi-card {color}"
    return f"""
    <div class="{clase}">
        <span class="kpi-icon">{icono}</span>
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{valor}</div>
        <div class="kpi-sub">{sub}</div>
    </div>"""


def barra(label, valor, maximo, color="#3B82F6", sub=""):
    pct = min(100, round((valor / maximo * 100) if maximo > 0 else 0, 1))
    return f"""
    <div class="prog-wrap">
        <div class="prog-header">
            <span class="prog-label">{label}</span>
            <span class="prog-val">{sub}</span>
        </div>
        <div class="prog-bar-bg">
            <div class="prog-bar-fill" style="width:{pct}%; background:{color}"></div>
        </div>
    </div>"""


# ── Cache de procesamiento ────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def procesar(bytes_archivo: bytes, nombre: str) -> dict:
    buf = io.BytesIO(bytes_archivo)
    buf.name = nombre
    datos    = limpiar_datos(cargar_datos(archivo=buf))
    metricas = calcular_metricas(datos)
    alertas  = generar_alertas(datos)
    return {"datos": datos, "metricas": metricas, "alertas": alertas}


# ── Pantalla de carga ─────────────────────────────────────────────────────────
def pantalla_inicio():
    st.markdown("""
    <div style="text-align:center; padding:60px 0 20px">
        <div style="font-size:52px; margin-bottom:12px">🚜</div>
        <div style="font-size:28px; font-weight:800; color:#0F172A; margin-bottom:8px">
            Monitor Operacional
        </div>
        <div style="font-size:15px; color:#64748B; margin-bottom:32px">
            Harcha Maquinaria · Dashboard ejecutivo
        </div>
    </div>
    """, unsafe_allow_html=True)

    _, col_cen, _ = st.columns([1, 2, 1])
    with col_cen:
        st.markdown("""
        <div class="upload-zone">
            <div class="upload-title">📂 Sube el archivo Excel</div>
            <div class="upload-sub">Descarga el reporte desde Google Sheets y súbelo aquí</div>
        </div>
        """, unsafe_allow_html=True)
        archivo = st.file_uploader("", type=["xlsx"], label_visibility="collapsed")
        if archivo:
            return archivo

        st.markdown("""
        <div style="margin-top:20px; background:#F8FAFC; border:1px solid #E2E8F0;
                    border-radius:12px; padding:18px 22px">
            <div style="font-size:13px; font-weight:700; color:#0F172A; margin-bottom:8px">
                ¿Cómo obtener el archivo?
            </div>
            <div style="font-size:13px; color:#475569; line-height:1.9">
                1. Abre Google Sheets desde AppSheet<br>
                2. Archivo → Descargar → Microsoft Excel (.xlsx)<br>
                3. Sube el archivo descargado aquí
            </div>
        </div>

        <!-- Preparado para Google Sheets directo (fase futura) →
        Descomentar cuando se habilite la conexión directa:

        gsheet_url = st.text_input("URL Google Sheets", placeholder="https://docs.google.com/...")
        import gspread
        from google.oauth2 import service_account
        creds = service_account.Credentials.from_service_account_file("credentials.json")
        gc = gspread.authorize(creds)
        ...
        -->
        """, unsafe_allow_html=True)
    return None


# ── Estado de sesión ──────────────────────────────────────────────────────────
if "archivo_bytes" not in st.session_state:
    res = pantalla_inicio()
    if res is None:
        st.stop()
    st.session_state.archivo_bytes  = res.read()
    st.session_state.archivo_nombre = res.name
    st.rerun()

# ── Procesar datos ────────────────────────────────────────────────────────────
with st.spinner("Procesando datos..."):
    resultado = procesar(st.session_state.archivo_bytes, st.session_state.archivo_nombre)

datos         = resultado["datos"]
alertas_base  = resultado["alertas"]
df_rep_full   = datos["reportes"]

# ── BARRA SUPERIOR: logo · filtros · cambiar archivo ─────────────────────────
col_logo, col_f1, col_f2, col_btn = st.columns([2, 2, 2, 1.5])

with col_logo:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;padding:8px 0">
        <span style="font-size:28px">🚜</span>
        <div>
            <div style="font-size:15px;font-weight:800;color:#0F172A;line-height:1.1">
                Harcha Monitor
            </div>
            <div style="font-size:11px;color:#94A3B8">Dashboard Operacional</div>
        </div>
    </div>""", unsafe_allow_html=True)

fecha_min = df_rep_full["FECHAHORA_INICIO"].min().date()
fecha_max = df_rep_full["FECHAHORA_INICIO"].max().date()

with col_f1:
    fecha_ini = st.date_input("📅 Desde", value=fecha_min,
                               min_value=fecha_min, max_value=fecha_max)
with col_f2:
    fecha_fin = st.date_input("📅 Hasta", value=fecha_max,
                               min_value=fecha_min, max_value=fecha_max)
with col_btn:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    if st.button("🔄 Cambiar archivo", use_container_width=True):
        for k in ["archivo_bytes", "archivo_nombre"]:
            del st.session_state[k]
        st.rerun()

st.markdown("<div style='height:2px'></div>", unsafe_allow_html=True)

# ── Aplicar filtro de fechas ──────────────────────────────────────────────────
if fecha_ini > fecha_fin:
    st.error("⚠️ La fecha inicial no puede ser mayor a la final.")
    st.stop()

df_rep = df_rep_full[
    (df_rep_full["FECHAHORA_INICIO"].dt.date >= fecha_ini) &
    (df_rep_full["FECHAHORA_INICIO"].dt.date <= fecha_fin)
].copy()

datos_filtrados = {**datos, "reportes": df_rep}
metricas = calcular_metricas(datos_filtrados)
alertas  = generar_alertas(datos_filtrados)

maq_df  = metricas.get("por_maquina",     pd.DataFrame())
ops_df  = metricas.get("operadores",      pd.DataFrame())
comb_df = metricas.get("combustible",     pd.DataFrame())
act_df  = metricas.get("actividad_diaria",pd.DataFrame())

total_horas  = maq_df["total_horas"].sum()   if not maq_df.empty  else 0
total_litros = comb_df["total_litros"].sum()  if not comb_df.empty else 0
n_maquinas   = maq_df["ID_MAQUINA"].nunique() if not maq_df.empty  else 0
n_operadores = ops_df["USUARIO_TXT"].nunique()if not ops_df.empty  else 0
n_alertas    = len(alertas) if not alertas.empty else 0
n_dias       = (fecha_fin - fecha_ini).days + 1

# ── PESTAÑAS ─────────────────────────────────────────────────────────────────
tab_act, tab_maq, tab_ops, tab_comb, tab_alertas = st.tabs([
    "🎯  Vista Ejecutiva",
    "🚜  Máquinas",
    "👷  Operadores",
    "⛽  Combustible",
    f"🚨  Alertas  ({n_alertas})",
])



# ════════════════════════════════════════════════════════════
# TAB 1 — VISTA EJECUTIVA
# ════════════════════════════════════════════════════════════
with tab_act:

    # ── Cálculos centrales ────────────────────────────────────────────────────

    df_maq_cat       = datos.get("maquinas", pd.DataFrame())
    total_produccion = len(df_maq_cat[df_maq_cat["ESTADO"].isin(ESTADOS_ACTIVOS)]) \
                       if not df_maq_cat.empty else max(n_maquinas, 1)
    salud_pct        = min(round((n_maquinas / total_produccion * 100)
                                 if total_produccion > 0 else 0, 1), 100.0)

    # % cumplimiento de reporte (máquinas en producción que reportaron al menos 1 vez)
    maquinas_en_prod = set(
        df_maq_cat[df_maq_cat["ESTADO"].isin(ESTADOS_ACTIVOS)]["ID_MAQUINA"].dropna()
    ) if not df_maq_cat.empty else set()
    maquinas_reportaron = set(df_rep["ID_MAQUINA"].dropna()) if not df_rep.empty else set()
    cumplimiento_pct = min(round(
        len(maquinas_reportaron & maquinas_en_prod) / len(maquinas_en_prod) * 100
        if maquinas_en_prod else 0, 1), 100.0)

    # Semáforo
    if salud_pct >= 90:
        salud_color  = "#10B981"; salud_bg = "#ECFDF5"; salud_borde = "#6EE7B7"
        salud_emoji  = "🟢";     salud_label = "Operación saludable"
        estado_gral  = "VERDE";  estado_color = "#065F46"
        estado_fondo = "#ECFDF5"; estado_borde_css = "#6EE7B7"
        banner_critico = False
    elif salud_pct >= 70:
        salud_color  = "#F59E0B"; salud_bg = "#FFFBEB"; salud_borde = "#FCD34D"
        salud_emoji  = "🟡";     salud_label = "Atención requerida"
        estado_gral  = "AMARILLO"; estado_color = "#92400E"
        estado_fondo = "#FFFBEB"; estado_borde_css = "#FCD34D"
        banner_critico = False
    else:
        salud_color  = "#EF4444"; salud_bg = "#FEF2F2"; salud_borde = "#FCA5A5"
        salud_emoji  = "🔴";     salud_label = "Estado crítico"
        estado_gral  = "ROJO";   estado_color = "#B91C1C"
        estado_fondo = "#FEF2F2"; estado_borde_css = "#FCA5A5"
        banner_critico = True

    # Alertas por categoría — ordenadas por impacto (peor primero)
    sin_rep_df = pd.DataFrame()
    if not alertas.empty and "tipo_alerta" in alertas.columns:
        sin_rep_df = alertas[alertas["tipo_alerta"] == "SIN_REPORTE"].copy()
        if "horas_sin_reporte" in sin_rep_df.columns:
            sin_rep_df = sin_rep_df.sort_values(
                "horas_sin_reporte", ascending=False, na_position="first"
            )

    bajo_rend_df = pd.DataFrame()
    if not maq_df.empty:
        bajo_rend_df = maq_df[
            maq_df["promedio_horas_dia"].notna() & (maq_df["promedio_horas_dia"] < 4)
        ].sort_values("promedio_horas_dia", ascending=True).copy()   # peor rendimiento primero

    comb_inusuales = len(alertas[alertas["tipo_alerta"] == "COMBUSTIBLE_INUSUAL"]) \
                     if not alertas.empty and "tipo_alerta" in alertas.columns else 0

    # Problemas detectados (para mensaje automático)
    problemas = []
    if len(sin_rep_df) > 0:
        problemas.append(f"🔴 {len(sin_rep_df)} máquina(s) sin reporte activo")
    if len(bajo_rend_df) > 0:
        problemas.append(f"🟡 {len(bajo_rend_df)} máquina(s) con bajo rendimiento (<4 hrs/día)")
    if comb_inusuales > 0:
        problemas.append(f"🟡 {comb_inusuales} recarga(s) de combustible fuera de rango")

    # Recomendación automática según estado
    if not problemas:
        recomendacion = "✅ Sin acciones urgentes. Mantener monitoreo regular."
        rec_color = "#065F46"
    elif salud_pct >= 70:
        maq_sin = len(sin_rep_df)
        recomendacion = (
            f"⚡ Contactar a los jefes de obra para verificar el estado de "
            f"{maq_sin} máquina(s) sin reporte. Revisar conectividad de AppSheet."
            if maq_sin > 0 else
            "⚡ Revisar rendimiento de máquinas identificadas y evaluar reasignación de operadores."
        )
        rec_color = "#92400E"
    else:
        recomendacion = (
            f"🚨 ACCIÓN INMEDIATA: {len(sin_rep_df)} máquinas sin reporte. "
            "Activar protocolo de verificación de flota. Contactar supervisores en terreno."
        )
        rec_color = "#B91C1C"

    # Variación respecto al día anterior con flechas
    def delta_con_flecha(col: str) -> dict:
        if act_df.empty or col not in act_df.columns or len(act_df) < 2:
            return {"flecha": "", "texto": "—", "color": "#94A3B8"}
        ordenado = act_df.sort_values("FECHA", ascending=False)
        hoy  = float(ordenado.iloc[0][col])
        ayer = float(ordenado.iloc[1][col])
        dif  = hoy - ayer
        pct  = (dif / ayer * 100) if ayer != 0 else 0
        flecha = "↑" if dif > 0 else ("↓" if dif < 0 else "→")
        color  = "#10B981" if dif > 0 else ("#EF4444" if dif < 0 else "#94A3B8")
        return {
            "flecha": flecha,
            "texto": f"{flecha} {abs(dif):.0f} ({pct:+.1f}%)",
            "color": color,
        }

    delta_maq  = delta_con_flecha("maquinas_activas")
    delta_hrs  = delta_con_flecha("total_horas")

    # ── BANNER CRÍTICO ────────────────────────────────────────────────────────
    if banner_critico:
        st.markdown("""
        <div style="background:#7F1D1D; border-radius:10px; padding:12px 18px;
                    margin-bottom:12px; display:flex; align-items:center; gap:12px">
            <span style="font-size:22px">⛔</span>
            <div>
                <div style="font-size:13px; font-weight:800; color:#FEF2F2; letter-spacing:.04em">
                    RIESGO OPERACIONAL ALTO
                </div>
                <div style="font-size:12px; color:#FECACA; margin-top:2px">
                    La flota está por debajo del umbral mínimo de reporte.
                    Se recomienda revisión inmediata de la operación.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── MENSAJE DE ESTADO + RECOMENDACIÓN ────────────────────────────────────
    msg_body = "<br>".join(problemas) if problemas \
               else "✅ Sin problemas detectados. Flota operando con normalidad."

    st.markdown(f"""
    <div style="background:{estado_fondo}; border:1.5px solid {estado_borde_css};
                border-left:5px solid {salud_color}; border-radius:10px;
                padding:14px 18px; margin-bottom:14px">
        <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;
                    margin-bottom:6px">
            <span style="font-size:13px; font-weight:800; color:{estado_color};
                         letter-spacing:.05em">
                {salud_emoji} ESTADO OPERACIONAL: {estado_gral}
            </span>
            <span style="font-size:11.5px; color:{estado_color}; opacity:.75">
                · {fecha_ini.strftime('%d/%m/%Y')} → {fecha_fin.strftime('%d/%m/%Y')}
            </span>
        </div>
        <div style="font-size:12.5px; color:{estado_color}; opacity:.85;
                    line-height:1.8; margin-bottom:8px">
            {msg_body}
        </div>
        <div style="font-size:12px; color:{rec_color}; font-weight:600;
                    border-top:1px solid {estado_borde_css}; padding-top:8px">
            💡 Recomendación: {recomendacion}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── HEADER AZUL ──────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#1E40AF 0%,#2563EB 60%,#3B82F6 100%);
                border-radius:14px; padding:22px 28px 18px; margin-bottom:16px;
                position:relative; overflow:hidden">
        <div style="position:absolute;top:-30px;right:-20px;width:180px;height:180px;
                    border-radius:50%;background:rgba(255,255,255,.06)"></div>
        <div style="position:absolute;bottom:-40px;right:140px;width:120px;height:120px;
                    border-radius:50%;background:rgba(255,255,255,.04)"></div>
        <div style="display:flex;align-items:flex-start;justify-content:space-between;
                    flex-wrap:wrap;gap:12px;position:relative;z-index:1">
            <div>
                <div style="font-size:10px;font-weight:700;letter-spacing:.1em;
                            text-transform:uppercase;color:rgba(255,255,255,.55);margin-bottom:4px">
                    HARCHA MAQUINARIA · RESUMEN EJECUTIVO
                </div>
                <div style="font-size:22px;font-weight:800;color:#fff;line-height:1.1;margin-bottom:6px">
                    Vista Ejecutiva de Operaciones
                </div>
                <div style="font-size:12px;color:rgba(255,255,255,.7)">
                    📅 {fecha_ini.strftime('%d %b %Y')} → {fecha_fin.strftime('%d %b %Y')}
                    &nbsp;·&nbsp; {n_dias} días &nbsp;·&nbsp; {len(df_rep):,} reportes
                </div>
            </div>
            <div style="background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.22);
                        border-radius:12px;padding:14px 20px;text-align:center;min-width:148px">
                <div style="font-size:9px;font-weight:700;letter-spacing:.08em;
                            text-transform:uppercase;color:rgba(255,255,255,.5);margin-bottom:3px">
                    SALUD OPERACIONAL
                </div>
                <div style="font-size:32px;font-weight:800;color:#fff;line-height:1">
                    {salud_pct:.0f}%
                </div>
                <div style="font-size:11px;color:rgba(255,255,255,.8);margin-top:3px">
                    {salud_emoji} {salud_label}
                </div>
                <div style="font-size:10px;color:rgba(255,255,255,.5);margin-top:2px">
                    {n_maquinas} de {total_produccion} reportando
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPIs (5 + 1 nuevo: cumplimiento) ─────────────────────────────────────
    color_alerta = "kpi-alerta" if n_alertas > 0 else "kpi-verde"
    cumpl_color  = "kpi-verde" if cumplimiento_pct >= 90 \
                   else ("kpi-ambar" if cumplimiento_pct >= 70 else "kpi-alerta")
    kpis = "".join([
        kpi_card("⏱️", "Horas totales",    f"{total_horas:,.0f}",
                 f"prom. {total_horas/n_dias:,.0f} hrs/día" if n_dias else "—"),
        kpi_card("🚜", "Máquinas activas", str(n_maquinas),
                 f"de {total_produccion} en producción"),
        kpi_card("👷", "Operadores",       str(n_operadores),
                 "reportaron actividad", "kpi-verde"),
        kpi_card("⛽", "Litros totales",   f"{total_litros:,.0f}",
                 f"prom. {total_litros/n_dias:,.0f} L/día" if n_dias else "—", "kpi-ambar"),
        kpi_card("📋", "Cumplimiento",     f"{cumplimiento_pct:.0f}%",
                 f"{len(maquinas_reportaron & maquinas_en_prod)} de {len(maquinas_en_prod)} máquinas",
                 cumpl_color),
    ])
    st.markdown(f'<div class="kpi-grid">{kpis}</div>', unsafe_allow_html=True)

    # Deltas con flechas
    cd1, cd2, _, _, _ = st.columns(5)
    if delta_hrs["flecha"]:
        cd1.markdown(
            f"<div style='font-size:12px;color:{delta_hrs['color']};font-weight:600;"
            f"margin-top:-10px;padding-left:4px'>{delta_hrs['texto']} hrs vs ayer</div>",
            unsafe_allow_html=True,
        )
    if delta_maq["flecha"]:
        cd2.markdown(
            f"<div style='font-size:12px;color:{delta_maq['color']};font-weight:600;"
            f"margin-top:-10px;padding-left:4px'>{delta_maq['texto']} máquinas vs ayer</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── ALERTAS + GRÁFICO ────────────────────────────────────────────────────
    col_izq, col_der = st.columns([2, 3])

    with col_izq:

        # Bloque crítico
        n_crit = len(sin_rep_df)
        st.markdown(f"""
        <div class="seccion" style="border-left:3px solid #EF4444;margin-bottom:12px">
            <div class="seccion-titulo" style="color:#DC2626">
                🚨 Críticas — Sin reporte
                <span class="badge badge-rojo" style="margin-left:6px">{n_crit}</span>
            </div>
        """, unsafe_allow_html=True)

        if sin_rep_df.empty:
            st.markdown("""
            <div style="text-align:center;padding:18px 0">
                <div style="font-size:28px;margin-bottom:5px">✅</div>
                <div style="font-size:12.5px;font-weight:600;color:#065F46">
                    Todas reportando
                </div>
            </div>""", unsafe_allow_html=True)
        else:
            for _, a in sin_rep_df.head(8).iterrows():
                maq  = a.get("MAQUINA", a.get("ID_MAQUINA", "?"))
                tipo = a.get("TIPO_MAQUINA", "")
                hrs  = a.get("horas_sin_reporte", None)
                hrs_txt = f"{hrs:.0f} hs" if pd.notna(hrs) else "sin historial"
                st.markdown(f"""
                <div class="alerta-item alerta-rojo" style="padding:7px 11px">
                    <div class="alerta-dot alerta-dot-r"></div>
                    <div style="flex:1;min-width:0">
                        <div class="alerta-maq" style="overflow:hidden;text-overflow:ellipsis;
                             white-space:nowrap">{str(maq)[:32]}</div>
                        <div class="alerta-desc">{str(tipo)} · {hrs_txt} sin contacto</div>
                    </div>
                </div>""", unsafe_allow_html=True)
            if n_crit > 8:
                st.caption(f"… {n_crit - 8} más en la pestaña Alertas")

        st.markdown("</div>", unsafe_allow_html=True)

        # Bloque atención
        n_br = len(bajo_rend_df)
        st.markdown(f"""
        <div class="seccion" style="border-left:3px solid #F59E0B">
            <div class="seccion-titulo" style="color:#B45309">
                ⚠️ Atención — Bajo rendimiento
                <span class="badge badge-ambar" style="margin-left:6px">{n_br}</span>
            </div>
        """, unsafe_allow_html=True)

        if bajo_rend_df.empty:
            st.markdown("""
            <div style="text-align:center;padding:14px 0">
                <div style="font-size:12.5px;font-weight:600;color:#065F46">
                    ✅ Sin casos
                </div>
            </div>""", unsafe_allow_html=True)
        else:
            for _, row in bajo_rend_df.head(5).iterrows():
                nombre = str(row.get("MAQUINA_TXT", row.get("ID_MAQUINA", "?")))[:30]
                prom   = row["promedio_horas_dia"]
                total_h = row["total_horas"]
                st.markdown(f"""
                <div class="alerta-item alerta-ambar" style="padding:7px 11px">
                    <div class="alerta-dot alerta-dot-a"></div>
                    <div style="flex:1">
                        <div class="alerta-maq">{nombre}</div>
                        <div class="alerta-desc">
                            {prom:.1f} hrs/día · {total_h:.0f} hrs total
                        </div>
                    </div>
                </div>""", unsafe_allow_html=True)
            if n_br > 5:
                st.caption(f"… {n_br - 5} más en Máquinas")

        st.markdown("</div>", unsafe_allow_html=True)

    with col_der:
        st.markdown("""
        <div class="seccion">
            <div class="seccion-titulo">📈 Tendencia operacional</div>
        """, unsafe_allow_html=True)

        metrica_sel = st.radio(
            "",
            ["🚜 Máquinas activas", "⏱ Horas trabajadas", "⛽ Combustible diario"],
            horizontal=True,
            label_visibility="collapsed",
        )

        if not act_df.empty:
            act_plot = act_df.copy()
            act_plot["FECHA"] = pd.to_datetime(act_plot["FECHA"])
            act_plot = act_plot.sort_values("FECHA")

            if metrica_sel == "🚜 Máquinas activas":
                col_g, color_g = "maquinas_activas", "#3B82F6"
                label_g = "Máquinas"
            elif metrica_sel == "⏱ Horas trabajadas":
                col_g, color_g = "total_horas", "#10B981"
                label_g = "Horas"
            else:
                # Combustible diario real desde recargas
                rec = datos.get("recargas", pd.DataFrame())
                if not rec.empty:
                    rec = rec.copy()
                    rec["FECHA_DIA"] = pd.to_datetime(rec["FECHA"]).dt.date
                    comb_dia = (
                        rec.groupby("FECHA_DIA")["LITROS"].sum()
                        .reset_index()
                        .rename(columns={"FECHA_DIA": "FECHA", "LITROS": "litros_dia"})
                    )
                    comb_dia["FECHA"] = pd.to_datetime(comb_dia["FECHA"])
                    act_plot = comb_dia[
                        (comb_dia["FECHA"].dt.date >= fecha_ini) &
                        (comb_dia["FECHA"].dt.date <= fecha_fin)
                    ].sort_values("FECHA")
                    col_g, color_g = "litros_dia", "#F59E0B"
                    label_g = "Litros"
                else:
                    col_g, color_g, label_g = "total_horas", "#10B981", "Horas"

            if col_g in act_plot.columns and not act_plot.empty:
                import plotly.graph_objects as go

                vals = act_plot[col_g]
                avg  = vals.mean()

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=act_plot["FECHA"],
                    y=vals,
                    name=label_g,
                    marker_color=color_g,
                    marker_line_width=0,
                    opacity=0.85,
                ))
                fig.add_hline(
                    y=avg,
                    line_dash="dot",
                    line_color="#64748B",
                    line_width=1.5,
                    annotation_text=f" Prom: {avg:.1f}",
                    annotation_font_size=11,
                    annotation_font_color="#64748B",
                )
                fig.update_layout(
                    height=250,
                    margin=dict(l=0, r=8, t=8, b=0),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    showlegend=False,
                    xaxis=dict(showgrid=False, tickfont=dict(size=10)),
                    yaxis=dict(gridcolor="#F1F5F9", tickfont=dict(size=10)),
                )
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

                cs1, cs2, cs3 = st.columns(3)
                cs1.metric("Mínimo",  f"{vals.min():,.0f}")
                cs2.metric("Promedio",f"{avg:,.1f}")
                cs3.metric("Máximo",  f"{vals.max():,.0f}")

        st.markdown("</div>", unsafe_allow_html=True)

    # ── FILA INFERIOR ─────────────────────────────────────────────────────────
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    cb1, cb2 = st.columns(2)

    with cb1:
        st.markdown('<div class="seccion"><div class="seccion-titulo">🚜 Top 5 máquinas</div>', unsafe_allow_html=True)
        if not maq_df.empty:
            max_h = maq_df.head(5)["total_horas"].max()
            barras_html = "".join(
                barra(str(row.get("MAQUINA_TXT", row.get("ID_MAQUINA", "?")))[:28],
                      row["total_horas"], max_h, "#3B82F6",
                      f"{row['total_horas']:,.0f} hrs")
                for _, row in maq_df.head(5).iterrows()
            )
            st.markdown(barras_html, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with cb2:
        st.markdown('<div class="seccion"><div class="seccion-titulo">👷 Top 5 operadores</div>', unsafe_allow_html=True)
        if not ops_df.empty:
            max_o    = ops_df.head(5)["total_horas"].max()
            medallas = {1: "🥇", 2: "🥈", 3: "🥉"}
            barras_html = "".join(
                barra(f"{medallas.get(int(row['posicion']),'')} {str(row['USUARIO_TXT'])[:24]}",
                      row["total_horas"], max_o, "#10B981",
                      f"{row['total_horas']:,.0f} hrs")
                for _, row in ops_df.head(5).iterrows()
            )
            st.markdown(barras_html, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)





# ════════════════════════════════════════════════════════════
# TAB 2 — MÁQUINAS (orden por familia y código, todas visibles)
# ════════════════════════════════════════════════════════════
with tab_maq:

    # ─────────────────────────────────────────────────────────────────────────
    # CONSTANTES
    # ─────────────────────────────────────────────────────────────────────────

    IDS_DESCONTINUADOS = {
        "m000101","m000103","m000107","m000108","m000110","m000111",
        "m000132","m000133","m000139","m000142","68ae0f2a",
        "1c3365b8","704594fd","ad9b215c","cd9197b4",
        "m000023","m000024","m000029",
        "m000006","m000009","m000045","m000055","m000075","m000083",
    }

    FAMILIAS_SIN_ALARMA = {
        "CAMIONETA","SEMIREMOLQUE","REMOLQUE","CAMA BAJA","Batea",
        "ACCESORIOS","CUATRIMOTO","NO APLICA","ESTANQUE OBRA",
        "EQUIPO MOVIL","EXTERNO","EQUIPO INTEGRADO","TRILLADORA",
    }

    # Orden de aparición: primero camionetas, luego camiones por tipo,
    # luego maquinaria, generadores, semirremolques, otros.
    # Basado en el orden de hojas del archivo de mantenciones Harcha.
    ORDEN_PREFIJO = {
        # ── Camionetas ──────────────────────────────────────
        "C-":    (1,  "CAMIONETA"),
        "MB-":   (2,  "CAMIONETA"),       # Mini Bus
        "CUATRI":(3,  "CAMIONETA"),
        # ── Camiones ────────────────────────────────────────
        "CA-":   (10, "CAMIÓN ALJIBE"),
        "CG-":   (11, "CAMIÓN GANADERO"),
        "CK-":   (12, "CAMIÓN GANADERO"),
        "CM-":   (13, "CAMIÓN MIXER"),
        "CP-":   (14, "CAMIÓN PLANO / PLUMA"),
        "CT-":   (15, "CAMIÓN TOLVA"),
        "TC-":   (16, "TRACTO CAMIÓN"),
        "CI-":   (17, "CAMIÓN IMPRIMADOR"),
        "CS-":   (18, "CAMIÓN SLURRY"),
        # ── Maquinaria pesada ────────────────────────────────
        "CF-":   (20, "CARGADOR FRONTAL"),
        "MC-":   (21, "MINICARGADOR"),
        "EX-":   (22, "EXCAVADORA"),
        "MX-":   (23, "MINI EXCAVADORA"),
        "RX-":   (24, "RETROEXCAVADORA"),
        "RXM-":  (25, "RETROEXCAVADORA"),
        "BD-":   (26, "BULLDOZER"),
        "T-":    (27, "TRACTOR"),
        "MN-":   (28, "MOTONIVELADORA"),
        # ── Otros equipos ────────────────────────────────────
        "GM-":   (30, "GRÚA MÓVIL"),
        "P-":    (31, "PLANTA / OTROS"),
        "RC-":   (32, "RODILLO"),
        "RL-":   (33, "RODILLO"),
        "RN-":   (34, "RODILLO NEUMÁTICO"),
        "GV-":   (35, "GRAVILLADORA"),
        "BA-":   (36, "BARREDORA"),
        "VH-":   (37, "VIBROHINCADOR"),
        "EM-":   (38, "EQUIPO MENOR"),
        "PF-":   (39, "PERFORADORA"),
        "COM-":  (40, "COMPRESOR"),
        "EF-":   (41, "EQUIPO INTEGRADO"),
        # ── Generadores ──────────────────────────────────────
        "G-":    (50, "GENERADOR"),
        # ── Semirremolques / remolques ────────────────────────
        "B-":    (60, "BATEA"),
        "CB-":   (61, "CAMA BAJA"),
        "R-":    (62, "REMOLQUE"),
        # ── Externos y sin categoría ─────────────────────────
        "EXT-":  (80, "EXTERNO"),
        "TA-":   (81, "OTRO"),
        "TR-":   (82, "OTRO"),
        "ZZZ":   (99, "SIN CÓDIGO"),
    }

    import re as _re

    def parse_codigo(s):
        """Extrae (grupo_orden, etiqueta_grupo, número) del CODIGO_MAQUINA."""
        if pd.isna(s) or not str(s).strip():
            return 99, "SIN CÓDIGO", 9999
        s = str(s).strip()
        # Buscar prefijo más largo que coincida
        for prefix, (orden, etiqueta) in sorted(
            ORDEN_PREFIJO.items(), key=lambda x: -len(x[0])
        ):
            if s.upper().startswith(prefix.upper()):
                num_match = _re.search(r'(\d+)', s[len(prefix):])
                num = int(num_match.group(1)) if num_match else 9999
                return orden, etiqueta, num
        # Sin prefijo reconocido: buscar número genérico
        num_match = _re.search(r'(\d+)', s)
        num = int(num_match.group(1)) if num_match else 9999
        return 90, "OTRO", num

    # ─────────────────────────────────────────────────────────────────────────
    # DATOS
    # ─────────────────────────────────────────────────────────────────────────
    df_cat_full = datos.get("maquinas", pd.DataFrame()).copy()
    df_rep_all  = datos["reportes"].copy()
    df_rec_all  = datos.get("recargas", pd.DataFrame()).copy()
    df_rep_prd  = df_rep.copy()

    if df_cat_full.empty:
        st.info("Sin catálogo de máquinas disponible.")
    else:
        # Excluir descontinuadas
        df_cat = df_cat_full[
            ~df_cat_full["ID_MAQUINA"].isin(IDS_DESCONTINUADOS)
        ].copy().reset_index(drop=True)

        # ── Orden ─────────────────────────────────────────────────────────
        parsed = df_cat["CODIGO_MAQUINA"].apply(parse_codigo)
        df_cat["_ord"]    = parsed.apply(lambda x: x[0])
        df_cat["_grupo"]  = parsed.apply(lambda x: x[1])
        df_cat["_num"]    = parsed.apply(lambda x: x[2])
        df_cat = df_cat.sort_values(
            ["_ord", "_num"], ascending=[True, True]
        ).reset_index(drop=True)
        df_cat["#"] = range(1, len(df_cat) + 1)

        # ── A) Actividad últimos 10 días ───────────────────────────────────
        corte_10d = pd.Timestamp(fecha_fin) - pd.Timedelta(days=10)
        maq_10d = set()
        if not df_rep_all.empty:
            maq_10d |= set(
                df_rep_all[df_rep_all["FECHAHORA_INICIO"] >= corte_10d]
                ["ID_MAQUINA"].dropna()
            )
        if not df_rec_all.empty:
            fechas_rec = pd.to_datetime(df_rec_all["FECHA"], errors="coerce")
            maq_10d |= set(
                df_rec_all[fechas_rec >= corte_10d]["ID_MAQUINA"].dropna()
            )

        # ── B) Último operador y fecha ─────────────────────────────────────
        ult_info = {}
        if not df_rep_all.empty:
            ult_info = (
                df_rep_all.sort_values("FECHAHORA_INICIO")
                .groupby("ID_MAQUINA")
                .agg(ult_op=("USUARIO_TXT","last"),
                     ult_dt=("FECHAHORA_INICIO","max"))
                .to_dict("index")
            )

        # ── C) Cambio de obra ─────────────────────────────────────────────
        if not df_rep_all.empty:
            rep_s = df_rep_all.sort_values("FECHAHORA_INICIO")
            hist_rep = (
                rep_s.groupby("ID_MAQUINA")["OBRA_TXT"]
                .apply(lambda s: s.dropna().tolist()).to_dict()
            )
        else:
            hist_rep = {}

        if not df_rec_all.empty:
            rec_s = df_rec_all.copy()
            rec_s["_f"] = pd.to_datetime(rec_s["FECHA"], errors="coerce")
            rec_s = rec_s.sort_values("_f")
            hist_rec = (
                rec_s.groupby("ID_MAQUINA")["OBRA_ID"]
                .apply(lambda s: s.dropna().tolist()).to_dict()
            )
        else:
            hist_rec = {}

        def _n(s):
            return str(s).lower().strip() if pd.notna(s) and str(s).strip() else None

        def cambio_obra_info(mid, familia):
            if str(familia).strip() in FAMILIAS_SIN_ALARMA:
                return "", ""
            or_ = hist_rep.get(mid, [])
            oc_ = hist_rec.get(mid, [])
            if len(or_) >= 2 and or_[-1] != or_[-2]:
                return "🔔", f"Reportes: '{str(or_[-2])[:28]}' → '{str(or_[-1])[:28]}'"
            if len(oc_) >= 2 and oc_[-1] != oc_[-2]:
                return "🔔", f"Recargas: '{str(oc_[-2])[:28]}' → '{str(oc_[-1])[:28]}'"
            ult_r = _n(or_[-1]) if or_ else None
            ult_c = _n(oc_[-1]) if oc_ else None
            if ult_r and ult_c and ult_r not in ult_c and ult_c not in ult_r:
                return "🔔", (
                    f"Reporte ('{str(or_[-1])[:22]}') ≠ "
                    f"recarga ('{str(oc_[-1])[:22]}')"
                )
            return "", ""

        # ── D) Horas y litros del período ─────────────────────────────────
        agg_h = pd.DataFrame(columns=["ID_MAQUINA","horas_periodo","prom_hrs_dia"])
        if not df_rep_prd.empty:
            tmp = df_rep_prd.copy()
            tmp["_d"] = tmp["FECHAHORA_INICIO"].dt.date
            agg_h = (
                tmp.groupby("ID_MAQUINA")
                .agg(horas_periodo=("HORAS_TRABAJADAS","sum"),
                     _dias=("_d","nunique"))
                .reset_index()
            )
            for _c in ["horas_periodo","_dias"]:
                agg_h[_c] = pd.to_numeric(agg_h[_c], errors="coerce")
            agg_h["prom_hrs_dia"] = (
                agg_h["horas_periodo"]
                / agg_h["_dias"].where(agg_h["_dias"] > 0)
            ).round(1)
            agg_h = agg_h[["ID_MAQUINA","horas_periodo","prom_hrs_dia"]]

        agg_l = pd.DataFrame(columns=["ID_MAQUINA","litros_periodo"])
        if not df_rec_all.empty:
            rec_p = df_rec_all.copy()
            rec_p["_d"] = pd.to_datetime(rec_p["FECHA"], errors="coerce").dt.date
            mask_p = (rec_p["_d"] >= fecha_ini) & (rec_p["_d"] <= fecha_fin)
            agg_l = (
                rec_p[mask_p].groupby("ID_MAQUINA")["LITROS"]
                .sum().reset_index().rename(columns={"LITROS":"litros_periodo"})
            )
            agg_l["litros_periodo"] = pd.to_numeric(
                agg_l["litros_periodo"], errors="coerce"
            )

        # ── Ensamblar tabla ────────────────────────────────────────────────
        tabla = df_cat[[
            "#","ID_MAQUINA","CODIGO_MAQUINA","MAQUINA",
            "EQUIPO_FAMILIA","TIPO_MAQUINA","ESTADO","_grupo"
        ]].copy()
        tabla = tabla.merge(agg_h, on="ID_MAQUINA", how="left")
        tabla = tabla.merge(agg_l, on="ID_MAQUINA", how="left")
        for _c in ["horas_periodo","prom_hrs_dia","litros_periodo"]:
            tabla[_c] = pd.to_numeric(tabla[_c], errors="coerce")

        tabla["l_hr"] = (
            tabla["litros_periodo"]
            / tabla["horas_periodo"].where(tabla["horas_periodo"] > 0)
        ).round(2)

        ref_ts = pd.Timestamp(fecha_fin)

        tabla["en_prod"]    = tabla["ESTADO"].apply(
            lambda s: str(s).strip() in ESTADOS_ACTIVOS
        )
        tabla["activa_10d"] = tabla["ID_MAQUINA"].isin(maq_10d)

        def _estado_op(row):
            if not row["en_prod"]:    return "Fuera prod."
            if not row["activa_10d"]: return "Sin reporte"
            p = row["prom_hrs_dia"]
            if pd.notna(p) and p < 4: return "Bajo rend."
            return "Activa"

        tabla["estado_op"] = tabla.apply(_estado_op, axis=1)

        tabla["ult_op"] = tabla["ID_MAQUINA"].apply(
            lambda m: str(ult_info.get(m,{}).get("ult_op","—"))[:30]
        )
        tabla["dias_sr"] = tabla["ID_MAQUINA"].apply(
            lambda m: int((ref_ts - ult_info[m]["ult_dt"]).days)
                      if m in ult_info and pd.notna(ult_info[m]["ult_dt"])
                      else None
        )

        cambio_res = tabla.apply(
            lambda r: cambio_obra_info(r["ID_MAQUINA"], r["EQUIPO_FAMILIA"]),
            axis=1,
        )
        tabla["alarma"] = cambio_res.apply(lambda x: x[0])
        tabla["motivo"] = cambio_res.apply(lambda x: x[1])

        # ── KPIs ──────────────────────────────────────────────────────────
        n_tot   = len(tabla)
        n_act   = (tabla["estado_op"] == "Activa").sum()
        n_sr    = (tabla["estado_op"] == "Sin reporte").sum()
        n_br    = (tabla["estado_op"] == "Bajo rend.").sum()
        n_fp    = (tabla["estado_op"] == "Fuera prod.").sum()
        n_alarm = (tabla["alarma"] == "🔔").sum()

        # Badges KPI en estilo similar a la web de referencia
        st.markdown(f"""
        <div style="display:flex;gap:10px;margin-bottom:16px;flex-wrap:wrap">
            <div style="background:#065F46;color:#fff;border-radius:8px;
                        padding:10px 18px;text-align:center;min-width:90px">
                <div style="font-size:22px;font-weight:800">{n_act}</div>
                <div style="font-size:10px;opacity:.85;letter-spacing:.05em">ACTIVAS</div>
            </div>
            <div style="background:#B91C1C;color:#fff;border-radius:8px;
                        padding:10px 18px;text-align:center;min-width:90px">
                <div style="font-size:22px;font-weight:800">{n_sr}</div>
                <div style="font-size:10px;opacity:.85;letter-spacing:.05em">SIN REPORTE</div>
            </div>
            <div style="background:#92400E;color:#fff;border-radius:8px;
                        padding:10px 18px;text-align:center;min-width:90px">
                <div style="font-size:22px;font-weight:800">{n_br}</div>
                <div style="font-size:10px;opacity:.85;letter-spacing:.05em">BAJO REND.</div>
            </div>
            <div style="background:#475569;color:#fff;border-radius:8px;
                        padding:10px 18px;text-align:center;min-width:90px">
                <div style="font-size:22px;font-weight:800">{n_fp}</div>
                <div style="font-size:10px;opacity:.85;letter-spacing:.05em">FUERA PROD.</div>
            </div>
            <div style="background:#1E40AF;color:#fff;border-radius:8px;
                        padding:10px 18px;text-align:center;min-width:90px">
                <div style="font-size:22px;font-weight:800">{n_tot}</div>
                <div style="font-size:10px;opacity:.85;letter-spacing:.05em">TOTAL FLOTA</div>
            </div>
            <div style="background:#7C3AED;color:#fff;border-radius:8px;
                        padding:10px 18px;text-align:center;min-width:90px">
                <div style="font-size:22px;font-weight:800">{n_alarm}</div>
                <div style="font-size:10px;opacity:.85;letter-spacing:.05em">🔔 CAMBIO OBRA</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── FILTROS ────────────────────────────────────────────────────────
        st.markdown('<div class="seccion">', unsafe_allow_html=True)
        fc1, fc2, fc3, fc4 = st.columns([2, 2, 1, 3])

        with fc1:
            # Grupos en el orden correcto (no alfabético)
            grupos_ord = sorted(
                tabla[["_grupo","EQUIPO_FAMILIA"]].drop_duplicates()
                .set_index("EQUIPO_FAMILIA")["_grupo"].to_dict().items(),
                key=lambda x: x[1]
            )
            grupos_lista = ["Todas"] + [g[0] for g in grupos_ord
                                         if g[0] in tabla["_grupo"].values]
            # Dedup preservando order
            seen = set()
            grupos_uniq = ["Todas"]
            for g in [x[0] for x in grupos_ord]:
                if g not in seen and g in tabla["_grupo"].values:
                    grupos_uniq.append(g); seen.add(g)
            fam_sel = st.selectbox("Grupo / Familia", grupos_uniq)

        with fc2:
            est_lista = ["Todos"] + sorted(tabla["estado_op"].dropna().unique().tolist())
            est_sel = st.selectbox("Estado", est_lista)

        with fc3:
            solo_alarm = st.checkbox("🔔 Alarmas")

        with fc4:
            q = st.text_input("🔎 Buscar", placeholder="Código, marca, familia…")

        st.markdown("</div>", unsafe_allow_html=True)

        # ── Aplicar filtros ────────────────────────────────────────────────
        df_f = tabla.copy()
        if fam_sel  != "Todas": df_f = df_f[df_f["_grupo"]    == fam_sel]
        if est_sel  != "Todos": df_f = df_f[df_f["estado_op"] == est_sel]
        if solo_alarm:          df_f = df_f[df_f["alarma"]    == "🔔"]
        if q.strip():
            _q = q.strip().lower()
            mask = (
                df_f["CODIGO_MAQUINA"].astype(str).str.lower().str.contains(_q, na=False) |
                df_f["MAQUINA"].astype(str).str.lower().str.contains(_q, na=False) |
                df_f["EQUIPO_FAMILIA"].astype(str).str.lower().str.contains(_q, na=False) |
                df_f["TIPO_MAQUINA"].astype(str).str.lower().str.contains(_q, na=False)
            )
            df_f = df_f[mask]

        # ── Columna de estado con emoji ────────────────────────────────────
        def _estado_emoji(s):
            return {
                "Activa":       "🟢 Activa",
                "Sin reporte":  "🔴 Sin reporte",
                "Bajo rend.":   "🟡 Bajo rend.",
                "Fuera prod.":  "⚫ Fuera prod.",
            }.get(s, s)

        df_f = df_f.copy()
        df_f["_estado_fmt"] = df_f["estado_op"].apply(_estado_emoji)

        # ── Preparar vista ─────────────────────────────────────────────────
        # Extraer el código corto (ej: "C-52") desde CODIGO_MAQUINA
        def _codigo_corto(s):
            if pd.isna(s): return "—"
            m = _re.match(r'([A-Za-z\-]+\d+)', str(s).strip())
            return m.group(1) if m else str(s).split()[0]

        df_f["_cod"] = df_f["CODIGO_MAQUINA"].apply(_codigo_corto)

        df_v = df_f[[
            "#","_cod","TIPO_MAQUINA","_estado_fmt","ult_op",
            "horas_periodo","litros_periodo","l_hr",
            "alarma","motivo","dias_sr",
        ]].copy().rename(columns={
            "#":           "#",
            "_cod":        "Código",
            "TIPO_MAQUINA":"Tipo",
            "_estado_fmt": "Estado",
            "ult_op":      "Último operador",
            "horas_periodo":"Horas",
            "litros_periodo":"Litros",
            "l_hr":        "L/hr",
            "alarma":      "🔔",
            "motivo":      "Motivo alarma",
            "dias_sr":     "Días s/rep.",
        })

        df_v["Horas"]  = df_v["Horas"].apply(
            lambda x: f"{x:,.1f}" if pd.notna(x) and x > 0 else "—"
        )
        df_v["Litros"] = df_v["Litros"].apply(
            lambda x: f"{x:,.0f}" if pd.notna(x) and x > 0 else "—"
        )
        df_v["L/hr"]   = df_v["L/hr"].apply(
            lambda x: f"{x:.2f}" if pd.notna(x) else "—"
        )
        df_v["Días s/rep."] = df_v["Días s/rep."].apply(
            lambda x: f"{int(x)}d" if pd.notna(x) else "—"
        )

        # ── Tabla ──────────────────────────────────────────────────────────
        st.markdown(
            f'<div class="seccion">'
            f'<div class="seccion-titulo">'
            f'Mostrando {len(df_v)} de {n_tot} máquinas'
            f'<span style="font-size:11px;color:var(--texto-3);'
            f'font-weight:400;margin-left:10px">'
            f'Horas/Litros: {fecha_ini.strftime("%d/%m/%Y")} → '
            f'{fecha_fin.strftime("%d/%m/%Y")}'
            f' · Estado/Alarmas: historial completo'
            f'</span></div>',
            unsafe_allow_html=True,
        )

        st.dataframe(
            df_v,
            use_container_width=True,
            hide_index=True,
            height=min(40 * len(df_v) + 42, 620),
            column_config={
                "#": st.column_config.NumberColumn("#", width="small"),
                "Código": st.column_config.TextColumn(
                    "Código", width="small"
                ),
                "Tipo": st.column_config.TextColumn("Tipo / Familia"),
                "Estado": st.column_config.TextColumn(
                    "Estado",
                    help=(
                        "🟢 Activa = acción en últimos 10 días\n"
                        "🔴 Sin reporte = sin actividad 10 días\n"
                        "🟡 Bajo rend. = < 4 hrs/día promedio\n"
                        "⚫ Fuera prod. = estado en catálogo"
                    ),
                ),
                "Último operador": st.column_config.TextColumn("Último operador"),
                "Horas":  st.column_config.TextColumn("Horas", width="small"),
                "Litros": st.column_config.TextColumn("Litros", width="small"),
                "L/hr":   st.column_config.TextColumn("L/hr",   width="small"),
                "🔔": st.column_config.TextColumn(
                    "🔔", width="small",
                    help="🔔 cambio de obra detectado — ver columna 'Motivo alarma'"
                ),
                "Motivo alarma": st.column_config.TextColumn(
                    "Motivo alarma",
                    help=(
                        "Razón de la alarma:\n"
                        "• Últimas 2 obras de reportes distintas\n"
                        "• Últimas 2 obras de recargas distintas\n"
                        "• Obra último reporte ≠ obra última recarga\n"
                        "⚠ Camionetas y remolques están exentos."
                    ),
                ),
                "Días s/rep.": st.column_config.TextColumn(
                    "Días s/rep.",
                    width="small",
                    help="Días desde el último reporte (historial completo)"
                ),
            },
        )

        st.markdown("</div>", unsafe_allow_html=True)

        # Exportar
        st.download_button(
            "⬇ Exportar CSV",
            df_f[["#","_cod","EQUIPO_FAMILIA","TIPO_MAQUINA","ESTADO",
                  "estado_op","ult_op","horas_periodo","litros_periodo",
                  "l_hr","alarma","motivo","dias_sr"]]
            .rename(columns={"_cod":"Código","estado_op":"Estado Op",
                              "ult_op":"Último operador",
                              "horas_periodo":"Horas","litros_periodo":"Litros",
                              "l_hr":"L/hr","alarma":"🔔 Alarma",
                              "motivo":"Motivo","dias_sr":"Días s/rep."})
            .to_csv(index=False).encode("utf-8-sig"),
            "flota_ordenada.csv", "text/csv",
        )

# TAB 3 — OPERADORES
# ════════════════════════════════════════════════════════════
with tab_ops:
    if ops_df.empty:
        st.info("Sin datos de operadores para el período seleccionado.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Operadores activos",     n_operadores)
        c2.metric("Horas promedio",          f"{ops_df['total_horas'].mean():,.1f} hrs")
        c3.metric("Operador top",            str(ops_df.iloc[0]["USUARIO_TXT"])[:26])
        c4.metric("Máx horas un operador",   f"{ops_df['total_horas'].max():,.0f} hrs")

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        crank, ctabla = st.columns([2, 3])

        with crank:
            st.markdown('<div class="seccion"><div class="seccion-titulo">🏆 Ranking</div>', unsafe_allow_html=True)
            medallas = {1:"🥇", 2:"🥈", 3:"🥉"}
            rank_html = ""
            for _, row in ops_df.head(15).iterrows():
                pos  = int(row["posicion"])
                med  = medallas.get(pos, f"#{pos}")
                rank_html += f"""
                <div class="rank-row">
                    <span class="rank-pos">{med}</span>
                    <div style="flex:1">
                        <div class="rank-nombre">{str(row['USUARIO_TXT'])[:30]}</div>
                        <div class="rank-sub">{int(row['dias_trabajados'])} días · {int(row['maquinas_distintas'])} máq.</div>
                    </div>
                    <div class="rank-valor">{row['total_horas']:,.0f} hrs</div>
                </div>"""
            st.markdown(rank_html, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with ctabla:
            st.markdown('<div class="seccion"><div class="seccion-titulo">📊 Horas por operador (top 20)</div>', unsafe_allow_html=True)
            top20_ops = ops_df.head(20).copy()
            top20_ops["Nombre"] = top20_ops["USUARIO_TXT"].str[:26]
            st.bar_chart(top20_ops.set_index("Nombre")["total_horas"],
                         height=360, color="#10B981", horizontal=True, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="seccion"><div class="seccion-titulo">📋 Detalle completo</div>', unsafe_allow_html=True)
        st.dataframe(ops_df.rename(columns={
            "posicion":"#","USUARIO_TXT":"Operador","total_horas":"Horas",
            "dias_trabajados":"Días","total_reportes":"Reportes",
            "maquinas_distintas":"Máquinas","promedio_horas_dia":"Prom hrs/día",
        }), use_container_width=True, hide_index=True, height=280)
        st.download_button("⬇ Exportar CSV",
            ops_df.to_csv(index=False).encode("utf-8-sig"),
            "operadores.csv", "text/csv")
        st.markdown("</div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# TAB 4 — COMBUSTIBLE
# ════════════════════════════════════════════════════════════
with tab_comb:
    if comb_df.empty:
        st.info("Sin datos de combustible para el período seleccionado.")
    else:
        ncol = "MAQUINA" if "MAQUINA" in comb_df.columns else "ID_MAQUINA"
        top_c = str(comb_df.iloc[0].get("MAQUINA", comb_df.iloc[0]["ID_MAQUINA"]))

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total litros",           f"{total_litros:,.0f} L")
        c2.metric("Máquinas con recargas",  len(comb_df))
        c3.metric("Promedio por recarga",   f"{comb_df['promedio_litros_recarga'].mean():,.1f} L")
        c4.metric("Mayor consumidora",      top_c[:22] if pd.notna(top_c) else "—")

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        cg, cp = st.columns([3, 2])

        with cg:
            st.markdown('<div class="seccion"><div class="seccion-titulo">⛽ Consumo por máquina (top 20)</div>', unsafe_allow_html=True)
            top20_c = comb_df.head(20).copy()
            top20_c["Nombre"] = top20_c[ncol].fillna(top20_c["ID_MAQUINA"]).str[:28]
            st.bar_chart(top20_c.set_index("Nombre")["total_litros"],
                         height=360, color="#F59E0B", horizontal=True, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with cp:
            st.markdown('<div class="seccion"><div class="seccion-titulo">📊 Participación en consumo</div>', unsafe_allow_html=True)
            max_l = comb_df.head(10)["total_litros"].max()
            barras_html = ""
            for _, row in comb_df.head(10).iterrows():
                nombre = str(row.get("MAQUINA", row["ID_MAQUINA"]))[:22]
                lts    = row["total_litros"]
                pct    = (lts / total_litros * 100) if total_litros > 0 else 0
                barras_html += barra(nombre, lts, max_l, "#F59E0B",
                                     f"{lts:,.0f} L ({pct:.1f}%)")
            st.markdown(barras_html, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="seccion"><div class="seccion-titulo">📋 Detalle de recargas</div>', unsafe_allow_html=True)
        cols_c = [c for c in [ncol,"TIPO_MAQUINA","total_litros",
                               "num_recargas","promedio_litros_recarga","ultima_recarga"]
                  if c in comb_df.columns]
        st.dataframe(comb_df[cols_c].rename(columns={
            ncol:"Máquina","TIPO_MAQUINA":"Tipo",
            "total_litros":"Litros","num_recargas":"Recargas",
            "promedio_litros_recarga":"Prom. L/recarga","ultima_recarga":"Última recarga",
        }), use_container_width=True, hide_index=True, height=280)
        st.download_button("⬇ Exportar CSV",
            comb_df.to_csv(index=False).encode("utf-8-sig"),
            "combustible.csv", "text/csv")
        st.markdown("</div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# TAB 5 — ALERTAS
# ════════════════════════════════════════════════════════════
with tab_alertas:
    if alertas.empty:
        st.markdown("""
        <div style="text-align:center; padding:56px 0">
            <div style="font-size:44px; margin-bottom:10px">✅</div>
            <div style="font-size:20px; font-weight:700; color:#065F46">Sin alertas activas</div>
            <div style="font-size:13px; color:#64748B; margin-top:6px">
                Todas las máquinas están reportando correctamente
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        tipos_al = alertas["tipo_alerta"].unique() if "tipo_alerta" in alertas.columns else []
        cols_ka  = st.columns(len(tipos_al) + 1)
        cols_ka[0].metric("Total alertas", n_alertas)
        for i, tipo in enumerate(tipos_al):
            n = len(alertas[alertas["tipo_alerta"] == tipo])
            cols_ka[i+1].metric(tipo.replace("_"," ").title(), n)

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        tipo_sel = st.selectbox("Filtrar por tipo",
            ["Todas las alertas"] + list(tipos_al), label_visibility="collapsed")
        df_al = alertas if tipo_sel == "Todas las alertas" \
                else alertas[alertas["tipo_alerta"] == tipo_sel]

        # Cards de máquinas sin reporte
        sin_rep = df_al[df_al.get("tipo_alerta", pd.Series(dtype=str)) == "SIN_REPORTE"] \
                  if "tipo_alerta" in df_al.columns else pd.DataFrame()

        if not sin_rep.empty:
            st.markdown('<div class="seccion"><div class="seccion-titulo" style="color:#DC2626">🚨 Máquinas sin reporte</div>', unsafe_allow_html=True)
            cols_c = st.columns(3)
            for i, (_, a) in enumerate(sin_rep.head(12).iterrows()):
                maq  = a.get("MAQUINA", a.get("ID_MAQUINA", "?"))
                tipo = a.get("TIPO_MAQUINA", "")
                desc = a.get("descripcion", "")
                hrs  = a.get("horas_sin_reporte", None)
                hrs_html = (f'<div class="alerta-desc" style="font-weight:700;color:#DC2626">'
                            f'{hrs:.0f} horas de silencio</div>' if pd.notna(hrs) else "")
                with cols_c[i % 3]:
                    st.markdown(f"""
                    <div class="alerta-item alerta-rojo" style="flex-direction:column; gap:5px">
                        <div style="display:flex; align-items:center; gap:7px">
                            <div class="alerta-dot alerta-dot-r"></div>
                            <span class="badge badge-rojo">SIN REPORTE</span>
                        </div>
                        <div class="alerta-maq">{str(maq)[:30]}</div>
                        <div class="alerta-desc">{str(tipo)} · {desc}</div>
                        {hrs_html}
                    </div>""", unsafe_allow_html=True)
            if len(sin_rep) > 12:
                st.caption(f"Mostrando 12 de {len(sin_rep)} alertas")
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="seccion"><div class="seccion-titulo">📋 Todas las alertas</div>', unsafe_allow_html=True)
        cols_al = [c for c in ["tipo_alerta","ID_MAQUINA","MAQUINA","TIPO_MAQUINA",
                                "descripcion","ultimo_reporte","horas_sin_reporte",
                                "FECHA","LITROS"] if c in df_al.columns]
        st.dataframe(df_al[cols_al].rename(columns={
            "tipo_alerta":"Tipo","ID_MAQUINA":"ID Máquina","MAQUINA":"Máquina",
            "TIPO_MAQUINA":"Tipo equipo","descripcion":"Descripción",
            "ultimo_reporte":"Último reporte","horas_sin_reporte":"Horas sin reporte",
            "FECHA":"Fecha","LITROS":"Litros",
        }), use_container_width=True, hide_index=True, height=340)
        st.download_button("⬇ Exportar alertas CSV",
            df_al.to_csv(index=False).encode("utf-8-sig"),
            "alertas.csv", "text/csv")
        st.markdown("</div>", unsafe_allow_html=True)


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="margin-top:28px; padding-top:14px; border-top:1px solid #E2E8F0;
            display:flex; justify-content:space-between; align-items:center">
    <span style="font-size:11.5px; color:#94A3B8">
        🚜 Harcha Maquinaria · Monitor Operacional v1.1
    </span>
    <span style="font-size:11.5px; color:#94A3B8">
        {fecha_ini.strftime('%d/%m/%Y')} → {fecha_fin.strftime('%d/%m/%Y')}
        · {len(df_rep):,} reportes procesados
    </span>
</div>
""", unsafe_allow_html=True)
