import csv
import pandas as pd
import streamlit as st
import folium
from folium import plugins
from pyproj import Transformer
from streamlit_folium import st_folium
import requests, json
from geopy.distance import geodesic
import plotly.express as px
from collections import Counter

API_KEY = "09b30b28-b517-4e00-b091-7209feb8e107"
url = "https://api.openchargemap.io/v3/poi/"
datafile = 'PUNTOS_PUBLICOS_RECARGA_VEHICULOS_ELECTRICOS.csv'
# Configurar transformador: de EPSG:25830 (UTM Madrid) a EPSG:4326 (lat/lon WGS84) (modelo que usa streamlit)
transformer = Transformer.from_crs("EPSG:25830", "EPSG:4326", always_xy=True)

def find_ocm_match(p, api_points):
    if not api_points:
        return
    
    # Comparar por distancia
    best_match = None
    min_dist = 1e9
    for r in api_points:
        r_lat = r["AddressInfo"]["Latitude"]
        r_lon = r["AddressInfo"]["Longitude"]
        dist = geodesic((p['lat'], p['lon']), (r_lat, r_lon)).meters
        if dist < min_dist:
            min_dist = dist
            best_match = r

    p["usageCost"] = best_match.get("UsageCost", "No info")
    cnt = Counter()
    power = dict()
    for c in best_match.get("Connections", []):
        cnt[c["ConnectionType"]["Title"]] += 1
        power[c["ConnectionType"]["Title"]] = c["PowerKW"]
    p["connections"] = cnt
    p["connectionsKW"] = power
    p["status"] = best_match.get("StatusType", {}).get("Title", "Desconocido")
    return

# Leer fichero csv y conseguir las coordenadas de cada punto de recarga
@st.cache_data # Guarda el primer DatFrame creado y permite saltarse read_data si no han cambiado los datos de entrada o la función 
               # (osea, si generan el mismo output)
def read_dataCSV():
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
    return points_data
@st.cache_data
def read_dataAPI():
    # Leer puntos de recarga respectivos en la API OpenChargeMap para complementar
    params = {
        "key": API_KEY,
        "latitude": 40.4168,   # centro de Madrid
        "longitude": -3.7038,
        "distance": 100,       
        "distanceunit": "KM",
        "maxresults": 2000,
        "usagetypeid": [1, 4] # Públicos o públicos con membresía
    }
    resp = requests.get(url, params=params)
    ocm_data = resp.json()
    # Leer puntos de recarga de la base de datos del ayuntamiento
    csv_data = read_dataCSV()

    # Complementar cada punto de csv_data con la info. de ocm_data
    for p in csv_data:
        find_ocm_match(p, ocm_data)
    return pd.DataFrame(csv_data)

station_points = read_dataAPI()
filtered_points = station_points.copy()


# Título de la página
st.header("Puntos de recarga públicos para vehículos eléctricos en Madrid (España)")

