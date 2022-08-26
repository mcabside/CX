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
    
        
    
    