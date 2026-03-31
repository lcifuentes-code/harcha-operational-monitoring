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






# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — MÁQUINAS
# ════════════════════════════════════════════════════════════════════════════
# Lógica:
#   BASE FIJA  → catálogo completo de datos["maquinas"] (nunca cambia por fechas)
#   DINÁMICO   → horas, litros, operador, ubicación cambian con el período
#   HISTORIAL  → estado, cambio-obra, días-sin-reporte usan TODO el historial
# ════════════════════════════════════════════════════════════════════════════
with tab_maq:

    import re as _re_maq

    # ────────────────────────────────────────────────────────────────────────
    # BLOQUE 1 — CONSTANTES
    # ────────────────────────────────────────────────────────────────────────

    # Máquinas marcadas como DESCONTINUADAS en el archivo de mantenciones.
    # Se excluyen de la tabla definitivamente.
    _IDS_DISC = {
        "m000101","m000103","m000107","m000108","m000110","m000111",
        "m000132","m000133","m000139","m000142","68ae0f2a",
        "1c3365b8","704594fd","ad9b215c","cd9197b4",
        "m000023","m000024","m000029",
        "m000006","m000009","m000045","m000055","m000075","m000083",
    }

    # Familias exentas de la alarma de cambio de obra.
    # Las camionetas no hacen reportes operacionales, no aplica la lógica.
    _FAMILIAS_SIN_ALARMA = {
        "CAMIONETA","SEMIREMOLQUE","REMOLQUE","CAMA BAJA","Batea",
        "ACCESORIOS","CUATRIMOTO","NO APLICA","ESTANQUE OBRA",
        "EQUIPO MOVIL","EXTERNO","EQUIPO INTEGRADO","TRILLADORA",
    }

    # Orden de familias en la tabla (de menor a mayor número → aparece antes).
    # Dentro de cada familia, las máquinas se ordenan por su número de código.
    _ORDEN_FAM = {
        # Grupo 1 — Camionetas
        "C-":    (1,  "Camioneta"),
        "MB-":   (2,  "Camioneta"),
        "CUATRI":(3,  "Camioneta"),
        # Grupo 2 — Camiones (por tipo)
        "CA-":   (10, "Camión Aljibe"),
        "CG-":   (11, "Camión Ganadero"),
        "CK-":   (12, "Camión Ganadero"),
        "CM-":   (13, "Camión Mixer"),
        "CP-":   (14, "Camión Plano/Pluma"),
        "CT-":   (15, "Camión Tolva"),
        "TC-":   (16, "Tracto Camión"),
        "CI-":   (17, "Camión Imprimador"),
        "CS-":   (18, "Camión Slurry"),
        # Grupo 3 — Maquinaria pesada
        "CF-":   (20, "Cargador Frontal"),
        "MC-":   (21, "Minicargador"),
        "EX-":   (22, "Excavadora"),
        "MX-":   (23, "Mini Excavadora"),
        "RX-":   (24, "Retroexcavadora"),
        "RXM-":  (25, "Retroexcavadora"),
        "BD-":   (26, "Bulldozer"),
        "T-":    (27, "Tractor"),
        "MN-":   (28, "Motoniveladora"),
        # Grupo 4 — Otros equipos
        "GM-":   (30, "Grúa Móvil"),
        "P-":    (31, "Planta/Otros"),
        "RC-":   (32, "Rodillo"),
        "RL-":   (33, "Rodillo"),
        "RN-":   (34, "Rodillo Neumático"),
        "GV-":   (35, "Gravilladora"),
        "BA-":   (36, "Barredora"),
        "VH-":   (37, "Vibrohincador"),
        "EM-":   (38, "Equipo Menor"),
        "PF-":   (39, "Perforadora"),
        "COM-":  (40, "Compresor"),
        "EF-":   (41, "Equipo Integrado"),
        # Grupo 5 — Generadores
        "G-":    (50, "Generador"),
        # Grupo 6 — Semirremolques
        "B-":    (60, "Batea"),
        "CB-":   (61, "Cama Baja"),
        "R-":    (62, "Remolque"),
        # Resto
        "EXT-":  (80, "Externo"),
        "TA-":   (81, "Otro"),
        "TR-":   (82, "Otro"),
        "ZZZ":   (99, "Sin código"),
    }

    # ────────────────────────────────────────────────────────────────────────
    # BLOQUE 2 — FUNCIONES AUXILIARES
    # ────────────────────────────────────────────────────────────────────────

    def _parse_codigo(codigo: str) -> tuple:
        """
        Extrae (orden_familia, etiqueta_grupo, numero) de un CODIGO_MAQUINA.
        Ejemplo: 'CT-14 RCKP70' → (15, 'Camión Tolva', 14)
        Usado para ordenar la tabla de forma estable.
        """
        if pd.isna(codigo) or not str(codigo).strip():
            return (99, "Sin código", 9999)
        s = str(codigo).strip()
        # Buscar el prefijo más largo que coincida (orden descendente de longitud)
        for prefix, (orden, etq) in sorted(
            _ORDEN_FAM.items(), key=lambda x: -len(x[0])
        ):
            if s.upper().startswith(prefix.upper()):
                rest = s[len(prefix):]
                m = _re_maq.search(r"(\d+)", rest)
                num = int(m.group(1)) if m else 9999
                return (orden, etq, num)
        # Sin prefijo reconocido
        m = _re_maq.search(r"(\d+)", s)
        return (90, "Otro", int(m.group(1)) if m else 9999)

    def _codigo_corto(codigo: str) -> str:
        """Extrae el código corto visible: 'CT-14 RCKP70' → 'CT-14'."""
        if pd.isna(codigo):
            return "—"
        m = _re_maq.match(r"([A-Za-z\-]+\d+)", str(codigo).strip())
        return m.group(1) if m else str(codigo).split()[0]

    def _normalizar_obra(s) -> str | None:
        """Normaliza texto de obra para comparación (minúsculas, sin espacios extra)."""
        if pd.isna(s) or not str(s).strip():
            return None
        return str(s).lower().strip()

    def _calcular_cambio_obra(mid: str, familia: str,
                               hist_rep: dict, hist_rec: dict) -> tuple:
        """
        Determina si una máquina tiene una alarma de cambio de obra.
        Retorna (icono, motivo_texto).

        Reglas:
          R1: Las últimas 2 obras de REPORTES son distintas.
          R2: Las últimas 2 obras de RECARGAS son distintas.
          R3: Última obra de reporte ≠ última obra de recarga.

        Familias en _FAMILIAS_SIN_ALARMA quedan exentas.
        """
        if str(familia).strip() in _FAMILIAS_SIN_ALARMA:
            return ("", "")

        obras_rep = hist_rep.get(mid, [])   # lista ordenada por fecha asc
        obras_rec = hist_rec.get(mid, [])

        # R1: cambio consecutivo en reportes
        if len(obras_rep) >= 2 and obras_rep[-1] != obras_rep[-2]:
            return ("🔔",
                    f"Reportes: '{str(obras_rep[-2])[:30]}'"
                    f" → '{str(obras_rep[-1])[:30]}'")

        # R2: cambio consecutivo en recargas
        if len(obras_rec) >= 2 and obras_rec[-1] != obras_rec[-2]:
            return ("🔔",
                    f"Recargas: '{str(obras_rec[-2])[:30]}'"
                    f" → '{str(obras_rec[-1])[:30]}'")

        # R3: reporte vs recarga apuntan a obras distintas
        ult_r = _normalizar_obra(obras_rep[-1]) if obras_rep else None
        ult_c = _normalizar_obra(obras_rec[-1]) if obras_rec else None
        if ult_r and ult_c and ult_r not in ult_c and ult_c not in ult_r:
            return ("🔔",
                    f"Reporte ('{str(obras_rep[-1])[:25]}')"
                    f" ≠ recarga ('{str(obras_rec[-1])[:25]}')")

        return ("", "")

    # ────────────────────────────────────────────────────────────────────────
    # BLOQUE 3 — CARGAR DATOS BASE (sin filtro de fechas)
    # ────────────────────────────────────────────────────────────────────────

    # Catálogo completo — base fija inamovible
    _df_cat_raw  = datos.get("maquinas",  pd.DataFrame()).copy()
    # Historial completo de reportes (para estado, operador, cambio obra)
    _df_rep_hist = datos["reportes"].copy()
    # Historial completo de recargas (para cambio obra y litros)
    _df_rec_hist = datos.get("recargas",  pd.DataFrame()).copy()
    # Reportes en el período seleccionado (para horas del período)
    _df_rep_prd  = df_rep.copy()

    if _df_cat_raw.empty:
        st.info("Sin catálogo de máquinas disponible.")
    else:

        # ──────────────────────────────────────────────────────────────────
        # BLOQUE 4 — CONSTRUIR BASE FIJA
        # Aplica exclusiones + orden permanente. NO depende de fechas.
        # ──────────────────────────────────────────────────────────────────

        # 4a. Excluir descontinuadas
        _base = _df_cat_raw[
            ~_df_cat_raw["ID_MAQUINA"].isin(_IDS_DISC)
        ][["ID_MAQUINA","CODIGO_MAQUINA","MAQUINA","EQUIPO_FAMILIA",
           "TIPO_MAQUINA","ESTADO"]].copy()

        # 4b. Calcular campos de orden (una vez, permanente)
        _parsed       = _base["CODIGO_MAQUINA"].apply(_parse_codigo)
        _base["_ord"] = _parsed.apply(lambda x: x[0])
        _base["_num"] = _parsed.apply(lambda x: x[2])
        _base["_grp"] = _parsed.apply(lambda x: x[1])
        _base["_cod"] = _base["CODIGO_MAQUINA"].apply(_codigo_corto)

        # 4c. Ordenar: por grupo → por número dentro del grupo
        _base = _base.sort_values(
            ["_ord", "_num"], ascending=True
        ).reset_index(drop=True)
        _base["#"] = range(1, len(_base) + 1)

        # ──────────────────────────────────────────────────────────────────
        # BLOQUE 5 — PRECALCULAR HISTORIAL COMPLETO
        # Todo lo que NO depende del período seleccionado.
        # ──────────────────────────────────────────────────────────────────

        # 5a. Actividad últimos 10 días desde fecha_fin
        _corte_10d = pd.Timestamp(fecha_fin) - pd.Timedelta(days=10)
        _maq_10d   = set()
        if not _df_rep_hist.empty:
            _maq_10d |= set(
                _df_rep_hist[_df_rep_hist["FECHAHORA_INICIO"] >= _corte_10d]
                ["ID_MAQUINA"].dropna()
            )
        if not _df_rec_hist.empty:
            _fechas_rec = pd.to_datetime(_df_rec_hist["FECHA"], errors="coerce")
            _maq_10d |= set(
                _df_rec_hist[_fechas_rec >= _corte_10d]["ID_MAQUINA"].dropna()
            )

        # 5b. Último operador y fecha de último reporte (historial completo)
        _ult_info: dict = {}
        if not _df_rep_hist.empty:
            _ult_info = (
                _df_rep_hist.sort_values("FECHAHORA_INICIO")
                .groupby("ID_MAQUINA")
                .agg(
                    _ult_op = ("USUARIO_TXT",    "last"),
                    _ult_dt = ("FECHAHORA_INICIO","max"),
                    _ult_ob = ("OBRA_TXT",        "last"),
                )
                .to_dict("index")
            )

        # 5c. Historial de obras para alarma de cambio de obra
        if not _df_rep_hist.empty:
            _hist_rep_obras = (
                _df_rep_hist.sort_values("FECHAHORA_INICIO")
                .groupby("ID_MAQUINA")["OBRA_TXT"]
                .apply(lambda s: s.dropna().tolist())
                .to_dict()
            )
        else:
            _hist_rep_obras = {}

        if not _df_rec_hist.empty:
            _rec_s = _df_rec_hist.copy()
            _rec_s["_f"] = pd.to_datetime(_rec_s["FECHA"], errors="coerce")
            _hist_rec_obras = (
                _rec_s.sort_values("_f")
                .groupby("ID_MAQUINA")["OBRA_ID"]
                .apply(lambda s: s.dropna().tolist())
                .to_dict()
            )
        else:
            _hist_rec_obras = {}

        # ──────────────────────────────────────────────────────────────────
        # BLOQUE 6 — CALCULAR DATOS DINÁMICOS (dependen del período)
        # ──────────────────────────────────────────────────────────────────

        # 6a. Horas trabajadas en el período
        _agg_h = pd.DataFrame(columns=["ID_MAQUINA","horas_periodo","prom_hrs_dia"])
        if not _df_rep_prd.empty:
            _tmp = _df_rep_prd.copy()
            _tmp["_dia"] = _tmp["FECHAHORA_INICIO"].dt.date
            _agg_h = (
                _tmp.groupby("ID_MAQUINA")
                .agg(horas_periodo=("HORAS_TRABAJADAS","sum"),
                     _dias=("_dia","nunique"))
                .reset_index()
            )
            _agg_h["horas_periodo"] = pd.to_numeric(
                _agg_h["horas_periodo"], errors="coerce"
            ).fillna(0)
            _agg_h["_dias"] = pd.to_numeric(
                _agg_h["_dias"], errors="coerce"
            ).fillna(0)
            _agg_h["prom_hrs_dia"] = (
                _agg_h["horas_periodo"]
                / _agg_h["_dias"].where(_agg_h["_dias"] > 0)
            ).round(1)
            _agg_h = _agg_h[["ID_MAQUINA","horas_periodo","prom_hrs_dia"]]

        # 6b. Litros consumidos en el período
        _agg_l = pd.DataFrame(columns=["ID_MAQUINA","litros_periodo"])
        if not _df_rec_hist.empty:
            _rec_p = _df_rec_hist.copy()
            _rec_p["_dia"] = pd.to_datetime(
                _rec_p["FECHA"], errors="coerce"
            ).dt.date
            _mask_p = (
                (_rec_p["_dia"] >= fecha_ini) &
                (_rec_p["_dia"] <= fecha_fin)
            )
            _agg_l = (
                _rec_p[_mask_p]
                .groupby("ID_MAQUINA")["LITROS"]
                .sum().reset_index()
                .rename(columns={"LITROS":"litros_periodo"})
            )
            _agg_l["litros_periodo"] = pd.to_numeric(
                _agg_l["litros_periodo"], errors="coerce"
            ).fillna(0)

        # ──────────────────────────────────────────────────────────────────
        # BLOQUE 7 — LEFT JOIN: base fija ← datos dinámicos
        # La base NUNCA pierde máquinas (left join garantizado).
        # ──────────────────────────────────────────────────────────────────
        _tabla = _base.copy()
        _tabla = _tabla.merge(_agg_h, on="ID_MAQUINA", how="left")
        _tabla = _tabla.merge(_agg_l, on="ID_MAQUINA", how="left")

        # Forzar dtypes numéricos después del left join (evita object dtype)
        for _col in ["horas_periodo","prom_hrs_dia","litros_periodo"]:
            _tabla[_col] = pd.to_numeric(
                _tabla[_col], errors="coerce"
            ).fillna(0)

        # 7a. L/hr — rendimiento
        _tabla["l_hr"] = (
            _tabla["litros_periodo"]
            / _tabla["horas_periodo"].where(_tabla["horas_periodo"] > 0)
        ).round(2).fillna(0)

        # ──────────────────────────────────────────────────────────────────
        # BLOQUE 8 — COLUMNAS DE HISTORIAL COMPLETO
        # Estas columnas no cambian con el período; usan todo el historial.
        # ──────────────────────────────────────────────────────────────────
        _ref_ts = pd.Timestamp(fecha_fin)

        # 8a. Estado operacional (últimos 10 días)
        _tabla["en_prod"] = _tabla["ESTADO"].apply(
            lambda s: str(s).strip() in ESTADOS_ACTIVOS
        )
        _tabla["activa_10d"] = _tabla["ID_MAQUINA"].isin(_maq_10d)

        def _calcular_estado(row) -> str:
            if not row["en_prod"]:    return "Fuera prod."
            if not row["activa_10d"]: return "Sin actividad"
            if row["prom_hrs_dia"] > 0 and row["prom_hrs_dia"] < 4:
                return "Bajo rend."
            return "Activa"

        _tabla["estado_op"] = _tabla.apply(_calcular_estado, axis=1)

        # 8b. Último operador (desde historial completo)
        _tabla["ult_op"] = _tabla["ID_MAQUINA"].apply(
            lambda m: str(_ult_info.get(m, {}).get("_ult_op", "—"))[:32]
            if _ult_info.get(m, {}).get("_ult_op") else "—"
        )

        # 8c. Ubicación: última obra del historial
        _tabla["ubicacion"] = _tabla["ID_MAQUINA"].apply(
            lambda m: str(_ult_info.get(m, {}).get("_ult_ob", "Sin datos"))[:35]
            if _ult_info.get(m, {}).get("_ult_ob") else "Sin datos"
        )

        # 8d. Cambio de obra (con motivo para tooltip)
        _cambio = _tabla.apply(
            lambda r: _calcular_cambio_obra(
                r["ID_MAQUINA"], r["EQUIPO_FAMILIA"],
                _hist_rep_obras, _hist_rec_obras
            ),
            axis=1,
        )
        _tabla["alarma"]       = _cambio.apply(lambda x: x[0])
        _tabla["motivo_alarm"] = _cambio.apply(lambda x: x[1])

        # 8e. Días sin reporte
        _tabla["dias_sr"] = _tabla["ID_MAQUINA"].apply(
            lambda m: int(
                (_ref_ts - _ult_info[m]["_ult_dt"]).days
            ) if m in _ult_info and pd.notna(_ult_info[m]["_ult_dt"])
            else None
        )

        # ──────────────────────────────────────────────────────────────────
        # BLOQUE 9 — MÉTRICAS RÁPIDAS (KPIs)
        # ──────────────────────────────────────────────────────────────────
        _n_tot   = len(_tabla)
        _n_act   = (_tabla["estado_op"] == "Activa").sum()
        _n_si    = (_tabla["estado_op"] == "Sin actividad").sum()
        _n_br    = (_tabla["estado_op"] == "Bajo rend.").sum()
        _n_fp    = (_tabla["estado_op"] == "Fuera prod.").sum()
        _n_alarm = (_tabla["alarma"]    == "🔔").sum()

        st.markdown(f"""
        <div style="display:flex;gap:10px;margin-bottom:16px;flex-wrap:wrap">
            <div style="background:#065F46;color:#fff;border-radius:8px;
                        padding:10px 20px;text-align:center;min-width:88px">
                <div style="font-size:22px;font-weight:800">{_n_act}</div>
                <div style="font-size:10px;opacity:.85;letter-spacing:.05em">ACTIVAS</div>
            </div>
            <div style="background:#B91C1C;color:#fff;border-radius:8px;
                        padding:10px 20px;text-align:center;min-width:88px">
                <div style="font-size:22px;font-weight:800">{_n_si}</div>
                <div style="font-size:10px;opacity:.85;letter-spacing:.05em">SIN ACTIVIDAD</div>
            </div>
            <div style="background:#92400E;color:#fff;border-radius:8px;
                        padding:10px 20px;text-align:center;min-width:88px">
                <div style="font-size:22px;font-weight:800">{_n_br}</div>
                <div style="font-size:10px;opacity:.85;letter-spacing:.05em">BAJO REND.</div>
            </div>
            <div style="background:#475569;color:#fff;border-radius:8px;
                        padding:10px 20px;text-align:center;min-width:88px">
                <div style="font-size:22px;font-weight:800">{_n_fp}</div>
                <div style="font-size:10px;opacity:.85;letter-spacing:.05em">FUERA PROD.</div>
            </div>
            <div style="background:#1E40AF;color:#fff;border-radius:8px;
                        padding:10px 20px;text-align:center;min-width:88px">
                <div style="font-size:22px;font-weight:800">{_n_tot}</div>
                <div style="font-size:10px;opacity:.85;letter-spacing:.05em">TOTAL FLOTA</div>
            </div>
            <div style="background:#6D28D9;color:#fff;border-radius:8px;
                        padding:10px 20px;text-align:center;min-width:88px">
                <div style="font-size:22px;font-weight:800">{_n_alarm}</div>
                <div style="font-size:10px;opacity:.85;letter-spacing:.05em">🔔 CAMBIO OBRA</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ──────────────────────────────────────────────────────────────────
        # BLOQUE 10 — FILTROS
        # Los filtros solo reducen lo que se ve, NUNCA cambian el orden base.
        # ──────────────────────────────────────────────────────────────────
        st.markdown('<div class="seccion">', unsafe_allow_html=True)
        _fc1, _fc2, _fc3, _fc4 = st.columns([2, 2, 1, 3])

        with _fc1:
            # Lista de grupos en el orden correcto (no alfabético)
            _grupos_ord = (
                _tabla[["_grp","_ord"]]
                .drop_duplicates()
                .sort_values("_ord")["_grp"]
                .tolist()
            )
            _grupos_uniq = ["Todos"] + list(dict.fromkeys(_grupos_ord))
            _fam_sel = st.selectbox("Grupo / Familia", _grupos_uniq,
                                     key="maq_fam_sel")

        with _fc2:
            _est_lista = ["Todos"] + sorted(
                _tabla["estado_op"].dropna().unique().tolist()
            )
            _est_sel = st.selectbox("Estado", _est_lista,
                                     key="maq_est_sel")

        with _fc3:
            _solo_alarm = st.checkbox("🔔 Solo alarmas", key="maq_alarm_cb")

        with _fc4:
            _q = st.text_input(
                "🔎 Buscar",
                placeholder="Código, marca, tipo, familia…",
                key="maq_buscar"
            )

        st.markdown("</div>", unsafe_allow_html=True)

        # ──────────────────────────────────────────────────────────────────
        # BLOQUE 11 — APLICAR FILTROS
        # Filtros sobre la copia, preservando orden original.
        # ──────────────────────────────────────────────────────────────────
        _df_f = _tabla.copy()

        if _fam_sel   != "Todos":  _df_f = _df_f[_df_f["_grp"]      == _fam_sel]
        if _est_sel   != "Todos":  _df_f = _df_f[_df_f["estado_op"] == _est_sel]
        if _solo_alarm:            _df_f = _df_f[_df_f["alarma"]    == "🔔"]
        if _q.strip():
            _qn = _q.strip().lower()
            _mask = (
                _df_f["_cod"].str.lower().str.contains(_qn, na=False) |
                _df_f["MAQUINA"].astype(str).str.lower().str.contains(_qn, na=False) |
                _df_f["EQUIPO_FAMILIA"].astype(str).str.lower().str.contains(_qn, na=False) |
                _df_f["TIPO_MAQUINA"].astype(str).str.lower().str.contains(_qn, na=False)
            )
            _df_f = _df_f[_mask]

        # ──────────────────────────────────────────────────────────────────
        # BLOQUE 12 — PREPARAR VISTA FINAL
        # ──────────────────────────────────────────────────────────────────

        # Estado con emoji de color para lectura rápida
        _estado_emoji = {
            "Activa":        "🟢 Activa",
            "Sin actividad": "🔴 Sin actividad",
            "Bajo rend.":    "🟡 Bajo rend.",
            "Fuera prod.":   "⚫ Fuera prod.",
        }
        _df_f = _df_f.copy()
        _df_f["_est_fmt"] = _df_f["estado_op"].map(_estado_emoji).fillna(_df_f["estado_op"])

        # Formateo de columnas numéricas (0 → "—")
        def _fmt_num(x, decimales=1, suffix=""):
            if pd.isna(x) or x == 0:
                return "—"
            fmt = f"{x:,.{decimales}f}"
            return fmt + suffix

        _df_v = _df_f[[
            "#","_cod","TIPO_MAQUINA","_est_fmt","ult_op",
            "horas_periodo","litros_periodo","l_hr",
            "ubicacion","alarma","motivo_alarm","dias_sr",
        ]].copy()

        _df_v["horas_periodo"]  = _df_v["horas_periodo"].apply(
            lambda x: _fmt_num(x, 1)
        )
        _df_v["litros_periodo"] = _df_v["litros_periodo"].apply(
            lambda x: _fmt_num(x, 0)
        )
        _df_v["l_hr"] = _df_v["l_hr"].apply(
            lambda x: _fmt_num(x, 2) if not pd.isna(x) and x > 0 else "—"
        )
        _df_v["dias_sr"] = _df_v["dias_sr"].apply(
            lambda x: f"{int(x)} d" if pd.notna(x) else "Sin hist."
        )

        _df_v = _df_v.rename(columns={
            "#":             "#",
            "_cod":          "Código",
            "TIPO_MAQUINA":  "Tipo",
            "_est_fmt":      "Estado",
            "ult_op":        "Último operador",
            "horas_periodo": "Horas",
            "litros_periodo":"Litros",
            "l_hr":          "L/hr",
            "ubicacion":     "Ubicación",
            "alarma":        "🔔",
            "motivo_alarm":  "Motivo alarma",
            "dias_sr":       "Días s/rep.",
        })

        # ──────────────────────────────────────────────────────────────────
        # BLOQUE 13 — TABLA
        # ──────────────────────────────────────────────────────────────────
        st.markdown(
            f'<div class="seccion">'
            f'<div class="seccion-titulo">'
            f'Mostrando <b>{len(_df_v)}</b> de {_n_tot} máquinas'
            f'<span style="font-size:11px;color:var(--texto-3);'
            f'font-weight:400;margin-left:10px">'
            f'Horas / Litros: {fecha_ini.strftime("%d/%m/%Y")}'
            f' → {fecha_fin.strftime("%d/%m/%Y")}'
            f' &nbsp;·&nbsp; Estado / Alarmas: historial completo'
            f'</span></div>',
            unsafe_allow_html=True,
        )

        st.dataframe(
            _df_v,
            use_container_width=True,
            hide_index=True,
            # Altura adaptativa: 40px/fila + header, máx 620px
            height=min(40 * len(_df_v) + 42, 620),
            column_config={
                "#": st.column_config.NumberColumn(
                    "#", width="small", format="%d"
                ),
                "Código": st.column_config.TextColumn(
                    "Código", width="small"
                ),
                "Tipo": st.column_config.TextColumn(
                    "Tipo"
                ),
                "Estado": st.column_config.TextColumn(
                    "Estado",
                    help=(
                        "🟢 Activa        — alguna acción en los últimos 10 días\n"
                        "🔴 Sin actividad — sin reportes ni recargas en 10 días\n"
                        "🟡 Bajo rend.    — < 4 hrs/día promedio en el período\n"
                        "⚫ Fuera prod.   — estado 'fuera de producción' en catálogo"
                    ),
                ),
                "Último operador": st.column_config.TextColumn(
                    "Último operador",
                    help="Operador del último reporte en todo el historial",
                ),
                "Horas": st.column_config.TextColumn(
                    "Horas",
                    width="small",
                    help="Horas trabajadas en el período seleccionado",
                ),
                "Litros": st.column_config.TextColumn(
                    "Litros",
                    width="small",
                    help="Litros de combustible en el período seleccionado",
                ),
                "L/hr": st.column_config.TextColumn(
                    "L/hr",
                    width="small",
                    help="Litros por hora trabajada en el período (rendimiento)",
                ),
                "Ubicación": st.column_config.TextColumn(
                    "Ubicación",
                    help="Última obra reportada en el historial completo",
                ),
                "🔔": st.column_config.TextColumn(
                    "🔔",
                    width="small",
                    help="🔔 = cambio de obra detectado — ver columna 'Motivo alarma'",
                ),
                "Motivo alarma": st.column_config.TextColumn(
                    "Motivo alarma",
                    help=(
                        "Razón del 🔔:\n"
                        "• Últimas 2 obras de reportes distintas\n"
                        "• Últimas 2 obras de recargas distintas\n"
                        "• Obra último reporte ≠ obra última recarga\n"
                        "⚠ Camionetas y remolques están exentos."
                    ),
                ),
                "Días s/rep.": st.column_config.TextColumn(
                    "Días s/rep.",
                    width="small",
                    help="Días desde el último reporte (historial completo)",
                ),
            },
        )

        st.markdown("</div>", unsafe_allow_html=True)

        # ──────────────────────────────────────────────────────────────────
        # BLOQUE 14 — EXPORTAR CSV
        # ──────────────────────────────────────────────────────────────────
        _csv_export = _df_f[[
            "#","_cod","EQUIPO_FAMILIA","TIPO_MAQUINA","ESTADO",
            "estado_op","ult_op","horas_periodo","litros_periodo",
            "l_hr","ubicacion","alarma","motivo_alarm","dias_sr",
        ]].rename(columns={
            "_cod":          "Código",
            "EQUIPO_FAMILIA":"Familia",
            "TIPO_MAQUINA":  "Tipo",
            "ESTADO":        "Estado catálogo",
            "estado_op":     "Estado operacional",
            "ult_op":        "Último operador",
            "horas_periodo": "Horas período",
            "litros_periodo":"Litros período",
            "l_hr":          "L/hr",
            "ubicacion":     "Ubicación",
            "alarma":        "Alarma obra",
            "motivo_alarm":  "Motivo alarma",
            "dias_sr":       "Días sin reporte",
        }).to_csv(index=False).encode("utf-8-sig")

        st.download_button(
            "⬇ Exportar tabla CSV",
            _csv_export,
            "flota_maquinas.csv",
            "text/csv",
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
