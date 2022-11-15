from   flask import request, render_template, flash
from   firebase_admin import firestore
import json
import plotly
from   CX import app
from   CX.logic.functions import reporteGeneral, speedmeter, tablaReporteGeneral, getRangosyPonderaciones, roundPropio, addOthersYear, filterClients
import datetime

#Global variables
CON_KPIS, PCS_KPIS, CDC_KPIS, clients_name, clients_list, year_cargados  = [], [], [], [], [], []

#Chart Page
@app.route('/chart_general', methods=['GET', 'POST'])
def chart_general():
    
    #Global variables
    global CON_KPIS, PCS_KPIS, CDC_KPIS, clients_name, clients_list, year_cargados
    
    #Local variables
    CON_KPIS_USE, CDC_KPIS_USE, PCS_KPIS_USE = [], [], []
    trimestre, year, client = "Todos",  datetime.date.today().year, "Todos"
    client_img = None
    
    #Conexión con la DB
    db = firestore.client()
    
    #Guardar Parametros URL
    trimestre_input = request.form.get('trimestre_input')
    year_input      = request.form.get('year_input')
    client_input    = request.form.get('client_input')
    
    #Validar inputs
    if(trimestre_input != None):
        trimestre = str(trimestre_input)
        
    if(year_input != None):
        year = int(year_input)
        
    if(client_input != None):
        client = str(client_input)
                            
    if request.method == "GET":
        
        #Firts load data
        if(len(year_cargados) == 0):
            try:
                #Get KPI's from one year 
                CON_KPIS = db.collection('Consultoria_KPIS').where('Year','==', year).get()
                CDC_KPIS = db.collection('CDC_KPIS').where('Year','==', year).get()
                PCS_KPIS = db.collection('PCS_KPIS').where('Year','==', year).get()
                
                year_cargados.append(year)
            except:
                flash("Error al cargas los cargos del periodo "+year, "Error")
        
        #Client list 
        if(len(clients_name) == 0):
            try:
                #Get list Clients
                clients_list = db.collection("Clientes").order_by("Cliente").get()
                
                #Get all clients name
                for doc in clients_list:
                    if doc.to_dict()["Cliente"] not in clients_name:
                        clients_name.append(doc.to_dict()["Cliente"])         
                clients_name.sort() #Ordenar
            except:
                flash("Error al cargas los cargos de clientes del periodo "+year, "Error")

        CON_KPIS_USE = CON_KPIS
        CDC_KPIS_USE = CDC_KPIS
        PCS_KPIS_USE = PCS_KPIS
            
    if request.method == "POST":
         
        if(year in year_cargados):
            
            #Fitrar por cliente
            if(client_input != "Todos"): 
                CON_KPIS_USE = filterClients(CON_KPIS, client_input, year)
                CDC_KPIS_USE = filterClients(CDC_KPIS, client_input, year)
                PCS_KPIS_USE = filterClients(PCS_KPIS, client_input, year)
                            
            else:
                CON_KPIS_USE = filterClients(CON_KPIS, None, year)
                CDC_KPIS_USE = filterClients(CDC_KPIS, None, year)
                PCS_KPIS_USE = filterClients(PCS_KPIS, None, year)
                        
        else: #ADD NEW DATA 
            
            try:
                CON_KPIS_NEW_DATA    = db.collection('Consultoria_KPIS').where('Year','==',year).get()
                CDC_KPIS_NEW_DATA    = db.collection('CDC_KPIS').where('Year','==',year).get()
                PCS_KPIS_NEW_DATA    = db.collection('PCS_KPIS').where('Year','==', year).get()
                
                year_cargados.append(year)

                #Validacion, Add data 
                if(len(CON_KPIS_NEW_DATA) > 0):
                    CON_KPIS = CON_KPIS + CON_KPIS_NEW_DATA
                    
                if(len(CDC_KPIS_NEW_DATA) > 0):
                    CDC_KPIS = CON_KPIS + CDC_KPIS_NEW_DATA
                    
                if(len(PCS_KPIS_NEW_DATA) > 0):
                    PCS_KPIS = CON_KPIS + PCS_KPIS_NEW_DATA
                
                #Unificar
                if(client_input != "Todos"): 
                    #Fitrar por cliente
                    CDC_KPIS_USE = filterClients(CDC_KPIS_NEW_DATA, client_input, None)
                    CON_KPIS_USE = filterClients(CON_KPIS_NEW_DATA, client_input, None)
                    PCS_KPIS_USE = filterClients(PCS_KPIS_NEW_DATA, client_input, None)
                else:
                    CON_KPIS_USE = CON_KPIS_NEW_DATA
                    CDC_KPIS_USE = CDC_KPIS_NEW_DATA
                    PCS_KPIS_USE = PCS_KPIS_NEW_DATA
            except:
                flash("Error al añadir la información del periodo "+year, "Error")
    
    #Get Img Client
    try:
        if(client_input != "Todos"):
            for i in clients_list:
                if(i.to_dict()['Cliente'] == client_input):
                    client_img = i.to_dict()['Imagen']
    except:
        flash("Error al cargar la imagen del cliente "+client_input, "Error")      
              
    # Variables
    #["Esfuerzo", "Satisfacción","Lealtad", "Valor, "General"] 
    c_q1, c_q2, c_q3, c_q4          = reporteGeneral(CON_KPIS_USE) #KPI's Consultoria
    cdc_q1, cdc_q2, cdc_q3, cdc_q4  = reporteGeneral(CDC_KPIS_USE) #KPI's CDC
    pc_q1, pc_q2, pc_q3, pc_q4      = reporteGeneral(PCS_KPIS_USE) #KPI's Proceso comercial satisfacción
        
    avg_general, avg_lealtad, avg_satisfaccion, avg_esfuerzo, avg_valor = 0, 0, 0, 0, 0
    avg_general_previus, avg_nps_previus, avg_csat_previus, avg_ces_previus, avg_va_previus = -1, -1, -1, -1, -1 
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
        avg_general_previus, avg_nps_previus, avg_csat_previus, avg_ces_previus, avg_va_previus = tablaReporteGeneral(c_q1, cdc_q1, pc_q1)
        avg_general, avg_lealtad, avg_satisfaccion, avg_esfuerzo, avg_valor = tablaReporteGeneral(c_q2, cdc_q2, pc_q2)
    elif(trimestre == "Q3"):
        avg_general_previus, avg_nps_previus, avg_csat_previus, avg_ces_previus, avg_va_previus = tablaReporteGeneral(c_q2, cdc_q2, pc_q2)
        avg_general, avg_lealtad, avg_satisfaccion, avg_esfuerzo, avg_valor = tablaReporteGeneral(c_q3, cdc_q3, pc_q3) 
    elif(trimestre == "Q4"):
        avg_general_previus, avg_nps_previus, avg_csat_previus, avg_ces_previus, avg_va_previus = tablaReporteGeneral(c_q3, cdc_q3, pc_q3)
        avg_general, avg_lealtad, avg_satisfaccion, avg_esfuerzo, avg_valor = tablaReporteGeneral(c_q4, cdc_q4, pc_q4) 
        
    if(avg_general != 0):
        hayDatos = True
    
    try:
        #Rangos y ponderaciones
        config = db.collection('Rangos_Ponderaciones').where('year','==',int(year)).get()
            
        if(len(config)>0):
            #Recuperar rangos y ponderaciones desde Firebase
            kpi_nps, kpi_csat, kpi_va, kpi_ces = getRangosyPonderaciones(config)
            find_range = True
        else:
            find_range = False
            year_search = int(datetime.date.today().year)
            while(find_range == False):
                config = db.collection('Rangos_Ponderaciones').where('year','==',year_search).get()
                if(len(config)>0):
                    kpi_nps, kpi_csat, kpi_va, kpi_ces = getRangosyPonderaciones(config)
                    find_range = True
                year_search = year_search -1
    except:
        flash("Error al carga la información de los rangos y ponderaciones", "Error")
        
    if(avg_general_previus != -1):
        avg_general_delta = roundPropio(avg_general-avg_general_previus)
        fig_esfuerzo      = speedmeter(kpi_ces['kpi_name'],  roundPropio(avg_esfuerzo),     kpi_ces['min'],  kpi_ces['max'],  kpi_ces['ponderacion'], avg_ces_previus)
        fig_satisfaccion  = speedmeter(kpi_csat['kpi_name'], roundPropio(avg_satisfaccion), kpi_csat['min'], kpi_csat['max'], kpi_csat['ponderacion'], avg_csat_previus)
        fig_lealtad       = speedmeter(kpi_nps['kpi_name'],  roundPropio(avg_lealtad),      kpi_nps['min'],  kpi_nps['max'],  kpi_nps['ponderacion'], avg_nps_previus)
        fig_valor         = speedmeter(kpi_va['kpi_name'],   roundPropio(avg_valor),        kpi_va['min'],   kpi_va['max'],   kpi_va['ponderacion'], avg_va_previus)
    else:
        avg_general_delta = -1
        fig_esfuerzo      = speedmeter(kpi_ces['kpi_name'],  roundPropio(avg_esfuerzo),     kpi_ces['min'],  kpi_ces['max'],  kpi_ces['ponderacion'])
        fig_satisfaccion  = speedmeter(kpi_csat['kpi_name'], roundPropio(avg_satisfaccion), kpi_csat['min'], kpi_csat['max'], kpi_csat['ponderacion'])
        fig_lealtad       = speedmeter(kpi_nps['kpi_name'],  roundPropio(avg_lealtad),      kpi_nps['min'],  kpi_nps['max'],  kpi_nps['ponderacion'])
        fig_valor         = speedmeter(kpi_va['kpi_name'],   roundPropio(avg_valor),        kpi_va['min'],   kpi_va['max'],   kpi_va['ponderacion'])          
    
    graph_esfuerzo     = json.dumps(fig_esfuerzo,     cls=plotly.utils.PlotlyJSONEncoder)
    graph_satisfaccion = json.dumps(fig_satisfaccion, cls=plotly.utils.PlotlyJSONEncoder)
    graph_lealtad      = json.dumps(fig_lealtad,      cls=plotly.utils.PlotlyJSONEncoder)
    graph_valor        = json.dumps(fig_valor,        cls=plotly.utils.PlotlyJSONEncoder)
                
    return render_template('general.html', 
                           kpi_total              = roundPropio(avg_general),
                           avg_general_delta      = avg_general_delta,
                           trimestre              = trimestre,
                           year                   = year,
                           list_years             = addOthersYear([], int(datetime.date.today().year)),
                           client                 = client,
                           client_img             = client_img,
                           graphJSON_esfuerzo     = graph_esfuerzo,
                           graphJSON_satisfaccion = graph_satisfaccion,
                           graphJSON_lealtad      = graph_lealtad,
                           graphJSON_valor        = graph_valor,
                           hayDatos               = hayDatos,
                           clients_list           = clients_name)
    
    


