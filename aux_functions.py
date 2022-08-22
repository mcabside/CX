import pandas as pd
import json
from cdc_questions import Preguntas_esfuerzo,Preguntas_satisfaccion,Preguntas_lealtad,Preguntas_valor


def carga_preguntas(dataframe,CDC_Respuestas_Ref,Trimestre,Year):
    for row in range(len(dataframe)):
        data = ""
        kpi_esfuerzo = 0
        kpi_esfuerzo_cont = 0
        kpi_satisfaccion = 0
        kpi_satisfaccion_cont = 0
        kpi_lealtad = 0
        kpi_lealtad_cont = 0
        kpi_valor = 0
        kpi_valor_cont = 0
        for column in range(len(dataframe.columns)):
            colname = dataframe.columns[column]
            if dataframe.iloc[row,column] != "" and dataframe.iloc[row,column] != "No Aplica" and not pd.isna(dataframe.iloc[row,column]):
                
                data = data + str('"' + colname + '"'+ " : " + '"'+str(dataframe.iloc[row,column]) +'"'+ ',') 
                
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
                    if colname in pregunta:
                        
                        kpi_satisfaccion += int(dataframe.iloc[row,column])
                        kpi_satisfaccion_cont += 1
                
                
        kpi_valor = kpi_valor/kpi_valor_cont
        kpi_lealtad = kpi_lealtad/kpi_lealtad_cont
        kpi_esfuerzo = kpi_esfuerzo/kpi_esfuerzo_cont
        print(kpi_valor)
        print(kpi_lealtad)
        print(kpi_esfuerzo)
        print(data)
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
        CDC_Respuestas_Ref.add(json.loads(data))
            
        
        
    
    