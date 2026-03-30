"""
scripts/alerts.py
=================
PASO 4A: Generar alertas operacionales automáticas.

Detecta situaciones que requieren atención:
  - Máquinas activas que no han reportado en X horas
  - Máquinas con recargas de combustible inusuales
  - Máquinas sin ningún reporte en el período analizado

Uso:
    from scripts.alerts import generar_alertas
    alertas = generar_alertas(datos_limpios)
"""

import pandas as pd
from datetime import datetime, timedelta, timezone
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import HORAS_SIN_REPORTE, ESTADOS_ACTIVOS


# ─── Tipos de alerta (constantes) ─────────────────────────────────────────────
ALERTA_SIN_REPORTE    = "SIN_REPORTE"
ALERTA_COMBUSTIBLE    = "COMBUSTIBLE_INUSUAL"
ALERTA_SIN_ACTIVIDAD  = "SIN_ACTIVIDAD_EN_PERIODO"


def alerta_maquinas_sin_reporte(
    df_maquinas: pd.DataFrame,
    df_reportes: pd.DataFrame,
    horas_umbral: int = HORAS_SIN_REPORTE,
) -> pd.DataFrame:
    """
    Detecta máquinas que están 'En producción' pero no han enviado
    ningún reporte en las últimas N horas.

    Parámetros:
        df_maquinas:  catálogo de máquinas (limpio)
        df_reportes:  reportes diarios (limpio)
        horas_umbral: horas de silencio para generar alerta

    Retorna:
        DataFrame con las máquinas en alerta
    """
    if df_maquinas.empty or df_reportes.empty:
        return pd.DataFrame()

    # Filtrar solo máquinas que deberían estar reportando
    maq_activas = df_maquinas[
        df_maquinas["ESTADO"].isin(ESTADOS_ACTIVOS)
    ].copy()

    if maq_activas.empty:
        return pd.DataFrame()

    # Obtener la última vez que cada máquina reportó
    ultimo_reporte = (
        df_reportes
        .groupby("ID_MAQUINA")["FECHAHORA_INICIO"]
        .max()
        .reset_index()
        .rename(columns={"FECHAHORA_INICIO": "ultimo_reporte"})
    )

    # Unir al catálogo de máquinas activas
    maq_activas = maq_activas.merge(ultimo_reporte, on="ID_MAQUINA", how="left")

    # Calcular horas desde el último reporte
    # Usar la fecha más reciente en los datos como referencia
    # (no datetime.now() para que sea reproducible con datos históricos)
    fecha_referencia = df_reportes["FECHAHORA_INICIO"].max()
    if pd.isna(fecha_referencia):
        return pd.DataFrame()

    # Si nunca reportó, "ultimo_reporte" será NaT → se considera como alerta
    maq_activas["horas_sin_reporte"] = (
        fecha_referencia - maq_activas["ultimo_reporte"]
    ).dt.total_seconds() / 3600

    # Máquinas que superan el umbral O que nunca reportaron
    en_alerta = maq_activas[
        maq_activas["horas_sin_reporte"].isna() |
        (maq_activas["horas_sin_reporte"] >= horas_umbral)
    ].copy()

    if en_alerta.empty:
        return pd.DataFrame()

    # Construir DataFrame de alertas
    cols_salida = ["ID_MAQUINA", "MAQUINA", "TIPO_MAQUINA", "ESTADO",
                   "ultimo_reporte", "horas_sin_reporte"]
    cols_disponibles = [c for c in cols_salida if c in en_alerta.columns]
    alertas = en_alerta[cols_disponibles].copy()

    alertas["tipo_alerta"]  = ALERTA_SIN_REPORTE
    alertas["descripcion"]  = alertas["horas_sin_reporte"].apply(
        lambda h: f"Sin reporte hace {h:.0f} hs" if pd.notna(h) else "Nunca ha reportado"
    )
    alertas["umbral_horas"] = horas_umbral

    return alertas.sort_values("horas_sin_reporte", ascending=False, na_position="first")


