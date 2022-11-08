from   flask import flash, request, render_template
from   firebase_admin import firestore
import json
import plotly
from   CX.static.questions.cdc_questions import Preguntas_esfuerzo,Preguntas_satisfaccion,Preguntas_lealtad,Preguntas_valor
from   CX import app
from   CX.logic.functions import roundPropio, saveSelectData, speedmeter, promedioQuarter, tablaDinamica, validarParametros
from   CX.logic.functions import carga_kpi, carga_preguntas, deltaKPI, getRangosyPonderaciones, filtrarxyear
from   CX.logic.functions import getLastAndCurrentYear, orderClients, addOthersYear, filterClients, getImageClient, addNewData

#Global variables (Que venguenza, sorry si alguien ve esto :c)
kpi_clients = []
last_year, current_year, area = None, None, None
Years, lista_clientes, year_loaded = None, None, None

#Carga Respuestas (Falta ajustar)
def cargaRespuestas(db, area, Year,Trimestre, results, found_list):
    
    try:
        #Cargar respuesta para un trimestre en particular
        query_trimestre = db.collection('CDC_Respuestas').where('Year', '==',str(Year) ).where('Trimestre', '==', str(Trimestre)).get()
        
        #Verificar si ya se ingreso el archivo
        if len(query_trimestre)>0:
            flash('Ya se ingreso el archivo', 'warning')
                    
        else:
            #Firebase CDC Respuestas
            CDC_Respuestas_Ref = db.collection("CDC_Respuestas")
            carga_preguntas(results, CDC_Respuestas_Ref,Trimestre,Year,Preguntas_esfuerzo,Preguntas_satisfaccion,Preguntas_lealtad,Preguntas_valor)
            
            #Firebase CDC KPI's
            CDC_KPI_Ref        = db.collection("CDC_KPIS")
            found_set          = set(found_list)
            found_list_unique  = list(found_set)
            
            for cliente in found_list_unique:
                #Variables
                kpi_esfuerzo, kpi_satisfaccion, kpi_lealtad, kpi_valor, numero_de_respuestas = 0, 0, 0, 0, 0
            
                #Firebase
                query_kpi = db.collection('CDC_Respuestas').where('Year', '==',str(Year) ).where('Trimestre', '==', str(Trimestre)).where("Nombre_de_la_empresa_a_la_que_pertenece", '==', cliente).get()
                
                #Rangos y ponderaciones
                config = db.collection('Rangos_Ponderaciones').where('year','==',int(Year)).get()
                
                #Recuperar rangos y ponderaciones desde Firebase
                kpi_nps, kpi_csat, kpi_va, kpi_ces = getRangosyPonderaciones(config)
                
                for doc in query_kpi:
                    kpi_esfuerzo         += float(doc.to_dict()['kpi_esfuerzo'])
                    kpi_satisfaccion     += float(doc.to_dict()['kpi_satisfaccion'])
                    kpi_lealtad          += float(doc.to_dict()['kpi_lealtad'])
                    kpi_valor            += float(doc.to_dict()['kpi_valor'])
                    numero_de_respuestas += 1
                    
                kpi_esfuerzo     = roundPropio(kpi_esfuerzo/numero_de_respuestas)
                kpi_satisfaccion = roundPropio(kpi_satisfaccion/numero_de_respuestas)
                kpi_lealtad      = roundPropio(kpi_lealtad/numero_de_respuestas)
                kpi_valor        = roundPropio(kpi_valor/numero_de_respuestas)
                kpi_total        = roundPropio((kpi_esfuerzo*(kpi_ces['ponderacion']/100)) + (kpi_satisfaccion*(kpi_csat['ponderacion']/100)) + (kpi_lealtad*(kpi_nps['ponderacion']/100)) + (kpi_valor*(kpi_va['ponderacion']/100)))
                
                carga_kpi(cliente,CDC_KPI_Ref,Trimestre,Year,kpi_esfuerzo,kpi_satisfaccion,kpi_lealtad,kpi_valor,kpi_total)
                
    except Exception as e: 
            print(e)
            flash('Error al carga info CDC', 'error')
           
