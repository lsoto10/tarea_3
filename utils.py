import geopandas as gpd
import pandas as pd
import streamlit as st
import numpy as np

def _normaliza_cod(gdf, posibles, nuevo):
    """Renombra la primera columna encontrada en `posibles` a `nuevo`."""
    for col in posibles:
        if col in gdf.columns:
            gdf = gdf.rename(columns={col: nuevo})
            return gdf
    st.error(
        f"No encuentro ninguna de estas columnas {posibles} en "
        f"{nuevo == 'region' and 'regiones' or 'comunas'} .shp"
    )
    st.stop()

@st.cache_data
def cargar_datos():
    """Carga y procesa todos los datos necesarios para la aplicación."""
    try:
        # ── 1. Geometrías ───────────────────────────────
        regiones = gpd.read_file("data/Regiones/Regional.shp").to_crs(4326)
        comunas = gpd.read_file("data/Comunas/comunas.shp").to_crs(4326)

        # Normalizar nombres de columnas
        regiones = _normaliza_cod(regiones,
                    ["codregion","REGION","REGION_C","COD_REG","COD_REGION",
                     "REGIONCOD"], "region_id")

        comunas = _normaliza_cod(comunas,
                    ["cod_comuna","COMUNA","COD_COMUNA","COMUNA_COD",
                     "Cod_Comun","ID_COMUNA"], "comuna_id")
        
        # Asegurar que codregion existe en comunas
        if 'codregion' in comunas.columns:
            comunas = comunas.rename(columns={'codregion': 'region_id_com'})
        
        # Limpiar nombres de regiones y comunas
        if 'Region' in regiones.columns:
            regiones['region_nombre'] = regiones['Region'].str.strip()
        if 'Comuna' in comunas.columns:
            comunas['comuna_nombre'] = comunas['Comuna'].str.strip()
        if 'Provincia' in comunas.columns:
            comunas['provincia_nombre'] = comunas['Provincia'].str.strip()

        # ── 2. Censo (OPTIMIZADO) ───────────────────────────────────
        col_map = {"REGION": "region_id", "COMUNA": "comuna_id",
                   "P08": "sexo", "P09": "edad", "P16": "trabajo",
                   "ESCOLARIDAD": "escolaridad"}
        
        # Cargar con muestreo para mejor rendimiento
        censo = pd.read_csv("data/Microdato_Censo2017-Personas.csv",
                           sep=";", encoding="latin1",
                           usecols=col_map.keys(),
                           dtype={"REGION": "int8", "COMUNA": "int32",
                                 "P08": "uint8", "P09": "uint8"},
                           chunksize=500000)  # Leer en chunks
        
        # Procesar en chunks para optimizar memoria
        censo_chunks = []
        for chunk in censo:
            chunk = chunk.rename(columns=col_map)
            chunk["sexo_cat"] = chunk["sexo"].map({1: "Hombre", 2: "Mujer"})
            chunk['grupo_edad'] = pd.cut(chunk['edad'], 
                                        bins=[0, 18, 30, 45, 65, 100],
                                        labels=['0-17', '18-29', '30-44', '45-64', '65+'])
            censo_chunks.append(chunk)
        
        # Combinar chunks
        censo = pd.concat(censo_chunks, ignore_index=True)
        del censo_chunks  # Liberar memoria
        
        # Convertir tipos para optimizar memoria
        try:
            regiones['region_id'] = pd.to_numeric(regiones['region_id'], errors='coerce').astype('int8')
            comunas['comuna_id'] = pd.to_numeric(comunas['comuna_id'], errors='coerce').astype('int32')
            if 'region_id_com' in comunas.columns:
                comunas['region_id_com'] = pd.to_numeric(comunas['region_id_com'], errors='coerce').astype('int8')
        except Exception as e:
            st.error(f"Error al convertir tipos de datos: {e}")
            st.stop()

        return regiones, comunas, censo
        
    except Exception as e:
        st.error(f"Error al cargar los datos: {e}")
        st.stop()

@st.cache_data
def procesar_datos_comuna(censo, region_id=None):
    """Procesa datos del censo a nivel comunal."""
    if region_id:
        censo_filtrado = censo[censo['region_id'] == region_id]
    else:
        censo_filtrado = censo
    
    # Agregaciones por comuna
    datos_comuna = censo_filtrado.groupby('comuna_id').agg({
        'sexo': 'count',  # población total
        'edad': ['mean', 'median'],  # edad promedio y mediana
        'sexo_cat': lambda x: (x == 'Mujer').sum() / len(x) * 100,  # % mujeres
    }).round(2)
    
    # Aplanar nombres de columnas
    datos_comuna.columns = ['poblacion_total', 'edad_promedio', 'edad_mediana', 'pct_mujeres']
    datos_comuna = datos_comuna.reset_index()
    
    return datos_comuna

@st.cache_data
def procesar_datos_region(censo):
    """Procesa datos del censo a nivel regional."""
    datos_region = censo.groupby('region_id').agg({
        'sexo': 'count',  # población total
        'edad': 'mean',   # edad promedio
        'sexo_cat': lambda x: (x == 'Mujer').sum() / len(x) * 100,  # % mujeres
    }).round(2)
    
    datos_region.columns = ['poblacion_total', 'edad_promedio', 'pct_mujeres']
    datos_region = datos_region.reset_index()
    
    return datos_region

