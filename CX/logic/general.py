from pydoc import cli
from   flask import request, render_template
from   firebase_admin import firestore
import json
import plotly
from   CX import app
from   CX.logic.functions import reporteGeneral, speedmeter, tablaReporteGeneral, getRangosyPonderaciones, roundPropio
import datetime

#Chart Page
@app.route('/chart_general', methods=['GET', 'POST'])
def chart_general():
    
    #Parametros Trimestre y año (Por Defacto)
    trimestre, year, client = "Todos",  datetime.date.today().year, "Todos"
    client_img = None
        
    #Guardar Parametros URL
    trimestre_input = (request.args.get('trimestre_input'))
    year_input      = (request.args.get('year_input'))
    client_input    = (request.args.get('client_input'))
    
    if(trimestre_input != None):
        trimestre = str(trimestre_input)
        
    if(year_input != None):
        year = int(year_input)
        
    if(client_input != None):
        client = str(client_input)
                
    #Conexion con la DB - KPI's CDC/Consultaria/Proceso Comercial Satisfacción from one specific year
    db = firestore.client()
    
    #Get list Clients
    Clients_list = db.collection("Clientes").order_by("Cliente").get()
    
    if(client == "Todos"):
        CON_KPIS = db.collection('Consultoria_KPIS').where('Year','==',year).get()
        CDC_KPIS = db.collection('CDC_KPIS').where('Year','==',year).get()
        PCS_KPIS = db.collection('PCS_KPIS').where('Year','==', year).get()
    else:
        CON_KPIS   = db.collection('Consultoria_KPIS').where('Year','==',year).where('Cliente','==',client).get()
        CDC_KPIS   = db.collection('CDC_KPIS').where('Year','==',year).where('Cliente','==',client).get()
        PCS_KPIS   = db.collection('PCS_KPIS').where('Year','==', year).where('Cliente','==',client).get()
        client_data = db.collection("Clientes").where('Cliente', '==', client).get()
        for i in client_data:
            client_img = i.to_dict()['Imagen']
            #print(client_img)
        
    # Variables
    #["General", "Lealtad", "Satisfacción", "Esfuerzo", "Valor"]
    c_q1, c_q2, c_q3, c_q4          = reporteGeneral(CON_KPIS) #KPI's Consultoria
    cdc_q1, cdc_q2, cdc_q3, cdc_q4  = reporteGeneral(CDC_KPIS) #KPI's CDC
    pc_q1, pc_q2, pc_q3, pc_q4      = reporteGeneral(PCS_KPIS) #KPI's Proceso comercial satisfacción
        
    avg_general, avg_lealtad, avg_satisfaccion, avg_esfuerzo, avg_valor = 0, 0, 0, 0, 0 
    hayDatos = False
    
    if(trimestre == "Todos"):
        cont = 4
        avg_general_q1, avg_lealtad_q1, avg_satisfaccion_q1, avg_esfuerzo_q1, avg_valor_q1 = tablaReporteGeneral(c_q1, cdc_q1, pc_q1)    
        avg_general_q2, avg_lealtad_q2, avg_satisfaccion_q2, avg_esfuerzo_q2, avg_valor_q2 = tablaReporteGeneral(c_q2, cdc_q2, pc_q2)   
        avg_general_q3, avg_lealtad_q3, avg_satisfaccion_q3, avg_esfuerzo_q3, avg_valor_q3 = tablaReporteGeneral(c_q3, cdc_q3, pc_q3)   
        avg_general_q4, avg_lealtad_q4, avg_satisfaccion_q4, avg_esfuerzo_q4, avg_valor_q4 = tablaReporteGeneral(c_q4, cdc_q4, pc_q4)

        #Trimestres vacios
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
        avg_general, avg_lealtad, avg_satisfaccion, avg_esfuerzo, avg_valor = tablaReporteGeneral(c_q1, cdc_q1, pc_q1)           
    elif(trimestre == "Q2"):
        avg_general, avg_lealtad, avg_satisfaccion, avg_esfuerzo, avg_valor = tablaReporteGeneral(c_q2, cdc_q2, pc_q2)    
    elif(trimestre == "Q3"):
        avg_general, avg_lealtad, avg_satisfaccion, avg_esfuerzo, avg_valor = tablaReporteGeneral(c_q3, cdc_q3, pc_q3) 
    elif(trimestre == "Q4"):
        avg_general, avg_lealtad, avg_satisfaccion, avg_esfuerzo, avg_valor = tablaReporteGeneral(c_q4, cdc_q4, pc_q4) 
        
    if(avg_general != 0):
         hayDatos = True
         
    #Rangos y ponderaciones
    config = db.collection('Rangos_Ponderaciones').where('year','==',int(year)).get()
    
    #Recuperar rangos y ponderaciones desde Firebase
    kpi_nps, kpi_csat, kpi_va, kpi_ces = getRangosyPonderaciones(config)

    fig_esfuerzo     = speedmeter(kpi_ces['kpi_name'],  avg_esfuerzo,     kpi_ces['min'],  kpi_ces['max'],  kpi_ces['ponderacion'])
    fig_satisfaccion = speedmeter(kpi_csat['kpi_name'], avg_satisfaccion, kpi_csat['min'], kpi_csat['max'], kpi_csat['ponderacion'])
    fig_lealtad      = speedmeter(kpi_nps['kpi_name'],  avg_lealtad,      kpi_nps['min'],  kpi_nps['max'],  kpi_nps['ponderacion'])
    fig_valor        = speedmeter(kpi_va['kpi_name'],   avg_valor,        kpi_va['min'],   kpi_va['max'],   kpi_va['ponderacion'])
                    
    graph_esfuerzo     = json.dumps(fig_esfuerzo,     cls=plotly.utils.PlotlyJSONEncoder)
    graph_satisfaccion = json.dumps(fig_satisfaccion, cls=plotly.utils.PlotlyJSONEncoder)
    graph_lealtad      = json.dumps(fig_lealtad,      cls=plotly.utils.PlotlyJSONEncoder)
    graph_valor        = json.dumps(fig_valor,        cls=plotly.utils.PlotlyJSONEncoder)
                
    return render_template('general.html', 
                           kpi_total=roundPropio(avg_general), 
                           trimestre = trimestre,
                           year = year,
                           client = client,
                           client_img = client_img,
                           graphJSON_esfuerzo     = graph_esfuerzo,
                           graphJSON_satisfaccion = graph_satisfaccion,
                           graphJSON_lealtad      = graph_lealtad,
                           graphJSON_valor        = graph_valor,
                           hayDatos               = hayDatos,
                           Clients_list           = Clients_list)
    
    


