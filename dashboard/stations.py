import csv

datafile = 'PUNTOS_PUBLICOS_RECARGA_VEHICULOS_ELECTRICOS.csv'

# Leer fichero csv y conseguir las coordenadas de cada punto de recarga
def read_data():
    points_data = []
    with open(datafile, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            coorX, coorY = row['POINT_X'], row['POINT_Y']
            points_data.append({
                'coorX' : float(coorX),
                'coorY' : float(coorY)
            })
        return points_data
    
print(read_data())