def obtener_regiones_disponibles(regiones):
    """Obtiene lista de regiones disponibles con sus nombres."""
    if 'region_nombre' in regiones.columns:
        regiones_lista = regiones[['region_id', 'region_nombre']].drop_duplicates()
        regiones_lista = regiones_lista.sort_values('region_id')
        return regiones_lista
    else:
        return regiones[['region_id']].drop_duplicates().sort_values('region_id')

@st.cache_data
def crear_datos_optimizados(censo):
    """Crea versiones pre-agregadas de los datos para visualizaciones más rápidas."""
    
    # 1. Datos regionales agregados
    datos_region = censo.groupby('region_id').agg({
        'sexo': 'count',  # población total
        'edad': ['mean', 'median', 'std'],   # estadísticas de edad
        'sexo_cat': lambda x: (x == 'Mujer').sum() / len(x) * 100,  # % mujeres
    }).round(2)
    
    datos_region.columns = ['poblacion_total', 'edad_promedio', 'edad_mediana', 'edad_std', 'pct_mujeres']
    datos_region = datos_region.reset_index()
    
    # 2. Datos por grupos de edad y región
    edad_region = censo.groupby(['region_id', 'grupo_edad']).size().reset_index(name='poblacion')
    
    # 3. Datos por sexo y región
    sexo_region = censo.groupby(['region_id', 'sexo_cat']).size().reset_index(name='poblacion')
    
    # 4. Datos para pirámides poblacionales (muestreados)
    sample_size = min(100000, len(censo))  # Máximo 100k registros para pirámides
    censo_sample = censo.sample(n=sample_size, random_state=42)
    
    return datos_region, edad_region, sexo_region, censo_sample

@st.cache_data
def obtener_muestra_censo(censo, size=50000):
    """Obtiene una muestra representativa del censo para visualizaciones rápidas."""
    if len(censo) <= size:
        return censo
    return censo.sample(n=size, random_state=42)

@st.cache_data
def optimizar_geometrias_para_web(_gdf, tolerance=0.01, max_points=1000):
    """
    Optimiza geometrías para visualización web reduciendo puntos y simplificando formas.
    
    Args:
        _gdf: GeoDataFrame con geometrías (underscore para evitar hashing)
        tolerance: Tolerancia para simplificación (mayor = más simple)
        max_points: Máximo número de puntos por geometría
    
    Returns:
        GeoDataFrame optimizado
    """
    gdf_optimized = _gdf.copy()
    
    # Simplificar geometrías
    gdf_optimized['geometry'] = gdf_optimized['geometry'].simplify(
        tolerance, preserve_topology=True
    )
    
    # Función para reducir puntos en geometrías complejas
    def reduce_geometry_points(geom, max_points):
        if hasattr(geom, 'exterior') and geom.exterior is not None:
            # Para polígonos
            coords = list(geom.exterior.coords)
            if len(coords) > max_points:
                # Seleccionar puntos equidistantes
                step = len(coords) // max_points
                coords = coords[::step]
                # Asegurar que el polígono se cierre
                if coords[0] != coords[-1]:
                    coords.append(coords[0])
                from shapely.geometry import Polygon
                return Polygon(coords)
        return geom
    
    # Aplicar reducción de puntos si es necesario
    if max_points:
        gdf_optimized['geometry'] = gdf_optimized['geometry'].apply(
            lambda geom: reduce_geometry_points(geom, max_points)
        )
    
    return gdf_optimized

@st.cache_data
def preparar_datos_mapa_ligeros(_gdf, campos_datos, max_registros=None):
    """
    Prepara datos optimizados para mapas web, manteniendo solo campos esenciales.
    
    Args:
        _gdf: GeoDataFrame original (underscore para evitar hashing)
        campos_datos: Lista de campos de datos a mantener
        max_registros: Máximo número de registros (None = todos)
    
    Returns:
        GeoDataFrame optimizado para web
    """
    # Campos esenciales
    campos_esenciales = ['geometry']
    
    # Agregar ID fields
    for id_field in ['region_id', 'comuna_id']:
        if id_field in _gdf.columns:
            campos_esenciales.append(id_field)
    
    # Agregar name fields  
    for name_field in ['region_nombre', 'comuna_nombre']:
        if name_field in _gdf.columns:
            campos_esenciales.append(name_field)
    
    # Agregar campos de datos solicitados
    for campo in campos_datos:
        if campo in _gdf.columns:
            campos_esenciales.append(campo)
    
    # Filtrar solo campos disponibles
    campos_disponibles = [campo for campo in campos_esenciales if campo in _gdf.columns]
    
    # Crear GDF ligero
    gdf_ligero = _gdf[campos_disponibles].copy()
    
    # Limitar registros si es necesario
    if max_registros and len(gdf_ligero) > max_registros:
        gdf_ligero = gdf_ligero.head(max_registros)
    
    # Optimizar geometrías
    gdf_ligero = optimizar_geometrias_para_web(gdf_ligero, tolerance=0.01, max_points=500)
    
    # Redondear valores numéricos para reducir tamaño
    for col in gdf_ligero.columns:
        if gdf_ligero[col].dtype in ['float64', 'float32']:
            gdf_ligero[col] = gdf_ligero[col].round(2)
    
    return gdf_ligero