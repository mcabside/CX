import pandas as pd
import json


def carga_preguntas(dataframe,CDC_Respuestas_Ref,Trimestre,Year):
    for row in range(len(dataframe)):
        data = ""
        for column in range(len(dataframe.columns)):
            colname = dataframe.columns[column]
            if dataframe.iloc[row,column] != "" and dataframe.iloc[row,column] != "No Aplica" and not pd.isna(dataframe.iloc[row,column]):
                data = data + str('"' + colname + '"'+ " : " + '"'+str(dataframe.iloc[row,column]) +'"'+ ',') 
                #print(colname)
                #print(colname.replace("\n"," "))
                #data.append(colname + " : " + str(dataframe.iloc[row,column]))
        #data.append("Trimestre : " + str(Trimestre))
        data = data +str('"' + 'Trimestre"' + ':' +'"'+ str(Trimestre)+'"' + ',') 
        #data.append("Year : " + str(Year))  
        data = data +str('"' +'Year"'+ ':' + '"'+str(Year)+'"' )  
        
        data =  data.replace("\n", "")
        print(data)
        data = "{" + data + "}"
        CDC_Respuestas_Ref.add(json.loads(data))
            
        
        
    
    