# Crear pestañas
tab1, tab2 = st.tabs(['Mapa de Estaciones', 'Estadísticas'])

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
    st.html('''
        <style>
        /* Restringir la altura máxima de las opciones seleccionadas, 
            incluyendo un scroll si es mecesario */
        div[data-testid="stMultiSelect"] [data-baseweb="select"] > div > div {
            max-height: 114px; 
            overflow: auto;
        }
            
        [data-testid="stSidebarHeader"] {
            height: 1.25rem; 
        }
        </style>
    ''')
    st.sidebar.header("Filtros")
    # Creamos un contenedor vacío en el sidebar (arriba de los filtros)
    contador = st.sidebar.empty()
    # Filtro por distrito
    districs = sorted(station_points['neighborhood'].unique())
    selected_district = st.sidebar.multiselect("**Selecciona barrio(s):**", districs, placeholder="")
    # Filtro por operador 
    managements = sorted(station_points['management'].unique())
    selected_management = st.sidebar.multiselect("**Selecciona tipo(s) de gestión:**", managements, placeholder="")
    # Filtro por operador 
    operators = sorted(station_points['operator'].unique())
    selected_operator = st.sidebar.multiselect("**Selecciona operador(es):**", operators, placeholder="")
    # Filtro por tipo de conector
    all_connectors = sorted({c for conns in station_points['connections'] for c in conns})  # set para evitar duplicados
    selected_connectors = st.sidebar.multiselect("**Selecciona tipo(s) de conector:**", all_connectors, placeholder="")
    # Aplicar filtros
    if selected_district:
        filtered_points = filtered_points[filtered_points['neighborhood'].isin(selected_district)]
    if selected_operator:
        filtered_points = filtered_points[filtered_points['operator'].isin(selected_operator)]
    if selected_management:
        filtered_points = filtered_points[filtered_points['management'].isin(selected_management)]
    if selected_connectors:
        filtered_points = filtered_points[
        filtered_points['connections'].apply(lambda conns: any(conn in conns for conn in selected_connectors))
        ]
    # Conteo de puntos de recarga filtrados
    contador.metric(label="**Puntos de recarga coincidentes:**", value=len(filtered_points))
    

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
    def popup_html(point):
        # Construir descripción de conectores
        if isinstance(point["connections"], dict) and isinstance(point["connectionsKW"], dict):
            rows = []
            for ctype in point["connections"].keys():
                count = point["connections"].get(ctype, "N/A")
                kw = point["connectionsKW"].get(ctype, "N/A")
                rows.append(f"<tr><td>{ctype}</td><td>{kw} kW</td><td>{count}</td></tr>")
            
            connectors_str = f"""
            <table style="width:100%; font-size:11px; border-collapse:collapse;" border="1">
                <tr style="font-weight:bold; background-color:#f0f0f0;">
                    <td>Tipo</td>
                    <td>Potencia</td>
                    <td>Cargadores</td>
                </tr>
                {''.join(rows)}
            </table>
            """
        else:
            connectors_str = "N/A"

        return f"""
        <div style="width: 250px; font-size: 12px;">
        <b>Ubicación:</b> {point['location']}<br>
        <b>Barrio:</b> {point['neighborhood']}<br>
        <b>Operador:</b> {point['operator']}<br>
        <b>Horario:</b> {point['timetable']}<br>
        <b>Coste:</b> {point['usageCost']}<br>
        <b>Conectores:</b><br>{connectors_str}<br>
        <b>Estado:</b> {point['status']}<br>
        """
    for _, point in filtered_points.iterrows():
        mark = point['lat'], point['lon']
        folium.Marker(
            mark,
            popup=popup_html(point),
            tooltip=point["location"],
            icon=folium.Icon(color='green', icon='bolt', icon_color='white', prefix='fa')  # ícono tipo "rayo" de FontAwesome (fa)
        ).add_to(marker_cluster)

    # Crear el mapa con los puntos encontrados
    st.header("Mapa Interactivo")
    # llamar a renderizar el Folium map en Streamlit
    st_data = st_folium(map, width=700, height=450)


with tab2:
    st.header("Estadísticas Relevantes")
    # Algunas estadísticas sobre la distribución y características de los puntos de recarga representados
    # Agrupar por barrio y contar
    df_barrios = (
        filtered_points.groupby("neighborhood")
        .size()
        .reset_index(name="count")
    )
    # Ordenar de mayor a menor y quedarte con los 10 primeros
    df_top10 = df_barrios.sort_values("count", ascending=False).head(10)
    # Crear gráfico de barras
    chart1 = px.bar(
        df_top10,
        x="neighborhood",
        y="count",
        title="Top 10 barrios con más puntos de recarga",
        color="count",
        text="count",
        labels={
            "neighborhood": "Barrio",   # renombra eje X
            "count": "Número de puntos de recarga"  # renombra eje Y
        }
    )
    # Ordenar las barras en el eje X según la cantidad
    chart1.update_layout(xaxis={'categoryorder': 'total descending'})
    # Mostrar en Streamlit
    st.plotly_chart(chart1, use_container_width=True)

    df_operadores = filtered_points.groupby("operator").size().reset_index(name="count")
    chart2 = px.pie(
        df_operadores,
        names="operator",      
        values="count",        
        title="Número de puntos de recarga por operador",
        hover_data=["count"], 
        labels={
            "operator": "Operador",   # renombra eje X
            "count": "Número de puntos de recarga"  # renombra eje Y
        } 
    )   
    st.plotly_chart(chart2, use_container_width=True)