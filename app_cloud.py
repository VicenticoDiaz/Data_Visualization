import streamlit as st
import pandas as pd
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os
import json
from streamlit.components.v1 import html

# =============================================================================
# Configuración y Estilo Minimalista
# =============================================================================
st.set_page_config(page_title="Dashboard habitacional y demográfico", layout="wide", initial_sidebar_state="expanded")

COLORS = {
    "azul": "#1F4E5B", "mostaza": "#D97706", "rojo": "#BE123C", 
    "verde": "#10B981", "neutro": "#64748B", "blanco": "#ffffff"
}

st.markdown("""
<style>
    .stApp { background-color: #ffffff; font-family: 'Inter', sans-serif; }
    h1, h2, h3, h4 { color: #1F4E5B !important; font-weight: 400 !important; }
    [data-testid="stMetricValue"] { color: #1F4E5B !important; font-weight: 600 !important; }
    [data-testid="stMetricLabel"] { color: #64748B !important; font-size: 1.05rem !important; }
    [data-testid="stSidebar"] { background-color: #f8f9fa !important; border-right: 1px solid #e0e0e0; }
    .stTabs [data-baseweb="tab-list"] { gap: 2rem; border-bottom: 2px solid #F1F5F9; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: transparent; padding-top: 10px; padding-bottom: 10px; color: #64748B; font-weight: 500; font-size: 1.1rem; }
    .stTabs [aria-selected="true"] { color: #1F4E5B !important; border-bottom-color: #1F4E5B !important; font-weight: 600; }
    .block-container { padding-top: 2rem !important; padding-bottom: 3rem !important; padding-left: 5rem !important; padding-right: 5rem !important; }
</style>
""", unsafe_allow_html=True)

LAYOUT_BASE = dict(
    template="plotly_white", width=950, height=750,
    margin=dict(l=60, r=60, t=100, b=120),
    font=dict(family="Inter, Helvetica Neue, Arial, sans-serif", size=15, color="#1F4E5B"),
    title=dict(x=0.5, xanchor="center", font=dict(size=19, color="#1F4E5B")),
    legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5, font=dict(size=14)),
    xaxis=dict(showgrid=True, gridcolor="#F1F5F9"), yaxis=dict(showgrid=True, gridcolor="#F1F5F9"),
)
def titulo(principal, subtitulo):
    return f"<b>{principal}</b><br><span style='font-size:14px;color:#64748B;'>{subtitulo}</span>"

ORDEN_REGIONES = [
    'Arica y Parinacota', 'Tarapacá', 'Antofagasta', 'Atacama', 'Coquimbo',
    'Valparaíso', 'Metropolitana', "O'Higgins", 'Maule', 'Ñuble', 'Biobío',
    'La Araucanía', 'Los Ríos', 'Los Lagos', 'Aysén', 'Magallanes'
]
REG_NAMES = {
    15:'Arica y Parinacota', 1:'Tarapacá', 2:'Antofagasta', 3:'Atacama', 4:'Coquimbo',
    5:'Valparaíso', 13:'Metropolitana', 6:"O'Higgins", 7:'Maule', 16:'Ñuble', 8:'Biobío',
    9:'La Araucanía', 14:'Los Ríos', 10:'Los Lagos', 11:'Aysén', 12:'Magallanes'
}
TIPO_VIV_NAMES = {
    1: 'Casa', 2: 'Departamento', 3: 'Pieza en casa antigua', 4: 'Mediagua/rancho',
    5: 'Móvil', 6: 'Otro tipo particular', 7: 'Vivienda colectiva'
}
COLORES_TENENCIA = {'propia': '#1F4E5B', 'arrendada': '#D97706', 'cedida': '#64748B', 'poseedor': '#BE123C', 'poseedor / ocupante irregular, usufructo u otro': '#BE123C'}
NOMBRES_TENENCIA = {'propia': 'Vivienda propia', 'arrendada': 'Vivienda arrendada', 'cedida': 'Vivienda cedida', 'poseedor': 'Ocupante irregular', 'poseedor / ocupante irregular, usufructo u otro': 'Ocupante irregular / otro'}

