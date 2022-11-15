from   flask import flash, request, render_template, redirect
from   firebase_admin import firestore
import json
import plotly
from   CX.static.questions.cdc_questions             import Preguntas_esfuerzo_cdc,Preguntas_satisfaccion_cdc,Preguntas_lealtad_cdc,Preguntas_valor_cdc
from   CX.static.questions.consultoria_questions     import Preguntas_esfuerzo_con,Preguntas_satisfaccion_con,Preguntas_lealtad_con,Preguntas_valor_con
from   CX.static.questions.pc_declinacion_questions  import Preguntas_esfuerzo_pcd,Preguntas_satisfaccion_pcd,Preguntas_lealtad_pcd,Preguntas_valor_pcd
from   CX.static.questions.pc_satisfaccion_questions import Preguntas_esfuerzo_pcs,Preguntas_satisfaccion_pcs,Preguntas_lealtad_pcs,Preguntas_valor_pcs
from   CX.logic.functions                            import roundPropio, saveSelectData, speedmeter, promedioQuarter, tablaDinamica, validarParametros
from   CX.logic.functions                            import carga_kpi, carga_preguntas, deltaKPI, getRangosyPonderaciones, filtrarxyear
from   CX.logic.functions                            import getLastAndCurrentYear, orderClients, addOthersYear, getImageClient, addNewData
from   CX import app
import CX.logic.general as General
import datetime

#Global variables (Un poco venguenza, sorry si alguien ve esto :c)
kpi_clients, years, lista_clientes, year_loaded = [], [], [], []
last_year, current_year, area = None, None, None, 

#Carga Respuestas Area
def cargaRespuestasArea(db, Year, Trimestre, results, found_list, area):
    try:
        #Cargar respuesta para un trimestre en particular
        query_trimestre = db.collection(area+'_Respuestas').where('Year', '==',str(Year) ).where('Trimestre', '==', str(Trimestre)).get()
        name_campo = None
        
        #Verificar si ya se ingreso el archivo
        if len(query_trimestre)>0:
            flash('Ya se ingreso el archivo', 'warning')
                    
        else:   
            #Firebase CDC Respuestas
            area_Respuestas_Ref = db.collection(area+"_Respuestas")
            if(area=="CDC"):
                name_campo = "Nombre_de_la_empresa_a_la_que_pertenece"
                carga_preguntas(results, area_Respuestas_Ref, Trimestre,Year, Preguntas_esfuerzo_cdc, Preguntas_satisfaccion_cdc, Preguntas_lealtad_cdc, Preguntas_valor_cdc)
            elif(area=="Consultoria"):
                name_campo = "Nombre_de_la_empresa_a_la_que_pertenece"
                carga_preguntas(results, area_Respuestas_Ref, Trimestre,Year, Preguntas_esfuerzo_con, Preguntas_satisfaccion_con, Preguntas_lealtad_con, Preguntas_valor_con)
            elif(area=="PCS"):
                name_campo = "NOMBRE_DE_LA_EMPRESA__CLIENTE_"
                carga_preguntas(results, area_Respuestas_Ref, Trimestre,Year, Preguntas_esfuerzo_pcs, Preguntas_satisfaccion_pcs, Preguntas_lealtad_pcs, Preguntas_valor_pcs)
            elif(area=="PCD"):
                name_campo = "NOMBRE_DE_LA_EMPRESA__CLIENTE_"
                carga_preguntas(results, area_Respuestas_Ref, Trimestre,Year, Preguntas_esfuerzo_pcd, Preguntas_satisfaccion_pcd, Preguntas_lealtad_pcd, Preguntas_valor_pcd)

            #Firebase Area KPI's
            area_KPI_Ref      = db.collection(area+"_KPIS")
            found_set         = set(found_list)
            found_list_unique = list(found_set)
            
            for cliente in found_list_unique:
                #Variables
                kpi_esfuerzo, kpi_satisfaccion, kpi_lealtad, kpi_valor, numero_de_respuestas = 0, 0, 0, 0, 0
            
                #Firebase
                query_kpi = db.collection(area+'_Respuestas').where('Year', '==',str(Year) ).where('Trimestre', '==', str(Trimestre)).where(name_campo, '==', cliente).get()
                
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
                
                carga_kpi(cliente,area_KPI_Ref,Trimestre,Year,kpi_esfuerzo,kpi_satisfaccion,kpi_lealtad,kpi_valor,kpi_total)
                
                #Reset Global variables
                General.year_cargados = []
                global year_loaded
                year_loaded = []
                
    except Exception as e: 
        print("error ", e)
        flash('Error al carga información '+area, 'error')
           
