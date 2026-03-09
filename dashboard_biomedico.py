# DASHBOARD DE GESTIÓN DE EQUIPOS BIOMÉDICOS
# Fuente de datos: inventario_equipos.csv + ordenes_trabajo.csv
# KPIs: MTBF, MTTR, Disponibilidad, Cumplimiento PM, Costos en COP
# Autor: Valentín Moreno Vasquez · Ingeniería Clínica · 2024


import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings

warnings.filterwarnings("ignore")


# CONFIGURACIÓN DE PÁGINA — debe ser la primera instrucción de Streamlit

st.set_page_config(
    page_title="BI · Equipos Biomédicos",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ESTILOS CSS — tema hospitalario oscuro, azul clínico

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .main { background-color: #0a0e1a; color: #e2e8f0; }

    /* Tarjeta de KPI base */
    .kpi-card {
        background: linear-gradient(135deg, #0f1829 0%, #162032 100%);
        border-radius: 12px; padding: 18px 20px;
        border: 1px solid #1e3a5f;
        box-shadow: 0 4px 15px rgba(0,100,200,0.1);
        text-align: center; margin-bottom: 10px;
    }
    /* Valores con semáforo de colores */
    .kpi-value       { font-size:1.9rem; font-weight:700; color:#38bdf8; line-height:1.2; }
    .kpi-value-alert { font-size:1.9rem; font-weight:700; color:#f87171; line-height:1.2; }
    .kpi-value-warn  { font-size:1.9rem; font-weight:700; color:#fbbf24; line-height:1.2; }
    .kpi-value-ok    { font-size:1.9rem; font-weight:700; color:#34d399; line-height:1.2; }
    .kpi-label { font-size:0.75rem; color:#64748b; text-transform:uppercase; letter-spacing:1.2px; margin-top:4px; }
    .kpi-icon  { font-size:1.4rem; margin-bottom:4px; }

    /* Títulos de sección */
    .dash-title { font-size:2.2rem; font-weight:700; color:#38bdf8; margin-bottom:2px; }
    .dash-sub   { font-size:0.9rem; color:#475569; margin-bottom:20px; }
    .sec-title  {
        font-size:1.05rem; font-weight:600; color:#94a3b8;
        margin:22px 0 10px 0;
        border-left:3px solid #38bdf8; padding-left:10px;
    }

    [data-testid="stSidebar"] { background-color:#0a0e1a; border-right:1px solid #1e3a5f; }
    .block-container { padding-top:1.8rem; }
</style>
""", unsafe_allow_html=True)


# CARGA DE DATOS DESDE CSV
# @st.cache_data evita recargar los archivos en cada interacción del usuario

@st.cache_data
def cargar_datos():
    """
    Lee los dos CSV del proyecto y los enriquece con columnas de fecha.
    Retorna:
        df_ot  — órdenes de trabajo con columnas temporales añadidas
        df_inv — inventario completo de equipos
    """
    # Leer el inventario de equipos biomédicos
    df_inv = pd.read_csv("inventario_equipos.csv")

    # Leer las órdenes de trabajo (correctivos + preventivos)
    df_ot = pd.read_csv("ordenes_trabajo.csv")

    # Convertir la columna Fecha a tipo datetime para operaciones temporales
    df_ot["Fecha"] = pd.to_datetime(df_ot["Fecha"])

    # Extraer componentes de fecha útiles para filtros y agrupaciones
    df_ot["Año"]       = df_ot["Fecha"].dt.year
    df_ot["Mes"]       = df_ot["Fecha"].dt.month
    df_ot["Trimestre"] = df_ot["Fecha"].dt.quarter
    df_ot["YearMonth"] = df_ot["Fecha"].dt.to_period("M").astype(str)  # "2023-01"

    return df_ot, df_inv


# Cargar datos al inicio (una sola vez gracias al caché)
df_ot_original, df_inv = cargar_datos()



# FUNCIÓN PARA FORMATEAR VALORES EN PESOS COLOMBIANOS (COP)

def fmt_cop(valor):
    """
    Formatea un número como moneda colombiana abreviada.
    Ejemplos: 1_500_000 → '$1.5M'  |  850_000 → '$850K'
    """
    if valor >= 1_000_000_000:
        return f"${valor/1_000_000_000:.1f}B"    # Miles de millones
    elif valor >= 1_000_000:
        return f"${valor/1_000_000:.1f}M"         # Millones
    elif valor >= 1_000:
        return f"${valor/1_000:.0f}K"             # Miles
    else:
        return f"${valor:,.0f}"



# CÁLCULO DE KPIs DE CONFIABILIDAD POR EQUIPO

@st.cache_data
def calcular_kpis(df_correctivo):
    """
    Calcula MTBF, MTTR y Disponibilidad para cada equipo a partir de sus
    órdenes correctivas cerradas.

    MTBF  = (3 años × 8760 h) / N° fallas        → mayor es mejor
    MTTR  = promedio de horas de reparación       → menor es mejor
    Disp% = MTBF / (MTBF + MTTR) × 100           → meta hospitalaria ≥95%
    """
    HORAS_PERIODO = 3 * 8760   # Horas totales del período de análisis (3 años)

    # Solo órdenes correctivas cerradas (fallas reales resueltas)
    df_c = df_correctivo[
        (df_correctivo["Tipo_OT"] == "Correctivo") &
        (df_correctivo["Estado_OT"] == "Cerrada")
    ]

    # Agrupar por equipo y calcular métricas base
    kpis = (
        df_c.groupby(["Equipo_ID", "Nombre_Equipo", "Servicio", "Criticidad"])
        .agg(
            N_Fallas    = ("OT_ID",      "count"),      # Número de fallas
            MTTR        = ("MTTR_Horas", "mean"),       # Tiempo promedio de reparación
            Costo_Total = ("Costo_OT_COP", "sum"),      # Costo total correctivo en COP
        )
        .reset_index()
    )

    # MTBF: horas del período divididas entre número de fallas
    kpis["MTBF"] = HORAS_PERIODO / kpis["N_Fallas"].clip(lower=1)

    # Disponibilidad con la fórmula estándar de confiabilidad
    kpis["Disponibilidad"] = (kpis["MTBF"] / (kpis["MTBF"] + kpis["MTTR"])) * 100

    # Clasificación semáforo para la tabla de equipos críticos
    kpis["Estado_Disp"] = pd.cut(
        kpis["Disponibilidad"],
        bins=[0, 90, 95, 100],
        labels=["🔴 Crítico", "🟡 Atención", "🟢 OK"]
    )

    return kpis.round(2)



# SIDEBAR — FILTROS INTERACTIVOS

with st.sidebar:
    st.markdown("## 🏥 Filtros")
    st.markdown("---")

    # Filtro por año (multiselect: permite seleccionar uno o varios)
    años = sorted(df_ot_original["Año"].unique().tolist())
    año_sel = st.multiselect("📅 Año", años, default=años)

    # Filtro por servicio clínico
    servicios = sorted(df_ot_original["Servicio"].unique().tolist())
    serv_sel = st.multiselect("🏨 Servicio", servicios, default=servicios)

    # Filtro por nivel de criticidad del equipo
    crits = ["Crítico", "Alto", "Medio", "Bajo"]
    crit_sel = st.multiselect("⚠️ Criticidad", crits, default=crits)

    # Filtro por tipo de orden de trabajo
    tipo_ot_sel = st.radio("📋 Tipo OT", ["Todas", "Correctivo", "Preventivo"])

    # Filtro por técnico responsable
    tecnicos = sorted(df_ot_original["Tecnico"].unique().tolist())
    tec_sel = st.multiselect("👷 Técnico", tecnicos, default=tecnicos)

    st.markdown("---")
    # Métricas de contexto del dataset en la barra lateral
    st.markdown(f"**🔧 Equipos en inventario:** `{len(df_inv):,}`")
    st.markdown(f"**📋 Total OTs en BD:** `{len(df_ot_original):,}`")
    st.markdown(f"**🏥 Servicios clínicos:** `{df_inv['Servicio'].nunique()}`")
    st.markdown(f"**🏷️ Marcas en inventario:** `{df_inv['Marca'].nunique()}`")


# APLICAR FILTROS AL DATAFRAME PRINCIPAL

df = df_ot_original[
    (df_ot_original["Año"].isin(año_sel)) &
    (df_ot_original["Servicio"].isin(serv_sel)) &
    (df_ot_original["Criticidad"].isin(crit_sel)) &
    (df_ot_original["Tecnico"].isin(tec_sel))
]

# Aplicar filtro de tipo de OT si no es "Todas"
if tipo_ot_sel != "Todas":
    df = df[df["Tipo_OT"] == tipo_ot_sel]

# Verificar que haya datos tras los filtros antes de continuar
if df.empty:
    st.warning("⚠️ Sin datos para los filtros seleccionados. Ajusta los filtros.")
    st.stop()

# Subconjunto solo de OTs correctivas (para KPIs de confiabilidad)
df_corr = df[df["Tipo_OT"] == "Correctivo"]

# Subconjunto de preventivos para cumplimiento de PM
df_prev = df[df["Tipo_OT"] == "Preventivo"]

# Inventario filtrado por servicio seleccionado
df_inv_filt = df_inv[df_inv["Servicio"].isin(serv_sel)]



# CABECERA DEL DASHBOARD

st.markdown('<p class="dash-title">🏥 Gestión de Equipos Biomédicos</p>', unsafe_allow_html=True)
st.markdown(
    f'<p class="dash-sub">Ingeniería Clínica · {len(df_inv_filt):,} equipos · '
    f'{df_inv_filt["Servicio"].nunique()} servicios · Costos en COP</p>',
    unsafe_allow_html=True
)



# SECCIÓN 1: KPIs PRINCIPALES

st.markdown('<p class="sec-title">Indicadores Clave de Rendimiento</p>', unsafe_allow_html=True)

# --- CÁLCULO DE MÉTRICAS GLOBALES ---
total_ot          = len(df)                                                    # Total OTs filtradas
total_correctivo  = len(df_corr)                                               # Solo correctivos
total_preventivo  = len(df_prev)                                               # Solo preventivos
costo_total       = df["Costo_OT_COP"].sum()                                   # Costo total en COP
mttr_global       = df_corr["MTTR_Horas"].mean() if len(df_corr) > 0 else 0   # MTTR promedio
equipos_activos   = df["Equipo_ID"].nunique()                                  # Equipos con actividad

# Calcular KPIs de confiabilidad por equipo
kpis_eq   = calcular_kpis(df_ot_original)                                     # KPIs de todo el dataset
kpis_filt = kpis_eq[kpis_eq["Servicio"].isin(serv_sel)]                       # Filtrar por servicio
disp_flota = kpis_filt["Disponibilidad"].mean()                                # Disponibilidad promedio flota

# Calcular cumplimiento de PM: % de preventivos ejecutados (no pendientes)
pm_cerrados    = len(df_prev[df_prev["Estado_OT"] == "Cerrada"])
cumpl_pm       = (pm_cerrados / max(len(df_prev), 1)) * 100

# Valor total del inventario filtrado en COP
valor_inventario = df_inv_filt["Costo_COP"].sum()

# Relación correctivo/preventivo (meta: que preventivos superen correctivos)
ratio_cp = total_correctivo / max(total_preventivo, 1)

# --- HELPER PARA RENDERIZAR TARJETAS ---
def kpi(col, icono, valor, etiqueta, clase="kpi-value"):
    """Renderiza una tarjeta de KPI con color semáforo según la clase CSS."""
    with col:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon">{icono}</div>
            <div class="{clase}">{valor}</div>
            <div class="kpi-label">{etiqueta}</div>
        </div>""", unsafe_allow_html=True)

# Determinar clase de color según umbrales clínicos estándar
clase_disp  = "kpi-value-ok"    if disp_flota  >= 95 else ("kpi-value-warn" if disp_flota  >= 90 else "kpi-value-alert")
clase_mttr  = "kpi-value-ok"    if mttr_global <= 8  else ("kpi-value-warn" if mttr_global <= 24 else "kpi-value-alert")
clase_pm    = "kpi-value-ok"    if cumpl_pm    >= 85 else ("kpi-value-warn" if cumpl_pm    >= 70 else "kpi-value-alert")
clase_ratio = "kpi-value-alert" if ratio_cp    >  1  else "kpi-value-ok"   # Malo si correctivos > preventivos

# Renderizar las 8 tarjetas de KPI en una fila
c1,c2,c3,c4,c5,c6,c7,c8 = st.columns(8)
kpi(c1, "📋", f"{total_ot:,}",           "Total OTs")
kpi(c2, "🚨", f"{total_correctivo:,}",   "Correctivos",     "kpi-value-alert" if total_correctivo > total_preventivo else "kpi-value")
kpi(c3, "✅", f"{total_preventivo:,}",   "Preventivos",     "kpi-value-ok")
kpi(c4, "📡", f"{disp_flota:.1f}%",      "Disponibilidad",  clase_disp)
kpi(c5, "⏱️", f"{mttr_global:.1f}h",     "MTTR Promedio",   clase_mttr)
kpi(c6, "📅", f"{cumpl_pm:.0f}%",        "Cumplimiento PM", clase_pm)
kpi(c7, "⚖️", f"{ratio_cp:.2f}",         "Ratio C/P",       clase_ratio)
kpi(c8, "💰", fmt_cop(costo_total),      "Costo Mant. COP")



# SECCIÓN 2: TENDENCIA TEMPORAL Y DISTRIBUCIÓN DE FALLAS

st.markdown('<p class="sec-title">Tendencias de Mantenimiento</p>', unsafe_allow_html=True)

col_l, col_r = st.columns([3, 2])

# --- LÍNEA TEMPORAL: OTs por mes separadas por tipo ---
with col_l:
    tendencia = (
        df_ot_original[
            (df_ot_original["Año"].isin(año_sel)) &
            (df_ot_original["Servicio"].isin(serv_sel))
        ]
        .groupby(["YearMonth", "Tipo_OT"])
        .size()
        .reset_index(name="Cantidad")
        .sort_values("YearMonth")
    )

    fig_tend = px.line(
        tendencia,
        x="YearMonth", y="Cantidad", color="Tipo_OT",
        title="Órdenes de Trabajo por Mes",
        markers=True,
        color_discrete_map={"Correctivo": "#f87171", "Preventivo": "#38bdf8"},
        labels={"YearMonth": "", "Cantidad": "N° OTs", "Tipo_OT": "Tipo"}
    )
    fig_tend.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,24,41,0.8)",
        font=dict(color="#94a3b8", family="Inter"), height=340,
        margin=dict(l=0,r=0,t=40,b=0),
        xaxis=dict(showgrid=False, tickangle=45),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.04)"),
        hovermode="x unified"
    )
    st.plotly_chart(fig_tend, use_container_width=True)

# --- DONA: Distribución por tipo de falla ---
with col_r:
    dist_falla = (
        df_corr.groupby("Tipo_Falla")
        .size().reset_index(name="Cantidad")
        .sort_values("Cantidad", ascending=False)
    )
    fig_dona = px.pie(
        dist_falla, names="Tipo_Falla", values="Cantidad",
        title="Distribución por Tipo de Falla",
        hole=0.5,
        color_discrete_sequence=px.colors.sequential.Blues_r
    )
    fig_dona.update_traces(
        textposition="outside", textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>%{value} fallas (%{percent})<extra></extra>"
    )
    fig_dona.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8", family="Inter"),
        height=340, margin=dict(l=0,r=0,t=40,b=30), showlegend=False
    )
    st.plotly_chart(fig_dona, use_container_width=True)



# SECCIÓN 3: CONFIABILIDAD — DISPONIBILIDAD POR SERVICIO

st.markdown('<p class="sec-title">Confiabilidad de Equipos · Disponibilidad por Servicio</p>', unsafe_allow_html=True)

# Calcular disponibilidad promedio por servicio (todos los servicios visibles con scroll)
disp_serv = (
    kpis_filt.groupby("Servicio")
    .agg(Disponibilidad=("Disponibilidad","mean"), Equipos=("Equipo_ID","count"))
    .reset_index()
    .sort_values("Disponibilidad", ascending=True)
    .round(1)
)
disp_serv["No_Disponible"] = 100 - disp_serv["Disponibilidad"]  # Complemento al 100%

# Altura dinámica: 40px por servicio garantiza que todos sean visibles con scroll interno
altura_disp = 400

fig_disp = go.Figure()
# Porción disponible en azul clínico
fig_disp.add_trace(go.Bar(
    y=disp_serv["Servicio"], x=disp_serv["Disponibilidad"],
    orientation="h", name="Disponible",
    marker_color="#38bdf8",
    text=disp_serv["Disponibilidad"].astype(str) + "%",
    textposition="inside",
    hovertemplate="<b>%{y}</b><br>Disponibilidad: %{x:.1f}%<extra></extra>"
))
# Porción no disponible en rojo semitransparente
fig_disp.add_trace(go.Bar(
    y=disp_serv["Servicio"], x=disp_serv["No_Disponible"],
    orientation="h", name="No Disponible",
    marker_color="rgba(248,113,113,0.5)",
    hovertemplate="<b>%{y}</b><br>No disponible: %{x:.1f}%<extra></extra>"
))
# Línea de meta hospitalaria estándar (95%)
fig_disp.add_vline(x=95, line_dash="dot", line_color="#fbbf24",
                   annotation_text="Meta 95%", annotation_font_color="#fbbf24")
fig_disp.update_layout(
    barmode="stack", title="Disponibilidad por Servicio Clínico (todos los servicios)",
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,24,41,0.8)",
    font=dict(color="#94a3b8", family="Inter"),
    height=altura_disp,                        # Altura dinámica para mostrar todos los servicios
    margin=dict(l=0,r=0,t=40,b=0),
    xaxis=dict(range=[0,100], showgrid=True, gridcolor="rgba(255,255,255,0.04)", title=""),
    yaxis=dict(showgrid=False),
    legend=dict(orientation="h", y=1.02)
)
# use_container_width + altura dinámica activan scroll automático en el contenedor
st.plotly_chart(fig_disp, use_container_width=True)


# SECCIÓN 4: COSTOS EN COP

st.markdown('<p class="sec-title">Análisis de Costos (COP)</p>', unsafe_allow_html=True)

col_p, col_q = st.columns(2)   # Costos por servicio y técnico en columnas iguales

# --- COSTOS POR SERVICIO ---
with col_p:
    costos_serv = (
        df.groupby("Servicio")
        .agg(Costo=("Costo_OT_COP", "sum"))
        .reset_index()
        .sort_values("Costo", ascending=True)
    )
    # Formatear etiquetas con abreviaciones en COP
    costos_serv["Costo_Label"] = costos_serv["Costo"].apply(fmt_cop)

    fig_costo = px.bar(
        costos_serv, x="Costo", y="Servicio", orientation="h",
        title="Costo de Mantenimiento por Servicio (COP)",
        color="Costo", color_continuous_scale="Blues",
        text="Costo_Label",
        labels={"Costo": "COP", "Servicio": ""}
    )
    fig_costo.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,24,41,0.8)",
        font=dict(color="#94a3b8", family="Inter"),
        height=400, margin=dict(l=0,r=0,t=40,b=0),
        coloraxis_showscale=False
    )
    fig_costo.update_traces(textposition="outside")
    st.plotly_chart(fig_costo, use_container_width=True)

# --- CARGA DE TRABAJO POR TÉCNICO ---
with col_q:
    carga_tec = (
        df.groupby("Tecnico")
        .agg(OTs=("OT_ID","count"), Horas=("MTTR_Horas","sum"), Costo=("Costo_OT_COP","sum"))
        .reset_index()
        .sort_values("OTs", ascending=False)
    )
    carga_tec["Costo_Label"] = carga_tec["Costo"].apply(fmt_cop)

    fig_tec = px.bar(
        carga_tec, x="Tecnico", y="OTs",
        title="OTs por Técnico",
        color="Horas",                              # Color según horas acumuladas
        color_continuous_scale="Blues",
        text="OTs",
        labels={"OTs": "N° Órdenes", "Tecnico": ""}
    )
    fig_tec.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,24,41,0.8)",
        font=dict(color="#94a3b8", family="Inter"),
        height=400, margin=dict(l=0,r=0,t=40,b=0),
        coloraxis_showscale=False,
        xaxis=dict(showgrid=False, tickangle=20)
    )
    fig_tec.update_traces(textposition="outside")
    st.plotly_chart(fig_tec, use_container_width=True)

# --- TREEMAP: Costo total por Servicio → Equipo (ancho completo, más grande) ---
st.markdown('<p class="sec-title" style="margin-top:8px">Distribución de Costos por Servicio y Equipo</p>', unsafe_allow_html=True)

cost_tree = (
    df.groupby(["Servicio", "Nombre_Equipo"])
    .agg(Costo=("Costo_OT_COP","sum"), OTs=("OT_ID","count"))
    .reset_index()
)
cost_tree["Costo_Label"] = cost_tree["Costo"].apply(fmt_cop)

fig_tree = px.treemap(
    cost_tree,
    path=["Servicio", "Nombre_Equipo"],   # Jerarquía: Servicio → Equipo
    values="Costo",
    color="OTs",
    color_continuous_scale="Blues",
    title="Distribución de Costos de Mantenimiento (COP)",
    custom_data=["Costo_Label"]
)
fig_tree.update_traces(
    hovertemplate="<b>%{label}</b><br>Costo: %{customdata[0]}<br>OTs: %{color:.0f}<extra></extra>"
)
fig_tree.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#94a3b8", family="Inter"),
    height=600,                            # Más alto al ocupar todo el ancho
    margin=dict(l=0,r=0,t=40,b=0),
    coloraxis_showscale=False
)
st.plotly_chart(fig_tree, use_container_width=True)



