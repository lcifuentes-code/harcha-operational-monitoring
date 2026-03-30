"""
scripts/transform.py
====================
PASO 3: Transformar datos limpios en métricas operacionales.

Responsabilidad: calcular indicadores de negocio a partir de
los datos ya limpios. Produce DataFrames listos para dashboards.

Métricas generadas:
  - Horas trabajadas por máquina por día
  - Consumo de combustible por máquina
  - Rendimiento por operador
  - Resumen diario de actividad

Uso:
    from scripts.transform import calcular_metricas
    metricas = calcular_metricas(datos_limpios)
"""

import pandas as pd
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import ESTADOS_ACTIVOS


def metricas_por_maquina(df_reportes: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula horas trabajadas totales y días activos por máquina.

    Retorna un DataFrame con columnas:
        ID_MAQUINA, MAQUINA_TXT, MAQUINA_TIPO, total_horas,
        dias_activos, promedio_horas_dia, ultimo_reporte
    """
    if df_reportes.empty:
        return pd.DataFrame()

    resultado = (
        df_reportes
        .groupby(["ID_MAQUINA", "MAQUINA_TXT", "MAQUINA_TIPO"], dropna=False)
        .agg(
            total_horas      = ("HORAS_TRABAJADAS", "sum"),
            dias_activos     = ("FECHA", "nunique"),
            ultimo_reporte   = ("FECHAHORA_INICIO", "max"),
            total_reportes   = ("ID_REPORTE", "count"),
        )
        .reset_index()
    )

    # Calcular promedio de horas por día activo (evitar división por cero)
    resultado["promedio_horas_dia"] = (
        resultado["total_horas"] / resultado["dias_activos"].replace(0, pd.NA)
    ).round(2)

    resultado = resultado.sort_values("total_horas", ascending=False)
    return resultado


def metricas_combustible(df_recargas: pd.DataFrame, df_maquinas: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula consumo de combustible por máquina.

    Retorna un DataFrame con columnas:
        ID_MAQUINA, total_litros, num_recargas,
        promedio_litros_recarga, ultima_recarga
    """
    if df_recargas.empty:
        return pd.DataFrame()

    resultado = (
        df_recargas
        .groupby("ID_MAQUINA")
        .agg(
            total_litros           = ("LITROS", "sum"),
            num_recargas           = ("LITROS", "count"),
            promedio_litros_recarga= ("LITROS", "mean"),
            ultima_recarga         = ("FECHAHORA_RECARGA", "max"),
        )
        .reset_index()
    )

    resultado["promedio_litros_recarga"] = resultado["promedio_litros_recarga"].round(1)
    resultado["total_litros"] = resultado["total_litros"].round(1)

    # Enriquecer con nombre de máquina si está disponible
    if not df_maquinas.empty and "ID_MAQUINA" in df_maquinas.columns:
        nombres = df_maquinas[["ID_MAQUINA", "MAQUINA", "TIPO_MAQUINA"]].drop_duplicates()
        resultado = resultado.merge(nombres, on="ID_MAQUINA", how="left")

    resultado = resultado.sort_values("total_litros", ascending=False)
    return resultado


def ranking_operadores(df_reportes: pd.DataFrame) -> pd.DataFrame:
    """
    Genera un ranking de operadores según horas trabajadas.

    Retorna un DataFrame con columnas:
        USUARIO_TXT, total_horas, dias_trabajados,
        total_reportes, maquinas_distintas, promedio_horas_dia
    """
    if df_reportes.empty:
        return pd.DataFrame()

    # Filtrar registros sin operador identificado
    df = df_reportes[df_reportes["USUARIO_TXT"].notna()].copy()
    df = df[df["USUARIO_TXT"] != "nan"]

    resultado = (
        df
        .groupby("USUARIO_TXT")
        .agg(
            total_horas       = ("HORAS_TRABAJADAS", "sum"),
            dias_trabajados   = ("FECHA", "nunique"),
            total_reportes    = ("ID_REPORTE", "count"),
            maquinas_distintas= ("ID_MAQUINA", "nunique"),
        )
        .reset_index()
    )

    resultado["promedio_horas_dia"] = (
        resultado["total_horas"] / resultado["dias_trabajados"].replace(0, pd.NA)
    ).round(2)

    # Ranking: posición según horas totales
    resultado = resultado.sort_values("total_horas", ascending=False)
    resultado.insert(0, "posicion", range(1, len(resultado) + 1))

    return resultado


def actividad_por_dia(df_reportes: pd.DataFrame) -> pd.DataFrame:
    """
    Resumen diario: cuántas máquinas y operadores estuvieron activos cada día.

    Retorna un DataFrame con columnas:
        FECHA, maquinas_activas, operadores_activos,
        total_horas, total_reportes
    """
    if df_reportes.empty:
        return pd.DataFrame()

    resultado = (
        df_reportes
        .groupby("FECHA")
        .agg(
            maquinas_activas  = ("ID_MAQUINA", "nunique"),
            operadores_activos= ("USUARIO_TXT", "nunique"),
            total_horas       = ("HORAS_TRABAJADAS", "sum"),
            total_reportes    = ("ID_REPORTE", "count"),
        )
        .reset_index()
    )

    resultado["total_horas"] = resultado["total_horas"].round(1)
    resultado = resultado.sort_values("FECHA", ascending=False)
    return resultado


def calcular_metricas(datos: dict) -> dict:
    """
    Orquesta el cálculo de todas las métricas.

    Parámetros:
        datos: dict con DataFrames limpios (salida de clean_data.limpiar_datos)

    Retorna:
        dict con claves:
            'por_maquina', 'combustible', 'operadores', 'actividad_diaria'
    """
    print("\n📐 Calculando métricas...")

    df_reportes = datos.get("reportes", pd.DataFrame())
    df_recargas = datos.get("recargas", pd.DataFrame())
    df_maquinas = datos.get("maquinas", pd.DataFrame())

    metricas = {
        "por_maquina":    metricas_por_maquina(df_reportes),
        "combustible":    metricas_combustible(df_recargas, df_maquinas),
        "operadores":     ranking_operadores(df_reportes),
        "actividad_diaria": actividad_por_dia(df_reportes),
    }

    # Mostrar resumen en consola
    for nombre, df in metricas.items():
        if not df.empty:
            print(f"  ✓ {nombre}: {len(df)} registros calculados")
        else:
            print(f"  ⚠ {nombre}: sin datos")

    return metricas


# ─── Ejecución directa para pruebas ───────────────────────────────────────────
if __name__ == "__main__":
    from scripts.load_data import cargar_datos
    from scripts.clean_data import limpiar_datos

    datos = limpiar_datos(cargar_datos())
    metricas = calcular_metricas(datos)

    print("\n🔍 Muestra de métricas:")
    for nombre, df in metricas.items():
        print(f"\n--- {nombre.upper()} ---")
        if not df.empty:
            print(df.head(5).to_string(index=False))
