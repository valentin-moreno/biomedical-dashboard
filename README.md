# 🏥 Dashboard de Gestión de Equipos Biomédicos

Dashboard de Business Intelligence para **Ingeniería Clínica**, construido con **Streamlit** y **Plotly**. Monitorea confiabilidad, disponibilidad y costos de mantenimiento de equipos médicos en pesos colombianos (COP).

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python) ![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red?logo=streamlit) ![Plotly](https://img.shields.io/badge/Plotly-5.18+-purple?logo=plotly) ![Domain](https://img.shields.io/badge/Domain-Biomedical%20Engineering-teal) ![Currency](https://img.shields.io/badge/Currency-COP-green)

---

## 🚀 Inicio rápido

```bash
git clone https://github.com/tu-usuario/dashboard-biomedico.git
cd dashboard-biomedico

pip install -r requirements.txt

streamlit run dashboard_biomedico.py
```

> ⚠️ Los archivos `inventario_equipos.csv` y `ordenes_trabajo.csv` deben estar en la **misma carpeta** que `dashboard_biomedico.py`.

---

## 📁 Estructura del proyecto

```
dashboard-biomedico/
├── dashboard_biomedico.py    # App principal (cada línea comentada)
├── inventario_equipos.csv    # 436 equipos · 23 servicios · costos COP
├── ordenes_trabajo.csv       # 8,032 OTs · 2022–2024 · correctivos + preventivos
├── requirements.txt          # Dependencias
└── README.md                 # Este archivo
```

---

## 📊 KPIs implementados

| KPI | Fórmula | Meta hospitalaria |
|-----|---------|-------------------|
| **MTBF** | Horas del período / N° fallas | Mayor = más confiable |
| **MTTR** | Σ horas reparación / N° fallas | ≤ 8h equipos críticos |
| **Disponibilidad** | MTBF / (MTBF + MTTR) × 100% | ≥ 95% equipos críticos |
| **Cumplimiento PM** | PMs cerrados / PMs programados | ≥ 85% |
| **Ratio C/P** | Correctivos / Preventivos | < 1 (más preventivos que correctivos) |

---

## ✨ Secciones del dashboard

| Sección | Descripción |
|---|---|
| 🔢 KPIs con semáforo | 8 indicadores clave con colores verde/amarillo/rojo según umbrales clínicos |
| 📈 Tendencia mensual | Evolución de OTs correctivos vs preventivos (2022–2024) |
| 🍩 Tipos de falla | Distribución: eléctrica, mecánica, software, sensor, calibración... |
| 🫧 MTBF vs MTTR | Bubble chart de confiabilidad coloreado por disponibilidad |
| 📊 Disponibilidad | Barras apiladas por servicio clínico vs meta 95% |
| 💰 Costos COP | Pareto por servicio, carga por técnico y treemap de distribución |
| 🏷️ Inventario | Estado de equipos, top marcas por valor, antigüedad del parque tecnológico |
| 🚨 Equipos críticos | Top 20 equipos con menor disponibilidad + exportación CSV |
| 🎛️ Filtros | Año, servicio, criticidad, tipo OT y técnico |

---

## 🗄️ Dataset

### `inventario_equipos.csv` — 436 equipos
| Columna | Descripción |
|---------|-------------|
| `Equipo_ID` | Identificador único (BIO-XXXX) |
| `Nombre_Equipo` | Tipo de equipo |
| `Servicio` | Servicio clínico donde opera |
| `Criticidad` | Crítico / Alto / Medio / Bajo |
| `Marca` / `Modelo` / `Serie` | Datos del fabricante |
| `Año_Adquisicion` | Año de compra |
| `Vida_Util_Anos` | Vida útil estimada según criticidad |
| `Año_Vencimiento` | Año proyectado de reemplazo |
| `Costo_COP` | Valor del equipo en pesos colombianos |
| `Estado` | Operativo / En mantenimiento / Dado de baja |
| `Ubicacion` | Piso y cama o servicio |
| `Freq_PM_Meses` | Frecuencia de mantenimiento preventivo |

### `ordenes_trabajo.csv` — 8,032 OTs
| Columna | Descripción |
|---------|-------------|
| `OT_ID` | Identificador único de la orden |
| `Equipo_ID` | Equipo al que pertenece la OT |
| `Fecha` | Fecha de la falla o PM (YYYY-MM-DD) |
| `Tipo_OT` | Correctivo / Preventivo |
| `Tipo_Falla` | Categoría de la falla |
| `MTTR_Horas` | Horas de reparación |
| `Costo_OT_COP` | Costo de la orden en pesos colombianos |
| `Tecnico` | Ingeniero responsable |
| `Estado_OT` | Cerrada / En proceso / Pendiente |

---

## 🛠️ Stack tecnológico

- **[Streamlit](https://streamlit.io/)** — Framework web para apps de datos
- **[Plotly](https://plotly.com/python/)** — Visualizaciones interactivas
- **[Pandas](https://pandas.pydata.org/)** — Análisis y transformación de datos
- **[NumPy](https://numpy.org/)** — Cálculo numérico

---

## 📄 Licencia

MIT — libre para uso personal y comercial.
