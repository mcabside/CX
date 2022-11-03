#from contextlib import nullcontext
from   audioop import avg
from   types import new_class
import pandas as pd
import json
import plotly.graph_objects as go
from   plotly.graph_objs import *
from   datetime import date
from   flask import flash
import plotly.express as px

#Add Kpi rango y ponderaciones
def addKPIRange(Kpis_Ref, name, min, max, pond, fecha):
     Kpis_Ref.add({
        'kpi_name': name,
        'min': min,
        'max': max,
        'ponderacion': pond,
        'fecha': fecha,
        'year': int(fecha[:4])
    })

#Update Kpi rango y ponderaciones
def updateKPIRange(Kpis_Ref, kpi_q, result):
    for i in kpi_q:
        id = i.id
        if(i.to_dict()['kpi_name'] == "Customer Effort Score (CES)"):
            Kpis_Ref.document(id).update({
                'min': result[0]['min_ces'],
                'max': result[0]['max_ces'],
                'ponderacion': result[0]['ponde_ces']
            })
        elif(i.to_dict()['kpi_name'] == "Net Promoter Score (NPS)"):
            Kpis_Ref.document(id).update({
                'min': result[0]['min_nps'],
                'max': result[0]['max_nps'],
                'ponderacion': result[0]['ponde_nps']
            })
        elif(i.to_dict()['kpi_name'] == "Customer Satisfaction Score (CSAT)"):
            Kpis_Ref.document(id).update({
                'min': result[0]['min_csat'],
                'max': result[0]['max_csat'],
                'ponderacion': result[0]['ponde_csat']
            })
        elif(i.to_dict()['kpi_name'] == "Valor Añadido (VA)"):
            Kpis_Ref.document(id).update({
                'min': result[0]['min_va'],
                'max': result[0]['max_va'],
                'ponderacion': result[0]['ponde_va']
                        })
             
#FiltrarKPIxAño
def filtrarxyear(kpi_clients, year_input):
    aux = [] 
    for i in kpi_clients:
            if(i.to_dict()['Year'] == year_input):
                aux.append(i)
    return aux

#Recuperar rangos y ponderaciones desde Firebase
def getRangosyPonderaciones(config):
    for i in config:
        aux = i.to_dict()
        if aux['kpi_name'] == "Net Promoter Score (NPS)":
            kpi_nps = aux
            
        elif(aux['kpi_name'] == "Customer Satisfaction Score (CSAT)"):
            kpi_csat = aux
           
        elif(aux['kpi_name'] == "Valor Añadido (VA)"):
            kpi_va = aux
          
        elif(aux['kpi_name'] == "Customer Effort Score (CES)"):
            kpi_ces = aux
            
    return kpi_nps, kpi_csat, kpi_va, kpi_ces
    
def reporteGeneral(KPIS):
    # Variables
    q1, q2, q3, q4 = [], [], [], []
    # Q1
    q1.append(promedioQuarter(KPIS, "kpi_esfuerzo",     1))
    q1.append(promedioQuarter(KPIS, "kpi_satisfaccion", 1))
    q1.append(promedioQuarter(KPIS, "kpi_lealtad",      1))
    q1.append(promedioQuarter(KPIS, "kpi_valor",        1))
    q1.append(promedioQuarter(KPIS, "kpi_total",        1))

    # Q2
    q2.append(promedioQuarter(KPIS, "kpi_esfuerzo",     2))
    q2.append(promedioQuarter(KPIS, "kpi_satisfaccion", 2))
    q2.append(promedioQuarter(KPIS, "kpi_lealtad",      2))
    q2.append(promedioQuarter(KPIS, "kpi_valor",        2))
    q2.append(promedioQuarter(KPIS, "kpi_total",        2))
    # Q3
    q3.append(promedioQuarter(KPIS, "kpi_esfuerzo",     3))
    q3.append(promedioQuarter(KPIS, "kpi_satisfaccion", 3))
    q3.append(promedioQuarter(KPIS, "kpi_lealtad",      3))
    q3.append(promedioQuarter(KPIS, "kpi_valor",        3))
    q3.append(promedioQuarter(KPIS, "kpi_total",        3))
    # Q4
    q4.append(promedioQuarter(KPIS, "kpi_esfuerzo",     4))
    q4.append(promedioQuarter(KPIS, "kpi_satisfaccion", 4))
    q4.append(promedioQuarter(KPIS, "kpi_lealtad",      4))
    q4.append(promedioQuarter(KPIS, "kpi_valor",        4))
    q4.append(promedioQuarter(KPIS, "kpi_total",        4))
    
    return q1, q2, q3, q4