COMUNAS_DICT = {"1101": "Iquique", "1107": "Alto Hospicio", "1401": "Pozo Almonte", "1402": "Camiña", "1403": "Colchane", "1404": "Huara", "1405": "Pica", "2101": "Antofagasta", "2102": "Mejillones", "2103": "Sierra Gorda", "2104": "Taltal", "2201": "Calama", "2202": "Ollagüe", "2203": "San Pedro de Atacama", "2301": "Tocopilla", "2302": "María Elena", "3101": "Copiapó", "3102": "Caldera", "3103": "Tierra Amarilla", "3201": "Chañaral", "3202": "Diego de Almagro", "3301": "Vallenar", "3302": "Alto del Carmen", "3303": "Freirina", "3304": "Huasco", "4101": "La Serena", "4102": "Coquimbo", "4103": "Andacollo", "4104": "La Higuera", "4105": "Paiguano", "4106": "Vicuña", "4201": "Illapel", "4202": "Canela", "4203": "Los Vilos", "4204": "Salamanca", "4301": "Ovalle", "4302": "Combarbalá", "4303": "Monte Patria", "4304": "Punitaqui", "4305": "Río Hurtado", "5101": "Valparaíso", "5102": "Casablanca", "5103": "Concón", "5104": "Juan Fernández", "5105": "Puchuncaví", "5107": "Quintero", "5109": "Viña del Mar", "5201": "Isla de Pascua", "5301": "Los Andes", "5302": "Calle Larga", "5303": "Rinconada", "5304": "San Esteban", "5401": "La Ligua", "5402": "Cabildo", "5403": "Papudo", "5404": "Petorca", "5405": "Zapallar", "5501": "Quillota", "5502": "Calera", "5503": "Hijuelas", "5504": "La Cruz", "5506": "Nogales", "5601": "San Antonio", "5602": "Algarrobo", "5603": "Cartagena", "5604": "El Quisco", "5605": "El Tabo", "5606": "Santo Domingo", "5701": "San Felipe", "5702": "Catemu", "5703": "Llaillay", "5704": "Panquehue", "5705": "Putaendo", "5706": "Santa María", "5801": "Quilpué", "5802": "Limache", "5803": "Olmué", "5804": "Villa Alemana", "6101": "Rancagua", "6102": "Codegua", "6103": "Coinco", "6104": "Coltauco", "6105": "Doñihue", "6106": "Graneros", "6107": "Las Cabras", "6108": "Machalí", "6109": "Malloa", "6110": "Mostazal", "6111": "Olivar", "6112": "Peumo", "6113": "Pichidegua", "6114": "Quinta de Tilcoco", "6115": "Rengo", "6116": "Requínoa", "6117": "San Vicente", "6201": "Pichilemu", "6202": "La Estrella", "6203": "Litueche", "6204": "Marchihue", "6205": "Navidad", "6206": "Paredones", "6301": "San Fernando", "6302": "Chépica", "6303": "Chimbarongo", "6304": "Lolol", "6305": "Nancagua", "6306": "Palmilla", "6307": "Peralillo", "6308": "Placilla", "6309": "Pumanque", "6310": "Santa Cruz", "7101": "Talca", "7102": "Constitución", "7103": "Curepto", "7104": "Empedrado", "7105": "Maule", "7106": "Pelarco", "7107": "Pencahue", "7108": "Río Claro", "7109": "San Clemente", "7110": "San Rafael", "7201": "Cauquenes", "7202": "Chanco", "7203": "Pelluhue", "7301": "Curicó", "7302": "Hualañé", "7303": "Licantén", "7304": "Molina", "7305": "Rauco", "7306": "Romeral", "7307": "Sagrada Familia", "7308": "Teno", "7309": "Vichuquén", "7401": "Linares", "7402": "Colbún", "7403": "Longaví", "7404": "Parral", "7405": "Retiro", "7406": "San Javier", "7407": "Villa Alegre", "7408": "Yerbas Buenas", "8101": "Concepción", "8102": "Coronel", "8103": "Chiguayante", "8104": "Florida", "8105": "Hualqui", "8106": "Lota", "8107": "Penco", "8108": "San Pedro de la Paz", "8109": "Santa Juana", "8110": "Talcahuano", "8111": "Tomé", "8112": "Hualpén", "8201": "Lebu", "8202": "Arauco", "8203": "Cañete", "8204": "Contulmo", "8205": "Curanilahue", "8206": "Los Álamos", "8207": "Tirúa", "8301": "Los Ángeles", "8302": "Antuco", "8303": "Cabrero", "8304": "Laja", "8305": "Mulchén", "8306": "Nacimiento", "8307": "Negrete", "8308": "Quilaco", "8309": "Quilleco", "8310": "San Rosendo", "8311": "Santa Bárbara", "8312": "Tucapel", "8313": "Yumbel", "8314": "Alto Biobío", "9101": "Temuco", "9102": "Carahue", "9103": "Cunco", "9104": "Curarrehue", "9105": "Freire", "9106": "Galvarino", "9107": "Gorbea", "9108": "Lautaro", "9109": "Loncoche", "9110": "Melipeuco", "9111": "Nueva Imperial", "9112": "Padre Las Casas", "9113": "Perquenco", "9114": "Pitrufquén", "9115": "Pucón", "9116": "Saavedra", "9117": "Teodoro Schmidt", "9118": "Toltén", "9119": "Vilcún", "9120": "Villarrica", "9121": "Cholchol", "9201": "Angol", "9202": "Collipulli", "9203": "Curacautín", "9204": "Ercilla", "9205": "Lonquimay", "9206": "Los Sauces", "9207": "Lumaco", "9208": "Purén", "9209": "Renaico", "9210": "Traiguén", "9211": "Victoria", "10101": "Puerto Montt", "10102": "Calbuco", "10103": "Cochamó", "10104": "Fresia", "10105": "Frutillar", "10106": "Los Muermos", "10107": "Llanquihue", "10108": "Maullín", "10109": "Puerto Varas", "10201": "Castro", "10202": "Ancud", "10203": "Chonchi", "10204": "Curaco de Vélez", "10205": "Dalcahue", "10206": "Puqueldón", "10207": "Queilén", "10208": "Quellón", "10209": "Quemchi", "10210": "Quinchao", "10301": "Osorno", "10302": "Puerto Octay", "10303": "Purranque", "10304": "Puyehue", "10305": "Río Negro", "10306": "San Juan de la Costa", "10307": "San Pablo", "10401": "Chaitén", "10402": "Futaleufú", "10403": "Hualaihué", "10404": "Palena", "11101": "Coyhaique", "11102": "Lago Verde", "11201": "Aysén", "11202": "Cisnes", "11203": "Guaitecas", "11301": "Cochrane", "11302": "O'Higgins", "11303": "Tortel", "11401": "Chile Chico", "11402": "Río Ibáñez", "12101": "Punta Arenas", "12102": "Laguna Blanca", "12103": "Río Verde", "12104": "San Gregorio", "12201": "Cabo de Hornos", "12202": "Antártica", "12301": "Porvenir", "12302": "Primavera", "12303": "Timaukel", "12401": "Natales", "12402": "Torres del Paine", "13101": "Santiago", "13102": "Cerrillos", "13103": "Cerro Navia", "13104": "Conchalí", "13105": "El Bosque", "13106": "Estación Central", "13107": "Huechuraba", "13108": "Independencia", "13109": "La Cisterna", "13110": "La Florida", "13111": "La Granja", "13112": "La Pintana", "13113": "La Reina", "13114": "Las Condes", "13115": "Lo Barnechea", "13116": "Lo Espejo", "13117": "Lo Prado", "13118": "Macul", "13119": "Maipú", "13120": "Ñuñoa", "13121": "Pedro Aguirre Cerda", "13122": "Peñalolén", "13123": "Providencia", "13124": "Pudahuel", "13125": "Quilicura", "13126": "Quinta Normal", "13127": "Recoleta", "13128": "Renca", "13129": "San Joaquín", "13130": "San Miguel", "13131": "San Ramón", "13132": "Vitacura", "13201": "Puente Alto", "13202": "Pirque", "13203": "San José de Maipo", "13301": "Colina", "13302": "Lampa", "13303": "Tiltil", "13401": "San Bernardo", "13402": "Buin", "13403": "Calera de Tango", "13404": "Paine", "13501": "Melipilla", "13502": "Alhué", "13503": "Curacaví", "13504": "María Pinto", "13505": "San Pedro", "13601": "Talagante", "13602": "El Monte", "13603": "Isla de Maipo", "13604": "Padre Hurtado", "13605": "Peñaflor", "14101": "Valdivia", "14102": "Corral", "14103": "Lanco", "14104": "Los Lagos", "14105": "Máfil", "14106": "Mariquina", "14107": "Paillaco", "14108": "Panguipulli", "14201": "La Unión", "14202": "Futrono", "14203": "Lago Ranco", "14204": "Río Bueno", "15101": "Arica", "15102": "Camarones", "15201": "Putre", "15202": "General Lagos", "16101": "Chillán", "16102": "Bulnes", "16103": "Chillán Viejo", "16104": "El Carmen", "16105": "Pemuco", "16106": "Pinto", "16107": "Quillón", "16108": "San Ignacio", "16109": "Yungay", "16201": "Quirihue", "16202": "Cobquecura", "16203": "Coelemu", "16204": "Ninhue", "16205": "Portezuelo", "16206": "Ranquil", "16207": "Treguaco", "16301": "San Carlos", "16302": "Coihueco", "16303": "Ñiquén", "16304": "San Fabián", "16305": "San Nicolás"}
COMUNAS_DICT = {int(k): v for k, v in COMUNAS_DICT.items()}

