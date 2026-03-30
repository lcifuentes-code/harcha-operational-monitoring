"""
scripts/clean_data.py
=====================
PASO 2: Limpiar los datos cargados.

Responsabilidad: corregir tipos de datos, eliminar duplicados,
manejar valores nulos y estandarizar formatos de texto.
No calcula métricas, solo limpia.

Uso:
    from scripts.clean_data import limpiar_datos
    datos_limpios = limpiar_datos(datos_crudos)
"""

import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def limpiar_reportes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia la hoja de reportes diarios de trabajo.
    Columnas clave: ID_MAQUINA, USUARIO_ID, FECHAHORA_INICIO,
                    HORAS_TRABAJADAS, MAQUINA_TXT, USUARIO_TXT
    """
    if df.empty:
        return df

    df = df.copy()

    # Convertir fechas al tipo correcto
    for col in ["FECHAHORA_INICIO", "FECHAHORA_FIN"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Asegurarse de que horas trabajadas es numérico
    if "HORAS_TRABAJADAS" in df.columns:
        df["HORAS_TRABAJADAS"] = pd.to_numeric(df["HORAS_TRABAJADAS"], errors="coerce")

    # Eliminar filas sin fecha de inicio (no tienen valor operacional)
    df = df.dropna(subset=["FECHAHORA_INICIO"])

    # Eliminar reportes duplicados por ID
    if "ID_REPORTE" in df.columns:
        df = df.drop_duplicates(subset=["ID_REPORTE"])

    # Limpiar espacios en textos de operador y máquina
    for col in ["USUARIO_TXT", "MAQUINA_TXT", "USUARIO_ID", "ID_MAQUINA"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # Columna auxiliar: solo la fecha (sin hora) para agrupar por día
    df["FECHA"] = df["FECHAHORA_INICIO"].dt.date

    print(f"  Reportes limpios: {len(df)} filas (de {len(df)} válidas)")
    return df


def limpiar_recargas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia la hoja de recargas de combustible.
    Columnas clave: ID_MAQUINA, LITROS, FECHA, ODOMETRO
    """
    if df.empty:
        return df

    df = df.copy()

    # Convertir fecha
    if "FECHA" in df.columns:
        df["FECHA"] = pd.to_datetime(df["FECHA"], errors="coerce")

    if "FECHAHORA_RECARGA" in df.columns:
        df["FECHAHORA_RECARGA"] = pd.to_datetime(df["FECHAHORA_RECARGA"], errors="coerce")

    # Litros debe ser numérico y positivo
    if "LITROS" in df.columns:
        df["LITROS"] = pd.to_numeric(df["LITROS"], errors="coerce")
        df = df[df["LITROS"].fillna(0) > 0]  # Elimina recargas inválidas

    # Odómetro numérico
    if "ODOMETRO" in df.columns:
        df["ODOMETRO"] = pd.to_numeric(df["ODOMETRO"], errors="coerce")

    # Limpiar IDs
    if "ID_MAQUINA" in df.columns:
        df["ID_MAQUINA"] = df["ID_MAQUINA"].astype(str).str.strip()

    # Eliminar duplicados
    if "ID_RECARGA" in df.columns:
        df = df.drop_duplicates(subset=["ID_RECARGA"])

    print(f"  Recargas limpias: {len(df)} registros válidos")
    return df


def limpiar_maquinas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia el catálogo de máquinas.
    Columnas clave: ID_MAQUINA, MAQUINA, ESTADO, HR_Actual, KM_Actual, Fecha_Ultima
    """
    if df.empty:
        return df

    df = df.copy()

    # Fechas de última actualización
    for col in ["Ultima_Actualizacion_HR", "Ultima_Actualizacion_KM",
                "Fecha_Horometro", "Fecha_CuentaKm", "Fecha_Ultima"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Valores numéricos
    for col in ["HR_Actual", "KM_Actual"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Limpiar texto de estado
    if "ESTADO" in df.columns:
        df["ESTADO"] = df["ESTADO"].astype(str).str.strip()

    # Eliminar filas sin ID de máquina
    if "ID_MAQUINA" in df.columns:
        df = df.dropna(subset=["ID_MAQUINA"])
        df["ID_MAQUINA"] = df["ID_MAQUINA"].astype(str).str.strip()

    print(f"  Máquinas limpias: {len(df)} registros")
    return df


def limpiar_datos(datos: dict) -> dict:
    """
    Aplica limpieza a todos los DataFrames del diccionario de datos.

    Parámetros:
        datos: dict devuelto por load_data.cargar_datos()

    Retorna:
        dict con los mismos keys pero DataFrames limpios
    """
    print("\n🧹 Limpiando datos...")

    return {
        "reportes":         limpiar_reportes(datos.get("reportes", pd.DataFrame())),
        "recargas":         limpiar_recargas(datos.get("recargas", pd.DataFrame())),
        "maquinas":         limpiar_maquinas(datos.get("maquinas", pd.DataFrame())),
        # Usuarios y contratos se usan como lookup, no requieren limpieza profunda
        "usuarios":         datos.get("usuarios", pd.DataFrame()).copy(),
        "contratos":        datos.get("contratos", pd.DataFrame()).copy(),
        "ingresos_salidas": datos.get("ingresos_salidas", pd.DataFrame()).copy(),
    }


# ─── Ejecución directa para pruebas ───────────────────────────────────────────
if __name__ == "__main__":
    from scripts.load_data import cargar_datos
    datos_crudos = cargar_datos()
    datos_limpios = limpiar_datos(datos_crudos)
    print("\n📊 Resultado de la limpieza:")
    for k, v in datos_limpios.items():
        print(f"  {k}: {v.shape}")