#Table Reporte General
def tablaReporteGeneral(consul, cdc, pc):
    #Contador
    cont = 3     #Es 3 porque hay 3 reportes
    avg_general, avg_lealtad, avg_satisfaccion, avg_esfuerzo, avg_valor = 0, 0, 0, 0, 0
    
    #Check Vacio
    if(consul[4] == 0.0):   #Si no hay datos de ese reporte para ese trimestre, pos 4 es KPI General
        consul = [0.0, 0,0, 0.0, 0.0, 0.0]
        cont = cont -1
        
    if(cdc[4] == 0.0):      #Si no hay datos de ese reporte para ese trimestre
        cdc = [0.0, 0.0, 0.0, 0.0, 0.0]
        cont = cont -1
        
    if(pc[4] == 0.0):       #Si no hay datos de ese reporte para ese trimestre
        pc = [0.0, 0.0, 0.0, 0.0, 0.0]
        cont = cont -1
        
    #Verificar divisin entre 0 ["CES","CSAT","NPS","VA","General"]
    if(cont > 0):
        avg_esfuerzo     = (consul[0] + cdc[0] + pc[0]) / cont 
        avg_satisfaccion = (consul[1] + cdc[1] + pc[1]) / cont
        avg_lealtad      = (consul[2] + cdc[2] + pc[2]) / cont
        avg_valor        = (consul[3] + cdc[3] + pc[3]) / cont
        avg_general      = (consul[4] + cdc[4] + pc[4]) / cont
      
    return avg_general, avg_lealtad, avg_satisfaccion, avg_esfuerzo, avg_valor

#Delta KPI Qi vs KPI Qi-1
def deltaKPI(kpis_client, trimestre_input):
    kpi_client, kpi_delta = [], []
    
    #CALCULATE DELTA     
    for i in kpis_client:
    
    #GET KPI SPECIFIC QUARTER 
        if(i.to_dict()['Trimestre'] == int(trimestre_input)):
            kpi_client.append(i)
            
    #GET KPI PREVIUS
        if(int(trimestre_input) != 1 and (i.to_dict()['Trimestre'] == (int(trimestre_input)-1))):
            kpi_delta.append(i)
            
    return kpi_client, kpi_delta

#Graficar velocimetro
def speedmeter(title, value, red, green, porcentaje, delta=None):
    if delta != None:
        delta = roundPropio(float(delta))
        
    fig_total = go.Figure(go.Indicator(
            domain = {'x': [0, 1], 'y': [0, 1]},
            value = roundPropio(float(value)),
            mode = "gauge+number+delta",
            title = {'text': title , 'font': {'size': 16, 'family': "Arial"}, },
            delta = {'reference': delta },
            gauge = {'axis': {'range': [0, 10]},
                    'bar': {'color': "hsla(120, 100%, 50%, 0.0)"},
                    'borderwidth': 0,
                    'steps' : [
                        {'range': [0, red], 'color': "#EA4335"},
                        {'range': [red+0.001, green-0.001], 'color': "#FEDC41"},
                        {'range': [green, 10], 'color': "#01C48B"}],
                    'threshold' : {'line': {'color': "#454E52", 'width': 6}, 'thickness': 0.85, 'value': value}},
            ),Layout(
                   height=400,
                   paper_bgcolor='rgba(0,0,0,0)',
                   plot_bgcolor='rgba(0,0,0,0)',                   
                   margin=dict(l=25, r=25, t=0, b=0),
                   annotations=[{'x': 0.5, 'y':0.25
                                      ,'text':str(porcentaje)+"%"
                                      ,'font': { 'color': "hsl(36, 100%, 50%)", 'size': 20, 'family': "Arial"}
                                      ,'showarrow':False, 'xanchor':'center' }]),
            )
    return fig_total