# =============================================================================
# Carga de Datos (Polars)
# =============================================================================
@st.cache_data(show_spinner="Cargando datos pre-procesados...")
def load_data():
    df_merged = pd.read_parquet('Data/precomputed_merged.parquet')
    df_merged['region_name'] = pd.Categorical(df_merged['region_name'], categories=ORDEN_REGIONES, ordered=True)
    agg_tipo = pd.read_parquet('Data/precomputed_tipo.parquet')
    agg_sunburst = pd.read_parquet('Data/precomputed_sunburst.parquet')
    return df_merged, agg_tipo, agg_sunburst

df, df_treemap, df_sunburst = load_data()

# =============================================================================
# Sidebar
# =============================================================================
st.sidebar.title("Filtros de análisis")
regiones_disponibles = ["Nacional (todas)"] + ORDEN_REGIONES
region_seleccionada = st.sidebar.selectbox("Seleccione la región", options=regiones_disponibles)

if region_seleccionada == "Nacional (todas)":
    comuna_seleccionada = "Todas"
else:
    comunas_disponibles = ["Todas"] + sorted([str(c) for c in df[df['region_name'] == region_seleccionada]['comuna_name'].unique()])
    comuna_seleccionada = st.sidebar.selectbox("Seleccione la comuna", options=comunas_disponibles)

