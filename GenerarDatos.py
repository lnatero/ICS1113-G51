import pandas as pd
import random
import os
from DatosSolarAtlas import GeneracionSolar_ZonasNaranjas,GeneracionSolar_ZonasAmarillas,GeneracionSolar_ZonasRojas,GeneracionSolar_ZonasVerdes,DatosDemanda
#La ubicaciones disponibles U y K estan ordenadas de norte a sur.
#Modelaremos de Arica hasta Puerto Montt, porque, la zona mas austral de chile es muy compleja de modelar, debido a que es muy dificil encontrar un patron en los datos en esa zona.

abspath = os.path.abspath(__file__)
root = os.path.dirname(abspath)
os.chdir(root)

N_AEROGENERADORES = 10 #Cantidad de aerogeneradores por central eolica

def limpiar_datos_eolica(file):
    with open(file, encoding="utf-8") as f:
        f = list(f)
        meses = []
        for i in range(len(f)):
            f[i] = f[i].strip().split(",")
            f[i].pop(0)
        for lines in f[40:]:
            meses.append(float(lines[0]))
        return meses

def ProduccionSolar(u, t): # Consideramos la construcción de plantas solares de 10 MW
    
    ZonaRoja= u_max * 3 // 5  #Ubicaciones de Arica a Petorca (Primero 3/5 de Chile)
    ZonaNaranja =  ZonaRoja + (u_max -  ZonaRoja) // 2 #Ubicaciones de Petorca hasta los Angeles
    
    #El resto de Ubicaciones es de los Angeles a Puerto Montt
    
    # Asigna diferentes valores de G_iut según la ubicacion
    if u <=  ZonaRoja:
        return int(GeneracionSolar_ZonasRojas[t]) * 32 # kW/m^2 * m^2
    
    elif  ZonaRoja < u <= ZonaNaranja:
        return int(GeneracionSolar_ZonasNaranjas[t]) * 32 # 32 porque de esa forma se alcanza un promedio de 10 MW
    
    else:
        return int(GeneracionSolar_ZonasAmarillas[t]) * 32
   
def ProduccionEolica(u, t):
    for zona in range(7):
        if u < u_max // 8:
            return int(limpiar_datos_eolica("datos/eolica/meses/zona0.csv")[t]) * N_AEROGENERADORES
        elif u_max // 8 <= u < 2 * u_max // 8:
            return int(limpiar_datos_eolica("datos/eolica/meses/zona1.csv")[t]) * N_AEROGENERADORES
        elif 2 * u_max // 8 <= u < 3 * u_max // 8:
            return int(limpiar_datos_eolica("datos/eolica/meses/zona2.csv")[t]) * N_AEROGENERADORES
        elif 3 * u_max // 8 <= u < 4 * u_max // 8:
            return int(limpiar_datos_eolica("datos/eolica/meses/zona3.csv")[t]) * N_AEROGENERADORES
        elif 4 * u_max // 8 <= u < 6 * u_max // 8:
            return int(limpiar_datos_eolica("datos/eolica/meses/zona4.csv")[t]) * N_AEROGENERADORES
        elif 6 * u_max // 8 <= u < 7 * u_max // 8:
            return int(limpiar_datos_eolica("datos/eolica/meses/zona5.csv")[t]) * N_AEROGENERADORES
        else:
            return int(limpiar_datos_eolica("datos/eolica/meses/zona6.csv")[t]) * N_AEROGENERADORES

def ProduccionMaritima(u, t):
    # Aquí puedes definir tu propia fórmula para calcular G_iut de energia Maritima
    return 100 + u * 10 + t * 2  

def ProduccionHidroelectrica(u, t):
    # Aquí puedes definir tu propia fórmula para calcular G_iut de energia Hidroelectrica
    return 100 + u * 10 + t * 2  





def Calculo_CostoContruccion(i,u): #Calcular costo segun ubicacion y tipo de energia
    if i == 1: # Si es solar cuesta tanto contruir la central
        return 993 # US por kW
    elif i == 2: # Si es eolica cuesta tanto construir la central
        return 1448 # US por kW
    
def Calculo_CostoProduccion(i,u): #Calcular costo Produccion segun ubicacion y tipo de energia
    if i == 1: # Si es solar cuesta tanto producirla  (y/o mantenerla)
        return 993 * 0.015
    elif i == 2: # Si es eolica cuesta tanto prducirla
        return 1448 * 0.015


