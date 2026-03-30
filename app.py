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

    # ── Cálculos previos ──────────────────────────────────────────────────────

    # Salud operacional (capped a 100%)
    df_maq_cat       = datos.get("maquinas", pd.DataFrame())
    total_produccion = len(df_maq_cat[df_maq_cat["ESTADO"].isin(ESTADOS_ACTIVOS)]) \
                       if not df_maq_cat.empty else max(n_maquinas, 1)
    salud_pct        = min(round((n_maquinas / total_produccion * 100)
                                 if total_produccion > 0 else 0, 1), 100.0)

    if salud_pct >= 90:
        salud_color = "#10B981"; salud_bg = "#ECFDF5"; salud_borde = "#6EE7B7"
        salud_emoji = "🟢";     salud_label = "Operación saludable"
        estado_gral = "VERDE";  estado_color = "#065F46"; estado_fondo = "#ECFDF5"
        estado_borde = "#6EE7B7"
    elif salud_pct >= 70:
        salud_color = "#F59E0B"; salud_bg = "#FFFBEB"; salud_borde = "#FCD34D"
        salud_emoji = "🟡";     salud_label = "Atención requerida"
        estado_gral = "AMARILLO"; estado_color = "#92400E"; estado_fondo = "#FFFBEB"
        estado_borde = "#FCD34D"
    else:
        salud_color = "#EF4444"; salud_bg = "#FEF2F2"; salud_borde = "#FCA5A5"
        salud_emoji = "🔴";     salud_label = "Estado crítico"
        estado_gral = "ROJO";   estado_color = "#B91C1C"; estado_fondo = "#FEF2F2"
        estado_borde = "#FCA5A5"

    # Alertas separadas por categoría
    sin_rep_df = alertas[alertas["tipo_alerta"] == "SIN_REPORTE"] \
                 if not alertas.empty and "tipo_alerta" in alertas.columns \
                 else pd.DataFrame()
    bajo_rend_df = maq_df[
        maq_df["promedio_horas_dia"].notna() & (maq_df["promedio_horas_dia"] < 4)
    ] if not maq_df.empty else pd.DataFrame()

    # Variación respecto al día anterior (desde act_df)
    def delta_dia(col: str) -> tuple:
        """Retorna (valor_hoy, variacion_abs, variacion_pct) comparando últimos 2 días."""
        if act_df.empty or col not in act_df.columns:
            return None, None, None
        ordenado = act_df.sort_values("FECHA", ascending=False)
        if len(ordenado) < 2:
            return ordenado.iloc[0][col], None, None
        hoy  = ordenado.iloc[0][col]
        ayer = ordenado.iloc[1][col]
        dif  = hoy - ayer
        pct  = (dif / ayer * 100) if ayer != 0 else 0
        return hoy, dif, pct

    _, d_maq, p_maq   = delta_dia("maquinas_activas")
    _, d_hrs, p_hrs   = delta_dia("total_horas")
    hoy_rep, d_rep, _ = delta_dia("total_reportes")

    def fmt_delta(dif, pct, unidad=""):
        """Formatea el delta para st.metric."""
        if dif is None:
            return None, None
        signo = "+" if dif >= 0 else ""
        return f"{signo}{dif:.0f}{unidad}", None   # None = color automático

    # Lista de problemas detectados para el mensaje ejecutivo
    problemas = []
    if len(sin_rep_df) > 0:
        problemas.append(f"🔴 {len(sin_rep_df)} máquina(s) sin reporte")
    if len(bajo_rend_df) > 0:
        problemas.append(f"🟡 {len(bajo_rend_df)} máquina(s) con bajo rendimiento (<4 hrs/día)")
    comb_inusuales = len(alertas[alertas["tipo_alerta"] == "COMBUSTIBLE_INUSUAL"]) \
                     if not alertas.empty and "tipo_alerta" in alertas.columns else 0
    if comb_inusuales > 0:
        problemas.append(f"🟡 {comb_inusuales} recarga(s) de combustible inusual")

    # ── 1. MENSAJE DE ESTADO AUTOMÁTICO ───────────────────────────────────────
    if not problemas:
        msg_body = "✅ Sin problemas detectados. Todas las máquinas operan con normalidad."
    else:
        msg_body = "<br>".join(problemas)

    st.markdown(f"""
    <div style="background:{estado_fondo}; border:1.5px solid {estado_borde};
                border-left:5px solid {salud_color}; border-radius:10px;
                padding:14px 18px; margin-bottom:14px">
        <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap">
            <span style="font-size:13px; font-weight:800; color:{estado_color};
                         letter-spacing:.05em">
                {salud_emoji} ESTADO OPERACIONAL: {estado_gral}
            </span>
            <span style="font-size:12px; color:{estado_color}; opacity:.8">
                · {fecha_ini.strftime('%d/%m/%Y')} → {fecha_fin.strftime('%d/%m/%Y')}
            </span>
        </div>
        <div style="font-size:12.5px; color:{estado_color}; margin-top:7px;
                    opacity:.85; line-height:1.8">
            {msg_body}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 2. HEADER AZUL ────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1E40AF 0%, #2563EB 65%, #3B82F6 100%);
                border-radius: 14px; padding: 24px 28px 20px; margin-bottom: 18px;
                position: relative; overflow: hidden;">
        <div style="position:absolute;top:-30px;right:-20px;width:180px;height:180px;
                    border-radius:50%;background:rgba(255,255,255,.06)"></div>
        <div style="position:absolute;bottom:-40px;right:140px;width:120px;height:120px;
                    border-radius:50%;background:rgba(255,255,255,.04)"></div>
        <div style="display:flex; align-items:flex-start; justify-content:space-between;
                    flex-wrap:wrap; gap:14px; position:relative; z-index:1">
            <div>
                <div style="font-size:10.5px; font-weight:700; letter-spacing:.1em;
                            text-transform:uppercase; color:rgba(255,255,255,.6); margin-bottom:5px">
                    HARCHA MAQUINARIA · RESUMEN EJECUTIVO
                </div>
                <div style="font-size:24px; font-weight:800; color:#fff; line-height:1.1; margin-bottom:7px">
                    Vista Ejecutiva de Operaciones
                </div>
                <div style="font-size:12.5px; color:rgba(255,255,255,.75)">
                    📅 {fecha_ini.strftime('%d %b %Y')} → {fecha_fin.strftime('%d %b %Y')}
                    &nbsp;·&nbsp; {n_dias} días &nbsp;·&nbsp; {len(df_rep):,} reportes
                </div>
            </div>
            <div style="background:rgba(255,255,255,.12); border:1px solid rgba(255,255,255,.22);
                        border-radius:12px; padding:14px 20px; text-align:center; min-width:150px">
                <div style="font-size:9.5px; font-weight:700; letter-spacing:.08em;
                            text-transform:uppercase; color:rgba(255,255,255,.55); margin-bottom:4px">
                    SALUD OPERACIONAL
                </div>
                <div style="font-size:34px; font-weight:800; color:#fff; line-height:1">
                    {salud_pct:.0f}%
                </div>
                <div style="font-size:11px; color:rgba(255,255,255,.8); margin-top:4px">
                    {salud_emoji} {salud_label}
                </div>
                <div style="font-size:10px; color:rgba(255,255,255,.5); margin-top:2px">
                    {n_maquinas} de {total_produccion} reportando
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 3. KPIs CON VARIACIÓN ─────────────────────────────────────────────────
    color_alerta = "kpi-alerta" if n_alertas > 0 else "kpi-verde"
    kpis = "".join([
        kpi_card("⏱️", "Horas totales",    f"{total_horas:,.0f}",
                 f"prom. {total_horas/n_dias:,.0f} hrs/día" if n_dias else "—"),
        kpi_card("🚜", "Máquinas activas", str(n_maquinas),
                 f"de {total_produccion} en producción"),
        kpi_card("👷", "Operadores",       str(n_operadores),
                 "reportaron actividad", "kpi-verde"),
        kpi_card("⛽", "Litros totales",   f"{total_litros:,.0f}",
                 f"prom. {total_litros/n_dias:,.0f} L/día" if n_dias else "—", "kpi-ambar"),
        kpi_card("🚨", "Alertas activas",  str(n_alertas),
                 f"{len(sin_rep_df)} críticas · {len(bajo_rend_df)} bajo rend.", color_alerta),
    ])
    st.markdown(f'<div class="kpi-grid">{kpis}</div>', unsafe_allow_html=True)

    # Fila de deltas (variación vs día anterior)
    cd1, cd2, cd3, cd4, cd5 = st.columns(5)
    if d_maq is not None:
        cd2.metric("vs. día anterior (máquinas)", "",
                   delta=f"{'+' if d_maq>=0 else ''}{d_maq:.0f} ({p_maq:+.1f}%)",
                   delta_color="normal")
    if d_hrs is not None:
        cd1.metric("vs. día anterior (horas)", "",
                   delta=f"{'+' if d_hrs>=0 else ''}{d_hrs:.0f} hrs ({p_hrs:+.1f}%)",
                   delta_color="normal")

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # ── 4. ALERTAS + GRÁFICO ─────────────────────────────────────────────────
    col_izq, col_der = st.columns([2, 3])

    # ── Columna izquierda: Alertas separadas ──────────────────────────────────
    with col_izq:

        # 4a. Alertas críticas — sin reporte
        n_crit = len(sin_rep_df)
        st.markdown(f"""
        <div class="seccion" style="border-left:3px solid #EF4444; margin-bottom:14px">
            <div class="seccion-titulo" style="color:#DC2626">
                🚨 Críticas — Sin reporte
                <span class="badge badge-rojo" style="margin-left:6px">{n_crit}</span>
            </div>
        """, unsafe_allow_html=True)

        if sin_rep_df.empty:
            st.markdown("""
            <div style="text-align:center;padding:20px 0">
                <div style="font-size:28px;margin-bottom:6px">✅</div>
                <div style="font-size:13px;font-weight:600;color:#065F46">
                    Todas reportando
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            for _, a in sin_rep_df.head(8).iterrows():
                maq  = a.get("MAQUINA", a.get("ID_MAQUINA", "?"))
                tipo = a.get("TIPO_MAQUINA", "")
                hrs  = a.get("horas_sin_reporte", None)
                hrs_txt = f"{hrs:.0f} hs" if pd.notna(hrs) else "sin historial"
                st.markdown(f"""
                <div class="alerta-item alerta-rojo" style="padding:8px 11px">
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

        # 4b. Atención — bajo rendimiento
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
            <div style="text-align:center;padding:16px 0">
                <div style="font-size:13px;font-weight:600;color:#065F46">✅ Sin casos detectados</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            for _, row in bajo_rend_df.head(5).iterrows():
                nombre = str(row.get("MAQUINA_TXT", row.get("ID_MAQUINA", "?")))[:30]
                prom   = row["promedio_horas_dia"]
                total  = row["total_horas"]
                st.markdown(f"""
                <div class="alerta-item alerta-ambar" style="padding:8px 11px">
                    <div class="alerta-dot alerta-dot-a"></div>
                    <div style="flex:1">
                        <div class="alerta-maq">{nombre}</div>
                        <div class="alerta-desc">
                            {prom:.1f} hrs/día prom. · {total:.0f} hrs totales
                        </div>
                    </div>
                </div>""", unsafe_allow_html=True)
            if n_br > 5:
                st.caption(f"… {n_br - 5} más en la pestaña Máquinas")

        st.markdown("</div>", unsafe_allow_html=True)

    # ── Columna derecha: único gráfico con selector ───────────────────────────
    with col_der:
        st.markdown("""
        <div class="seccion">
            <div class="seccion-titulo">📈 Tendencia operacional</div>
        """, unsafe_allow_html=True)

        metrica_sel = st.radio(
            "Ver:",
            ["🚜 Máquinas activas", "⏱ Horas trabajadas", "⛽ Combustible diario"],
            horizontal=True,
            label_visibility="collapsed",
        )

        if not act_df.empty:
            act_plot = act_df.copy()
            act_plot["FECHA"] = pd.to_datetime(act_plot["FECHA"])
            act_plot = act_plot.sort_values("FECHA")

            if metrica_sel == "🚜 Máquinas activas":
                col_g, color_g, label_g = "maquinas_activas", "#3B82F6", "Máquinas"
            elif metrica_sel == "⏱ Horas trabajadas":
                col_g, color_g, label_g = "total_horas", "#10B981", "Horas"
            else:
                # Combustible diario — agrupar recargas por fecha si está disponible
                if not datos.get("recargas", pd.DataFrame()).empty:
                    rec = datos["recargas"].copy()
                    rec["FECHA_DIA"] = pd.to_datetime(rec["FECHA"]).dt.date
                    comb_dia = (rec.groupby("FECHA_DIA")["LITROS"].sum()
                                   .reset_index()
                                   .rename(columns={"FECHA_DIA": "FECHA", "LITROS": "litros_dia"}))
                    comb_dia["FECHA"] = pd.to_datetime(comb_dia["FECHA"])
                    # Filtrar por período
                    comb_dia = comb_dia[
                        (comb_dia["FECHA"].dt.date >= fecha_ini) &
                        (comb_dia["FECHA"].dt.date <= fecha_fin)
                    ].sort_values("FECHA")
                    act_plot = comb_dia
                    col_g, color_g, label_g = "litros_dia", "#F59E0B", "Litros"
                else:
                    col_g, color_g, label_g = "total_horas", "#10B981", "Horas"

            if col_g in act_plot.columns:
                st.bar_chart(
                    act_plot.set_index("FECHA")[col_g],
                    height=280, color=color_g, use_container_width=True,
                )
                # Mini estadísticas
                vals = act_plot[col_g]
                cs1, cs2, cs3 = st.columns(3)
                cs1.metric("Mínimo", f"{vals.min():,.0f}")
                cs2.metric("Promedio", f"{vals.mean():,.1f}")
                cs3.metric("Máximo", f"{vals.max():,.0f}")

        st.markdown("</div>", unsafe_allow_html=True)

    # ── 5. FILA INFERIOR: Top 5 máquinas + Top 5 operadores ──────────────────
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
            max_o   = ops_df.head(5)["total_horas"].max()
            medallas = {1: "🥇", 2: "🥈", 3: "🥉"}
            barras_html = "".join(
                barra(f"{medallas.get(int(row['posicion']),'')} {str(row['USUARIO_TXT'])[:24]}",
                      row["total_horas"], max_o, "#10B981",
                      f"{row['total_horas']:,.0f} hrs")
                for _, row in ops_df.head(5).iterrows()
            )
            st.markdown(barras_html, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# TAB 2 — MÁQUINAS
# ════════════════════════════════════════════════════════════
with tab_maq:
    if maq_df.empty:
        st.info("Sin datos de máquinas para el período seleccionado.")
    else:
        prom_dia = (total_horas / n_dias) if n_dias > 0 else 0
        top_maq  = maq_df.iloc[0]["MAQUINA_TXT"] if not maq_df.empty else "—"
        max_hrs  = maq_df["total_horas"].max()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Máquinas activas",     n_maquinas)
        c2.metric("Horas promedio/día",   f"{prom_dia:,.1f} hrs")
        c3.metric("Máquina líder",        str(top_maq)[:24] if pd.notna(top_maq) else "—")
        c4.metric("Máx. horas (período)", f"{max_hrs:,.0f} hrs")

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        cg, cp = st.columns([3, 2])

        with cg:
            st.markdown('<div class="seccion"><div class="seccion-titulo">📊 Horas por máquina (top 20)</div>', unsafe_allow_html=True)
            top20 = maq_df.head(20).copy()
            top20["Nombre"] = top20["MAQUINA_TXT"].fillna(top20["ID_MAQUINA"]).str[:28]
            st.bar_chart(top20.set_index("Nombre")["total_horas"],
                         height=360, color="#3B82F6", horizontal=True, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with cp:
            st.markdown('<div class="seccion"><div class="seccion-titulo">🏭 Por tipo de equipo</div>', unsafe_allow_html=True)
            tipo_grp = maq_df.groupby("MAQUINA_TIPO")["total_horas"].sum().sort_values(ascending=False)
            max_t    = tipo_grp.max()
            colores  = ["#3B82F6","#10B981","#F59E0B","#EF4444",
                        "#8B5CF6","#06B6D4","#F97316","#84CC16"]
            barras_html = ""
            for i, (tipo, hrs) in enumerate(tipo_grp.items()):
                barras_html += barra(
                    str(tipo)[:22] if pd.notna(tipo) else "Sin tipo",
                    hrs, max_t, colores[i % len(colores)], f"{hrs:,.0f} hrs"
                )
            st.markdown(barras_html, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="seccion"><div class="seccion-titulo">📋 Detalle completo</div>', unsafe_allow_html=True)
        cols_v = [c for c in ["MAQUINA_TXT","MAQUINA_TIPO","total_horas",
                               "dias_activos","promedio_horas_dia",
                               "total_reportes","ultimo_reporte"] if c in maq_df.columns]
        st.dataframe(maq_df[cols_v].rename(columns={
            "MAQUINA_TXT":"Máquina","MAQUINA_TIPO":"Tipo",
            "total_horas":"Horas","dias_activos":"Días activos",
            "promedio_horas_dia":"Prom hrs/día",
            "total_reportes":"Reportes","ultimo_reporte":"Último reporte",
        }), use_container_width=True, hide_index=True, height=320)
        st.download_button("⬇ Exportar CSV",
            maq_df.to_csv(index=False).encode("utf-8-sig"),
            "maquinas.csv", "text/csv")
        st.markdown("</div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
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