#Chart Page
@app.route('/chart', methods=['GET', 'POST'])
def chart():
    
    # Variables Globales
    global kpi_clients, area, last_year, current_year, years, lista_clientes, year_loaded
    
    # Variables locales
    kpi_q1, kpi_q2, kpi_q3, kpi_q4, list_avg_kpi = [], [], [], [], []
    kpi_total, kpi_total_delta = 0, 0
    graph_ces, graph_csat, graph_nps, graph_va, imagen_cliente = False, False, False, False, False
    trimestre_input, year_input, cliente_input = None, None, None
    
    #Firebase connection
    db = firestore.client()
    
    #Guardar Parametros form
    trimestre_input = request.form.get('trimestre_input')
    cliente_input   = request.form.get('cliente_input')
    year_input      = request.form.get('year_input')

    #Guardar Parametros URL 
    if request.args.get('area') is not None and len(request.args.get('area'))>0:
        area = request.args.get('area')
    else:
        return redirect('/error_page') #Redirect error page
        
    #Case 1: Config initial
    if request.method == 'GET' or len(year_loaded) == 0:
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
            years           = saveSelectData(kpi_clients, "Year",      False)
            
            #Validate parameters    
            trimestre_input, year_input = validarParametros(trimestre_input, year_input, years)
        except:
            flash("Error Carga inicial "+area)
                   
    #Check if years is empty         
    if(len(years)<4):  
        current_year, last_year = getLastAndCurrentYear()
        addOthersYear(years, current_year)  
            
    #Check is cliente_input is None
    if(cliente_input is None):
        cliente_input = "Todos" 
    
    #Check is cliente_input is None
    if(year_input is None):
        year_input = current_year
            
    #if year_input is not null and the information for that year has not been loaded
    if(year_input is not None and int(year_input) not in year_loaded):
            try:       
                #Add new data
                kpi_clients = addNewData(db, int(year_input), area, kpi_clients)
                
                #Guardar Listas Trimestres y años de la DB
                lista_clientes  = saveSelectData(kpi_clients, "Cliente", False)

                #Add Year Data loaded
                year_loaded.append(int(year_input))
            except:
                flash("Error cargar nueva información "+area)   
    
    if (cliente_input == "Todos"): # Show Table
        try:
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
        except:
            flash("Error al generar la tabla "+area, "Error")  
    
    #Show speedmeter               
    else:   
        try:
            # Variables
            trimestre_input = int(trimestre_input)
            year_input      = int(year_input)
                
            #GET Cliente IMAGE
            imagen_cliente = getImageClient(db, cliente_input)
                
            #KPI's CDC FROM A Q and Q-1 (If exist)
            kpi_client, kpi_delta = deltaKPI(kpi_clients, trimestre_input)
                    
            #SHOW GRAFICOS          
            if len(kpi_client) > 0:
                
                kpi_total = roundPropio(float(kpi_client[0]["kpi_total"]))
                client    = kpi_client[0]
                    
                #Recuperar rangos y ponderaciones desde Firebase
                config = db.collection('Rangos_Ponderaciones').where('year','==',int(year_input)).get()
              
                if(len(config)>0):
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
                          
                if(len(kpi_delta) > 0):
                    delta           = kpi_delta[0]
                    kpi_total_delta = roundPropio(kpi_total-delta['kpi_total'])
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
            flash("Error al generar el speedmeter "+area, "Error")  
            
    return render_template('chart.html',
                           kpi_total              = kpi_total,
                           kpi_total_delta        = kpi_total_delta,
                           trimestre_input        = trimestre_input, 
                           years                  = years,
                           year                   = year_input,
                           lista_clientes         = lista_clientes,
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
