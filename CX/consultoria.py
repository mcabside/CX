from   flask import request, render_template
from   firebase_admin import firestore
import json
import plotly

from CX import app
from CX.functions import saveSelectData, speedmeter, promedioQuarter, tablaDinamica, validarParametros, carga_kpi, carga_preguntas

#Carga Respuestas CDC
def cargaRespuestasConsultoria(db, Year,Trimestre, results, found_list):
    
    query_trimestre = db.collection('CDC_Consultoria').where('Year', '==',str(Year) ).where('Trimestre', '==', str(Trimestre)).get()
        
    if len(query_trimestre)>0:
        print("ya se ingreso el archivo")
                
    else:
        CDC_Respuestas_Ref = db.collection("CDC_Respuestas")
        carga_preguntas(results, CDC_Respuestas_Ref,Trimestre,Year)
        CDC_KPI_Ref       = db.collection("CDC_KPIS")
        found_set         = set(found_list)
        found_list_unique = list(found_set)
        
        for cliente in found_list_unique:
            kpi_esfuerzo, kpi_satisfaccion, kpi_lealtad, kpi_valor, numero_de_respuestas = 0, 0, 0, 0, 0
            query_kpi = db.collection('CDC_Respuestas').where('Year', '==',str(Year) ).where('Trimestre', '==', str(Trimestre)).where("Nombre_de_la_empresa_a_la_que_pertenece", '==', cliente).get()
            
            for doc in query_kpi:
                
                kpi_esfuerzo     += (float(doc.to_dict()['kpi_esfuerzo']))
                kpi_satisfaccion += (float(doc.to_dict()['kpi_satisfaccion']))
                kpi_lealtad      += (float(doc.to_dict()['kpi_lealtad']))
                kpi_valor        += (float(doc.to_dict()['kpi_valor']))
                
                numero_de_respuestas += 1
                
            kpi_esfuerzo     = round(kpi_esfuerzo/numero_de_respuestas, 2)
            kpi_satisfaccion = round(kpi_satisfaccion/numero_de_respuestas,2)
            kpi_lealtad      = round(kpi_lealtad/numero_de_respuestas,2)
            kpi_valor        = round(kpi_valor/numero_de_respuestas,2)
            kpi_total        = round((kpi_esfuerzo*0.20) + (kpi_satisfaccion*0.35) + (kpi_lealtad*0.35) + (kpi_valor*0.10), 2)
            
            carga_kpi(cliente,CDC_KPI_Ref,Trimestre,Year,kpi_esfuerzo,kpi_satisfaccion,kpi_lealtad,kpi_valor,kpi_total) 


#Chart Page
@app.route('/chart_consultoria', methods=['GET', 'POST'])
def chart_consultoria():
    
    return render_template('test.html')


