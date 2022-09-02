import pandas as pd
import json
from   CX.static.questions.cdc_questions import Preguntas_esfuerzo,Preguntas_satisfaccion,Preguntas_lealtad,Preguntas_valor
import plotly.graph_objects as go
from   plotly.graph_objs import *
from   datetime import date

#Graficar velocimetro
def speedmeter(title, value, delta, red, green, porcentaje):
    fig_total = go.Figure(go.Indicator(
            domain = {'x': [0, 1], 'y': [0, 1]},
            value = value,
            mode = "gauge+number+delta",
            title = {'text': title , 'font': {'size': 18}},
            delta = {'reference': delta},
            gauge = {'axis': {'range': [0, 10]},
                    'bar': {'color': "hsla(120, 100%, 50%, 0.0)"},
                    'steps' : [
                        {'range': [0, red], 'color': "red"},
                        {'range': [red+0.001, green-0.001], 'color': "yellow"},
                        {'range': [green, 10], 'color': "green"}],
                    'threshold' : {'line': {'color': "black", 'width': 6}, 'thickness': 0.85, 'value': value}},
            ),
            Layout(paper_bgcolor='rgba(0,0,0,0)',
                   plot_bgcolor='rgba(0,0,0,0)',
                   margin=dict(l=25, r=25, t=0, b=0), 
                   annotations=[{'x': 0.5, 'y':0.25 
                                      ,'text': porcentaje
                                      ,'font': { 'color': "hsl(36, 100%, 50%)/", 'size': 25, 'family': "Open Sans"}
                                      ,'showarrow':False, 'xanchor':'center' },]),
            )
    return fig_total

#Promedio Q'S
def promedioQuarter(kpi_clients, kpi_name, trimestre):
    avg_kpi_q, cont_q = 0, 0
    for i in kpi_clients:
        if(i.to_dict()[kpi_name] != '' and i.to_dict()['Trimestre'] == trimestre):
            avg_kpi_q = avg_kpi_q + i.to_dict()[kpi_name]
            cont_q += 1
    
    if(cont_q != 0):    
        avg_kpi_q = round(avg_kpi_q/cont_q, 1)
    else:
        avg_kpi_q = "" 
        
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
            kpi1 = {'Cliente':cliente,'Trimestre':1,'kpi_valor':"",'kpi_satisfaccion':"","kpi_lealtad":"",
                        "kpi_esfuerzo":"","kpi_total":""}
            kpi2 = {'Cliente':cliente,'Trimestre':2,'kpi_valor':"",'kpi_satisfaccion':"","kpi_lealtad":"",
                        "kpi_esfuerzo":"","kpi_total":""}
            kpi3 = {'Cliente':cliente,'Trimestre':3,'kpi_valor':"",'kpi_satisfaccion':"","kpi_lealtad":"",
                        "kpi_esfuerzo":"","kpi_total":""}
            kpi4 = {'Cliente':cliente,'Trimestre':4,'kpi_valor':"",'kpi_satisfaccion':"","kpi_lealtad":"",
                        "kpi_esfuerzo":"","kpi_total":""}
            
            for i in range(1,len(cliente_kpis)):
                
                if cliente_kpis[i].to_dict()['Trimestre'] == 1:
                    kpi1 = cliente_kpis[i].to_dict()
                elif cliente_kpis[i].to_dict()['Trimestre'] == 2:
                    kpi2 = cliente_kpis[i].to_dict()
                elif cliente_kpis[i].to_dict()['Trimestre'] == 3:
                    kpi3 = cliente_kpis[i].to_dict()
                elif cliente_kpis[i].to_dict()['Trimestre'] == 4:
                    kpi4 = cliente_kpis[i].to_dict()
                    
            kpi_q1.append(kpi1)
            kpi_q2.append(kpi2)
            kpi_q3.append(kpi3)
            kpi_q4.append(kpi4)
            
    return kpi_q1, kpi_q2, kpi_q3, kpi_q4

#Guardar Listas Trimestres y años
def saveSelectData(CDC_KPIS):
    Trimestres, Years, clientes = [], [], []
    
    for doc in CDC_KPIS:
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
    
    
def carga_preguntas(dataframe,CDC_Respuestas_Ref,Trimestre,Year):
    lista_data = []
    for row in range(len(dataframe)):
        
        data = ""
        kpi_esfuerzo, kpi_esfuerzo_cont, kpi_satisfaccion, kpi_satisfaccion_cont = 0, 0, 0, 0
        kpi_lealtad, kpi_lealtad_cont, kpi_valor, kpi_valor_cont = 0, 0, 0, 0
    
        for column in range(len(dataframe.columns)):
            colname = dataframe.columns[column]
            if dataframe.iloc[row,column] != "" and dataframe.iloc[row,column] != "No Aplica" and not pd.isna(dataframe.iloc[row,column]):
                
                data = data + str('"' + colname.replace(' ','_').replace('"','').replace("'","") + '"'+ " : " + '"'+str(dataframe.iloc[row,column]).replace('"','').replace("'","") +'"'+ ',') 
                
                if colname in Preguntas_valor:
                    kpi_valor += int(dataframe.iloc[row,column])
                    kpi_valor_cont += 1
                elif colname in Preguntas_lealtad:
                    kpi_lealtad += int(dataframe.iloc[row,column])
                    kpi_lealtad_cont +=1
                elif colname in Preguntas_esfuerzo:
                    kpi_esfuerzo += int(dataframe.iloc[row,column])
                    kpi_esfuerzo_cont +=1
                
                for pregunta in Preguntas_satisfaccion:

                    if pregunta in colname:
                        
                        kpi_satisfaccion += int(dataframe.iloc[row,column])
                        kpi_satisfaccion_cont += 1
                
        kpi_valor       = kpi_valor/kpi_valor_cont
        kpi_lealtad     = kpi_lealtad/kpi_lealtad_cont
        kpi_esfuerzo    = kpi_esfuerzo/kpi_esfuerzo_cont
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
        CDC_Respuestas_Ref.add(json.loads(respuesta))
            
        
