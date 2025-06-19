import streamlit as st
import pandas as pd
from utils import cargar_datos, obtener_regiones_disponibles

# Configuración de página
st.set_page_config(
    page_title="Censo 2017 Chile - Visualización de Datos",
    page_icon="🇨🇱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #4ECDC4;
    }
    .info-box {
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4);
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #0277bd;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Título principal
st.markdown("""
<div class="main-header">
    <h1>🇨🇱 Visualización del Censo 2017 de Chile</h1>
    <p>Explora datos demográficos de Chile a través de mapas interactivos y gráficas dinámicas</p>
</div>
""", unsafe_allow_html=True)

# Cargar datos
try:
    with st.spinner("Cargando datos del censo..."):
        regiones, comunas, censo = cargar_datos()
        regiones_lista = obtener_regiones_disponibles(regiones)
except Exception as e:
    st.error(f"Error al cargar los datos: {str(e)}")
    st.stop()

# Información general en columnas
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="metric-card">
        <h3>📊 Total Población</h3>
        <h2>{:,}</h2>
        <p>personas registradas</p>
    </div>
    """.format(len(censo)), unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="metric-card">
        <h3>🏛️ Regiones</h3>
        <h2>{}</h2>
        <p>regiones disponibles</p>
    </div>
    """.format(len(regiones_lista)), unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="metric-card">
        <h3>🏘️ Comunas</h3>
        <h2>{}</h2>
        <p>comunas registradas</p>
    </div>
    """.format(len(comunas)), unsafe_allow_html=True)

with col4:
    edad_promedio = censo['edad'].mean()
    st.markdown("""
    <div class="metric-card">
        <h3>👥 Edad Promedio</h3>
        <h2>{:.1f}</h2>
        <p>años</p>
    </div>
    """.format(edad_promedio), unsafe_allow_html=True)

# Información del proyecto
st.markdown("""
<div class="info-box">
    <h3>📋 Sobre este proyecto</h3>
    <p>Esta aplicación presenta una visualización interactiva de los datos del Censo 2017 de Chile. 
    Puedes explorar información demográfica a través de diferentes vistas:</p>
    <ul>
        <li><strong>🗺️ Mapas:</strong> Visualización geográfica con mapas coropléticos interactivos</li>
        <li><strong>📈 Gráficas:</strong> Análisis estadístico con gráficos dinámicos</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# Navegación
st.markdown("---")
st.subheader("🧭 Navegación")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### 🗺️ Mapas Interactivos
    - Mapas coropléticos por región y comuna
    - Variables: población, densidad, edad promedio, % mujeres
    - Filtros interactivos por región
    - Tooltips informativos
    """)
    if st.button("🚀 Ir a Mapas", type="primary"):
        st.switch_page("pages/01_Mapas.py")

with col2:
    st.markdown("""
    ### 📈 Gráficas y Análisis
    - Distribución por edad y sexo
    - Comparativas entre regiones
    - Pirámides poblacionales
    - Análisis temporal y estadístico
    """)
    if st.button("🚀 Ir a Gráficas", type="primary"):
        st.switch_page("pages/02_Gráficas.py")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9em;'>
    📊 Datos: Censo 2017 - Instituto Nacional de Estadísticas (INE) | 
    🛠️ Desarrollado con Streamlit | 
    📅 Año: 2025
</div>
""", unsafe_allow_html=True)