# SECCIÓN 5: INVENTARIO — ESTADO Y VENCIMIENTO
# Columnas exclusivas del inventario: Modelo, Serie, Año_Adquisicion,
# Vida_Util_Anos, Año_Vencimiento, Costo_COP, Estado, Ubicacion

st.markdown('<p class="sec-title">Estado del Inventario</p>', unsafe_allow_html=True)

col_i1, col_i2 = st.columns(2)

# --- DONA: Estado operativo de los equipos ---
with col_i1:
    estado_inv = df_inv_filt["Estado"].value_counts().reset_index()
    estado_inv.columns = ["Estado", "Cantidad"]

    fig_estado = px.pie(
        estado_inv, names="Estado", values="Cantidad",
        title="Estado de Equipos",
        hole=0.5,
        color="Estado",
        color_discrete_map={
            "Operativo":         "#38bdf8",
            "En mantenimiento":  "#0369a1",
            "Dado de baja":      "#0f172a"
        }
    )
    fig_estado.update_traces(textposition="outside", textinfo="label+percent")
    fig_estado.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8", family="Inter"),
        height=320, margin=dict(l=0,r=0,t=40,b=30), showlegend=False
    )
    st.plotly_chart(fig_estado, use_container_width=True)

# --- BARRAS: Top marcas por valor de inventario ---
with col_i2:
    marcas_inv = (
        df_inv_filt.groupby("Marca")
        .agg(Valor=("Costo_COP","sum"), Equipos=("Equipo_ID","count"))
        .reset_index()
        .sort_values("Valor", ascending=False)
        .head(10)                                   # Top 10 marcas por valor
    )
    marcas_inv["Valor_Label"] = marcas_inv["Valor"].apply(fmt_cop)

    fig_marcas = px.bar(
        marcas_inv, x="Marca", y="Valor",
        title="Top Marcas por Valor en Inventario (COP)",
        color="Equipos",
        color_continuous_scale="Blues",
        text="Valor_Label",
        labels={"Valor": "COP", "Marca": ""}
    )
    fig_marcas.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,24,41,0.8)",
        font=dict(color="#94a3b8", family="Inter"),
        height=320, margin=dict(l=0,r=0,t=40,b=0),
        coloraxis_showscale=False,
        xaxis=dict(showgrid=False, tickangle=30)
    )
    fig_marcas.update_traces(textposition="outside")
    st.plotly_chart(fig_marcas, use_container_width=True)





