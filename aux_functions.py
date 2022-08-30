import pandas as pd
import json
from static.questions.cdc_questions import Preguntas_esfuerzo,Preguntas_satisfaccion,Preguntas_lealtad,Preguntas_valor
import plotly.graph_objects as go

#Graficar velocimetro
def speedmeter(title, value):
    fig_total = go.Figure(go.Indicator(
            domain = {'x': [0, 1], 'y': [0, 1]},
            value = value,
            mode = "gauge+number+delta",
            title = {'text': title},
            gauge = {'axis': {'range': [0, 10]},
                    'bar': {'color': "hsla(120, 100%, 50%, 0.0)"},
                    'steps' : [
                        {'range': [0, 7], 'color': "red"},
                        {'range': [7, 8], 'color': "orange"},
                        {'range': [8, 10], 'color': "green"}],
                    'threshold' : {'line': {'color': "black", 'width': 6}, 'thickness': 0.85, 'value': value}}))
    return fig_total

#Promedio Q1
def promedioQuarter(kpi_q):
    avg_q, cont_q = 0, 0
    for i in kpi_q:
        if(i['kpi_total'] != ''):
            avg_q = avg_q + i['kpi_total']
            cont_q += 1
        
    if(cont_q != 0):    
        avg_q = avg_q/cont_q
        
    return avg_q

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
          
    Trimestres.sort()
    clientes.sort()
    Years.sort()
    return Trimestres, Years, clientes
      

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
            
        
def carga_kpi(cliente,CDC_KPI_Ref,Trimestre,Year,kpi_esfuerzo,kpi_satisfaccion,kpi_lealtad,kpi_valor,kpi_total):
    CDC_KPI_Ref.add({
                        'Cliente': cliente,
                        'Trimestre': Trimestre,
                        'Year': Year,
                        'kpi_esfuerzo':kpi_esfuerzo,
                        'kpi_lealtad':kpi_lealtad,
                        'kpi_valor':kpi_valor,
                        'kpi_satisfaccion':kpi_satisfaccion,
                        'kpi_total':kpi_total
                    })
    
        
    
    