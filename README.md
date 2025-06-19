# 🇨🇱 Visualización del Censo 2017 de Chile

## 📋 Descripción

Aplicación web desarrollada con **Streamlit** para la visualización interactiva de los datos del Censo 2017 de Chile. Incluye mapas coropléticos y gráficas dinámicas para explorar información demográfica.

## 🗂️ Estructura del Proyecto

```
├── app.py                          # Página principal
├── utils.py                        # Funciones de procesamiento de datos
├── requirement.txt                 # Dependencias
├── .streamlit/
│   └── config.toml                 # Configuración de Streamlit
├── pages/
│   ├── 01_Mapas.py                # Mapas interactivos
│   └── 02_Gráficas.py             # Gráficas y análisis
└── data/
    ├── Microdato_Censo2017-Personas.csv  # Datos del censo
    ├── Regiones/                   # Shapefiles de regiones
    └── Comunas/                    # Shapefiles de comunas
```

## 🚀 Cómo ejecutar

### 1. Instalar dependencias
```bash
pip install -r requirement.txt
```

### 2. Ejecutar la aplicación
```bash
streamlit run app.py
```

### 3. Abrir en el navegador
La aplicación se abrirá automáticamente en `http://localhost:8501`

## ✨ Características

- **🗺️ Mapas Interactivos**: Visualización choroplética por región y comuna
- **📊 Gráficas Dinámicas**: Análisis demográfico con múltiples tipos de gráficos
- **🎛️ Controles Interactivos**: Filtros y parámetros configurables
- **📱 Diseño Responsivo**: Compatible con dispositivos móviles

## 📊 Fuentes de Datos

- **Censo 2017**: Instituto Nacional de Estadísticas (INE) de Chile
- **Geometrías**: Shapefiles oficiales de regiones y comunas

## 🛠️ Tecnologías

- Streamlit, Folium, GeoPandas, Pandas, Plotly, Altair
