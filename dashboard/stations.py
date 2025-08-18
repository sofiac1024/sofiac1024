import csv
import pandas as pd
import streamlit as st
from pyproj import Transformer

datafile = 'PUNTOS_PUBLICOS_RECARGA_VEHICULOS_ELECTRICOS.csv'

# Configurar transformador: de EPSG:25830 (UTM Madrid) a EPSG:4326 (lat/lon WGS84)
transformer = Transformer.from_crs("EPSG:25830", "EPSG:4326", always_xy=True)

# Leer fichero csv y conseguir las coordenadas de cada punto de recarga
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
                'lon' : lon,
                'lat' : lat
            })
    return pd.DataFrame(points_data)

station_points = read_data()

# Crear el mapa con los puntos encontrados
st.header("EV Fast-Charginig Stations in Madrid (Spain)")
st.map(station_points, latitude='lat', longitude='lon', zoom=10)