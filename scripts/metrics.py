"""
scripts/metrics.py
==================
PASO 4B: Guardar métricas y generar el resumen diario en texto.

Responsabilidad:
  - Guardar todos los DataFrames de métricas como archivos CSV
  - Generar un resumen diario legible (resumen_diario.txt)

Uso:
    from scripts.metrics import guardar_resultados
    guardar_resultados(metricas, alertas)
"""

import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import (
    DATA_OUTPUTS_DIR,
    OUTPUT_METRICAS,
    OUTPUT_ALERTAS,
    OUTPUT_COMBUSTIBLE,
    OUTPUT_OPERADORES,
    OUTPUT_RESUMEN,
    OUTPUT_REPORTE_LIMPIO,
)


def guardar_csv(df: pd.DataFrame, ruta: Path, nombre: str) -> None:
    """Guarda un DataFrame como CSV con manejo de errores."""
    if df.empty:
        print(f"  ⚠ {nombre}: sin datos, no se guardó archivo")
        return
    df.to_csv(ruta, index=False, encoding="utf-8-sig")  # utf-8-sig para compatibilidad con Excel
    print(f"  ✓ {nombre}: guardado en {ruta.name} ({len(df)} filas)")


def generar_resumen_texto(metricas: dict, alertas: pd.DataFrame, fecha_proceso: str) -> str:
    """
    Genera un resumen diario en formato texto plano.
    Útil para enviar por email o revisar rápidamente.
    """
    lineas = [
        "=" * 60,
        f"  RESUMEN OPERACIONAL DIARIO - HARCHA MAQUINARIA",
        f"  Procesado: {fecha_proceso}",
        "=" * 60,
        "",
    ]

    # ── Actividad general ──────────────────────────────────────
    act = metricas.get("actividad_diaria", pd.DataFrame())
    if not act.empty:
        ultimo_dia = act.iloc[0]  # Ya está ordenado desc
        lineas += [
            "📅 ÚLTIMO DÍA ACTIVO:",
            f"   Fecha:              {ultimo_dia.get('FECHA', 'N/A')}",
            f"   Máquinas activas:   {int(ultimo_dia.get('maquinas_activas', 0))}",
            f"   Operadores activos: {int(ultimo_dia.get('operadores_activos', 0))}",
            f"   Total horas:        {ultimo_dia.get('total_horas', 0):.1f} hrs",
            f"   Total reportes:     {int(ultimo_dia.get('total_reportes', 0))}",
            "",
        ]

    # ── Top 5 máquinas más productivas ────────────────────────
    maq = metricas.get("por_maquina", pd.DataFrame())
    if not maq.empty:
        lineas.append("🚜 TOP 5 MÁQUINAS (por horas trabajadas en período):")
        for _, row in maq.head(5).iterrows():
            nombre = row.get("MAQUINA_TXT", row.get("ID_MAQUINA", "?"))
            horas  = row.get("total_horas", 0)
            lineas.append(f"   • {nombre[:40]:<40} {horas:>7.1f} hrs")
        lineas.append("")

    # ── Top 5 operadores ──────────────────────────────────────
    ops = metricas.get("operadores", pd.DataFrame())
    if not ops.empty:
        lineas.append("👷 TOP 5 OPERADORES (por horas):")
        for _, row in ops.head(5).iterrows():
            nombre = str(row.get("USUARIO_TXT", "?"))[:40]
            horas  = row.get("total_horas", 0)
            pos    = int(row.get("posicion", 0))
            lineas.append(f"   {pos}. {nombre:<40} {horas:>7.1f} hrs")
        lineas.append("")

    # ── Combustible ───────────────────────────────────────────
    comb = metricas.get("combustible", pd.DataFrame())
    if not comb.empty:
        total_litros = comb["total_litros"].sum()
        lineas += [
            "⛽ COMBUSTIBLE:",
            f"   Total consumido en período: {total_litros:,.1f} litros",
            f"   Máquinas con recargas:       {len(comb)}",
            "",
        ]

    # ── Alertas ───────────────────────────────────────────────
    if not alertas.empty:
        lineas += [
            f"🚨 ALERTAS ({len(alertas)} detectadas):",
        ]
        for _, alerta in alertas.head(10).iterrows():
            tipo = alerta.get("tipo_alerta", "?")
            desc = alerta.get("descripcion", "?")
            maquina = alerta.get("ID_MAQUINA", alerta.get("MAQUINA", "?"))
            lineas.append(f"   [{tipo}] {maquina} → {desc}")
        if len(alertas) > 10:
            lineas.append(f"   ... y {len(alertas) - 10} alertas más (ver alertas.csv)")
    else:
        lineas.append("✅ Sin alertas activas")

    lineas += ["", "=" * 60]
    return "\n".join(lineas)


def guardar_resultados(
    metricas: dict,
    alertas: pd.DataFrame,
    df_reportes_limpios: pd.DataFrame = None,
) -> None:
    """
    Guarda todos los resultados en /data/outputs/.

    Parámetros:
        metricas:             dict con DataFrames de métricas
        alertas:              DataFrame con alertas
        df_reportes_limpios:  DataFrame de reportes limpios (opcional)
    """
    print(f"\n💾 Guardando resultados en: {DATA_OUTPUTS_DIR}/")

    # Crear directorio si no existe
    DATA_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    # Guardar cada métrica como CSV
    guardar_csv(metricas.get("por_maquina", pd.DataFrame()),   OUTPUT_METRICAS,    "Métricas por máquina")
    guardar_csv(metricas.get("combustible", pd.DataFrame()),   OUTPUT_COMBUSTIBLE, "Consumo combustible")
    guardar_csv(metricas.get("operadores", pd.DataFrame()),    OUTPUT_OPERADORES,  "Ranking operadores")
    guardar_csv(alertas,                                        OUTPUT_ALERTAS,     "Alertas")

    # Guardar reportes limpios si se proporcionaron
    if df_reportes_limpios is not None and not df_reportes_limpios.empty:
        guardar_csv(df_reportes_limpios, OUTPUT_REPORTE_LIMPIO, "Reportes limpios")

    # Generar y guardar resumen en texto
    fecha_proceso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    resumen = generar_resumen_texto(metricas, alertas, fecha_proceso)

    with open(OUTPUT_RESUMEN, "w", encoding="utf-8") as f:
        f.write(resumen)
    print(f"  ✓ Resumen diario: guardado en {OUTPUT_RESUMEN.name}")

    # También mostrar en consola
    print("\n" + resumen)


# ─── Ejecución directa para pruebas ───────────────────────────────────────────
if __name__ == "__main__":
    from scripts.load_data import cargar_datos
    from scripts.clean_data import limpiar_datos
    from scripts.transform import calcular_metricas
    from scripts.alerts import generar_alertas

    datos    = limpiar_datos(cargar_datos())
    metricas = calcular_metricas(datos)
    alertas  = generar_alertas(datos)
    guardar_resultados(metricas, alertas, datos.get("reportes"))