#Promedio Q'S
def promedioQuarter(kpi_clients, kpi_name, trimestre):
    avg_kpi_q, cont_q = 0, 0
    for i in kpi_clients:
        if(i.to_dict()['Trimestre'] == trimestre):
            avg_kpi_q = avg_kpi_q + i.to_dict()[kpi_name]
            cont_q += 1
    if(cont_q != 0):    
        avg_kpi_q = roundPropio(avg_kpi_q/cont_q)
    else:
        avg_kpi_q = 0.0 
        
    return avg_kpi_q

#Tabla dinamica
def tablaDinamica(kpi_clients):
    kpi, kpi_q1, kpi_q2, kpi_q3, kpi_q4  = [], [], [], [], []
    for i, doc in enumerate(kpi_clients):
            if i == 0:
                kpi.append([doc.to_dict()['Cliente'], doc])
            else:
                esta = False
                posi = 0
                for j, client in enumerate(kpi):
                    if doc.to_dict()['Cliente'] in client: 
                        posi = j
                        esta = True
                        break
                if esta:
                    kpi[posi].append(doc)
                else:
                    kpi.append([doc.to_dict()['Cliente'], doc])
                    
    for cliente_kpis in kpi:
            cliente = cliente_kpis[0]
            kpi1 = {'Cliente':cliente,'Trimestre':1,'kpi_valor':0.0,'kpi_satisfaccion':0.0,"kpi_lealtad":0.0,
                        "kpi_esfuerzo":0.0,"kpi_total":0.0}
            kpi2 = {'Cliente':cliente,'Trimestre':2,'kpi_valor':0.0,'kpi_satisfaccion':0.0,"kpi_lealtad":0.0,
                        "kpi_esfuerzo":0.0,"kpi_total":0.0}
            kpi3 = {'Cliente':cliente,'Trimestre':3,'kpi_valor':0.0,'kpi_satisfaccion':0.0,"kpi_lealtad":0.0,
                        "kpi_esfuerzo":0.0,"kpi_total":0.0}
            kpi4 = {'Cliente':cliente,'Trimestre':4,'kpi_valor':0.0,'kpi_satisfaccion':0.0,"kpi_lealtad":0.0,
                        "kpi_esfuerzo":0.0,"kpi_total":0.0}
            
            for i in range(1, len(cliente_kpis)):
                if cliente_kpis[i].to_dict()['Trimestre'] == 1:
                    kpi1 = changeDecimal(cliente_kpis[i].to_dict())
                elif cliente_kpis[i].to_dict()['Trimestre'] == 2:
                    kpi2 = changeDecimal(cliente_kpis[i].to_dict())
                elif cliente_kpis[i].to_dict()['Trimestre'] == 3:
                    kpi3 = changeDecimal(cliente_kpis[i].to_dict())
                elif cliente_kpis[i].to_dict()['Trimestre'] == 4:
                    kpi4 = changeDecimal(cliente_kpis[i].to_dict())
                    
            kpi_q1.append(kpi1)
            kpi_q2.append(kpi2)
            kpi_q3.append(kpi3)
            kpi_q4.append(kpi4)
            
    return kpi_q1, kpi_q2, kpi_q3, kpi_q4

#Change decimals
def changeDecimal(client_kpi):
    new_client_kpi = {
        'kpi_lealtad':      roundPropio(client_kpi['kpi_lealtad']),
        'kpi_valor':        roundPropio(client_kpi['kpi_valor']),
        'kpi_satisfaccion': roundPropio(client_kpi['kpi_satisfaccion']),
        'kpi_total':        roundPropio(client_kpi['kpi_total']),
        'kpi_esfuerzo':     roundPropio(client_kpi['kpi_esfuerzo']),
        'Cliente':          client_kpi['Cliente'],
        'Year':             client_kpi['Year'],
        'Trimestre':        client_kpi['Trimestre']
    }
    return new_client_kpi