# SECCIÓN 6: TABLA — EQUIPOS CON MENOR DISPONIBILIDAD (PRIORIZACIÓN)

st.markdown('<p class="sec-title">🚨 Equipos Prioritarios (Menor Disponibilidad)</p>', unsafe_allow_html=True)

# Enriquecer KPIs con datos del inventario (Modelo, Serie, Ubicación, Costo_COP)
kpis_enriq = kpis_filt.merge(
    df_inv[["Equipo_ID","Modelo","Serie","Ubicacion","Costo_COP","Año_Adquisicion","Año_Vencimiento"]].drop_duplicates("Equipo_ID"),
    on="Equipo_ID", how="left"
)

# Top 20 equipos con peor disponibilidad
peores = (
    kpis_enriq
    .sort_values("Disponibilidad", ascending=True)
    .head(20)
    [["Equipo_ID","Nombre_Equipo","Servicio","Criticidad","Modelo",
      "Ubicacion","N_Fallas","MTBF","MTTR","Disponibilidad",
      "Costo_Total","Costo_COP","Año_Vencimiento","Estado_Disp"]]
)

# Mostrar tabla con estilos condicionales
st.dataframe(
    peores.style
    .format({
        "MTBF":          "{:.0f}h",
        "MTTR":          "{:.1f}h",
        "Disponibilidad":"{:.1f}%",
        "Costo_Total":   "${:,.0f}",     # Costo de mantenimiento acumulado en COP
        "Costo_COP":     "${:,.0f}",     # Valor del equipo en COP
    })
    .background_gradient(
        subset=["Disponibilidad"],
        cmap="RdYlGn", vmin=85, vmax=100   # Verde=alta disponibilidad, Rojo=baja
    )
    .background_gradient(
        subset=["N_Fallas"],
        cmap="Reds", vmin=0, vmax=peores["N_Fallas"].max()
    ),
    use_container_width=True,
    height=480
)

# Exportar la tabla como CSV para reportes de gerencia
csv_out = peores.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Exportar equipos prioritarios (CSV)",
    data=csv_out,
    file_name="equipos_prioritarios.csv",
    mime="text/csv"
)



# PIE DE PÁGINA

st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#1e3a5f;font-size:0.8rem;'>"
    "🏥 Dashboard de Equipos Biomédicos · Ingeniería Clínica · Streamlit + Plotly · Valentín Moreno Vasquez"
    "</p>",
    unsafe_allow_html=True
)