def alerta_combustible_inusual(
    df_recargas: pd.DataFrame,
    multiplicador: float = 2.5,
) -> pd.DataFrame:
    """
    Detecta recargas de combustible inusualmente altas para cada máquina.
    Una recarga es 'inusual' si supera X veces el promedio de esa máquina.

    Parámetros:
        df_recargas:      recargas limpias
        multiplicador:    factor sobre el promedio para considerar inusual

    Retorna:
        DataFrame con las recargas sospechosas
    """
    if df_recargas.empty or "LITROS" not in df_recargas.columns:
        return pd.DataFrame()

    # Calcular promedio y desviación por máquina
    estadisticas = (
        df_recargas.groupby("ID_MAQUINA")["LITROS"]
        .agg(["mean", "std", "count"])
        .reset_index()
        .rename(columns={"mean": "promedio_litros", "std": "std_litros", "count": "num_recargas"})
    )

    # Solo analizar máquinas con más de 2 recargas (para tener estadística válida)
    estadisticas = estadisticas[estadisticas["num_recargas"] > 2]

    df_analisis = df_recargas.merge(estadisticas, on="ID_MAQUINA", how="inner")

    # Detectar outliers: litros > promedio * multiplicador
    df_analisis["umbral_alerta"] = df_analisis["promedio_litros"] * multiplicador
    inusuales = df_analisis[
        df_analisis["LITROS"] > df_analisis["umbral_alerta"]
    ].copy()

    if inusuales.empty:
        return pd.DataFrame()

    inusuales["tipo_alerta"] = ALERTA_COMBUSTIBLE
    inusuales["descripcion"] = inusuales.apply(
        lambda r: f"Recarga de {r['LITROS']:.0f} L (promedio: {r['promedio_litros']:.0f} L)", axis=1
    )

    cols = ["ID_MAQUINA", "FECHA", "LITROS", "promedio_litros",
            "tipo_alerta", "descripcion"]
    cols_disp = [c for c in cols if c in inusuales.columns]
    return inusuales[cols_disp]


def generar_alertas(datos: dict) -> pd.DataFrame:
    """
    Ejecuta todos los detectores de alerta y consolida los resultados.

    Parámetros:
        datos: dict con DataFrames limpios

    Retorna:
        DataFrame con todas las alertas, con columnas estandarizadas:
        tipo_alerta, descripcion, ID_MAQUINA, ...
    """
    print("\n🚨 Generando alertas...")

    lista_alertas = []

    # Alerta 1: Máquinas activas sin reporte
    a1 = alerta_maquinas_sin_reporte(
        datos.get("maquinas", pd.DataFrame()),
        datos.get("reportes", pd.DataFrame()),
    )
    if not a1.empty:
        lista_alertas.append(a1)
        print(f"  ⚠ {ALERTA_SIN_REPORTE}: {len(a1)} máquina(s) sin reporte")

    # Alerta 2: Recargas de combustible inusuales
    a2 = alerta_combustible_inusual(datos.get("recargas", pd.DataFrame()))
    if not a2.empty:
        lista_alertas.append(a2)
        print(f"  ⚠ {ALERTA_COMBUSTIBLE}: {len(a2)} recarga(s) inusual(es)")

    # Consolidar
    if lista_alertas:
        todas = pd.concat(lista_alertas, ignore_index=True, sort=False)
        print(f"\n  📋 Total de alertas generadas: {len(todas)}")
        return todas
    else:
        print("  ✅ No se detectaron alertas")
        return pd.DataFrame(columns=["tipo_alerta", "descripcion", "ID_MAQUINA"])


# ─── Ejecución directa para pruebas ───────────────────────────────────────────
if __name__ == "__main__":
    from scripts.load_data import cargar_datos
    from scripts.clean_data import limpiar_datos

    datos = limpiar_datos(cargar_datos())
    alertas = generar_alertas(datos)

    if not alertas.empty:
        print("\n📋 Alertas detectadas:")
        print(alertas[["tipo_alerta", "descripcion", "ID_MAQUINA"]].to_string(index=False))