#Guardar Listas Trimestres y años
def saveSelectData(LIST_KPIS):
    Trimestres, Years, clientes = [], [], []
    
    for doc in LIST_KPIS:
        if doc.to_dict()["Trimestre"] not in Trimestres:
            Trimestres.append(doc.to_dict()["Trimestre"])
            
        if doc.to_dict()["Year"] not in Years:
            Years.append(doc.to_dict()["Year"])
            
        if doc.to_dict()["Cliente"] not in clientes:
            clientes.append(doc.to_dict()["Cliente"])
    #Ordenar
    Trimestres.sort()
    clientes.sort()
    Years.sort()
    return Trimestres, Years, clientes
      
#Validación parametros
def validarParametros(trimestre_input, year_input, Trimestres, Years):
    if trimestre_input is None:
        if len(Trimestres) > 0:
            trimestre_input = Trimestres[len(Trimestres)-1]
        else:
            trimestre_input = 1
    if year_input is None:
        if len(Years) > 0:
            year_input = Years[len(Years)-1]
        else:
            year_input = int(date.today().year)
    return trimestre_input, year_input
    
#Cargar preguntas en Firebase
def carga_preguntas(dataframe,Respuestas_Ref,Trimestre,Year,Preguntas_esfuerzo,Preguntas_satisfaccion,Preguntas_lealtad,Preguntas_valor,area=False):
    lista_data = []
    for row in range(len(dataframe)):
        
        data = ""
        kpi_valor_cont, kpi_esfuerzo_cont, kpi_satisfaccion_cont, kpi_lealtad_cont = 0, 0, 0, 0
        kpi_satisfaccion, kpi_lealtad, kpi_valor, kpi_esfuerzo = 0, 0, 0, 0
    
        for column in range(len(dataframe.columns)):
            colname = dataframe.columns[column]
            if colname == "¿Qué tan satisfecho se encuentra con el Servicio de Consultoría recibido de ABSIDE?" and str(dataframe.iloc[row,column]).isnumeric() and area == 'Consultoria Corta': # en el caso de consultoria corta
                dataframe.iloc[row,column] = int(dataframe.iloc[row,column]) *2
                
            if colname == "¿Como le parece en general el aspecto Profesional de nuestra Compañía?": #va del 1 al 4, quizas revisar area si esta pregunta se repite
                dataframe.iloc[row,column] = int(dataframe.iloc[row,column]) + (int(dataframe.iloc[row,column])/4)
                
            if dataframe.iloc[row,column] != "" and dataframe.iloc[row,column] != "No Aplica" and not pd.isna(dataframe.iloc[row,column]):
                
                data = data + str('"' + colname.replace(' ','_').replace('"','').replace("'","").replace(":","").replace("\t","").replace("(","_").replace(")","_") + '"'+ " : " + '"'+str(dataframe.iloc[row,column]).replace('"','').replace("'","").replace(":","") +'"'+ ',') 
                
                if colname in Preguntas_valor:
                    kpi_valor += int(dataframe.iloc[row,column])
                    kpi_valor_cont += 1
                elif colname in Preguntas_lealtad:
                    kpi_lealtad += int(dataframe.iloc[row,column])
                    kpi_lealtad_cont +=1
                elif colname in Preguntas_esfuerzo:
                    
                    if area == "Proceso Comercial Declinación":
                        kpi_esfuerzo += int(dataframe.iloc[row,column])*2
                        
                    else:
                        kpi_esfuerzo += int(dataframe.iloc[row,column])
                    kpi_esfuerzo_cont +=1
                                        
                for pregunta in Preguntas_satisfaccion:

                    if pregunta in colname:
                        
                        if area == "Proceso Comercial Declinación":
                        
                            kpi_satisfaccion += int(dataframe.iloc[row,column])*2
                            
                        else:
                            kpi_satisfaccion += int(dataframe.iloc[row,column])
                        kpi_satisfaccion_cont += 1
                            
                            
        kpi_valor        = kpi_valor/kpi_valor_cont
        kpi_lealtad      = kpi_lealtad/kpi_lealtad_cont
        kpi_esfuerzo     = kpi_esfuerzo/kpi_esfuerzo_cont
        kpi_satisfaccion = kpi_satisfaccion/kpi_satisfaccion_cont
                
        #kpi_lealtad = kp
        data = data +str('"' + 'kpi_valor"' + ':' +'"'+ str(kpi_valor)+'"' + ',') 
        data = data +str('"' + 'kpi_lealtad"' + ':' +'"'+ str(kpi_lealtad)+'"' + ',') 
        data = data +str('"' + 'kpi_satisfaccion"' + ':' +'"'+ str(kpi_satisfaccion)+'"' + ',') 
        data = data +str('"' + 'kpi_esfuerzo"' + ':' +'"'+ str(kpi_esfuerzo)+'"' + ',') 
        data = data +str('"' + 'Trimestre"' + ':' +'"'+ str(Trimestre)+'"' + ',') 
        data = data +str('"' +'Year"'+ ':' + '"'+str(Year)+'"' )  
        data =  data.replace("\n", "")

        data = "{" + data + "}"
        lista_data.append(data)
        
    for respuesta in lista_data:
        #print(respuesta)
        Respuestas_Ref.add(json.loads(respuesta))
            
