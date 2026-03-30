"""
app.py
======
Dashboard interactivo de monitoreo operacional con Streamlit.

Ejecutar con:
    streamlit run app.py

El usuario sube el Excel directamente desde el navegador.
Los scripts de procesamiento (scripts/) se reutilizan sin cambios.
"""

import streamlit as st
import pandas as pd
import io
import sys
from pathlib import Path

# Asegura que Python encuentre los módulos del proyecto
sys.path.insert(0, str(Path(__file__).resolve().parent))

from scripts.load_data  import cargar_datos
from scripts.clean_data import limpiar_datos
from scripts.transform  import calcular_metricas
from scripts.alerts     import generar_alertas

# ─── Configuración de la página ───────────────────────────────────────────────
st.set_page_config(
    page_title="Harcha Maquinaria - Monitor",
    page_icon="🚜",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Estilos mínimos ──────────────────────────────────────────────────────────
st.markdown("""
<style>
    [data-testid="stMetricValue"] { font-size: 1.8rem; }
    .alerta-card { background: #fff3cd; border-left: 4px solid #ffc107;
                   padding: 10px 14px; margin: 6px 0; border-radius: 4px; }
    .alerta-card.roja { background: #f8d7da; border-left-color: #dc3545; }
</style>
""", unsafe_allow_html=True)


# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🚜 Harcha Monitor")
    st.caption("Sistema de monitoreo operacional")
    st.divider()

    archivo = st.file_uploader(
        "📂 Subir Excel de Google Sheets",
        type=["xlsx"],
        help="Descarga el archivo desde Google Sheets y súbelo aquí",
    )

    st.divider()
    st.subheader("⚙️ Configuración")
    horas_alerta = st.slider(
        "Horas sin reporte para alerta",
        min_value=6, max_value=72, value=24, step=6,
        help="Máquinas 'En producción' que no reporten en este tiempo generarán una alerta",
    )

    # Filtro de fecha (solo si hay datos)
    filtro_fechas = None
    if "datos" in st.session_state and not st.session_state.datos["reportes"].empty:
        df_rep = st.session_state.datos["reportes"]
        fecha_min = df_rep["FECHAHORA_INICIO"].min().date()
        fecha_max = df_rep["FECHAHORA_INICIO"].max().date()
        st.divider()
        st.subheader("📅 Filtro de período")
        filtro_fechas = st.date_input(
            "Rango de fechas",
            value=(fecha_min, fecha_max),
            min_value=fecha_min,
            max_value=fecha_max,
        )

    st.divider()
    st.caption("Prototipo v1.0 · Harcha Maquinaria")


# ─── PROCESAMIENTO DE DATOS ───────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def procesar_archivo(contenido_bytes: bytes, nombre: str, horas: int) -> dict:
    """
    Procesa el archivo Excel y retorna todos los resultados.
    El decorador @st.cache_data evita reprocesar si el archivo no cambió.
    """
    archivo_io = io.BytesIO(contenido_bytes)
    archivo_io.name = nombre
    datos    = limpiar_datos(cargar_datos(archivo=archivo_io))
    metricas = calcular_metricas(datos)
    alertas  = generar_alertas(datos)
    return {"datos": datos, "metricas": metricas, "alertas": alertas}


# ─── PANTALLA DE INICIO (sin archivo) ─────────────────────────────────────────
if archivo is None:
    st.title("🚜 Monitor Operacional — Harcha Maquinaria")
    st.info("👈 Sube el archivo Excel de Google Sheets en el panel izquierdo para comenzar.")

    col1, col2, col3 = st.columns(3)
    col1.metric("Reportes procesados", "—")
    col2.metric("Máquinas activas hoy", "—")
    col3.metric("Alertas detectadas", "—")

    with st.expander("ℹ️ ¿Cómo usar este dashboard?"):
        st.markdown("""
        1. **Descarga el Excel** desde Google Sheets (el mismo archivo que se genera desde AppSheet)
        2. **Súbelo** usando el botón en el panel izquierdo
        3. El sistema procesará los datos automáticamente y mostrará:
           - KPIs generales del período
           - Actividad por máquina y operador
           - Consumo de combustible
           - Alertas automáticas
        4. Puedes **descargar los resultados** en CSV desde cada pestaña
        """)
    st.stop()


# ─── PROCESAMIENTO ────────────────────────────────────────────────────────────
with st.spinner("⏳ Procesando datos..."):
    resultado = procesar_archivo(archivo.read(), archivo.name, horas_alerta)

datos    = resultado["datos"]
metricas = resultado["metricas"]
alertas  = resultado["alertas"]

# Guardar en session_state para que el sidebar pueda leer las fechas
st.session_state.datos = datos

# Aplicar filtro de fechas si está activo
df_reportes = datos["reportes"].copy()
if filtro_fechas and len(filtro_fechas) == 2:
    inicio, fin = filtro_fechas
    df_reportes = df_reportes[
        (df_reportes["FECHAHORA_INICIO"].dt.date >= inicio) &
        (df_reportes["FECHAHORA_INICIO"].dt.date <= fin)
    ]
    # Recalcular métricas con datos filtrados
    datos_filtrados = {**datos, "reportes": df_reportes}
    from scripts.transform import calcular_metricas as recalc
    metricas = recalc(datos_filtrados)


# ─── ENCABEZADO ───────────────────────────────────────────────────────────────
st.title("🚜 Monitor Operacional")
st.caption(f"Fuente: `{archivo.name}` · {len(df_reportes):,} reportes en período seleccionado")

# ─── KPIs PRINCIPALES ─────────────────────────────────────────────────────────
maq_df   = metricas.get("por_maquina", pd.DataFrame())
ops_df   = metricas.get("operadores", pd.DataFrame())
comb_df  = metricas.get("combustible", pd.DataFrame())
act_df   = metricas.get("actividad_diaria", pd.DataFrame())

col1, col2, col3, col4, col5 = st.columns(5)

total_horas   = maq_df["total_horas"].sum() if not maq_df.empty else 0
total_litros  = comb_df["total_litros"].sum() if not comb_df.empty else 0
n_alertas     = len(alertas) if not alertas.empty else 0
n_maquinas    = maq_df["ID_MAQUINA"].nunique() if not maq_df.empty else 0
n_operadores  = ops_df["USUARIO_TXT"].nunique() if not ops_df.empty else 0

col1.metric("⏱ Horas totales", f"{total_horas:,.0f} hrs")
col2.metric("🚜 Máquinas activas", n_maquinas)
col3.metric("👷 Operadores", n_operadores)
col4.metric("⛽ Litros totales", f"{total_litros:,.0f} L")
col5.metric("🚨 Alertas", n_alertas, delta=f"{n_alertas} activas" if n_alertas else None,
            delta_color="inverse")

st.divider()

# ─── PESTAÑAS ─────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📅 Actividad diaria",
    "🚜 Máquinas",
    "👷 Operadores",
    "⛽ Combustible",
    "🚨 Alertas",
])


