from   flask import flash, request, render_template
from   firebase_admin import firestore
import json
import plotly
from   CX.static.questions.cdc_questions import Preguntas_esfuerzo,Preguntas_satisfaccion,Preguntas_lealtad,Preguntas_valor
from   CX import app
from   CX.logic.functions import saveSelectData, speedmeter, promedioQuarter, tablaDinamica, validarParametros
from   CX.logic.functions import carga_kpi, carga_preguntas, deltaKPI, getRangosyPonderaciones, filtrarxyear

#Carga Respuestas CDC
def cargaRespuestasCDC(db, Year,Trimestre, results, found_list):
    
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
                    kpi_esfuerzo         += (float(doc.to_dict()['kpi_esfuerzo']))
                    kpi_satisfaccion     += (float(doc.to_dict()['kpi_satisfaccion']))
                    kpi_lealtad          += (float(doc.to_dict()['kpi_lealtad']))
                    kpi_valor            += (float(doc.to_dict()['kpi_valor']))
                    numero_de_respuestas += 1
                    
                kpi_esfuerzo     = round(kpi_esfuerzo/numero_de_respuestas, 2)
                kpi_satisfaccion = round(kpi_satisfaccion/numero_de_respuestas,2)
                kpi_lealtad      = round(kpi_lealtad/numero_de_respuestas,2)
                kpi_valor        = round(kpi_valor/numero_de_respuestas,2)
                kpi_total        = round((kpi_esfuerzo*(kpi_ces['ponderacion']/100)) + (kpi_satisfaccion*(kpi_csat['ponderacion']/100)) + (kpi_lealtad*(kpi_nps['ponderacion']/100)) + (kpi_valor*(kpi_va['ponderacion']/100)), 2)
                
                carga_kpi(cliente,CDC_KPI_Ref,Trimestre,Year,kpi_esfuerzo,kpi_satisfaccion,kpi_lealtad,kpi_valor,kpi_total)
    except: 
            flash('Error al carga info CDC', 'error')
            