#Cargar KPI's en firebase    
def carga_kpi(cliente,Ref,Trimestre,Year,kpi_esfuerzo,kpi_satisfaccion,kpi_lealtad,kpi_valor,kpi_total):
    try:
        Ref.add({
                    'Cliente': cliente,
                    'Trimestre': Trimestre,
                    'Year': Year,
                    'kpi_esfuerzo':kpi_esfuerzo,
                    'kpi_lealtad':kpi_lealtad,
                    'kpi_valor':kpi_valor,
                    'kpi_satisfaccion':kpi_satisfaccion,
                    'kpi_total':kpi_total
            })
    except:
        flash("Error al cargar KPI's", "error")
        
#Reemplazar valores de los archivos planos por valores numericos    
def mappingValues(results):# no se verifica aun si hay espacios o mayusculas
    results.replace(["No satisfecho","Ningún Valor","En Desacuerdo","No Satisfecho","En Desacuerdo	","En desacuerdo","Ningún Valor","Muy Malo","Muy insatisfecho","MUY MALO","1 . MUY MALO","1.MUY MALO","1. No es Profesional"],2,inplace=True) 
    results.replace(["Baja Satisfacción","Poco Valor","Casi Nunca","Poco Valor","Malo","Insatisfecho","MALO","2. MALO","2.MALO","2. No muy Profesional"],4,inplace=True)
    results.replace(["Satisfacción Promedio","Valor Promedio","Normalmente de Acuerdo","Bueno","Neutral","Valor promedio","REGULAR","3. REGULAR","3.REGULAR","3. Profesional","Ni de acuerdo ni en desacuerdo"],6,inplace=True)
    results.replace(["Buena Satisfacción","Gran Valor","De acuerdo","Muy Bueno","Satisfecho","Muy bueno","Gran valor","BUENO","4. BUENO","4.BUENO","4. Muy Profesional"],8,inplace=True)
    results.replace(["Totalmente de Acuerdo","Totalmente de acuerdo","Supera las Expectativas","Muy satisfecho","Muy Satisfecho","MUY BUENO","5.MUY BUENO"],10,inplace=True)
    return results

