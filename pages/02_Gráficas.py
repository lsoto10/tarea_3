import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import altair as alt
from utils import cargar_datos, procesar_datos_region, obtener_regiones_disponibles, crear_datos_optimizados, obtener_muestra_censo

# Configuración de página
st.set_page_config(page_title="Gráficas - Censo 2017", page_icon="📈", layout="wide")

# CSS personalizado
st.markdown("""
<style>
    .chart-header {
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sidebar-section {
         background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Título
st.markdown("""
<div class="chart-header">
    <h1>📈 Análisis Estadístico y Gráficas Dinámicas</h1>
    <p>Explora las tendencias demográficas del Censo 2017 a través de visualizaciones interactivas</p>
</div>
""", unsafe_allow_html=True)

# Cargar datos (OPTIMIZADO)
@st.cache_data
def load_chart_data():
    """Carga datos optimizados para gráficas."""
    regiones, comunas, censo = cargar_datos()
    regiones_lista = obtener_regiones_disponibles(regiones)
    
    # Crear datos pre-agregados para mejor rendimiento
    datos_regionales, edad_region, sexo_region, censo_sample = crear_datos_optimizados(censo)
    
    # Unir con nombres de regiones
    if 'region_nombre' in regiones.columns:
        datos_regionales = datos_regionales.merge(
            regiones[['region_id', 'region_nombre']].drop_duplicates(),
            on='region_id', how='left'
        )
        edad_region = edad_region.merge(
            regiones[['region_id', 'region_nombre']].drop_duplicates(),
            on='region_id', how='left'
        )
        sexo_region = sexo_region.merge(
            regiones[['region_id', 'region_nombre']].drop_duplicates(),
            on='region_id', how='left'
        )
    
    return regiones, comunas, censo_sample, regiones_lista, datos_regionales, edad_region, sexo_region

try:
    with st.spinner("🔄 Cargando y procesando datos optimizados..."):
        regiones, comunas, censo_sample, regiones_lista, datos_regionales, edad_region, sexo_region = load_chart_data()
        st.success("✅ Datos cargados exitosamente!")
except Exception as e:
    st.error(f"❌ Error al cargar los datos: {str(e)}")
    st.stop()

# Sidebar para controles
st.sidebar.markdown("""
<div class="sidebar-section" style="background-color: #e3f2fd;">
    <h3>🎛️ Controles de Visualización</h3>
</div>
""", unsafe_allow_html=True)

# Selector de tipo de análisis
tipo_analisis = st.sidebar.selectbox(
    "📊 Tipo de Análisis:",
    [
        "🏛️ Comparación Regional",
        "👥 Distribución Demográfica",
        "🎂 Análisis por Edad",
        "⚖️ Distribución por Sexo"
    ],
    help="Selecciona el tipo de análisis que quieres visualizar"
)

# ===== ANÁLISIS 1: COMPARACIÓN REGIONAL =====
if tipo_analisis == "🏛️ Comparación Regional":
    st.subheader("🏛️ Comparación entre Regiones")
    
    # Métricas generales
    col1, col2, col3 = st.columns(3)
    with col1:
        total_poblacion = datos_regionales['poblacion_total'].sum()
        st.metric("👥 Población Total Nacional", f"{total_poblacion:,}")
    with col2:
        edad_promedio_nacional = datos_regionales['edad_promedio'].mean()
        st.metric("🎂 Edad Promedio Nacional", f"{edad_promedio_nacional:.1f} años")
    with col3:
        pct_mujeres_nacional = datos_regionales['pct_mujeres'].mean()
        st.metric("👩 % Mujeres Nacional", f"{pct_mujeres_nacional:.1f}%")
    
    # Gráfica 1: Población por Región (Barras)
    st.markdown("### 📊 Población Total por Región")
    
    # Preparar datos para gráfica
    datos_grafica = datos_regionales.copy()
    if 'region_nombre' in datos_grafica.columns:
        datos_grafica['region_label'] = datos_grafica['region_nombre']
    else:
        datos_grafica['region_label'] = 'Región ' + datos_grafica['region_id'].astype(str)
    
    # Ordenar por población
    datos_grafica = datos_grafica.sort_values('poblacion_total', ascending=True)
    
    fig_barras = px.bar(
        datos_grafica,
        x='poblacion_total',
        y='region_label',
        orientation='h',
        color='poblacion_total',
        color_continuous_scale='viridis',
        title="Población Total por Región (Censo 2017)",
        labels={'poblacion_total': 'Población Total', 'region_label': 'Región'}
    )
    fig_barras.update_layout(height=600, showlegend=False)
    st.plotly_chart(fig_barras, use_container_width=True)
    
    # Gráfica 2: Scatter Plot - Población vs Edad Promedio
    st.markdown("### 🎯 Relación: Población vs Edad Promedio")
    
    fig_scatter = px.scatter(
        datos_grafica,
        x='poblacion_total',
        y='edad_promedio',
        size='poblacion_total',
        color='pct_mujeres',
        hover_name='region_label',
        title="Población Total vs Edad Promedio por Región",
        labels={
            'poblacion_total': 'Población Total',
            'edad_promedio': 'Edad Promedio (años)',
            'pct_mujeres': '% Mujeres'
        },
        color_continuous_scale='RdYlBu_r'
    )
    fig_scatter.update_layout(height=500)
    st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Gráfica 3: Heatmap de correlaciones
    st.markdown("### 🔥 Matriz de Correlación")
    
    correlaciones = datos_regionales[['poblacion_total', 'edad_promedio', 'pct_mujeres']].corr()
    
    fig_heatmap = px.imshow(
        correlaciones,
        text_auto=True,
        aspect="auto",
        color_continuous_scale='RdBu_r',
        title="Matriz de Correlación entre Variables Demográficas"
    )
    fig_heatmap.update_layout(height=400)
    st.plotly_chart(fig_heatmap, use_container_width=True)

# ===== ANÁLISIS 2: DISTRIBUCIÓN DEMOGRÁFICA =====
elif tipo_analisis == "👥 Distribución Demográfica":
    st.subheader("👥 Distribución Demográfica Nacional")
    
    # Selector de región para análisis específico
    region_seleccionada = st.sidebar.selectbox(
        "🏛️ Región para Análisis Detallado:",
        options=['Nacional'] + list(regiones_lista['region_id']),
        format_func=lambda x: 'Nacional (Todas las regiones)' if x == 'Nacional' 
                    else f"Región {x}" + (f" - {regiones_lista[regiones_lista['region_id']==x]['region_nombre'].iloc[0]}" 
                                        if 'region_nombre' in regiones_lista.columns and len(regiones_lista[regiones_lista['region_id']==x]) > 0 else "")
    )
    
    # Filtrar datos según selección
    if region_seleccionada == 'Nacional':
        censo_filtrado = censo_sample.copy()
        titulo_region = "Nacional"
    else:
        censo_filtrado = censo_sample[censo_sample['region_id'] == region_seleccionada].copy()
        if 'region_nombre' in regiones.columns:
            nombre_region = regiones[regiones['region_id'] == region_seleccionada]['region_nombre'].iloc[0]
            titulo_region = f"Región {region_seleccionada} - {nombre_region}"
        else:
            titulo_region = f"Región {region_seleccionada}"
    
    # Métricas de la región seleccionada
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("👥 Población", f"{len(censo_filtrado):,}")
    with col2:
        edad_prom = censo_filtrado['edad'].mean()
        st.metric("🎂 Edad Promedio", f"{edad_prom:.1f} años")
    with col3:
        pct_mujeres = (censo_filtrado['sexo_cat'] == 'Mujer').sum() / len(censo_filtrado) * 100
        st.metric("👩 % Mujeres", f"{pct_mujeres:.1f}%")
    with col4:
        pct_jovenes = (censo_filtrado['edad'] <= 25).sum() / len(censo_filtrado) * 100
        st.metric("👶 % ≤25 años", f"{pct_jovenes:.1f}%")
    
    # Gráfica 1: Pirámide Poblacional con Altair (más rápida)
    st.markdown(f"### 🔺 Pirámide Poblacional - {titulo_region}")
    
    # Crear datos para la pirámide usando Altair
    censo_piramide = censo_filtrado.copy()
    censo_piramide['grupo_edad'] = pd.cut(
        censo_piramide['edad'],
        bins=list(range(0, 85, 5)) + [100],
        labels=[f"{i}-{i+4}" for i in range(0, 80, 5)] + ["80+"]
    )
    
    # Contar por grupo de edad y sexo
    piramide_data = censo_piramide.groupby(['grupo_edad', 'sexo_cat']).size().reset_index(name='count')
    
    # Para los hombres, hacer los valores negativos para la izquierda
    piramide_data.loc[piramide_data['sexo_cat'] == 'Hombre', 'count'] *= -1
    
    # Crear la pirámide con Altair
    base = alt.Chart(piramide_data).add_selection(
        alt.selection_interval(bind='scales')
    )
    
    piramide_chart = base.mark_bar().encode(
        x=alt.X('count:Q', 
                axis=alt.Axis(title='Población'),
                scale=alt.Scale(domain=[-piramide_data['count'].abs().max() * 1.1, 
                                      piramide_data['count'].abs().max() * 1.1])),
        y=alt.Y('grupo_edad:N', axis=alt.Axis(title='Grupo de Edad')),
        color=alt.Color('sexo_cat:N', 
                       scale=alt.Scale(range=['lightblue', 'pink']),
                       legend=alt.Legend(title="Sexo")),
        tooltip=['grupo_edad', 'sexo_cat', 'count']
    ).properties(
        width=600,
        height=400,
        title=f'Pirámide Poblacional - {titulo_region}'
    )
    
    st.altair_chart(piramide_chart, use_container_width=True)

# ===== ANÁLISIS 3: ANÁLISIS POR EDAD =====
elif tipo_analisis == "🎂 Análisis por Edad":
    st.subheader("🎂 Distribución por Grupos de Edad")
    
    # Crear grupos de edad más detallados
    censo_edad = censo_sample.copy()
    censo_edad['grupo_edad_detallado'] = pd.cut(
        censo_edad['edad'],
        bins=[0, 5, 15, 25, 35, 45, 55, 65, 75, 100],
        labels=['0-4', '5-14', '15-24', '25-34', '35-44', '45-54', '55-64', '65-74', '75+']
    )
    
    # Gráfica 1: Distribución general por edad usando Altair
    st.markdown("### 📊 Distribución de Población por Grupos de Edad")
    
    distribucion_edad = censo_edad['grupo_edad_detallado'].value_counts().reset_index()
    distribucion_edad.columns = ['grupo_edad', 'count']
    
    pie_chart = alt.Chart(distribucion_edad).mark_arc().encode(
        theta=alt.Theta(field="count", type="quantitative"),
        color=alt.Color(field="grupo_edad", type="nominal",
                       scale=alt.Scale(scheme='category20')),
        tooltip=['grupo_edad', 'count']
    ).properties(
        width=400,
        height=400,
        title="Distribución de Población por Grupos de Edad (Nacional)"
    )
    
    st.altair_chart(pie_chart, use_container_width=True)
    
    # Gráfica 2: Distribución de edad por región usando Altair
    st.markdown("### 🏛️ Distribución de Edad por Región")
    
    # Filtros para la visualización
    max_edad = st.sidebar.slider("Edad máxima a mostrar:", 0, 100, 80)
    muestra_size = st.sidebar.slider("Tamaño de muestra (por región):", 100, 10000, 1000)
    
    # Crear muestra para visualización más rápida
    censo_muestra = censo_sample[censo_sample['edad'] <= max_edad].groupby('region_id').apply(
        lambda x: x.sample(min(len(x), muestra_size), random_state=42)
    ).reset_index(drop=True)
    
    # Añadir nombres de región si están disponibles
    if 'region_nombre' in regiones.columns:
        censo_muestra = censo_muestra.merge(
            regiones[['region_id', 'region_nombre']].drop_duplicates(),
            on='region_id', how='left'
        )
        censo_muestra['region_label'] = censo_muestra['region_nombre']
    else:
        censo_muestra['region_label'] = 'Región ' + censo_muestra['region_id'].astype(str)
    
    # Boxplot de edades por región
    boxplot_chart = alt.Chart(censo_muestra).mark_boxplot(extent='min-max').encode(
        x=alt.X('region_label:N', 
                axis=alt.Axis(title='Región', labelAngle=-45)),
        y=alt.Y('edad:Q', axis=alt.Axis(title='Edad (años)')),
        color=alt.Color('region_label:N', legend=None)
    ).properties(
        width=800,
        height=400,
        title="Distribución de Edad por Región (Boxplot)"
    )
    
    st.altair_chart(boxplot_chart, use_container_width=True)

# ===== ANÁLISIS 4: DISTRIBUCIÓN POR SEXO =====
else:  # Distribución por Sexo
    st.subheader("⚖️ Análisis de Distribución por Sexo")
    
    # Métricas generales de género
    total_personas = len(censo_sample)
    total_mujeres = (censo_sample['sexo_cat'] == 'Mujer').sum()
    total_hombres = (censo_sample['sexo_cat'] == 'Hombre').sum()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("👩 Total Mujeres", f"{total_mujeres:,}", f"{total_mujeres/total_personas*100:.1f}%")
    with col2:
        st.metric("👨 Total Hombres", f"{total_hombres:,}", f"{total_hombres/total_personas*100:.1f}%")
    with col3:
        ratio = total_mujeres / total_hombres if total_hombres > 0 else 0
        st.metric("⚖️ Ratio M/H", f"{ratio:.3f}")
    
    # Gráfica 1: Distribución general usando Altair
    st.markdown("### 🥧 Distribución General por Sexo")
    
    distribucion_sexo = censo_sample['sexo_cat'].value_counts().reset_index()
    distribucion_sexo.columns = ['sexo', 'count']
    
    pie_sexo = alt.Chart(distribucion_sexo).mark_arc().encode(
        theta=alt.Theta(field="count", type="quantitative"),
        color=alt.Color(field="sexo", type="nominal",
                       scale=alt.Scale(range=['#87CEEB', '#FF69B4'])),
        tooltip=['sexo', 'count']
    ).properties(
        width=400,
        height=400,
        title="Distribución Nacional por Sexo"
    )
    
    st.altair_chart(pie_sexo, use_container_width=True)
    
    # Gráfica 2: Distribución por región
    st.markdown("### 🏛️ Porcentaje de Mujeres por Región")
    
    pct_mujeres_region = censo_sample.groupby('region_id').apply(
        lambda x: (x['sexo_cat'] == 'Mujer').sum() / len(x) * 100
    ).reset_index(name='pct_mujeres')
    
    # Añadir nombres de región
    if 'region_nombre' in regiones.columns:
        pct_mujeres_region = pct_mujeres_region.merge(
            regiones[['region_id', 'region_nombre']].drop_duplicates(),
            on='region_id', how='left'
        )
        pct_mujeres_region['region_label'] = pct_mujeres_region['region_nombre']
    else:
        pct_mujeres_region['region_label'] = 'Región ' + pct_mujeres_region['region_id'].astype(str)
    
    bar_mujeres = alt.Chart(pct_mujeres_region).mark_bar().encode(
        x=alt.X('region_label:N', 
                axis=alt.Axis(title='Región', labelAngle=-45),
                sort=alt.SortField(field='pct_mujeres', order='ascending')),
        y=alt.Y('pct_mujeres:Q', axis=alt.Axis(title='% Mujeres')),
        color=alt.Color('pct_mujeres:Q', 
                       scale=alt.Scale(scheme='reds'),
                       legend=alt.Legend(title="% Mujeres")),
        tooltip=['region_label', 'pct_mujeres']
    ).properties(
        width=800,
        height=400,
        title="Porcentaje de Mujeres por Región"
    )
    
    st.altair_chart(bar_mujeres, use_container_width=True)
    
    # Gráfica 3: Distribución por edad y sexo
    st.markdown("### 👥 Distribución por Edad y Sexo")
    
    # Crear grupos de edad
    censo_sexo_edad = censo_sample.copy()
    censo_sexo_edad['grupo_edad'] = pd.cut(
        censo_sexo_edad['edad'],
        bins=[0, 18, 30, 45, 65, 100],
        labels=['0-17', '18-29', '30-44', '45-64', '65+']
    )
    
    # Contar por grupo de edad y sexo
    distribucion_edad_sexo = censo_sexo_edad.groupby(['grupo_edad', 'sexo_cat']).size().reset_index(name='count')
    
    bar_edad_sexo = alt.Chart(distribucion_edad_sexo).mark_bar().encode(
        x=alt.X('grupo_edad:N', axis=alt.Axis(title='Grupo de Edad')),
        y=alt.Y('count:Q', axis=alt.Axis(title='Población')),
        color=alt.Color('sexo_cat:N', 
                       scale=alt.Scale(range=['#87CEEB', '#FF69B4']),
                       legend=alt.Legend(title="Sexo")),
        tooltip=['grupo_edad', 'sexo_cat', 'count']
    ).properties(
        width=600,
        height=400,
        title="Distribución por Grupos de Edad y Sexo"
    )
    
    st.altair_chart(bar_edad_sexo, use_container_width=True)

# Footer con información adicional
st.markdown("---")
with st.expander("📊 Información Técnica"):
    st.markdown("""
    **Fuente de Datos:** Censo 2017 - Instituto Nacional de Estadísticas (INE) de Chile
    
    **Herramientas de Visualización:**
    - Altair: Gráficos interactivos optimizados
    - Streamlit: Interfaz web
    - Pandas: Procesamiento de datos
    
    **Variables Analizadas:**
    - Población total por región/comuna
    - Edad promedio y distribución por grupos etarios
    - Distribución por sexo
    - Correlaciones entre variables demográficas
    
    **Optimizaciones:**
    - Uso de muestras para visualizaciones grandes
    - Cache de datos para mejorar rendimiento
    - Visualizaciones interactivas con zoom y filtros
    
    **Nota:** Los datos pueden contener valores faltantes o inconsistencias menores debido al proceso de recolección del censo.
    """)