def carga_kpi(cliente,Ref,Trimestre,Year,kpi_esfuerzo,kpi_satisfaccion,kpi_lealtad,kpi_valor,kpi_total):
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
    
def mappingValues(results):# no se verifica aun si hay espacios o mayusculas
    results.replace(["No satisfecho","Ningún Valor","En Desacuerdo","No Satisfecho","En Desacuerdo	","Ningún Valor","Muy Malo","Muy insatisfecho"],2,inplace=True) 
    results.replace(["Baja Satisfacción","Poco Valor","Casi Nunca","Poco Valor","Malo","Insatisfecho"],4,inplace=True)
    results.replace(["Satisfacción Promedio","Valor Promedio","Normalmente de Acuerdo","Bueno","Neutral","Valor promedio"],6,inplace=True)
    results.replace(["Buena Satisfacción","Gran Valor","Totalmente de Acuerdo","Muy Bueno","Satisfecho","Muy bueno","Gran valor"],8,inplace=True)
    results.replace(["Supera las Expectativas","Muy satisfecho","Muy Satisfecho"],10,inplace=True)
    return results

def SearchClients(results,not_found_list,found_list,Clientes_Data):
    for index, row in results.iterrows():

            Found = False
            Nombre_Cliente = row["Nombre de la empresa a la que pertenece"]
            print(row["Nombre de la empresa a la que pertenece"])
            aux = row["Nombre de la empresa a la que pertenece"].lower().replace(",","").replace(".","").replace("á",'a').replace("é",'e').replace("í",'i').replace("ó",'o').replace("ú",'u') 
            for doc in Clientes_Data:
                aux2 = doc.to_dict()['Cliente'].lower().replace(",","").replace(".","").replace("á",'a').replace("é",'e').replace("í",'i').replace("ó",'o').replace("ú",'u') 
    
                if aux in aux2 or aux2 in aux:
                    
                    Nombre_Cliente = doc.to_dict()['Cliente']
                    results["Nombre de la empresa a la que pertenece"] = results["Nombre de la empresa a la que pertenece"].replace([row["Nombre de la empresa a la que pertenece"]],Nombre_Cliente) 
                            
                    Found = True
                    break
                else:
                    for cliente_encuesta in doc.to_dict()['Encuestas']:
                        aux3 = cliente_encuesta.lower().replace(",","").replace(".","").replace("á",'a').replace("é",'e').replace("í",'i').replace("ó",'o').replace("ú",'u') 
                        
                        if (aux in aux3 or aux3 in aux):
                            Found = True
                            Nombre_Cliente = doc.to_dict()['Cliente']
                            results["Nombre de la empresa a la que pertenece"] = results["Nombre de la empresa a la que pertenece"].replace([row["Nombre de la empresa a la que pertenece"]],Nombre_Cliente) 
                            break
            if Found:
                print("ENTRO EN TRUE")
                found_list.append(Nombre_Cliente)
                print("se encontro : " + Nombre_Cliente)
            else:
                print("ENTRO EN FALSE")
                print(Nombre_Cliente)
                not_found_list.append(Nombre_Cliente)
                print("no se encontro : " + Nombre_Cliente)
                
    return found_list,not_found_list,results
        
    

def carga_preguntas_consultoria(dataframe,Consultoria_Respuestas_Ref,Trimestre,Year,Preguntas_esfuerzo,Preguntas_satisfaccion,Preguntas_lealtad,Preguntas_valor):
    lista_data = []
    for row in range(len(dataframe)):
        
        data = ""
        kpi_esfuerzo, kpi_esfuerzo_cont, kpi_satisfaccion, kpi_satisfaccion_cont = 0, 0, 0, 0
        kpi_lealtad, kpi_lealtad_cont, kpi_valor, kpi_valor_cont = 0, 0, 0, 0
    
        for column in range(len(dataframe.columns)):
            colname = dataframe.columns[column]
            if dataframe.iloc[row,column] != "" and dataframe.iloc[row,column] != "No Aplica" and not pd.isna(dataframe.iloc[row,column]):
                
                data = data + str('"' + colname.replace(' ','_').replace('"','').replace("'","") + '"'+ " : " + '"'+str(dataframe.iloc[row,column]).replace('"','').replace("'","") +'"'+ ',') 
                
                if colname in Preguntas_valor:
                    kpi_valor += int(dataframe.iloc[row,column])
                    kpi_valor_cont += 1
                elif colname in Preguntas_lealtad:
                    kpi_lealtad += int(dataframe.iloc[row,column])
                    kpi_lealtad_cont +=1
                elif colname in Preguntas_esfuerzo:
                    kpi_esfuerzo += int(dataframe.iloc[row,column])
                    kpi_esfuerzo_cont +=1
                
                for pregunta in Preguntas_satisfaccion:

                    if pregunta in colname:
                        
                        kpi_satisfaccion += int(dataframe.iloc[row,column])
                        kpi_satisfaccion_cont += 1
                
        kpi_valor       = kpi_valor/kpi_valor_cont
        kpi_lealtad     = kpi_lealtad/kpi_lealtad_cont
        kpi_esfuerzo    = kpi_esfuerzo/kpi_esfuerzo_cont
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
        Consultoria_Respuestas_Ref.add(json.loads(respuesta))