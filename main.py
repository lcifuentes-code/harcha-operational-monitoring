"""
main.py
=======
PUNTO DE ENTRADA del sistema de monitoreo operacional.

Orquesta el flujo completo en 5 pasos:
  1. Cargar datos desde el Excel en /data/raw/
  2. Limpiar datos (formatos, nulos, duplicados)
  3. Calcular métricas operacionales
  4. Detectar alertas automáticas
  5. Guardar resultados en /data/outputs/

USO:
  python main.py
  python main.py --archivo otro_archivo.xlsx   (para procesar un archivo diferente)

SALIDA:
  data/outputs/metricas_diarias.csv
  data/outputs/consumo_combustible.csv
  data/outputs/ranking_operadores.csv
  data/outputs/alertas.csv
  data/outputs/reportes_limpios.csv
  data/outputs/resumen_diario.txt
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Agregar la raíz del proyecto al path para imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Importar todos los módulos del sistema
from config.settings import DATA_RAW_DIR, INPUT_FILE_PATH
from scripts.load_data  import cargar_datos
from scripts.clean_data import limpiar_datos
from scripts.transform  import calcular_metricas
from scripts.alerts     import generar_alertas
from scripts.metrics    import guardar_resultados


def parsear_argumentos():
    """Permite pasar opciones por línea de comandos."""
    parser = argparse.ArgumentParser(
        description="Sistema de monitoreo operacional - Harcha Maquinaria"
    )
    parser.add_argument(
        "--archivo",
        type=str,
        default=None,
        help="Nombre del archivo Excel en data/raw/ (por defecto usa settings.py)"
    )
    return parser.parse_args()


def main():
    """Flujo principal del sistema."""

    inicio = datetime.now()
    print("\n" + "=" * 60)
    print("  🚀 SISTEMA DE MONITOREO OPERACIONAL - HARCHA MAQUINARIA")
    print(f"  Inicio: {inicio.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # ── Gestión de argumentos de línea de comandos ─────────────
    args = parsear_argumentos()
    archivo_input = None
    if args.archivo:
        archivo_input = DATA_RAW_DIR / args.archivo
        print(f"\n📁 Archivo especificado: {args.archivo}")

    # ── PASO 1: Cargar datos ───────────────────────────────────
    print("\n[1/5] Cargando datos...")
    try:
        datos_crudos = cargar_datos(archivo=archivo_input)
    except FileNotFoundError as e:
        print(e)
        print("\n💡 Instrucciones:")
        print("   1. Descarga el Excel desde Google Sheets")
        print(f"  2. Colócalo en la carpeta: {DATA_RAW_DIR}")
        print("   3. Vuelve a ejecutar: python main.py")
        sys.exit(1)

    # ── PASO 2: Limpiar datos ──────────────────────────────────
    print("\n[2/5] Limpiando datos...")
    datos_limpios = limpiar_datos(datos_crudos)

    # ── PASO 3: Calcular métricas ──────────────────────────────
    print("\n[3/5] Calculando métricas...")
    metricas = calcular_metricas(datos_limpios)

    # ── PASO 4: Generar alertas ────────────────────────────────
    print("\n[4/5] Generando alertas...")
    alertas = generar_alertas(datos_limpios)

    # ── PASO 5: Guardar resultados ─────────────────────────────
    print("\n[5/5] Guardando resultados...")
    guardar_resultados(
        metricas=metricas,
        alertas=alertas,
        df_reportes_limpios=datos_limpios.get("reportes"),
    )

    # ── Resumen de tiempo ──────────────────────────────────────
    fin = datetime.now()
    duracion = (fin - inicio).total_seconds()
    print(f"\n⏱ Proceso completado en {duracion:.1f} segundos")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