def  AsignacionDemanda(k_max,k,t):#Calcular costo Produccion segun ubicacion y tipo de energia 
    return (DatosDemanda[t]//k_max)*700 #Demanda mensual dividia en partes iguales por cada subestacion, Se multiplica las 700 horas que tiene un mes.


def  AsignacionDisponibilidad(u,i): #Calcular costo Produccion segun ubicacion y tipo de energia
    return 1
    
    

def crear_tablaGeneracion(i_range, u_max, t_max):
    datos = {
        "i": [],
        "u": [],
        "t": [],
        "G_iut": []
    }
    for i in i_range:
        for u in range(u_max + 1):
            for t in range(1, t_max + 1):
                if i == 1: 
                    G_iut = int(ProduccionSolar(u, t))
                elif i == 2:
                    G_iut = ProduccionEolica(u, t)
                elif i == 3:
                    G_iut = ProduccionHidroelectrica(u, t)
                elif i == 3:
                    G_iut = ProduccionMaritima(u, t)

                datos["i"].append(i)
                datos["u"].append(u)
                datos["t"].append(t)
                datos["G_iut"].append(G_iut)

    df = pd.DataFrame(datos)
    return df

def crear_tablaCostosContruccion(i_range, u_max):
    datos = {
        "i": [],
        "u": [],
        "C_iu": []
    }
    for i in i_range:
        for u in range(u_max + 1):
            C_iu = Calculo_CostoContruccion(i, u)
            datos["i"].append(i)
            datos["u"].append(u)
            datos["C_iu"].append(C_iu)

    df = pd.DataFrame(datos)
    return df

def crear_tablaCostoProduccion(i_range, u_max):
    datos = {
        "i": [],
        "u": [],
        "F_iu": []
    }
    for i in i_range:
        for u in range(u_max + 1):
            F_iu = Calculo_CostoProduccion(i, u)
            datos["i"].append(i)
            datos["u"].append(u)
            datos["F_iu"].append(F_iu)

    df = pd.DataFrame(datos)
    return df

def crear_tablaCostoProduccion(i_range, u_max):
    datos = {
        "i": [],
        "u": [],
        "F_iu": []
    }
    for i in i_range:
        for u in range(u_max + 1):
            F_iu = Calculo_CostoProduccion(i, u)
            datos["i"].append(i)
            datos["u"].append(u)
            datos["F_iu"].append(F_iu)

    df = pd.DataFrame(datos)
    return df

def crear_tablaDemanda(k_max, t_max):
    datos = {
        "k": [],
        "t": [],
        "D_kt": []
    }
    for t in range(1, t_max + 1):
        for k in range(k_max + 1):
            D_kt = AsignacionDemanda(k_max,k, t)
            datos["k"].append(k)
            datos["t"].append(t)
            datos["D_kt"].append(D_kt)

    df = pd.DataFrame(datos)
    return df

def crear_tablaDisponibilidad(i_range, u_max):
    datos = {
        "u": [],
        "i": [],
        "A_ui": []
    }
    for i in i_range:
        for u in range(u_max + 1):
            A_ui = AsignacionDisponibilidad(i_range, u_max)
            datos["u"].append(u)
            datos["i"].append(i)
            datos["A_ui"].append(A_ui)

    df = pd.DataFrame(datos)
    return df


def generar_tablaDistancias(u_max, k_max):
    datos = {
        "u": [],
        "k": [],
        "Dist_uk": []
    }
   

    # Calcular las distancias entre cada par de puntos en U y K
    for u in range(u_max+1):
        for k in range(k_max+1):
            
            distancia = int(abs(u-((u_max/k_max)*k)))*10
            if distancia == 0:
                distancia+=10
            datos["u"].append(u)
            datos["k"].append(k)
            datos["Dist_uk"].append(distancia)
    
    df = pd.DataFrame(datos)
    return df


# Especifica los rangos y valores máximos
i_range = [1,2] #Energias (1=solar, 2=eolica, 3 = Hidroelectricas)
k_max = 10 #Cantidad de subestaciones
u_max = 50 #Cantidad de ubicaciones
t_max = 12# Meses

# Crear la tabla
tablaGen = crear_tablaGeneracion(i_range, u_max, t_max)
tablaCostos_C = crear_tablaCostosContruccion(i_range, u_max)
tablaCostos_P = crear_tablaCostoProduccion(i_range, u_max)
tablaDemanda = crear_tablaDemanda(k_max, t_max)
tablaDisponibilidad = crear_tablaDisponibilidad(i_range, u_max)
tablaDistancias = generar_tablaDistancias(u_max, k_max)
# Mostrar

# Guardar la tabla en un archivo CSV
print(os.getcwd())
os.chdir("datos/tablas")
print(os.getcwd())

tablaGen.to_csv("tablaGeneracion.csv", index=False, encoding='utf-8')
tablaCostos_C.to_csv("tablaCostosContruccion.csv", index=False, encoding='utf-8')
tablaCostos_P.to_csv("tablaCostosProduccion.csv", index=False, encoding='utf-8')
tablaDemanda.to_csv("tablaDemanda.csv", index = False, encoding='utf-8')
tablaDisponibilidad.to_csv("tablaDisponibilidad.csv", index = False, encoding='utf-8')
tablaDistancias.to_csv("tablaDistancias.csv", index = False, encoding='utf-8')