import csv
import pandas as pd
import streamlit as st
import folium
from pyproj import Transformer
from streamlit_folium import st_folium

datafile = 'PUNTOS_PUBLICOS_RECARGA_VEHICULOS_ELECTRICOS.csv'

# Configurar transformador: de EPSG:25830 (UTM Madrid) a EPSG:4326 (lat/lon WGS84) (modelo que usa streamlit)
transformer = Transformer.from_crs("EPSG:25830", "EPSG:4326", always_xy=True)

# Leer fichero csv y conseguir las coordenadas de cada punto de recarga
@st.cache_data # Guarda el primer DatFrame creado y permite saltarse read_data si no han cambiado los datos de entrada o la función 
               # (osea, si generan el mismo output)
def read_data():
    points_data = []
    with open(datafile, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        for row in reader:
            # Python entiende la coma decimal como un punto
            coorX = float(row['POINT_X'].replace(',', '.'))
            coorY = float(row['POINT_Y'].replace(',', '.'))
            lon, lat = transformer.transform(coorX, coorY)
            points_data.append({
                'location' : row['UBICACIÓN'],
                'lon' : lon,
                'lat' : lat
            })
    return pd.DataFrame(points_data)

station_points = read_data()
# Creamos un mapa más dinámico con Streamlit_Folium centrado en MADRID
MADRID_CENTRE = (40.41677473410711, -3.7037457319298768) # Formato EPSG:4326 (lat/lon WGS84)
# Crear mapa centrado en Madrid Centro
map = folium.Map(location=MADRID_CENTRE, zoom_start=11)
# Añadir marcadores de las estaciones de recarga
for _, point in station_points.iterrows():
    mark = point['lat'], point['lon']
    folium.Marker(mark, popup=point['location'], tooltip=point['location']).add_to(map)

# Crear el mapa con los puntos encontrados
st.header("EV Fast-Charginig Stations in Madrid (Spain)")
# st.map(station_points, latitude='lat', longitude='lon', zoom=10) [Mapa de puntos plotteados estáticos]
# llamar a renderizar el Folium map en Streamlit
st_data = st_folium(map, width=725)