# ── TAB 1: Actividad diaria ──────────────────────────────────────────────────
with tab1:
    if act_df.empty:
        st.warning("Sin datos de actividad en el período seleccionado.")
    else:
        act_df["FECHA"] = pd.to_datetime(act_df["FECHA"])

        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.subheader("Máquinas activas por día")
            st.bar_chart(
                act_df.set_index("FECHA")["maquinas_activas"],
                use_container_width=True,
                color="#1f77b4",
            )

        with col_g2:
            st.subheader("Horas trabajadas por día")
            st.bar_chart(
                act_df.set_index("FECHA")["total_horas"],
                use_container_width=True,
                color="#2ca02c",
            )

        st.subheader("Detalle por día")
        st.dataframe(
            act_df.rename(columns={
                "FECHA": "Fecha",
                "maquinas_activas": "Máquinas activas",
                "operadores_activos": "Operadores activos",
                "total_horas": "Horas totales",
                "total_reportes": "Reportes",
            }).sort_values("Fecha", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

        csv_act = act_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇ Descargar CSV", csv_act, "actividad_diaria.csv", "text/csv")


# ── TAB 2: Máquinas ──────────────────────────────────────────────────────────
with tab2:
    if maq_df.empty:
        st.warning("Sin datos de máquinas en el período seleccionado.")
    else:
        col_a, col_b = st.columns([2, 1])

        with col_a:
            st.subheader("Top 20 máquinas — horas trabajadas")
            top20 = maq_df.head(20).copy()
            top20["Máquina"] = top20["MAQUINA_TXT"].fillna(top20["ID_MAQUINA"])
            st.bar_chart(
                top20.set_index("Máquina")["total_horas"],
                use_container_width=True,
                horizontal=True,
            )

        with col_b:
            st.subheader("Por tipo de máquina")
            tipo_resumen = (
                maq_df.groupby("MAQUINA_TIPO")["total_horas"]
                .sum()
                .sort_values(ascending=False)
                .reset_index()
                .rename(columns={"MAQUINA_TIPO": "Tipo", "total_horas": "Horas"})
            )
            st.dataframe(tipo_resumen, use_container_width=True, hide_index=True)

        st.subheader("Detalle completo")
        cols_mostrar = [c for c in [
            "MAQUINA_TXT", "MAQUINA_TIPO", "total_horas",
            "dias_activos", "promedio_horas_dia", "total_reportes", "ultimo_reporte"
        ] if c in maq_df.columns]
        st.dataframe(
            maq_df[cols_mostrar].rename(columns={
                "MAQUINA_TXT": "Máquina",
                "MAQUINA_TIPO": "Tipo",
                "total_horas": "Horas totales",
                "dias_activos": "Días activos",
                "promedio_horas_dia": "Prom. hrs/día",
                "total_reportes": "Reportes",
                "ultimo_reporte": "Último reporte",
            }),
            use_container_width=True,
            hide_index=True,
        )
        csv_maq = maq_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇ Descargar CSV", csv_maq, "metricas_maquinas.csv", "text/csv")


# ── TAB 3: Operadores ────────────────────────────────────────────────────────
with tab3:
    if ops_df.empty:
        st.warning("Sin datos de operadores en el período seleccionado.")
    else:
        col_r, col_d = st.columns([1, 2])

        with col_r:
            st.subheader("🏆 Ranking de operadores")
            for _, row in ops_df.head(10).iterrows():
                medalla = {1: "🥇", 2: "🥈", 3: "🥉"}.get(int(row["posicion"]), f"#{int(row['posicion'])}")
                st.markdown(
                    f"**{medalla} {row['USUARIO_TXT']}**  \n"
                    f"⏱ {row['total_horas']:.0f} hrs · "
                    f"📅 {int(row['dias_trabajados'])} días · "
                    f"🚜 {int(row['maquinas_distintas'])} máquinas"
                )

        with col_d:
            st.subheader("Horas por operador (top 20)")
            top20_ops = ops_df.head(20).copy()
            st.bar_chart(
                top20_ops.set_index("USUARIO_TXT")["total_horas"],
                use_container_width=True,
                horizontal=True,
            )

        st.subheader("Detalle completo")
        st.dataframe(
            ops_df.rename(columns={
                "posicion": "#",
                "USUARIO_TXT": "Operador",
                "total_horas": "Horas totales",
                "dias_trabajados": "Días trabajados",
                "total_reportes": "Reportes",
                "maquinas_distintas": "Máquinas distintas",
                "promedio_horas_dia": "Prom. hrs/día",
            }),
            use_container_width=True,
            hide_index=True,
        )
        csv_ops = ops_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇ Descargar CSV", csv_ops, "ranking_operadores.csv", "text/csv")


# ── TAB 4: Combustible ───────────────────────────────────────────────────────
with tab4:
    if comb_df.empty:
        st.warning("Sin datos de combustible en el período seleccionado.")
    else:
        col_c1, col_c2, col_c3 = st.columns(3)
        col_c1.metric("Total litros", f"{comb_df['total_litros'].sum():,.0f} L")
        col_c2.metric("Máquinas con recargas", len(comb_df))
        col_c3.metric("Prom. litros por recarga",
                      f"{comb_df['promedio_litros_recarga'].mean():,.1f} L")

        st.subheader("Top 20 consumidoras")
        top_comb = comb_df.head(20).copy()
        nombre_col = "MAQUINA" if "MAQUINA" in top_comb.columns else "ID_MAQUINA"
        top_comb["Máquina"] = top_comb[nombre_col].fillna(top_comb["ID_MAQUINA"])
        st.bar_chart(
            top_comb.set_index("Máquina")["total_litros"],
            use_container_width=True,
            horizontal=True,
            color="#ff7f0e",
        )

        st.subheader("Detalle completo")
        cols_comb = [c for c in [
            nombre_col, "TIPO_MAQUINA", "total_litros",
            "num_recargas", "promedio_litros_recarga", "ultima_recarga"
        ] if c in comb_df.columns]
        st.dataframe(
            comb_df[cols_comb].rename(columns={
                nombre_col: "Máquina",
                "TIPO_MAQUINA": "Tipo",
                "total_litros": "Litros totales",
                "num_recargas": "Nº recargas",
                "promedio_litros_recarga": "Prom. litros",
                "ultima_recarga": "Última recarga",
            }),
            use_container_width=True,
            hide_index=True,
        )
        csv_comb = comb_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇ Descargar CSV", csv_comb, "consumo_combustible.csv", "text/csv")


# ── TAB 5: Alertas ───────────────────────────────────────────────────────────
with tab5:
    if alertas.empty:
        st.success("✅ No se detectaron alertas en el período analizado.")
    else:
        tipos = alertas["tipo_alerta"].unique() if "tipo_alerta" in alertas.columns else []

        # Resumen por tipo
        cols_tipos = st.columns(max(len(tipos), 1))
        for i, tipo in enumerate(tipos):
            n = len(alertas[alertas["tipo_alerta"] == tipo])
            emoji = {"SIN_REPORTE": "📵", "COMBUSTIBLE_INUSUAL": "⛽"}.get(tipo, "⚠️")
            cols_tipos[i].metric(f"{emoji} {tipo.replace('_', ' ')}", n)

        st.divider()

        # Filtro por tipo
        tipo_sel = st.selectbox(
            "Filtrar por tipo de alerta",
            options=["Todas"] + list(tipos),
        )
        df_mostrar = alertas if tipo_sel == "Todas" else alertas[alertas["tipo_alerta"] == tipo_sel]

        st.subheader(f"Alertas ({len(df_mostrar)})")

        # Mostrar alertas como tabla
        cols_alerta = [c for c in [
            "tipo_alerta", "ID_MAQUINA", "MAQUINA", "descripcion",
            "ultimo_reporte", "horas_sin_reporte", "FECHA", "LITROS"
        ] if c in df_mostrar.columns]

        st.dataframe(
            df_mostrar[cols_alerta].rename(columns={
                "tipo_alerta": "Tipo",
                "ID_MAQUINA": "ID Máquina",
                "MAQUINA": "Máquina",
                "descripcion": "Descripción",
                "ultimo_reporte": "Último reporte",
                "horas_sin_reporte": "Horas sin reporte",
                "FECHA": "Fecha recarga",
                "LITROS": "Litros",
            }),
            use_container_width=True,
            hide_index=True,
        )

        csv_alertas = alertas.to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇ Descargar alertas CSV", csv_alertas, "alertas.csv", "text/csv")