#Chart Page
@app.route('/chart', methods=['GET', 'POST'])
def chart():
    # Variables Globales
    global kpi_clients, area, last_year, current_year, Years, lista_clientes, year_loaded
    
    # Variables locales
    kpi_q1, kpi_q2, kpi_q3, kpi_q4 = [], [], [], [], 
    kpi_total, kpi_total_delta = 0, 0
    cliente_unico, graph_ces, graph_csat, graph_nps, graph_va, imagen_cliente = False, False, False, False, False,False
    trimestre_input, year_input, cliente_input = None, None, None
    list_avg_kpi = []

    #Firebase connection
    db = firestore.client()
    
    #Guardar Parametros form
    trimestre_input = request.form.get('trimestre_input')
    cliente_input   = request.form.get('cliente_input')
    year_input      = request.form.get('year_input')

    #Guardar Parametros URL 
    if request.args.get('area') is not None:
        area = request.args.get('area')
        error = "Error al cargar reporte " + area   #Config Error message
    
    #Case 1: Config initial
    if request.method == 'GET':
        try:    
            #Get Current year and previus year
            current_year, last_year = getLastAndCurrentYear()
            
            #KPI's Area, get area KPI's from current year
            kpi_clients = db.collection(area+'_KPIS').where('Year', '==', current_year).get() 
                        
            #If dont data in current_year get data last year
            if(len(kpi_clients) == 0):
                kpi_clients = db.collection(area+'_KPIS').where('Year', '==', last_year).get() 

            #Order kpi's by clients
            kpi_clients = orderClients(kpi_clients, True)
                        
            #Guardar Listas Trimestres y años de la DB
            year_loaded     = saveSelectData(kpi_clients, "Year",      False)
            lista_clientes  = saveSelectData(kpi_clients, "Cliente",   False)
            Years           = saveSelectData(kpi_clients, "Year",      False)
                    
            #Add years
            addOthersYear(Years, last_year)
           
            #Default
            if cliente_input is None:
                cliente_input = "Todos"
                
            trimestre_input, year_input = validarParametros(trimestre_input, year_input, Years)
    
        except:
            flash(error, "Error Carga inicial "+area)        
         
    #Add data from year_input
    if(year_input is not None):
        
        year_input = int(year_input)
            
        if(year_input not in year_loaded):
                        
            kpi_clients = addNewData(db, year_input, last_year, area, kpi_clients)
             
            #Guardar Listas Trimestres y años de la DB
            lista_clientes  = saveSelectData(kpi_clients, "Cliente", False)

            #Add Year Data loaded
            year_loaded.append(year_input)
 
    
    if (cliente_input == "Todos"): # Show Table
        
        #Filtrar por año
        kpi_clients_year = filtrarxyear(kpi_clients, int(year_input))
       
        #Tabla dinamica
        kpi_q1, kpi_q2, kpi_q3, kpi_q4 = tablaDinamica(kpi_clients_year)
            
        #Promedio Q's    
        for i in range(4):
            list_avg_kpi.append(promedioQuarter(kpi_clients_year, 'kpi_valor',        i+1, False))
            list_avg_kpi.append(promedioQuarter(kpi_clients_year, 'kpi_satisfaccion', i+1, False))
            list_avg_kpi.append(promedioQuarter(kpi_clients_year, 'kpi_lealtad',      i+1, False))
            list_avg_kpi.append(promedioQuarter(kpi_clients_year, 'kpi_esfuerzo',     i+1, False))
            list_avg_kpi.append(promedioQuarter(kpi_clients_year, 'kpi_total',        i+1, False))
                
    else:   #Show speedmeter 
        
        try:
          
            # Variables
            cliente_unico   = True
            trimestre_input = int(trimestre_input)
            year_input      = int(year_input)
                
            #Filter client
            kpis_client = filterClients(kpi_clients, cliente_input, year_input, trimestre_input)
                
            #GET Cliente IMAGE
            imagen_cliente = getImageClient(db, cliente_input)
                
            #KPI's CDC FROM A SPECIFIC Q
            kpi_client, kpi_delta = deltaKPI(kpis_client, trimestre_input)
                
            #ONLY ONE CLIENT
            cliente_unico = True
                                        
            #SHOW GRAFICOS          
            if len(kpi_client) > 0:
                
                kpi_total = roundPropio(float(kpi_client[0]["kpi_total"]))
                client    = kpi_client[0]
                    
                #Rangos y ponderaciones
                config = db.collection('Rangos_Ponderaciones').where('year','==',int(year_input)).get()
                    
                #Check get rangos
                if(len(config) == 0):
                    error = "Error, no se encontraron los rangos para ese trimestre"
                    flash(error, 'Error')
                          
                #Recuperar rangos y ponderaciones desde Firebase
                kpi_nps, kpi_csat, kpi_va, kpi_ces = getRangosyPonderaciones(config)
                                
                if(len(kpi_delta) > 0):
                    delta           = kpi_delta[0]
                    kpi_total_delta =  roundPropio(kpi_total-delta['kpi_total'])
                    fig_ces  = speedmeter(kpi_ces['kpi_name'],  client["kpi_esfuerzo"],     kpi_ces['min'],  kpi_ces['max'],  kpi_ces['ponderacion'],  delta['kpi_esfuerzo'])
                    fig_csat = speedmeter(kpi_csat['kpi_name'], client["kpi_satisfaccion"], kpi_csat['min'], kpi_csat['max'], kpi_csat['ponderacion'], delta['kpi_satisfaccion'])
                    fig_nps  = speedmeter(kpi_nps['kpi_name'],  client["kpi_lealtad"],      kpi_nps['min'],  kpi_nps['max'],  kpi_nps['ponderacion'],  delta['kpi_lealtad'])                    
                    fig_va   = speedmeter(kpi_va['kpi_name'],   client["kpi_valor"],        kpi_va['min'],   kpi_va['max'],   kpi_va['ponderacion'],   delta['kpi_valor'])
                else:
                    kpi_total_delta = 0
                    fig_ces  = speedmeter(kpi_ces['kpi_name'],  client["kpi_esfuerzo"],     kpi_ces['min'],  kpi_ces['max'],  kpi_ces['ponderacion'])
                    fig_csat = speedmeter(kpi_csat['kpi_name'], client["kpi_satisfaccion"], kpi_csat['min'], kpi_csat['max'], kpi_csat['ponderacion'])
                    fig_nps  = speedmeter(kpi_nps['kpi_name'],  client["kpi_lealtad"],      kpi_nps['min'],  kpi_nps['max'],  kpi_nps['ponderacion'])
                    fig_va   = speedmeter(kpi_va['kpi_name'],   client["kpi_valor"],        kpi_va['min'],   kpi_va['max'],   kpi_va['ponderacion'])
                    
                graph_ces  = json.dumps(fig_ces,  cls=plotly.utils.PlotlyJSONEncoder)
                graph_csat = json.dumps(fig_csat, cls=plotly.utils.PlotlyJSONEncoder)
                graph_nps  = json.dumps(fig_nps,  cls=plotly.utils.PlotlyJSONEncoder)
                graph_va   = json.dumps(fig_va,   cls=plotly.utils.PlotlyJSONEncoder)
        except:
            flash(error, "Error "+area)  
            
    return render_template('chart.html',
                           kpi_total              = kpi_total,
                           kpi_total_delta        = kpi_total_delta,
                           Trimestres             = [1, 2, 3, 4],
                           trimestre_input        = trimestre_input, 
                           Years                  = Years,
                           year                   = year_input,
                           lista_clientes         = lista_clientes,
                           cliente_unico          = cliente_unico,
                           cliente_input          = cliente_input,
                           graphJSON_esfuerzo     = graph_ces,
                           graphJSON_satisfaccion = graph_csat,
                           graphJSON_lealtad      = graph_nps,
                           graphJSON_valor        = graph_va,
                           imagen_cliente         = imagen_cliente,
                           kpi_q1                 = kpi_q1, 
                           kpi_q2                 = kpi_q2, 
                           kpi_q3                 = kpi_q3, 
                           kpi_q4                 = kpi_q4,
                           list_avg_kpi           = list_avg_kpi,
                           area                   = area)