df_filtrado = df.copy()
if region_seleccionada != "Nacional (todas)":
    df_filtrado = df_filtrado[df_filtrado['region_name'] == region_seleccionada]
if region_seleccionada != "Nacional (todas)" and comuna_seleccionada != "Todas":
    df_filtrado = df_filtrado[df_filtrado['comuna_name'] == comuna_seleccionada]

st.title("Dinámica habitacional y demográfica en Chile")
st.markdown("<br>", unsafe_allow_html=True)
t_viv = df_filtrado['Total_Viviendas'].sum()
t_ocup = (df_filtrado['Ocupadas'].sum() / t_viv) * 100 if t_viv > 0 else 0
t_vac = (df_filtrado['De_Vacaciones'].sum() / t_viv) * 100 if t_viv > 0 else 0
t_des = (df_filtrado['Desocupadas'].sum() / t_viv) * 100 if t_viv > 0 else 0
t_prec = (df_filtrado['Viviendas_Precarias'].sum() / df_filtrado['Viviendas_Ocup_Presentes'].sum()) * 100 if df_filtrado['Viviendas_Ocup_Presentes'].sum() > 0 else 0

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total viviendas", f"{t_viv:,.0f}".replace(',', '.'))
c2.metric("Ocupadas", f"{t_ocup:.1f}%")
c3.metric("De vacaciones", f"{t_vac:.1f}%")
c4.metric("En venta/abandono", f"{t_des:.1f}%")
c5.metric("Materialidad precaria", f"{t_prec:.1f}%")

st.markdown("<br>", unsafe_allow_html=True)

# =============================================================================
# Pestañas (Tabs)
# =============================================================================
t1, t2, t3, t4 = st.tabs([
    "Dinámica demográfica", "Déficit y precariedad", "Calidad y tipos de vivienda", "Tenencia y regímenes (Casen)"
])

