from   flask import flash, request, render_template
from   firebase_admin import firestore
import json
import plotly
from   CX.static.questions.cdc_questions import Preguntas_esfuerzo,Preguntas_satisfaccion,Preguntas_lealtad,Preguntas_valor
from CX import app
from CX.functions import saveSelectData, speedmeter, promedioQuarter, tablaDinamica, validarParametros, carga_kpi, carga_preguntas, deltaKPI

#Carga Respuestas CDC
def cargaRespuestasCDC(db, Year,Trimestre, results, found_list):
    
    #Cargar respuesta para un trimestre en particular
    query_trimestre = db.collection('CDC_Respuestas').where('Year', '==',str(Year) ).where('Trimestre', '==', str(Trimestre)).get()
    
    #Verificar si ya se ingreso el archivo
    if len(query_trimestre)>0:
        flash('Ya se ingreso el archivo')
        print("ya se ingreso el archivo")
                
    else:
        CDC_Respuestas_Ref = db.collection("CDC_Respuestas")
        carga_preguntas(results, CDC_Respuestas_Ref,Trimestre,Year,Preguntas_esfuerzo,Preguntas_satisfaccion,Preguntas_lealtad,Preguntas_valor)
        CDC_KPI_Ref        = db.collection("CDC_KPIS")
        found_set          = set(found_list)
        found_list_unique  = list(found_set)
        
        for cliente in found_list_unique:
            kpi_esfuerzo, kpi_satisfaccion, kpi_lealtad, kpi_valor, numero_de_respuestas = 0, 0, 0, 0, 0
            query_kpi = db.collection('CDC_Respuestas').where('Year', '==',str(Year) ).where('Trimestre', '==', str(Trimestre)).where("Nombre_de_la_empresa_a_la_que_pertenece", '==', cliente).get()
            
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
            kpi_total        = round((kpi_esfuerzo*0.20) + (kpi_satisfaccion*0.35) + (kpi_lealtad*0.35) + (kpi_valor*0.10), 2)
            
            carga_kpi(cliente,CDC_KPI_Ref,Trimestre,Year,kpi_esfuerzo,kpi_satisfaccion,kpi_lealtad,kpi_valor,kpi_total) 

#Chart Page
@app.route('/chart_cdc', methods=['GET', 'POST'])
def chart_cdc():
    
    # Variables
    kpi_clients = None
    kpi_q1, kpi_q2, kpi_q3, kpi_q4 = [], [], [], []
    Trimestres, Years, lista_clientes = [], [], []
    kpi_total = 0
    cliente_unico, graphJSON_esfuerzo, graphJSON_satisfaccion = False, False, False
    graphJSON_lealtad, graphJSON_valor = False, False
    
    #Conexion con la DB - KPI's CDC
    db = firestore.client()
    CDC_KPIS = db.collection('CDC_KPIS').get() #Get All CDC KPI's
    
    #Guardar Listas Trimestres y años de la DB
    Trimestres, Years, lista_clientes = saveSelectData(CDC_KPIS)
    
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
        kpi_clients = db.collection('CDC_KPIS').order_by("Cliente").get()  #where('Trimestre','==',int(trimestre_input))
        
        #Tabla dinamica
        kpi_q1, kpi_q2, kpi_q3, kpi_q4 = tablaDinamica(kpi_clients)
       
        #Promedio Q's    
        for i in range(4):
            list_avg_kpi.append(promedioQuarter(kpi_clients, 'kpi_valor', i+1))
            list_avg_kpi.append(promedioQuarter(kpi_clients, 'kpi_satisfaccion', i+1))
            list_avg_kpi.append(promedioQuarter(kpi_clients, 'kpi_esfuerzo', i+1))
            list_avg_kpi.append(promedioQuarter(kpi_clients, 'kpi_lealtad', i+1))
            list_avg_kpi.append(promedioQuarter(kpi_clients, 'kpi_total', i+1))
            
    #Show speedmeter  
    else:
        #GET ALL KPI's CDC FROM A SPECIFIC YEAR ALL Q
        kpis_client = db.collection('CDC_KPIS').where('Year','==',int(year_input)).where('Cliente','==',cliente_input).get()
        
        #KPI's CDC FROM A SPECIFIC Q
        kpi_client, kpi_delta = deltaKPI(kpis_client, trimestre_input)
        
        #ONLY ONE CLIENT
        cliente_unico = True
                                   
        #SHOW GRAFICOS          
        if len(kpi_client) > 0:
            kpi_total = float(kpi_client[0].to_dict()["kpi_total"])
            client    = kpi_client[0].to_dict()
            
            #flash('Viva Chavez')
            
            if(len(kpi_delta) > 0):
                delta = kpi_delta[0].to_dict()
                fig_esfuerzo     = speedmeter("Customer Effort Score (CES)", float(client["kpi_esfuerzo"]),7.1, 8.2, "20%", delta['kpi_esfuerzo'])
                fig_satisfaccion = speedmeter("Customer Satisfaction Score (CSAT)", float(client["kpi_satisfaccion"]), 7.4, 8.5, "35%", delta['kpi_satisfaccion'])
                fig_lealtad      = speedmeter("Net Promoter Score (NPS)", float(client["kpi_lealtad"]), 6.9, 9,"35%", delta['kpi_lealtad'])
                fig_valor        = speedmeter("Valor Añadido (VA)",  float(client["kpi_valor"]), 6.4, 7.5, "10%", delta['kpi_valor'])
            else:
                fig_esfuerzo     = speedmeter("Customer Effort Score (CES)", float(client["kpi_esfuerzo"]),7.1, 8.2, "20%")
                fig_satisfaccion = speedmeter("Customer Satisfaction Score (CSAT)", float(client["kpi_satisfaccion"]), 7.4, 8.5, "35%")
                fig_lealtad      = speedmeter("Net Promoter Score (NPS)", float(client["kpi_lealtad"]), 6.9, 9,"35%")
                fig_valor        = speedmeter("Valor Añadido (VA)",  float(client["kpi_valor"]), 6.4, 7.5, "10%")
            
            graphJSON_esfuerzo     = json.dumps(fig_esfuerzo,     cls=plotly.utils.PlotlyJSONEncoder)
            graphJSON_satisfaccion = json.dumps(fig_satisfaccion, cls=plotly.utils.PlotlyJSONEncoder)
            graphJSON_lealtad      = json.dumps(fig_lealtad,      cls=plotly.utils.PlotlyJSONEncoder)
            graphJSON_valor        = json.dumps(fig_valor,        cls=plotly.utils.PlotlyJSONEncoder)
        
    return render_template('chart.html',
                           kpi_total              = kpi_total,
                           Trimestres             = Trimestres,
                           Years                  = Years,
                           lista_clientes         = lista_clientes,
                           cliente_unico          = cliente_unico,
                           cliente_input          = cliente_input,
                           trimestre_input        = int(trimestre_input), 
                           graphJSON_esfuerzo     = graphJSON_esfuerzo,
                           graphJSON_satisfaccion = graphJSON_satisfaccion,
                           graphJSON_lealtad      = graphJSON_lealtad,
                           graphJSON_valor        = graphJSON_valor,
                           kpi_q1 = kpi_q1, 
                           kpi_q2 = kpi_q2, 
                           kpi_q3 = kpi_q3, 
                           kpi_q4 = kpi_q4,
                           list_avg_kpi = list_avg_kpi,
                           area = "CDC",
                           year=year_input)
