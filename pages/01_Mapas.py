import streamlit as st
import folium
import geopandas as gpd
import pandas as pd
from streamlit_folium import st_folium
from utils import cargar_datos, procesar_datos_comuna, procesar_datos_region, obtener_regiones_disponibles, crear_datos_optimizados, obtener_muestra_censo, preparar_datos_mapa_ligeros, optimizar_geometrias_para_web

# Configuración de página
st.set_page_config(page_title="Mapas - Censo 2017", page_icon="🗺️", layout="wide")

# CSS personalizado
st.markdown("""
<style>
    .map-header {
        background: linear-gradient(90deg, #2196F3, #21CBF3);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sidebar-section {
        background: linear-gradient(90deg, #2196F3, #21CBF3);
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Título
st.markdown("""
<div class="map-header">
    <h1>🗺️ Mapas Coropléticos Interactivos</h1>
    <p>Explora los datos del Censo 2017 a través de visualizaciones geográficas</p>
</div>
""", unsafe_allow_html=True)

# Cargar datos (OPTIMIZADO)
@st.cache_data
def load_and_process_data():
    """Carga datos optimizados para mapas."""
    regiones, comunas, censo = cargar_datos()
    regiones_lista = obtener_regiones_disponibles(regiones)
    
    # Crear datos pre-agregados para mejor rendimiento
    datos_regionales, edad_region, sexo_region, censo_sample = crear_datos_optimizados(censo)
    
    return regiones, comunas, censo_sample, regiones_lista, datos_regionales

try:
    with st.spinner("🔄 Cargando datos geográficos optimizados..."):
        regiones, comunas, censo_sample, regiones_lista, datos_regionales = load_and_process_data()
        st.success("✅ Datos geográficos cargados exitosamente!")
        
except Exception as e:
    st.error(f"❌ Error al cargar los datos: {str(e)}")
    st.stop()

# Sidebar para controles
st.sidebar.markdown("""
<div class="sidebar-section">
    <h3>⚙️ Configuración del Mapa</h3>
</div>
""", unsafe_allow_html=True)

# Selector de nivel geográfico
nivel_geografico = st.sidebar.radio(
    "📍 Nivel Geográfico:",
    ["🏛️ Regional", "🏘️ Comunal"],
    help="Selecciona si quieres ver datos por región o por comuna"
)

# Variables disponibles
variables_regionales = {
    'poblacion_total': '👥 Población Total',
    'edad_promedio': '🎂 Edad Promedio',
    'pct_mujeres': '👩 Porcentaje de Mujeres'
}

variables_comunales = {
    'poblacion_total': '👥 Población Total',
    'densidad_poblacional': '🏘️ Densidad Poblacional',
    'edad_promedio': '🎂 Edad Promedio',
    'pct_mujeres': '👩 Porcentaje de Mujeres'
}

if nivel_geografico == "🏛️ Regional":
    # Selector de variable para nivel regional
    variable_seleccionada = st.sidebar.selectbox(
        "📊 Variable a Visualizar:",
        options=list(variables_regionales.keys()),
        format_func=lambda x: variables_regionales[x],
        help="Selecciona la variable que quieres visualizar en el mapa"
    )
    
    # Usar datos regionales pre-agregados (OPTIMIZADO)
    datos_procesados = datos_regionales.copy()
    
    # Unir con geometrías
    mapa_gdf = regiones.merge(datos_procesados, left_on='region_id', right_on='region_id', how='left')
    
    # Optimizar para web con funciones específicas
    campos_necesarios = ['poblacion_total', 'edad_promedio', 'pct_mujeres']
    mapa_gdf = preparar_datos_mapa_ligeros(mapa_gdf, campos_necesarios, max_registros=20)
    
    # Configuración del mapa
    center_lat, center_lon = -35.0, -71.0
    zoom_start = 4
    
else:  # Comunal
    # Selector de región para filtrar comunas
    if 'region_nombre' in regiones.columns:
        region_opciones = dict(zip(regiones_lista['region_id'], regiones_lista['region_nombre']))
        region_seleccionada = st.sidebar.selectbox(
            "🏛️ Región:",
            options=list(region_opciones.keys()),
            format_func=lambda x: f"{x} - {region_opciones[x]}",
            help="Selecciona la región para visualizar sus comunas"
        )
    else:
        region_seleccionada = st.sidebar.selectbox(
            "🏛️ Región:",
            options=regiones_lista['region_id'].tolist(),
            help="Selecciona la región para visualizar sus comunas"
        )
    
    # Selector de variable para nivel comunal
    variable_seleccionada = st.sidebar.selectbox(
        "📊 Variable a Visualizar:",
        options=list(variables_comunales.keys()),
        format_func=lambda x: variables_comunales[x],
        help="Selecciona la variable que quieres visualizar en el mapa"
    )
    
    # Filtrar comunas por región
    comunas_filtradas = comunas[comunas['region_id_com'] == region_seleccionada].copy()
    
    # Procesar datos comunales (OPTIMIZADO)
    datos_procesados = procesar_datos_comuna(censo_sample, region_seleccionada)
    
    # Calcular densidad poblacional si es necesario
    if variable_seleccionada == 'densidad_poblacional':
        # Calcular área en km²
        comunas_filtradas['area_km2'] = comunas_filtradas.to_crs('EPSG:3857').geometry.area / 1e6
        datos_procesados = datos_procesados.merge(
            comunas_filtradas[['comuna_id', 'area_km2']], 
            on='comuna_id', 
            how='left'
        )
        datos_procesados['densidad_poblacional'] = datos_procesados['poblacion_total'] / datos_procesados['area_km2']
        datos_procesados['densidad_poblacional'] = datos_procesados['densidad_poblacional'].fillna(0)
    
    # Unir con geometrías
    mapa_gdf = comunas_filtradas.merge(datos_procesados, on='comuna_id', how='left')
    
    # Optimizar para web - limitar registros en vista comunal
    campos_necesarios = ['poblacion_total', 'edad_promedio', 'pct_mujeres']
    if variable_seleccionada == 'densidad_poblacional':
        campos_necesarios.append('densidad_poblacional')
    
    # Limitar comunas a máximo 50 para evitar problemas de tamaño
    mapa_gdf = preparar_datos_mapa_ligeros(mapa_gdf, campos_necesarios, max_registros=50)
    
    # Configuración del mapa centrado en la región
    if len(mapa_gdf) > 0:
        bounds = mapa_gdf.total_bounds
        center_lat = (bounds[1] + bounds[3]) / 2
        center_lon = (bounds[0] + bounds[2]) / 2
        zoom_start = 8
    else:
        center_lat, center_lon = -35.0, -71.0
        zoom_start = 6

# Configuración de colores
esquemas_color = {
    'poblacion_total': 'YlOrRd',
    'densidad_poblacional': 'Reds',
    'edad_promedio': 'YlGnBu',
    'pct_mujeres': 'RdPu'
}

# Sidebar adicional con información
st.sidebar.markdown("---")
st.sidebar.markdown("""
<div class="sidebar-section">
    <h4>ℹ️ Información</h4>
    <p><strong>Datos:</strong> Censo 2017 (INE)</p>
    <p><strong>Proyección:</strong> WGS84 (EPSG:4326)</p>
</div>
""", unsafe_allow_html=True)

# Mostrar estadísticas
if len(mapa_gdf) > 0 and variable_seleccionada in mapa_gdf.columns:
    col1, col2, col3, col4 = st.columns(4)
    
    data_serie = mapa_gdf[variable_seleccionada].dropna()
    
    if len(data_serie) > 0:
        with col1:
            st.metric("📊 Mínimo", f"{data_serie.min():.1f}")
        with col2:
            st.metric("📈 Máximo", f"{data_serie.max():.1f}")
        with col3:
            st.metric("📊 Promedio", f"{data_serie.mean():.1f}")
        with col4:
            st.metric("🎯 Mediana", f"{data_serie.median():.1f}")
    else:
        st.warning("⚠️ No hay datos válidos para mostrar estadísticas.")

# Crear el mapa
if len(mapa_gdf) > 0 and variable_seleccionada in mapa_gdf.columns and mapa_gdf[variable_seleccionada].notna().sum() > 0:
    try:
        # Mostrar información sobre optimización
        st.info(f"🎯 Datos optimizados: {len(mapa_gdf)} registros | Geometrías simplificadas para mejor rendimiento")
        
        # Crear mapa base
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=zoom_start,
            tiles='CartoDB positron'
        )
        
        # Preparar datos para el choropleth - solo los campos necesarios
        choropleth_data = mapa_gdf[['comuna_id' if 'comuna_id' in mapa_gdf.columns else 'region_id', variable_seleccionada]].copy()
        
        # Crear GeoJSON simplificado solo con las propiedades necesarias
        geojson_data = mapa_gdf[['geometry', 'comuna_id' if 'comuna_id' in mapa_gdf.columns else 'region_id']].copy()
        
        # Añadir capa coroplética
        folium.Choropleth(
            geo_data=geojson_data.to_json(),
            data=choropleth_data,
            columns=['comuna_id' if 'comuna_id' in mapa_gdf.columns else 'region_id', variable_seleccionada],
            key_on='feature.properties.comuna_id' if 'comuna_id' in mapa_gdf.columns else 'feature.properties.region_id',
            fill_color=esquemas_color.get(variable_seleccionada, 'YlOrRd'),
            fill_opacity=0.7,
            line_opacity=0.2,
            legend_name=variables_regionales.get(variable_seleccionada, variables_comunales.get(variable_seleccionada, variable_seleccionada)),
            nan_fill_color="lightgray",
            nan_fill_opacity=0.4
        ).add_to(m)
        
        # Crear tooltips con datos mínimos para reducir tamaño
        tooltip_gdf = mapa_gdf.copy()
        
        # Añadir tooltips informativos (con datos limitados)
        if nivel_geografico == "🏛️ Regional":
            if 'region_nombre' in tooltip_gdf.columns:
                tooltip_fields = ['region_nombre', 'poblacion_total', 'edad_promedio']
                tooltip_aliases = ['Región:', 'Población:', 'Edad Promedio:']
            else:
                tooltip_fields = ['region_id', 'poblacion_total', 'edad_promedio']
                tooltip_aliases = ['Región ID:', 'Población:', 'Edad Promedio:']
        else:
            if 'comuna_nombre' in tooltip_gdf.columns:
                tooltip_fields = ['comuna_nombre', 'poblacion_total', 'edad_promedio']
                tooltip_aliases = ['Comuna:', 'Población:', 'Edad Promedio:']
            else:
                tooltip_fields = ['comuna_id', 'poblacion_total', 'edad_promedio']
                tooltip_aliases = ['Comuna ID:', 'Población:', 'Edad Promedio:']
        
        # Filtrar campos que existen y crear GeoJSON minimal para tooltips
        tooltip_fields_existentes = [f for f in tooltip_fields if f in tooltip_gdf.columns]
        tooltip_aliases_existentes = [tooltip_aliases[i] for i, f in enumerate(tooltip_fields) if f in tooltip_gdf.columns]
        
        if tooltip_fields_existentes:
            # Crear un GeoDataFrame minimal solo para tooltips
            tooltip_columns = ['geometry'] + tooltip_fields_existentes
            tooltip_minimal = tooltip_gdf[tooltip_columns].copy()
            
            folium.GeoJson(
                tooltip_minimal.to_json(),
                style_function=lambda feature: {
                    'fillColor': 'transparent',
                    'color': 'black',
                    'weight': 1,
                    'fillOpacity': 0
                },
                highlight_function=lambda x: {'weight': 3, 'color': 'red'},
                tooltip=folium.features.GeoJsonTooltip(
                    fields=tooltip_fields_existentes,
                    aliases=tooltip_aliases_existentes,
                    localize=True,
                    sticky=False,
                    labels=True,
                    style="""
                        background-color: white;
                        border: 2px solid black;
                        border-radius: 3px;
                        box-shadow: 3px;
                    """
                )
            ).add_to(m)
        
        # Mostrar el mapa con tamaño optimizado
        map_data = st_folium(m, width=1400, height=600, returned_objects=["last_object_clicked"])
        
        # Información adicional basada en clicks
        if map_data['last_object_clicked']:
            st.subheader("📍 Información Detallada")
            clicked_data = map_data['last_object_clicked']
            if 'properties' in clicked_data:
                props = clicked_data['properties']
                
                col1, col2 = st.columns(2)
                with col1:
                    for key, value in props.items():
                        if key not in ['geometry'] and value is not None:
                            st.write(f"**{key}:** {value}")
                            
    except Exception as e:
        st.error(f"❌ Error al crear el mapa: {str(e)}")
        st.error(f"💡 Detalles del error: {type(e).__name__}")
        st.info("🔧 Intentando optimización adicional...")
        
        # Intentar con geometrías aún más simplificadas
        try:
            mapa_gdf_ultra_simple = simplify_geometries(mapa_gdf, tolerance=0.05)
            st.warning(f"⚡ Usando geometrías ultra-simplificadas ({len(mapa_gdf_ultra_simple)} registros)")
            
            # Crear mapa básico sin tooltips complejos
            m_simple = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=zoom_start,
                tiles='CartoDB positron'
            )
            
            # Solo choropleth básico
            folium.Choropleth(
                geo_data=mapa_gdf_ultra_simple[['geometry', 'comuna_id' if 'comuna_id' in mapa_gdf_ultra_simple.columns else 'region_id']].to_json(),
                data=mapa_gdf_ultra_simple,
                columns=['comuna_id' if 'comuna_id' in mapa_gdf_ultra_simple.columns else 'region_id', variable_seleccionada],
                key_on='feature.properties.comuna_id' if 'comuna_id' in mapa_gdf_ultra_simple.columns else 'feature.properties.region_id',
                fill_color=esquemas_color.get(variable_seleccionada, 'YlOrRd'),
                fill_opacity=0.7,
                line_opacity=0.2,
                legend_name=variables_regionales.get(variable_seleccionada, variables_comunales.get(variable_seleccionada, variable_seleccionada)),
            ).add_to(m_simple)
            
            map_data = st_folium(m_simple, width=1400, height=600)
            st.success("✅ Mapa cargado con optimización ultra!")
            
        except Exception as e2:
            st.error(f"❌ Error persistente: {str(e2)}")
            st.info("📊 Mostrando tabla de datos como alternativa:")
            st.dataframe(mapa_gdf.drop('geometry', axis=1, errors='ignore').head(20))
        
else:
    st.warning("⚠️ No hay datos disponibles para mostrar. Verifica la configuración seleccionada.")
    
    # Debug info para ayudar a diagnosticar
    if len(mapa_gdf) == 0:
        st.info("🔍 No se encontraron registros en mapa_gdf")
    elif variable_seleccionada not in mapa_gdf.columns:
        st.info(f"🔍 Variable '{variable_seleccionada}' no encontrada en columnas: {list(mapa_gdf.columns)}")
    elif mapa_gdf[variable_seleccionada].notna().sum() == 0:
        st.info(f"🔍 Todos los valores de '{variable_seleccionada}' son nulos")

# Información adicional
st.markdown("---")
with st.expander("📚 Información sobre las Variables"):
    st.markdown("""
    **👥 Población Total:** Número total de personas registradas en el censo.
    
    **🏘️ Densidad Poblacional:** Habitantes por kilómetro cuadrado.
    
    **🎂 Edad Promedio:** Promedio de edad de la población.
    
    **👩 Porcentaje de Mujeres:** Porcentaje de mujeres respecto al total de población.
    """)