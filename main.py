from gurobipy import Model, GRB, quicksum
import pandas as pd
import csv
import os

abspath = os.path.abspath(__file__)
root = os.path.dirname(abspath)
os.chdir(root)

generacion_df = pd.read_csv('datos/tablas/tablaGeneracion.csv', encoding='utf-8')
demanda_df = pd.read_csv('datos/tablas/tablaDemanda.csv', encoding='utf-8')
costo_df = pd.read_csv('datos/tablas/tablaCostosContruccion.csv', encoding='utf-8')
disponibilidad_df = pd.read_csv('datos/tablas/tablaDisponibilidad.csv', encoding='utf-8')
distancia_df = pd.read_csv('datos/tablas/tablaDistancias.csv', encoding='utf-8')
costo_produccion = pd.read_csv('datos/tablas/tablaCostosProduccion.csv', encoding='utf-8')

G = {(row['i'], row['u'], row['t']): row['G_iut'] for idx, row in generacion_df.iterrows()}
D = {(row['k'], row['t']): row['D_kt'] for idx, row in demanda_df.iterrows()}
C = {(row['i'], row['u']): row['C_iu'] for idx, row in costo_df.iterrows()}
A = {(row['u'], row['i']): row['A_ui'] for idx, row in disponibilidad_df.iterrows()}
Dist = {(row['u'], row['k']): row['Dist_uk'] for idx, row in distancia_df.iterrows()}
F = {(row['i'], row['u']): row['F_iu'] for idx, row in costo_produccion.iterrows()}

Distmax = 130
M = 1000000000
C_transporte = 100
max_plantas_subestacion = 10

print("Generación Promedio Esperada (G):", G)
print("Demanda Energética Promedio (D):", D)
print("Costo de Construcción (C):", C)
print("Disponibilidad para Construcción (A):", A)


# Conjuntos
U = list(disponibilidad_df['u'].unique())  # Ubicaciones
I = list(disponibilidad_df['i'].unique())  # Tipos de plantas: 1 = Solar, 2 = Eólica
K = list(demanda_df['k'].unique())         # Subestaciones
T = list(generacion_df['t'].unique())      # Meses


m = Model("Minimize_Construction_Costs")

# Variables de decisión
y = m.addVars(I, U, vtype=GRB.BINARY, name="y")
z = m.addVars(U, K, vtype=GRB.BINARY, name="z")
X = m.addVars(U, K, T, vtype=GRB.CONTINUOUS, name="X")

# Función objetivo: Minimizar el costo de construcción
m.setObjective(quicksum(C[i, u] * y[i, u] for i in I for u in U) +
               quicksum(C_transporte * Dist[u, k] * z[u, k] for u in U for k in K) +
               quicksum(X[u, k, t] * F[i, u] for i in I for u in U for k in K for t in T),
               GRB.MINIMIZE)

# Restricción 1: Satisfacer la demanda total en cada mes con X
for t in T:
    for k in K:
        m.addConstr(quicksum(X[u, k, t] for u in U) >= D[k, t], name=f"Demand_satisfaction_{k}_{t}")
        

# Restricción: Una planta no puede repartir más que su generación por mes (con variable X)
for u in U:
    for t in T:
        m.addConstr(quicksum(G[i, u, t] * y[i, u] for i in I)>= quicksum(X[u, k, t] for k in K), 
                    name=f"Plant_generation_limit_{u}_{t}")

        
# Restricción 2: Disponibilidad de ubicaciones
for i in I:
    for u in U:
        m.addConstr(y[i, u] <= A[u, i], name=f"Availability_{i}_{u}")

# Restricción 3: Relacionar Z con y
for u in U:
    for k in K:
        m.addConstr(quicksum(y[i, u] for i in I) - z[u, k] >= 0, name=f"z_relation_{u}_{k}")

# Restricción 4: Condición para variable Z


for u in U:
    for k in K:
        m.addConstr(Distmax + M * (1 - z[u, k]) >= Dist[u, k], name=f"Condition_z_{u}_{k}")


# Restricción 5: Un punto donde no se construye ninguna planta no puede satisfacer puntos de demanda
for u in U:
    for k in K:
        m.addConstr(quicksum(y[i, u] for i in I) >= z[u, k], name=f"No_plant_demand_{u}_{k}")


#Retsriccion 7         
for u in U:
    m.addConstr(quicksum(y[i, u] for i in I) <= 1, name=f"One_plant_location_{u}")
    
#Restriccion para Z y X
for u in U:
    for k in K:
        for t in T:
            m.addConstr(X[u, k, t] <= z[u, k] * M, name=f"No_energy_disconnected_{u}_{k}_{t}")
            
            
#Maxima cantidad de plantas que pueden satisfacer a una subestacion         
for k in K:
    for t in T:
        m.addConstr(quicksum(z[u, k] for u in U) <= max_plantas_subestacion, name=f"Max_plants_per_substation_{k}_{t}")
   
#Reducir la densidad de plantas del mismo tipo: No pueden haber 5 plantas iguales en 5 ubicaciones consecutivas
for i in I:
    for u in range(len(U) - 4):  
        m.addConstr(quicksum(y[i, U[u + j]] for j in range(5)) <= 4, name=f"No_five_consecutive_{i}_{u}")
            
#No negatividad
for u in U:
    for k in K:
        for t in T:
            m.addConstr(X[u, k, t] >= 0, name=f"Non_negativity_X_{u}_{k}_{t}")

m.addConstr(quicksum(z[u, k] for u in U for k in K) >= 1, name="At_least_one_z")
# Optimizar modelo
m.optimize()



# Imprimir costo total
print(f"Costo anual total : {m.ObjVal}")

print(os.getcwd())
os.chdir("resultados")
print(os.getcwd())

for t in T:
    filename = f'mes{t}.csv'
    with open(filename, 'w', newline='', encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Ubicación', 'Tipo Energía', 'Subestación', 'Energía (MWh)'])
        for u in U:
            for k in K:
                if X[u, k, t].X > 0:
                    for i in I:
                        if y[i, u].X > 0.5:  # Verificar si se construyó una planta en la ubicación u
                            writer.writerow([u, i, k, X[u, k, t].X])

for u in U:
    for i in I:
        if y[i, u].X == 1:
            print(f"Se construyó una planta de tipo {i} en la ubicación {u}")