#Chart Page
@app.route('/chart_cdc', methods=['GET', 'POST'])
def chart_cdc():
    try:    
        # Variables
        kpi_clients = None
        kpi_q1, kpi_q2, kpi_q3, kpi_q4,  Trimestres, Years, lista_clientes = [], [], [], [], [], [], []
        kpi_total = 0
        cliente_unico, graph_ces, graph_csat, graph_nps, graph_va, imagen_cliente = False, False, False, False, False,False
        error = "Error al cargar reporte CDC"
        
        #Conexion con la DB - KPI's CDC
        db = firestore.client()
        kpi_clients = db.collection('CDC_KPIS').order_by("Cliente").get() #Get All CDC KPI's
        
        #Guardar Listas Trimestres y años de la DB
        Trimestres, Years, lista_clientes = saveSelectData(kpi_clients)
        
        #Guardar Parametros URL
        trimestre_input = (request.args.get('trimestre_input'))
        year_input      = (request.args.get('year_input'))
        cliente_input   = (request.args.get('cliente_input'))
        
        #Validación parametros URL
        trimestre_input, year_input = validarParametros(trimestre_input, year_input, Trimestres, Years)
        
        #Lista Avg Kpi's
        list_avg_kpi = []
        
        #Show Table
        if cliente_input is None or cliente_input=="Todos":
            
            #Filtrar por año
            kpi_clients = filtrarxyear(kpi_clients, int(year_input))        
            
            #Tabla dinamica
            kpi_q1, kpi_q2, kpi_q3, kpi_q4 = tablaDinamica(kpi_clients)
        
            #Promedio Q's    
            for i in range(4):
                list_avg_kpi.append(promedioQuarter(kpi_clients, 'kpi_valor',        i+1))
                list_avg_kpi.append(promedioQuarter(kpi_clients, 'kpi_satisfaccion', i+1))
                list_avg_kpi.append(promedioQuarter(kpi_clients, 'kpi_lealtad',      i+1))
                list_avg_kpi.append(promedioQuarter(kpi_clients, 'kpi_esfuerzo',     i+1))
                list_avg_kpi.append(promedioQuarter(kpi_clients, 'kpi_total',        i+1))
                
        #Show speedmeter  
        else:
            
            #GET ALL KPI's CDC FROM A SPECIFIC YEAR ALL Q
            print("entro")
            kpis_client = db.collection('CDC_KPIS').where('Year','==',int(year_input)).where('Cliente','==',cliente_input).get()
            
            #GET Cliente IMAGE
            Cliente = db.collection('Clientes').where('Cliente','==',cliente_input).get()
            try:
                imagen_cliente = Cliente[0].to_dict()["Imagen"]
            except:
                imagen_cliente = False
            
            
            #KPI's CDC FROM A SPECIFIC Q
            kpi_client, kpi_delta = deltaKPI(kpis_client, trimestre_input)
            
            #ONLY ONE CLIENT
            cliente_unico = True
                                    
            #SHOW GRAFICOS          
            if len(kpi_client) > 0:
                kpi_total = float(kpi_client[0].to_dict()["kpi_total"])
                client    = kpi_client[0].to_dict()
                
                #Rangos y ponderaciones
                config = db.collection('Rangos_Ponderaciones').where('year','==',int(year_input)).get()
                
                #Check get rangos
                if(len(config) == 0):
                    error = "Error, no se encontraron los rangos para ese trimestre"
                
                #Recuperar rangos y ponderaciones desde Firebase
                kpi_nps, kpi_csat, kpi_va, kpi_ces = getRangosyPonderaciones(config)
                            
                if(len(kpi_delta) > 0):
                    delta = kpi_delta[0].to_dict()
                    fig_ces  = speedmeter(kpi_ces['kpi_name'],  client["kpi_esfuerzo"],     kpi_ces['min'],  kpi_ces['max'],  kpi_ces['ponderacion'],  delta['kpi_esfuerzo'])
                    fig_csat = speedmeter(kpi_csat['kpi_name'], client["kpi_satisfaccion"], kpi_csat['min'], kpi_csat['max'], kpi_csat['ponderacion'], delta['kpi_satisfaccion'])
                    fig_nps  = speedmeter(kpi_nps['kpi_name'],  client["kpi_lealtad"],      kpi_nps['min'],  kpi_nps['max'],  kpi_nps['ponderacion'],  delta['kpi_lealtad'])
                    fig_va   = speedmeter(kpi_va['kpi_name'],   client["kpi_valor"],        kpi_va['min'],   kpi_va['max'],   kpi_va['ponderacion'],   delta['kpi_valor'])
                else:
                    fig_ces  = speedmeter(kpi_ces['kpi_name'],  client["kpi_esfuerzo"],     kpi_ces['min'],  kpi_ces['max'],  kpi_ces['ponderacion'])
                    fig_csat = speedmeter(kpi_csat['kpi_name'], client["kpi_satisfaccion"], kpi_csat['min'], kpi_csat['max'], kpi_csat['ponderacion'])
                    fig_nps  = speedmeter(kpi_nps['kpi_name'],  client["kpi_lealtad"],      kpi_nps['min'],  kpi_nps['max'],  kpi_nps['ponderacion'])
                    fig_va   = speedmeter(kpi_va['kpi_name'],   client["kpi_valor"],        kpi_va['min'],   kpi_va['max'],   kpi_va['ponderacion'])
                
                graph_ces  = json.dumps(fig_ces,  cls=plotly.utils.PlotlyJSONEncoder)
                graph_csat = json.dumps(fig_csat, cls=plotly.utils.PlotlyJSONEncoder)
                graph_nps  = json.dumps(fig_nps,  cls=plotly.utils.PlotlyJSONEncoder)
                graph_va   = json.dumps(fig_va,   cls=plotly.utils.PlotlyJSONEncoder)
    except:
        flash(error, "error")
        
    return render_template('chart.html',
                           kpi_total              = kpi_total,
                           Trimestres             = Trimestres,
                           Years                  = Years,
                           lista_clientes         = lista_clientes,
                           cliente_unico          = cliente_unico,
                           cliente_input          = cliente_input,
                           trimestre_input        = int(trimestre_input), 
                           graphJSON_esfuerzo     = graph_ces,
                           graphJSON_satisfaccion = graph_csat,
                           graphJSON_lealtad      = graph_nps,
                           graphJSON_valor        = graph_va,
                           imagen_cliente = imagen_cliente,
                           kpi_q1 = kpi_q1, 
                           kpi_q2 = kpi_q2, 
                           kpi_q3 = kpi_q3, 
                           kpi_q4 = kpi_q4,
                           list_avg_kpi = list_avg_kpi,
                           area = "CDC",
                           year=int(year_input))
