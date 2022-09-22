from   flask import flash, request, render_template
from   firebase_admin import firestore
import json
import plotly
from   CX.static.questions.consultoria_questions import Preguntas_esfuerzo,Preguntas_satisfaccion,Preguntas_lealtad,Preguntas_valor
from   CX import app
from   CX.logic.functions import saveSelectData, speedmeter, promedioQuarter, tablaDinamica, validarParametros
from   CX.logic.functions import carga_kpi, carga_preguntas, deltaKPI, getRangosyPonderaciones, filtrarxyear

#Carga Respuestas CDC
def cargaRespuestasConsultoria(db, Year,Trimestre, results, found_list, area):
    
    Consultoria_KPI_Ref       = db.collection("Consultoria_KPIS")
    PC_KPI_Ref        = db.collection("PCS_KPIS")

    carga_kpi("Arcotel", PC_KPI_Ref , 4, 2020, 8.6, 7.6, 7.5, 7.0, 7.9)
    carga_kpi("EPMAPS", PC_KPI_Ref , 4, 2020, 10.0, 10.0, 10.0, 10.0, 10.0)
    carga_kpi("Fundafarmacia", PC_KPI_Ref , 4, 2020, 8.0, 7.8, 7.0, 5.0, 7.6)
    carga_kpi("Locatel", PC_KPI_Ref , 4, 2020, 10.0, 9.8, 9.5, 5.0, 9.8)
    carga_kpi("Plásticos de Empaque", PC_KPI_Ref , 3, 2020, 10.0, 10.0, 10.0, 10.0, 10.0)
    carga_kpi("Policlínica Metropolitana", PC_KPI_Ref , 4, 2020, 7.2, 6.7, 6.5, 7.0, 6.8)
    carga_kpi("Tubrica/Paují", PC_KPI_Ref , 3, 2020, 8.4, 8.9, 8.5, 9.0, 8.6)


    carga_kpi("Bolivariana De Puertos", Consultoria_KPI_Ref , 1, 2020, 8.7, 8.9, 8.7, 0.0, 8.7)
    carga_kpi("Bolivariana De Puertos", Consultoria_KPI_Ref , 2, 2020, 10.0, 10.0, 10.0, 0.0, 10.0)
    carga_kpi("Corporación Eléctrica Nacional S.A. (CORPOELEC)", Consultoria_KPI_Ref , 1, 2020, 9.0, 8.7, 9.0, 0.0, 8.9)
    carga_kpi("Grupo +58", Consultoria_KPI_Ref , 1, 2020, 9.5, 9.9, 9.8, 0.0, 9.7)
    carga_kpi("La Fabril", Consultoria_KPI_Ref , 1, 2020, 9.3, 8.8, 9.3, 0.0, 9.1)
    carga_kpi("Abside", Consultoria_KPI_Ref , 4, 2020, 6.0, 6.4, 7.0, 8.0, 6.5)
    carga_kpi("Tubrica/Paují", Consultoria_KPI_Ref , 4, 2020, 7.5, 8.0, 8.0, 0.0, 7.8)
    carga_kpi("Locatel", Consultoria_KPI_Ref , 4, 2020, 6.9, 7.2, 7.0, 8.0, 7.0)
    

 
