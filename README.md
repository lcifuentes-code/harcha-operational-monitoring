# 🚜 Harcha Maquinaria — Sistema de Monitoreo Operacional

Sistema de procesamiento de datos para el **monitoreo diario de maquinaria pesada**. Procesa archivos Excel descargados desde Google Sheets (AppSheet) y genera métricas, alertas y datasets listos para dashboards.

---

## ¿Qué hace este sistema?

| Funcionalidad | Descripción |
|---|---|
| 🔍 **Detecta máquinas sin reporte** | Identifica máquinas "En producción" que no han enviado actividad en X horas |
| ⛽ **Consumo de combustible** | Calcula litros consumidos por máquina y detecta recargas inusuales |
| 👷 **Ranking de operadores** | Ordena operadores por horas trabajadas en el período |
| 📅 **Actividad diaria** | Resumen de cuántas máquinas y operadores estuvieron activos cada día |
| 🚨 **Alertas automáticas** | Genera un CSV con todas las situaciones que requieren atención |

---

## Estructura del proyecto

```
harcha_monitor/
│
├── data/
│   ├── raw/          ← Coloca aquí el Excel descargado de Google Sheets
│   ├── processed/    ← (uso futuro: datos intermedios)
│   └── outputs/      ← Resultados generados automáticamente
│
├── scripts/
│   ├── load_data.py  ← Paso 1: Lee el Excel y carga las hojas
│   ├── clean_data.py ← Paso 2: Limpia nulos, formatos y duplicados
│   ├── transform.py  ← Paso 3: Calcula métricas operacionales
│   ├── alerts.py     ← Paso 4A: Detecta alertas automáticas
│   └── metrics.py    ← Paso 4B: Guarda resultados y genera resumen
│
├── config/
│   └── settings.py   ← Configuración central (rutas, umbrales, parámetros)
│
├── main.py           ← Punto de entrada (ejecuta todo el flujo)
├── requirements.txt  ← Dependencias de Python
├── .env.example      ← Plantilla de variables de entorno
└── README.md         ← Este archivo
```

---

## Cómo ejecutarlo (paso a paso)

### 1. Instalar Python
Necesitas Python 3.9 o superior. Verifica con:
```bash
python --version
```

### 2. Clonar o descargar el repositorio
```bash
git clone https://github.com/tu-org/harcha_monitor.git
cd harcha_monitor
```

### 3. Crear entorno virtual e instalar dependencias
```bash
# Crear entorno virtual (solo la primera vez)
python -m venv venv

# Activar el entorno
# En Windows:
venv\Scripts\activate
# En Mac/Linux:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 4. Configurar variables de entorno (opcional)
```bash
# Copia el archivo de ejemplo
cp .env.example .env

# Edita .env con tus valores si necesitas cambiar algo
# (el sistema funciona con los valores por defecto)
```

### 5. Colocar el archivo Excel
Descarga el Excel desde Google Sheets y colócalo en:
```
data/raw/DB2_HARCHA_MAQUINAS__1_.xlsx
```
> **Nota:** El nombre del archivo se configura en `.env` o en `config/settings.py`

### 6. Ejecutar el sistema
```bash
python main.py
```

Para usar un archivo con nombre diferente:
```bash
python main.py --archivo MiArchivo_20250101.xlsx
```

### 7. Revisar los resultados
Los archivos generados estarán en `data/outputs/`:

| Archivo | Contenido |
|---|---|
| `metricas_diarias.csv` | Horas trabajadas por máquina |
| `consumo_combustible.csv` | Litros por máquina y promedios |
| `ranking_operadores.csv` | Operadores ordenados por horas |
| `alertas.csv` | Máquinas y situaciones que requieren atención |
| `reportes_limpios.csv` | Todos los reportes procesados |
| `resumen_diario.txt` | Resumen ejecutivo en texto plano |

---

## Cómo cambiar parámetros

Edita `config/settings.py` para cambiar:

```python
# ¿Cuántas horas sin reporte genera alerta?
HORAS_SIN_REPORTE = 24   # Cambiar a 48 para menos alertas, 12 para más

# ¿Qué estados de máquina se consideran "activos"?
ESTADOS_ACTIVOS = ["En producción", "En Producción"]
```

---

## Cómo ejecutar cada módulo por separado (para pruebas)

```bash
# Solo probar la carga de datos
python scripts/load_data.py

# Solo probar la limpieza
python scripts/clean_data.py

# Solo las métricas
python scripts/transform.py

# Solo las alertas
python scripts/alerts.py

# Solo guardar resultados
python scripts/metrics.py
```

---

## Cómo migrar a otra máquina o cuenta

1. **Copia la carpeta completa** del proyecto (sin `data/` si los datos son confidenciales)
2. En la nueva máquina, ejecuta el paso 3 de instalación (`pip install -r requirements.txt`)
3. Copia tu archivo `.env` si tienes configuraciones personalizadas
4. El sistema **no tiene rutas absolutas**: funciona en cualquier computador

> El sistema usa `pathlib.Path(__file__).parent` para detectar la raíz automáticamente.

---

## Arquitectura y escalabilidad futura

Este sistema está pensado como **prototipo local**. Cuando se migre a la nube, cada módulo se convierte en una pieza independiente:

```
Hoy (prototipo local)          Futuro (nube)
─────────────────────────      ────────────────────────────────
Excel desde Google Sheets  →   API de Google Sheets / BigQuery
python main.py             →   Cloud Function / Airflow DAG
data/outputs/ (CSVs)       →   Base de datos PostgreSQL / BigQuery
Dashboard manual           →   Looker Studio / Metabase conectado a DB
```

---

## Hojas del Excel utilizadas

El sistema lee las siguientes hojas del archivo de Harcha:

| Hoja | Uso |
|---|---|
| `Query_Contratos_Reportes` | Reportes diarios de trabajo (horas, operador, máquina) |
| `Query_Recargas_Combustible` | Recargas de combustible por máquina |
| `MAQUINAS` | Catálogo de máquinas con estado actual |
| `USUARIOS` | Operadores y personal |
| `CONTRATOS` | Contratos activos |
| `MAQUINAS_INGRESOS_SALIDAS` | Registro de ingresos/salidas de máquinas |

---

## Preguntas frecuentes

**¿Por qué los resultados están vacíos?**
Verifica que el Excel está en `data/raw/` y que el nombre coincide con `INPUT_FILENAME` en `.env` o `settings.py`.

**¿Cómo agrego una nueva métrica?**
Agrega una nueva función en `scripts/transform.py` siguiendo el patrón existente, luego inclúyela en el diccionario que retorna `calcular_metricas()`.

**¿Cómo agrego una nueva alerta?**
Agrega una función en `scripts/alerts.py` y llámala dentro de `generar_alertas()`.

---

## Equipo

Desarrollado para **Harcha Maquinaria** como prototipo de monitoreo operacional.
Fase siguiente: migración a arquitectura cloud con procesamiento en tiempo real.
