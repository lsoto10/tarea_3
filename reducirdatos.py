import pandas as pd

# Nombre del archivo original y del nuevo archivo
archivo_original = 'data/Microdato_Censo2017-Personas.csv'
archivo_reducido = 'data/Microdato_Censo2017-Personas_reducido.csv'

print(f"Cargando el archivo original: {archivo_original}...")
# Cargar el dataset completo
df = pd.read_csv(archivo_original)

print(f"El dataset original tiene {len(df)} filas.")

# Vamos a quedarnos con el 75% de las filas para asegurar que baje de 2 GB.
# frac=0.75 significa 75%. Puedes ajustar este número.
# random_state=42 asegura que si lo ejecutas de nuevo, obtengas la misma muestra aleatoria.
df_reducido = df.sample(frac=0.75, random_state=42)

print(f"El nuevo dataset tendrá {len(df_reducido)} filas.")

print(f"Guardando el archivo reducido en: {archivo_reducido}...")
# Guardar el nuevo dataframe en un nuevo archivo CSV
df_reducido.to_csv(archivo_reducido, index=False)

print("¡Proceso completado!")