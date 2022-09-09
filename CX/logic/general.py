from tkinter.tix import Tree
from   flask import request, render_template
from   firebase_admin import firestore
import json
import plotly
from CX import app
from CX.logic.functions import reporteGeneral, speedmeter, testReporteGeneral

#Chart Page
@app.route('/chart_general', methods=['GET', 'POST'])
def chart_general():
    
    #Parametros Trimestre y año
    trimestre, year = "Todos", 2022
    
    #Guardar Parametros URL
    trimestre_input = (request.args.get('trimestre_input'))
    year_input      = (request.args.get('year_input'))
    
    if(trimestre_input != None):
        trimestre = str(trimestre_input)
        
    if(year_input != None):
        year = int(year_input)
        
    #Conexion con la DB - KPI's CDC/Constultaria/Proceso Comercial Satisfacción from one specific year
    db = firestore.client()
    CON_KPIS = db.collection('Consultoria_KPIS').where('Year','==',year).get()
    CDC_KPIS = db.collection('CDC_KPIS').where('Year','==',year).get()
    PCS_KPIS = db.collection('PCS_KPIS').where('Year','==', year).get()
    
    # Variables
    #["General", "Lealtad", "Satisfacción", "Esfuerzo", "Valor"]
    c_q1, c_q2, c_q3, c_q4          = reporteGeneral(CON_KPIS) #KPI's Consultoria
    cdc_q1, cdc_q2, cdc_q3, cdc_q4  = reporteGeneral(CDC_KPIS) #KPI's CDC
    pc_q1, pc_q2, pc_q3, pc_q4      = reporteGeneral(PCS_KPIS) #KPI's Proceso comercial satisfacción
        
    avg_general, avg_lealtad, avg_satisfaccion, avg_esfuerzo, avg_valor = 0, 0, 0, 0, 0 
    hayDatos = False
    
    if(trimestre == "Todos"):
        cont = 4
        avg_general_q1, avg_lealtad_q1, avg_satisfaccion_q1, avg_esfuerzo_q1, avg_valor_q1 = testReporteGeneral(c_q1, cdc_q1, pc_q1)    
        avg_general_q2, avg_lealtad_q2, avg_satisfaccion_q2, avg_esfuerzo_q2, avg_valor_q2 = testReporteGeneral(c_q2, cdc_q2, pc_q2)   
        avg_general_q3, avg_lealtad_q3, avg_satisfaccion_q3, avg_esfuerzo_q3, avg_valor_q3 = testReporteGeneral(c_q3, cdc_q3, pc_q3)   
        avg_general_q4, avg_lealtad_q4, avg_satisfaccion_q4, avg_esfuerzo_q4, avg_valor_q4 = testReporteGeneral(c_q4, cdc_q4, pc_q4)

        #Vacio
        if(avg_general_q1 == 0):
            cont = cont - 1
        if(avg_general_q2 == 0):
            cont = cont - 1
        if(avg_general_q3 == 0):
            cont = cont - 1
        if(avg_general_q4 == 0):
            cont = cont - 1
        
        if(cont > 0):
            avg_general      = (avg_general_q1 + avg_general_q2 + avg_general_q3 + avg_general_q4) / cont
            avg_satisfaccion = (avg_satisfaccion_q1 + avg_satisfaccion_q2 + avg_satisfaccion_q3 + avg_satisfaccion_q4) / cont
            avg_lealtad      = (avg_lealtad_q1 + avg_lealtad_q2 + avg_lealtad_q3 + avg_lealtad_q4) / cont
            avg_esfuerzo     = (avg_esfuerzo_q1 + avg_esfuerzo_q2 + avg_esfuerzo_q3 + avg_esfuerzo_q4) / cont
            avg_valor        = (avg_valor_q1 + avg_valor_q2 + avg_valor_q3 + avg_valor_q4) / cont
          
    elif(trimestre == "Q1"):
        avg_general, avg_lealtad, avg_satisfaccion, avg_esfuerzo, avg_valor = testReporteGeneral(c_q1, cdc_q1, pc_q1)           
    elif(trimestre == "Q2"):
        avg_general, avg_lealtad, avg_satisfaccion, avg_esfuerzo, avg_valor = testReporteGeneral(c_q2, cdc_q2, pc_q2)    
    elif(trimestre == "Q3"):
        avg_general, avg_lealtad, avg_satisfaccion, avg_esfuerzo, avg_valor = testReporteGeneral(c_q3, cdc_q3, pc_q3) 
    elif(trimestre == "Q4"):
        avg_general, avg_lealtad, avg_satisfaccion, avg_esfuerzo, avg_valor = testReporteGeneral(c_q4, cdc_q4, pc_q4) 
        
    if(avg_general != 0):
         hayDatos = True
         
    fig_esfuerzo     = speedmeter("Customer Effort Score (CES)", avg_esfuerzo,7.1, 8.2, "20%")
    fig_satisfaccion = speedmeter("Customer Satisfaction Score (CSAT)", avg_satisfaccion, 7.4, 8.5, "35%")
    fig_lealtad      = speedmeter("Net Promoter Score (NPS)", avg_lealtad, 6.9, 9,"35%")
    fig_valor        = speedmeter("Valor Añadido (VA)",  avg_valor, 6.4, 7.5, "10%")

    graphJSON_esfuerzo     = json.dumps(fig_esfuerzo,     cls=plotly.utils.PlotlyJSONEncoder)
    graphJSON_satisfaccion = json.dumps(fig_satisfaccion, cls=plotly.utils.PlotlyJSONEncoder)
    graphJSON_lealtad      = json.dumps(fig_lealtad,      cls=plotly.utils.PlotlyJSONEncoder)
    graphJSON_valor        = json.dumps(fig_valor,        cls=plotly.utils.PlotlyJSONEncoder)
                
    return render_template('general.html', 
                           kpi_total=round(avg_general, 2), 
                           trimestre = trimestre,
                           year = year,
                           graphJSON_esfuerzo     = graphJSON_esfuerzo,
                           graphJSON_satisfaccion = graphJSON_satisfaccion,
                           graphJSON_lealtad      = graphJSON_lealtad,
                           graphJSON_valor        = graphJSON_valor,
                           hayDatos = hayDatos)
    
    