#Chart Page
@app.route('/chart_consultoria', methods=['GET', 'POST'])
def chart_consultoria():
    
    try:
        # Variables
        kpi_clients = None
        kpi_q1, kpi_q2, kpi_q3, kpi_q4,  Trimestres, Years, lista_clientes = [], [], [], [], [], [], []
        kpi_total = 0
        cliente_unico, graph_esfuerzo, graph_satisfaccion, graph_lealtad, graph_valor,imagen_cliente = False, False, False, False, False, False
        
        #Conexion con la DB - KPI's CDC
        db = firestore.client()
        Consultoria_KPIS = db.collection('Consultoria_KPIS').get()
        
        #Guardar Listas Trimestres y años de la DB
        Trimestres, Years, lista_clientes = saveSelectData(Consultoria_KPIS)
        
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
            
            #Nota: Se necesitan que esten ordenados?
            kpi_clients = db.collection('Consultoria_KPIS').order_by("Cliente").get()
            
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
            kpis_client = db.collection('Consultoria_KPIS').where('Year','==',int(year_input)).where('Cliente','==',cliente_input).get()
            
            #GET Cliente IMAGE
            Cliente = db.collection('Clientes').where('Cliente','==',cliente_input).get()
            imagen_cliente = Cliente[0].to_dict()["Imagen"]
            
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
                
                #Recuperar rangos y ponderaciones desde Firebase
                kpi_nps, kpi_csat, kpi_va, kpi_ces = getRangosyPonderaciones(config)
                                
                if(len(kpi_delta) > 0):
                    delta = kpi_delta[0].to_dict()
                    fig_ces   = speedmeter(kpi_ces['kpi_name'],  client["kpi_esfuerzo"],     kpi_ces['min'],  kpi_ces['max'],  kpi_ces['ponderacion'],  delta['kpi_esfuerzo'])
                    fig_csat  = speedmeter(kpi_csat['kpi_name'], client["kpi_satisfaccion"], kpi_csat['min'], kpi_csat['max'], kpi_csat['ponderacion'], delta['kpi_satisfaccion'])
                    fig_nps   = speedmeter(kpi_nps['kpi_name'],  client["kpi_lealtad"],      kpi_nps['min'],  kpi_nps['max'],  kpi_nps['ponderacion'],  delta['kpi_lealtad'])
                    fig_va    = speedmeter(kpi_va['kpi_name'],   client["kpi_valor"],        kpi_va['min'],   kpi_va['max'],   kpi_va['ponderacion'],   delta['kpi_valor'])
                else:
                    fig_ces   = speedmeter(kpi_ces['kpi_name'],  client["kpi_esfuerzo"],     kpi_ces['min'],  kpi_ces['max'],  kpi_ces['ponderacion'])
                    fig_csat  = speedmeter(kpi_csat['kpi_name'], client["kpi_satisfaccion"], kpi_csat['min'], kpi_csat['max'], kpi_csat['ponderacion'])
                    fig_nps   = speedmeter(kpi_nps['kpi_name'],  client["kpi_lealtad"],      kpi_nps['min'],  kpi_nps['max'],  kpi_nps['ponderacion'])
                    fig_va    = speedmeter(kpi_va['kpi_name'],   client["kpi_valor"],        kpi_va['min'],   kpi_va['max'],   kpi_va['ponderacion'])
                
                graph_esfuerzo     = json.dumps(fig_ces,  cls=plotly.utils.PlotlyJSONEncoder)
                graph_satisfaccion = json.dumps(fig_csat, cls=plotly.utils.PlotlyJSONEncoder)
                graph_lealtad      = json.dumps(fig_nps,  cls=plotly.utils.PlotlyJSONEncoder)
                graph_valor        = json.dumps(fig_va,   cls=plotly.utils.PlotlyJSONEncoder)
    except:
        flash("Error al cargar reporte Consultoria", "error")
            
    return render_template('chart.html',
                           kpi_total              = kpi_total,
                           Trimestres             = Trimestres,
                           Years                  = Years,
                           lista_clientes         = lista_clientes,
                           cliente_unico          = cliente_unico,
                           cliente_input          = cliente_input,
                           trimestre_input        = int(trimestre_input), 
                           graphJSON_esfuerzo     = graph_esfuerzo,
                           graphJSON_satisfaccion = graph_satisfaccion,
                           graphJSON_lealtad      = graph_lealtad,
                           graphJSON_valor        = graph_valor,
                           imagen_cliente = imagen_cliente,
                           kpi_q1 = kpi_q1, 
                           kpi_q2 = kpi_q2, 
                           kpi_q3 = kpi_q3, 
                           kpi_q4 = kpi_q4,
                           list_avg_kpi=list_avg_kpi,
                           area = "Consultoria",
                           year=int(year_input))
    
    