# -----------------------------------------------------------------------------
# TAB 1: Demográfica
# -----------------------------------------------------------------------------
with t1:
    st.markdown("### Composición y fenómenos demográficos")
    
    # KPI Resumen Tab 1
    with st.expander("📌 Resumen demográfico de tu selección", expanded=True):
        sc1, sc2, sc3 = st.columns(3)
        prom_env = df_filtrado['indice_envejecimiento'].mean()
        sc1.metric("Viviendas sin uso principal", f"{(df_filtrado['De_Vacaciones'].sum() + df_filtrado['Desocupadas'].sum()):,.0f}".replace(',','.'))
        sc2.metric("Índice de envejecimiento (promedio)", f"{prom_env:.1f}" if pd.notna(prom_env) else "N/A")
        sc3.metric("Comunas analizadas", len(df_filtrado['comuna_name'].unique()))

    col1, col2 = st.columns(2)
    labels = ['Ocupadas', 'De vacaciones', 'Desocupadas / venta / otro']
    values = [df_filtrado['Ocupadas'].sum(), df_filtrado['De_Vacaciones'].sum(), df_filtrado['Desocupadas'].sum()]
    fig_donut = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.6, marker=dict(colors=[COLORS['azul'], COLORS['mostaza'], COLORS['rojo']]), textinfo='percent')])
    fig_donut.update_layout(**LAYOUT_BASE)
    fig_donut.update_layout(title_text=titulo("Estado de ocupación", "Distribución general | Censo 2024"))
    col1.plotly_chart(fig_donut, use_container_width=True)
    
    if region_seleccionada == "Nacional (todas)":
        df_bars = df_filtrado.groupby('region_name', observed=True)[['Ocupadas', 'De_Vacaciones', 'Desocupadas', 'Total_Viviendas']].sum().reset_index()
        df_bars = df_bars.sort_values('region_name')
        x_col = 'region_name'
        t_bars = "Composición territorial por región"
    else:
        df_bars = df_filtrado.groupby('comuna_name', observed=True)[['Ocupadas', 'De_Vacaciones', 'Desocupadas', 'Total_Viviendas']].sum().reset_index()
        x_col = 'comuna_name'
        t_bars = f"Composición territorial - {region_seleccionada}"
        
    df_bars['% Ocupadas'] = df_bars['Ocupadas'] / df_bars['Total_Viviendas'] * 100
    df_bars['% Vacaciones'] = df_bars['De_Vacaciones'] / df_bars['Total_Viviendas'] * 100
    df_bars['% Desocupadas'] = df_bars['Desocupadas'] / df_bars['Total_Viviendas'] * 100

    fig_bars = go.Figure()
    fig_bars.add_trace(go.Bar(x=df_bars[x_col], y=df_bars['% Ocupadas'], name='Ocupadas', marker_color=COLORS['azul']))
    fig_bars.add_trace(go.Bar(x=df_bars[x_col], y=df_bars['% Vacaciones'], name='Vacaciones', marker_color=COLORS['mostaza']))
    fig_bars.add_trace(go.Bar(x=df_bars[x_col], y=df_bars['% Desocupadas'], name='Desocupadas', marker_color=COLORS['rojo']))
    fig_bars.update_layout(**LAYOUT_BASE)
    fig_bars.update_layout(barmode='stack', title_text=titulo(t_bars, "Al 100% | Censo 2024"), yaxis=dict(title="%"))
    col2.plotly_chart(fig_bars, use_container_width=True)

    df_scatter = df_filtrado.copy()
    df_scatter['Tasa_No_Habitual'] = ((df_scatter['De_Vacaciones'] + df_scatter['Desocupadas']) / df_scatter['Total_Viviendas']) * 100
    df_scatter = df_scatter.dropna(subset=['indice_envejecimiento', 'Tasa_No_Habitual'])
    
    if region_seleccionada == "Nacional (todas)":
        df_sc = df_scatter.groupby('region_name', observed=True).agg({'Tasa_No_Habitual':'mean', 'indice_envejecimiento':'mean', 'Total_Viviendas':'sum'}).reset_index()
        c_by = 'region_name'
    else:
        df_sc = df_scatter
        c_by = 'comuna_name'

    fig_sc = px.scatter(df_sc, x='indice_envejecimiento', y='Tasa_No_Habitual', size='Total_Viviendas', color=c_by, hover_name=c_by, title="Impacto demográfico", labels={'region_name': 'Regiones', 'comuna_name': 'Comunas'})
    fig_sc.update_layout(**LAYOUT_BASE)
    fig_sc.update_layout(title_text=titulo("Envejecimiento vs viviendas sin uso principal", "Censo 2024"), xaxis=dict(title="Índice de envejecimiento"), yaxis=dict(title="% Viviendas (vacaciones + desocupadas)"))
    st.plotly_chart(fig_sc, use_container_width=True)

