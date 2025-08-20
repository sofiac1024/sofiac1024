import csv
import pandas as pd
import streamlit as st
import folium
from folium import plugins
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
                'neighborhood' : row['BARRIO'],
                'operator' : row['OPERADOR'],
                'timetable' : row['HORARIO'],
                'management' : row['GESTIÓN'],
                'lon' : lon,
                'lat' : lat
            })
    return pd.DataFrame(points_data)

station_points = read_data()

# Crear pestañas
tab1, tab2 = st.tabs(["Mapa de Estaciones", "Dashboard"])

with tab1:
    # Creamos un mapa más dinámico con Streamlit_Folium centrado en MADRID
    MADRID_CENTRE = (40.41677473410711, -3.7037457319298768) # Formato EPSG:4326 (lat/lon WGS84)
    # Crear mapa centrado en Madrid Centro
    map = folium.Map(location=MADRID_CENTRE, zoom_start=11.5)
    # Añadir clustering de marcadores
    marker_cluster = plugins.MarkerCluster().add_to(map)

    # PLUGINS EXTRA
    # Añadir un buscador de localizaciones: GeoCoder
    plugins.Geocoder(collapsed=True).add_to(map)
    # Añadir filtros en la barra lateral
    st.sidebar.header("Filtros")
    # Filtro por distrito
    districs = station_points['neighborhood'].unique()
    selected_district = st.sidebar.multiselect("Selecciona distrito(s):", districs)
    # Filtro por operador 
    operators = station_points['operator'].unique()
    selected_operator = st.sidebar.multiselect("Selecciona operador(es):", operators)
    # Filtro por operador 
    managements = station_points['management'].unique()
    selected_management = st.sidebar.multiselect("Selecciona tipo(s) de gestión:", managements)

    # Aplicar filtros
    filtered_points = station_points.copy()
    if selected_district:
        filtered_points = filtered_points[filtered_points['neighborhood'].isin(selected_district)]
    if selected_operator:
        filtered_points = filtered_points[filtered_points['operator'].isin(selected_operator)]
    if selected_management:
        filtered_points = filtered_points[filtered_points['management'].isin(selected_management)]
    # Exportar datos filtrados a CSV
    @st.cache_data
    def download_stations_toCSV(df):
        return df.to_csv(index=False).encode('utf-8')
    csv_export = download_stations_toCSV(filtered_points)
    st.download_button(
        label="Exportar estaciones filtradas a CSV",
        data=csv_export,
        file_name="estaciones_filtradas.csv",
        mime="text/csv"
    )

    # Añadir marcadores de las estaciones de recarga
    for _, point in filtered_points.iterrows():
        mark = point['lat'], point['lon']
        folium.Marker(
            mark,
            popup=point["location"],
            tooltip=point["location"],
            icon=folium.Icon(color='green', icon='bolt', icon_color='white', prefix='fa')  # ícono tipo "rayo" de FontAwesome (fa)
        ).add_to(marker_cluster)


    # Crear el mapa con los puntos encontrados
    st.header("EV Fast-Charginig Stations in Madrid (Spain)")
    # st.map(station_points, latitude='lat', longitude='lon', zoom=10) [Mapa de puntos plotteados estáticos]
    # llamar a renderizar el Folium map en Streamlit
    st_data = st_folium(map, width=700, height=450)
