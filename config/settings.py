"""
config/settings.py
==================
Configuración central del sistema.

Todos los parámetros configurables están aquí.
Para cambiar rutas o umbrales, edita este archivo o usa variables de entorno.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carga las variables del archivo .env si existe
load_dotenv()

# ─── RUTAS DEL PROYECTO ────────────────────────────────────────────────────────
# Detecta la raíz del proyecto automáticamente (funciona en cualquier máquina)
BASE_DIR = Path(__file__).resolve().parent.parent

DATA_RAW_DIR       = BASE_DIR / "data" / "raw"
DATA_PROCESSED_DIR = BASE_DIR / "data" / "processed"
DATA_OUTPUTS_DIR   = BASE_DIR / "data" / "outputs"

# ─── ARCHIVO DE ENTRADA ────────────────────────────────────────────────────────
# Nombre del Excel descargado desde Google Sheets.
# Se puede sobreescribir con la variable de entorno INPUT_FILENAME.
INPUT_FILENAME = os.getenv("INPUT_FILENAME", "DB2_HARCHA_MAQUINAS__1_.xlsx")
INPUT_FILE_PATH = DATA_RAW_DIR / INPUT_FILENAME

# ─── NOMBRES DE LAS HOJAS EN EL EXCEL ─────────────────────────────────────────
# Si Google Sheets cambia el nombre de una hoja, solo actualiza aquí.
SHEET_REPORTES      = "Query_Contratos_Reportes"   # Reportes diarios de trabajo
SHEET_RECARGAS      = "Query_Recargas_Combustible"  # Recargas de combustible
SHEET_MAQUINAS      = "MAQUINAS"                    # Catálogo de máquinas
SHEET_USUARIOS      = "USUARIOS"                    # Operadores y usuarios
SHEET_CONTRATOS     = "CONTRATOS"                   # Contratos activos
SHEET_ING_SAL       = "MAQUINAS_INGRESOS_SALIDAS"   # Ingresos/salidas de máquinas

# ─── PARÁMETROS DE NEGOCIO ─────────────────────────────────────────────────────
# Horas sin actividad antes de emitir alerta de máquina sin reporte
HORAS_SIN_REPORTE = int(os.getenv("HORAS_SIN_REPORTE", 24))

# Estados de máquina que se consideran "activos" (en producción)
ESTADOS_ACTIVOS = ["En producción", "En Producción"]

# ─── ARCHIVOS DE SALIDA ────────────────────────────────────────────────────────
OUTPUT_REPORTE_LIMPIO  = DATA_OUTPUTS_DIR / "reportes_limpios.csv"
OUTPUT_METRICAS        = DATA_OUTPUTS_DIR / "metricas_diarias.csv"
OUTPUT_ALERTAS         = DATA_OUTPUTS_DIR / "alertas.csv"
OUTPUT_COMBUSTIBLE     = DATA_OUTPUTS_DIR / "consumo_combustible.csv"
OUTPUT_OPERADORES      = DATA_OUTPUTS_DIR / "ranking_operadores.csv"
OUTPUT_RESUMEN         = DATA_OUTPUTS_DIR / "resumen_diario.txt"