# -----------------------------------------------------------------------------
# TAB 2: Déficit y Precariedad
# -----------------------------------------------------------------------------
with t2:
    st.markdown("### Déficit de materiales y servicios básicos")
    
    # KPI Resumen Tab 2
    with st.expander("📌 Resumen de precariedad multidimensional", expanded=True):
        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("Hogares sin agua potable", f"{df_filtrado['Deficit_Agua'].sum():,.0f}".replace(',','.'))
        sc2.metric("Hogares sin saneamiento", f"{df_filtrado['Deficit_Saneamiento'].sum():,.0f}".replace(',','.'))
        sc3.metric("Hogares sin red eléctrica", f"{df_filtrado['Deficit_Elect'].sum():,.0f}".replace(',','.'))

    # Parallel Coordinates (Radar Alternativo Mejorado)
    df_def = df_filtrado.groupby('region_name', observed=True)[['Deficit_Agua', 'Deficit_Saneamiento', 'Deficit_Elect', 'Viviendas_Precarias', 'Viviendas_Ocup_Presentes']].sum().reset_index()
    df_def['% Agua'] = df_def['Deficit_Agua'] / df_def['Viviendas_Ocup_Presentes'] * 100
    df_def['% San.'] = df_def['Deficit_Saneamiento'] / df_def['Viviendas_Ocup_Presentes'] * 100
    df_def['% Elect.'] = df_def['Deficit_Elect'] / df_def['Viviendas_Ocup_Presentes'] * 100
    df_def['% Material'] = df_def['Viviendas_Precarias'] / df_def['Viviendas_Ocup_Presentes'] * 100
    df_def = df_def.dropna()
    df_def['region_id'] = range(len(df_def))
    # Índice de poliprecariedad para el color
    df_def['indice_malo'] = df_def['% Agua'] + df_def['% San.'] + df_def['% Elect.'] + df_def['% Material']
    
    # Reemplazar Parcoords por Scatter (Lineas) para permitir Tooltips y Leyenda
    fig_par = go.Figure()
    
    # Categorías del eje X
    categorias = ['% Agua', '% San.', '% Elect.', '% Material']
    
    # Ordenar regiones por el índice malo para que la leyenda y colores tengan sentido
    df_def = df_def.sort_values('indice_malo', ascending=False)
    
    import plotly.colors as pcolors
    if len(df_def) > 1:
        color_vals = [i/(len(df_def)-1) for i in range(len(df_def))]
    else:
        color_vals = [0.5]
    colors = pcolors.sample_colorscale('RdYlGn_r', color_vals)
    
    for i, (idx, row) in enumerate(df_def.iterrows()):
        fig_par.add_trace(go.Scatter(
            x=categorias,
            y=[row['% Agua'], row['% San.'], row['% Elect.'], row['% Material']],
            mode='lines+markers',
            name=row['region_name'],
            line=dict(width=3, color=colors[i]),
            marker=dict(size=8),
            hovertemplate="<b>" + row['region_name'] + "</b><br>%{x}: %{y:.2f}%<extra></extra>"
        ))
        
    fig_par.update_layout(**LAYOUT_BASE)
    fig_par.update_layout(
        title_text=titulo("Perfil multidimensional de precariedad", "Porcentaje de viviendas con carencias por región | Censo 2024"),
        yaxis=dict(title="Porcentaje de hogares (%)", showgrid=True),
        xaxis=dict(title="", showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5, font=dict(size=12)),
        margin=dict(t=120, b=100)
    )
    st.plotly_chart(fig_par, use_container_width=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    # Dotplot (grafico_1)
    if region_seleccionada == "Nacional (todas)":
        df_mat = df_filtrado.groupby('region_name', observed=True)[['Viviendas_Precarias', 'Viviendas_Ocup_Presentes']].sum().reset_index()
        y_c = 'region_name'
    else:
        df_mat = df_filtrado.groupby('comuna_name', observed=True)[['Viviendas_Precarias', 'Viviendas_Ocup_Presentes']].sum().reset_index()
        y_c = 'comuna_name'
        
    df_mat['tasa_precaria'] = (df_mat['Viviendas_Precarias'] / df_mat['Viviendas_Ocup_Presentes']) * 100
    df_mat = df_mat.dropna().sort_values('tasa_precaria')
    
    if len(df_mat) > 0:
        prom = df_mat['tasa_precaria'].mean()
        fig_dp = go.Figure()
        for _, row in df_mat.iterrows():
            fig_dp.add_trace(go.Scatter(x=[0, row["tasa_precaria"]], y=[row[y_c], row[y_c]], mode="lines", line=dict(color="#CBD5E1", width=1.5), showlegend=False))
        mask_above = df_mat["tasa_precaria"] > prom
        
        def add_p(mask, name, color):
            if mask.any():
                fig_dp.add_trace(go.Scatter(y=df_mat.loc[mask, y_c], x=df_mat.loc[mask, "tasa_precaria"], mode="markers+text", name=name, marker=dict(size=12, color=color, line=dict(color="white", width=1.5)), text=df_mat.loc[mask, "tasa_precaria"].apply(lambda v: f"{v:.1f}%"), textposition="middle right", textfont=dict(color=color)))
        add_p(mask_above, "Sobre el promedio", COLORS['rojo'])
        add_p(~mask_above, "Bajo el promedio", COLORS['azul'])
        fig_dp.add_vline(x=prom, line_dash="dash", line_color=COLORS["mostaza"], line_width=2)
        fig_dp.update_layout(**LAYOUT_BASE)
        fig_dp.update_layout(title_text=titulo("Déficit de materiales de las viviendas", "Porcentaje con materialidad precaria | Censo 2024"), xaxis=dict(title="Tasa (%)"), yaxis=dict(title=""), height=max(600, len(df_mat)*30))
        st.plotly_chart(fig_dp, use_container_width=True)

    for f in ['grafico_7.html', 'grafico_8.html', 'grafico_9.html']:
        if os.path.exists(f):
            st.markdown("<hr>", unsafe_allow_html=True)
            with open(f, 'r', encoding='utf-8') as h:
                html(h.read(), height=750, scrolling=False)

# -----------------------------------------------------------------------------
# TAB 3: Calidad y Tipos de Vivienda
# -----------------------------------------------------------------------------
with t3:
    st.markdown("### Tipología y estructura habitacional")
    
    with st.expander("📌 Resumen estructural (a nivel país)", expanded=True):
        st.write("La jerarquía de distribución del parque habitacional nos indica las prioridades estructurales.")
        
        df_sb = df_sunburst.copy()
        df_sb['area_name'] = df_sb['area'].map({1: 'Urbano', 2: 'Rural'}).fillna('Desconocido')
        
        # KPIs globales
        tot_urb = df_sb[df_sb['area_name'] == 'Urbano']['count'].sum()
        tot_rur = df_sb[df_sb['area_name'] == 'Rural']['count'].sum()
        
        k1, k2 = st.columns(2)
        k1.metric("Viviendas Urbanas", f"{tot_urb:,.0f}".replace(',','.'))
        k2.metric("Viviendas Rurales", f"{tot_rur:,.0f}".replace(',','.'))
    
    # Sunburst Chart
    df_sb['tipo_name'] = df_sb['p2_tipo_vivienda'].map(TIPO_VIV_NAMES).fillna('Desconocido')
    df_sb['ocupa_name'] = df_sb['p3b_estado_ocupacion'].map({1:'Ocupada', 2:'Ocupada (ausente)', 8:'Vacaciones', 6:'Venta', 7:'Arriendo', 9:'Abandonada', 10:'Otro'}).fillna('Otro')
    
    fig_sb = px.sunburst(df_sb, path=['area_name', 'tipo_name', 'ocupa_name'], values='count', color='area_name', color_discrete_map={'Urbano': COLORS['azul'], 'Rural': COLORS['mostaza'], 'Desconocido': COLORS['neutro']})
    fig_sb.update_layout(**LAYOUT_BASE)
    fig_sb.update_layout(title_text=titulo("Jerarquía de ocupación por área y tipo de vivienda", "Gráfico solar interactivo | Haz clic en los anillos para hacer zoom | Censo 2024"))
    st.plotly_chart(fig_sb, use_container_width=True)
    
    # Treemap (grafico_6)
    fig_tm = go.Figure(go.Treemap(
        labels=df_treemap["tipo_name"], parents=[""] * len(df_treemap), values=np.log1p(df_treemap["n"]),
        customdata=df_treemap[["n", "tasa_precaria"]].values,
        marker=dict(colors=df_treemap["tasa_precaria"], cmin=0, cmax=100, colorscale=[[0, "#E2E8F0"], [1, COLORS["rojo"]]], colorbar=dict(title="Precariedad (%)")),
        texttemplate="<b>%{label}</b><br>%{customdata[0]:,.0f} viv<br>%{customdata[1]:.1f}% precaria"
    ))
    fig_tm.update_layout(**LAYOUT_BASE)
    fig_tm.update_layout(title_text=titulo("Déficit de materiales por tipo de vivienda", "Censo 2024"))
    st.plotly_chart(fig_tm, use_container_width=True)
    
    if os.path.exists('grafico_4.html'):
        with open('grafico_4.html', 'r', encoding='utf-8') as h:
            html(h.read(), height=750, scrolling=False)

# -----------------------------------------------------------------------------
# TAB 4: Tenencia (CASEN)
# -----------------------------------------------------------------------------
with t4:
    st.markdown("### Régimen de tenencia y accesibilidad")
    
    with st.expander("📌 Resumen Casen 2024", expanded=True):
        st.write("**Migración y propiedad:** Los nacidos en Chile superan por abismo en vivienda propia a los migrantes (60% vs 14%). **Tendencia histórica:** El acceso a la propiedad ha decaído sostenidamente desde 2006, siendo reemplazado por el arriendo.")
    
    if os.path.exists('Data/Casen/hoja_1.csv'):
        df_casen = pd.read_csv('Data/Casen/hoja_1.csv', skiprows=4, nrows=4)
        df_casen.columns = ['categoria', 'desagregacion', '2006', '2009', '2011', '2013', '2015', '2017', '2020', '2022', '2024']
        años = ['2006', '2009', '2011', '2013', '2015', '2017', '2020', '2022', '2024']
        fig_ev = go.Figure()
        for _, row in df_casen.iterrows():
            cat = row['categoria']
            fig_ev.add_trace(go.Scatter(x=años, y=[row[a] for a in años], mode='lines+markers', name=NOMBRES_TENENCIA.get(cat, cat), line=dict(color=COLORES_TENENCIA.get(cat, '#999999'), width=3.5)))
        fig_ev.update_layout(**LAYOUT_BASE)
        fig_ev.update_layout(
            title_text=titulo("Evolución tenencia (2006-2024)", "Casen 2006-2024"), 
            xaxis_title='Año', yaxis_title='% de hogares', hovermode='x unified',
            legend=dict(orientation='h', yanchor='top', y=-0.15, xanchor='center', x=0.5, font=dict(size=13)),
            margin=dict(b=150)
        )
        st.plotly_chart(fig_ev, use_container_width=True)
    
    if os.path.exists('Data/Casen/hoja_8.csv'):
        df_q = pd.read_csv('Data/Casen/hoja_8.csv', skiprows=4, nrows=20)
        df_q.columns = ['cat', 'desag', '2006', '2009', '2011', '2013', '2015', '2017', '2020', '2022', '2024']
        df_2024 = df_q[df_q['cat'].isin(['propia', 'arrendada', 'cedida','poseedor',  'poseedor / ocupante irregular, usufructo u otro'])].copy()
        df_2024['desag'] = df_2024['desag'].str.replace('Quintil', 'quintil')
        quin = ['Primer quintil', 'Segundo quintil', 'Tercer quintil', 'Cuarto quintil', 'Quinto quintil']
        df_2024 = df_2024[df_2024['desag'].isin(quin)]
        df_2024['desag'] = pd.Categorical(df_2024['desag'], categories=quin, ordered=True)
        df_2024 = df_2024.sort_values('desag')
        
        fig_q = go.Figure()
        for cat in ['propia', 'arrendada', 'cedida','poseedor','poseedor / ocupante irregular, usufructo u otro']:
            datos = df_2024[df_2024['cat'] == cat]
            if len(datos)>0:
                fig_q.add_trace(go.Bar(name=NOMBRES_TENENCIA.get(cat, cat), x=datos['desag'], y=datos['2024'], marker_color=COLORES_TENENCIA.get(cat, '#000')))
        fig_q.update_layout(**LAYOUT_BASE)
        fig_q.update_layout(barmode='stack', title_text=titulo("Estructura del régimen de tenencia según quintil", "Casen 2024"), yaxis_title="% de hogares", legend=dict(orientation='h', yanchor='top', y=-0.15, xanchor='center', x=0.5, font=dict(size=12)), margin=dict(b=150))
        st.plotly_chart(fig_q, use_container_width=True)

    labels_pie = ['Vivienda propia', 'Vivienda arrendada', 'Vivienda cedida', 'Ocupación irregular / otro']
    chi_vals = [59.96, 22.13, 13.83, 4.08]
    ext_vals = [14.04, 75.73, 4.64, 5.59]
    col_pie = [COLORS['azul'], COLORS['mostaza'], COLORS['neutro'], COLORS['rojo']]
    
    from plotly.subplots import make_subplots
    fig_nac = make_subplots(rows=1, cols=2, specs=[[{'type': 'domain'}, {'type': 'domain'}]], subplot_titles=['<b>Jefes hogar nacidos en Chile</b>', '<b>Nacidos fuera de Chile</b>'])
    fig_nac.add_trace(go.Pie(labels=labels_pie, values=chi_vals, name='Chile', hole=0.45, marker=dict(colors=col_pie, line=dict(color='white', width=2)), textinfo='percent', textposition='inside', sort=False), 1, 1)
    fig_nac.add_trace(go.Pie(labels=labels_pie, values=ext_vals, name='Exterior', hole=0.45, marker=dict(colors=col_pie, line=dict(color='white', width=2)), textinfo='percent', textposition='inside', sort=False), 1, 2)
    fig_nac.update_layout(**LAYOUT_BASE)
    fig_nac.update_layout(
        title_text=titulo("Fractura habitacional migrante", "Casen 2024"),
        legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5, font=dict(size=13), traceorder="normal"),
        margin=dict(t=120, b=120)
    )
    st.plotly_chart(fig_nac, use_container_width=True)
