"""
scripts/load_data.py
====================
PASO 1: Cargar datos desde el archivo Excel.

Responsabilidad: solo leer las hojas necesarias del Excel y
devolver DataFrames crudos (sin transformar). Nada más.

Uso:
    from scripts.load_data import cargar_datos
    datos = cargar_datos()
"""

import pandas as pd
import sys
from pathlib import Path

# Asegura que Python encuentre el módulo config/ desde cualquier ubicación
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import (
    INPUT_FILE_PATH,
    SHEET_REPORTES,
    SHEET_RECARGAS,
    SHEET_MAQUINAS,
    SHEET_USUARIOS,
    SHEET_CONTRATOS,
    SHEET_ING_SAL,
)


def cargar_hoja(archivo: Path, nombre_hoja: str) -> pd.DataFrame:
    """
    Lee una hoja específica del Excel y la devuelve como DataFrame.
    Si la hoja no existe o hay error, devuelve un DataFrame vacío.
    """
    try:
        df = pd.read_excel(archivo, sheet_name=nombre_hoja)
        print(f"  ✓ Hoja '{nombre_hoja}': {len(df)} filas cargadas")
        return df
    except Exception as e:
        print(f"  ✗ Error al cargar hoja '{nombre_hoja}': {e}")
        return pd.DataFrame()


def cargar_datos(archivo=None) -> dict:
    """
    Carga todas las hojas necesarias del Excel.

    Parámetros:
        archivo: ruta al .xlsx (Path), objeto BytesIO (Streamlit upload),
                 o None para usar la configuración por defecto.

    Retorna:
        dict con claves: 'reportes', 'recargas', 'maquinas',
                         'usuarios', 'contratos', 'ingresos_salidas'
    """
    if archivo is None:
        archivo = INPUT_FILE_PATH

    # Solo verificar existencia si es una ruta en disco (no BytesIO de Streamlit)
    nombre = getattr(archivo, "name", str(archivo))
    if isinstance(archivo, Path) and not archivo.exists():
        raise FileNotFoundError(
            f"\n❌ No se encontró el archivo: {archivo}"
            f"\n   Descarga el Excel desde Google Sheets y colócalo en: {archivo.parent}"
        )

    print(f"\n📂 Cargando datos desde: {nombre}")

    datos = {
        "reportes":         cargar_hoja(archivo, SHEET_REPORTES),
        "recargas":         cargar_hoja(archivo, SHEET_RECARGAS),
        "maquinas":         cargar_hoja(archivo, SHEET_MAQUINAS),
        "usuarios":         cargar_hoja(archivo, SHEET_USUARIOS),
        "contratos":        cargar_hoja(archivo, SHEET_CONTRATOS),
        "ingresos_salidas": cargar_hoja(archivo, SHEET_ING_SAL),
    }

    print(f"\n✅ Carga completa. Hojas disponibles: {list(datos.keys())}\n")
    return datos


# ─── Ejecución directa para pruebas ───────────────────────────────────────────
if __name__ == "__main__":
    datos = cargar_datos()
    for nombre, df in datos.items():
        print(f"  {nombre}: {df.shape[0]} filas × {df.shape[1]} columnas")
