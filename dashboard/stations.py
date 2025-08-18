import csv

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
                'coorX' : coorX,
                'coorY' : coorY
            })
        return points_data
    
print(read_data())