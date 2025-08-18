import csv
import streamlit as st

datafile = 'PUNTOS_PUBLICOS_RECARGA_VEHICULOS_ELECTRICOS.csv'

# Leer fichero csv y conseguir las coordenadas de cada punto de recarga
def read_data():
    points_data = []
    with open(datafile, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        for row in reader:
            # Python entiende la coma decimal como un punto
            coorX = float(row['POINT_X'].replace(',', '.'))
            coorY = float(row['POINT_Y'].replace(',', '.'))
            points_data.append({
                'longitude' : coorX,
                'latitude' : coorY
            })
        return points_data

station_points = read_data()

# Crear el mapa con los puntos encontrados
st.header("EV Fast-Charginig Stations in Madrid (Spain)")
st.map(station_points, latitude='latitude', longitude='longitude', zoom=8)