#Buscar clientes en Firebase
def SearchClients(results,not_found_list,found_list,Clientes_Data):
    columna_cliente =""
    if "Nombre de la empresa a la que pertenece" in results.columns:
        columna_cliente = "Nombre de la empresa a la que pertenece"
    elif "NOMBRE DE LA EMPRESA (CLIENTE):							" in results.columns:
        columna_cliente = "NOMBRE DE LA EMPRESA (CLIENTE):							"
    for index, row in results.iterrows():
            Found = False
            Nombre_Cliente = row[columna_cliente]
            print(row[columna_cliente])
            aux = row[columna_cliente].lower().replace(",","").replace(".","").replace("á",'a').replace("é",'e').replace("í",'i').replace("ó",'o').replace("ú",'u') 
            for doc in Clientes_Data:
                aux2 = doc.to_dict()['Cliente'].lower().replace(",","").replace(".","").replace("á",'a').replace("é",'e').replace("í",'i').replace("ó",'o').replace("ú",'u') 
    
                if aux in aux2 or aux2 in aux:
                    
                    Nombre_Cliente = doc.to_dict()['Cliente']
                    results[columna_cliente] = results[columna_cliente].replace([row[columna_cliente]],Nombre_Cliente) 
                            
                    Found = True
                    break
                else:
                    for cliente_encuesta in doc.to_dict()['Encuestas']:
                        aux3 = cliente_encuesta.lower().replace(",","").replace(".","").replace("á",'a').replace("é",'e').replace("í",'i').replace("ó",'o').replace("ú",'u') 
                        
                        if (aux in aux3 or aux3 in aux):
                            Found = True
                            Nombre_Cliente = doc.to_dict()['Cliente']
                            results[columna_cliente] = results[columna_cliente].replace([row[columna_cliente]],Nombre_Cliente) 
                            break
            if Found:
                found_list.append(Nombre_Cliente)
                print("se encontro : " + Nombre_Cliente)
            else:
                print(Nombre_Cliente)
                not_found_list.append(Nombre_Cliente)
                print("no se encontro : " + Nombre_Cliente)
                
    return found_list,not_found_list,results
    
def getHistorico(Datos,Cliente,KPI,Area):
    
    historico, periodos, valores = [], [], []
   
    for doc in Datos:
        if doc.to_dict()["Cliente"] == Cliente:
            historico.append([doc.to_dict()["Trimestre"],doc.to_dict()["Year"],doc.to_dict()[KPI]])
    historico = OrderPeriods(historico)
    for valor in historico:
        periodos.append("Q" + str(valor[0]) + " " + str(valor[1]))
        valores.append(valor[2])
    
    fig = px.line(x=periodos, y=valores,labels={'x':'períodos', 'y':KPI[4:]}, title='Historico ' + KPI[4:] + " " + Cliente + " " + Area,
                  markers=True,text=valores)
    fig.update_layout(yaxis_range=[0,10.5])
    fig.update_traces(textposition="bottom center")
    return fig
        
def OrderPeriods(periodos):
    periodos_ord = []
    periodos_len =len(periodos)
    min_year = 99999
    min_trim = 5
    index=0
    while(len(periodos_ord)!=periodos_len):
        for periodo in periodos:
            if periodo[1] < min_year:
                min_year = periodo[1]
        
        for idx,periodo in enumerate(periodos):
            if periodo[0] < min_trim and periodo[1] == min_year:
                min_trim = periodo[0]
                index = idx
        
        
        periodos_ord.append([min_trim,min_year,periodos[index][2]])
        periodos.pop(index)
        min_year = 99999
        min_trim = 5
        index = 0
    return periodos_ord
    
def OrderClientsRankings(KPIS):
    periodos = []
    trimestres = []
    years = []
    cliente_lealtades = []
    
    for doc in KPIS:
        trimestre = doc.to_dict()["Trimestre"] 
        year = doc.to_dict()["Year"]
        cliente = doc.to_dict()["Cliente"]
        lealtad = doc.to_dict()["kpi_lealtad"]
        cliente_lealtad = [cliente,lealtad,trimestre,year]
        cliente_lealtades.append(cliente_lealtad)
        periodo = [trimestre,year]
        if periodo in periodos:
            None
        else:
            periodos.append(periodo)
            
    #periodos = OrderPeriods(periodos)
    return periodos

#Funcion para redondear personalizada
def roundPropio(num):
    aux  = num - int(num)
    aux2 = aux*10 - int(aux*10) 
    if(aux2 != 0 and aux2 >= 0.5): 
        return round(num+0.01, 1)
    else:
        return round(num, 1)

def unificarClientes(lista_clientes, lista_firebase):
    for doc in lista_firebase:
        if doc not in lista_clientes:
            lista_clientes.append(doc)
    return lista_clientes