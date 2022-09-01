from   ctypes.wintypes import CHAR
import os
from   pickle import NONE
from   flask import flash, request, redirect, url_for,render_template,jsonify
from   werkzeug.utils import secure_filename
import pandas as pd
import firebase_admin
from   firebase_admin import credentials, firestore
import json
import math
import plotly

from CX import app
from CX.functions import carga_preguntas, carga_kpi, saveSelectData, speedmeter, promedioQuarter, tablaDinamica, validarParametros

#Credenciales Firebase
cred = credentials.Certificate("CX/FirebaseKey/customer-experience-53371-firebase-adminsdk-wcb7p-879b654887.json")
firebase_admin.initialize_app(cred)

UPLOAD_FOLDER      = 'C:\\Users\Abside User\Desktop\customer experience'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xlsm'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#CHECK FILE TYPE
def allowed_file(filename): 
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


#SAVE NEW CLIENTS IN FIREBASE
@app.route('/SaveClients',methods=["GET", "POST"]) 
def SaveClients():
    
    if request.method == 'POST':
        
        db = firestore.client()
        Clientes_Ref = db.collection("Clientes")
        
        if request.is_json:

            output  = request.json
            output2 = json.dumps(output)
            result  = json.loads(output2) #this converts the json output to a python dictionary

            lista_agregados = []
            for cliente in result:
                
                if cliente['Es_nuevo'] == "True" and cliente['Input'] not in lista_agregados : 
                    Clientes_Ref.add({
                        'Cliente': cliente['Input'],
                        'Encuestas': [cliente['Excel']]
                    })
                    lista_agregados.append(cliente['Input'])
                else:
                    docs = Clientes_Ref.where("Cliente","==", cliente['Input']).get()
                    for doc in docs:
                        id = doc.id
                        array = doc.to_dict()['Encuestas']
                        array.append(cliente['Excel'])
                    Clientes_Ref.document(id).update({'Encuestas':array})
                    
            return jsonify(success=True)        
            
        else:
            print("no es json")
            
#Home Page
@app.route('/', methods=['GET', 'POST'])
def upload_file():
    
    if request.method == "GET":
        return render_template('home.html')
    
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            results = pd.read_excel(filename) 
            results.replace(["No satisfecho","Ningún Valor","En Desacuerdo","No Satisfecho","En Desacuerdo	"],2,inplace=True) # no se verifica aun si hay espacios o mayusculas
            results.replace(["Baja Satisfacción","Poco Valor","Casi Nunca"],4,inplace=True)
            results.replace(["Satisfacción Promedio","Valor Promedio","Normalmente de Acuerdo"],6,inplace=True)
            results.replace(["Buena Satisfacción","Gran Valor","Totalmente de Acuerdo"],8,inplace=True)
            results.replace(["Supera las Expectativas"],10,inplace=True)

        not_found_list, found_list, lista_clientes = [], [], []
        
        #Firebase
        db = firestore.client()
        Clientes_Data = db.collection("Clientes").get()
        CDC_Respuestas_Ref = db.collection("CDC_Respuestas")
        for doc in Clientes_Data:
            lista_clientes.append(doc.to_dict()['Cliente'])
            
        #Sort clients
        lista_clientes.sort()
        
        #Get trimestre from file
        Trimestre = math.ceil(int(str(results.loc[0,"Marca temporal"])[5:7])/3)
        
        #Get trimestre from year
        Year = int(str(results.loc[0,"Marca temporal"])[0:4])
        
        #verify client in DB
        for index, row in results.iterrows():

            Found = False
            Nombre_Cliente = row["Nombre de la empresa a la que pertenece"]
            aux = row["Nombre de la empresa a la que pertenece"].lower().replace(",","").replace(".","").replace("á",'a').replace("é",'e').replace("í",'i').replace("ó",'o').replace("ú",'u') 
            for doc in Clientes_Data:
                aux2 = doc.to_dict()['Cliente'].lower().replace(",","").replace(".","").replace("á",'a').replace("é",'e').replace("í",'i').replace("ó",'o').replace("ú",'u') 
    
                if aux in aux2 or aux2 in aux:
                    
                    Nombre_Cliente = doc.to_dict()['Cliente']
                    results["Nombre de la empresa a la que pertenece"] = results["Nombre de la empresa a la que pertenece"].replace([row["Nombre de la empresa a la que pertenece"]],Nombre_Cliente) 
                            
                    Found = True
                    break
                else:
                    for cliente_encuesta in doc.to_dict()['Encuestas']:
                        aux3 = cliente_encuesta.lower().replace(",","").replace(".","").replace("á",'a').replace("é",'e').replace("í",'i').replace("ó",'o').replace("ú",'u') 
                        
                        if (aux in aux3 or aux3 in aux):
                            Found = True
                            Nombre_Cliente = doc.to_dict()['Cliente']
                            results["Nombre de la empresa a la que pertenece"] = results["Nombre de la empresa a la que pertenece"].replace([row["Nombre de la empresa a la que pertenece"]],Nombre_Cliente) 
                            break
            if Found:
                found_list.append(Nombre_Cliente)
                print("se encontro : " + Nombre_Cliente)
            else:
                not_found_list.append(Nombre_Cliente)
                print("no se encontro : " + Nombre_Cliente)
        
        if len(not_found_list) == 0:
            
            query_trimestre = db.collection('CDC_Respuestas').where('Year', '==',str(Year) ).where('Trimestre', '==', str(Trimestre)).get()
        
            if len(query_trimestre)>0:
                print("ya se ingreso el archivo")
                
            else:
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
                            
            return redirect(url_for('chart'))
        
        else:
             return render_template('clients_form.html', your_list=not_found_list,lista_clientes=lista_clientes)

    return render_template('home.html')

#Chart Page
@app.route('/chart_cdc', methods=['GET', 'POST'])
def chart():
    
    # Variables
    kpi_clients = None
    kpi_q1, kpi_q2, kpi_q3, kpi_q4 = [], [], [], []
    Trimestres, Years, lista_clientes = [], [], []
    kpi_total, avg_q1, avg_q2, avg_q3, avg_q4 = 0, 0, 0, 0, 0
    cliente_unico, graphJSON_esfuerzo, graphJSON_satisfaccion = False, False, False
    graphJSON_lealtad, graphJSON_valor = False, False
    
    #Conexion con la DB - KPI's CDC
    db = firestore.client()
    CDC_KPIS = db.collection('CDC_KPIS').get()
    
    #Guardar Listas Trimestres y años de la DB
    Trimestres, Years, lista_clientes = saveSelectData(CDC_KPIS)
    
    #Guardar Parametros URL
    trimestre_input = (request.args.get('trimestre_input'))
    year_input      = (request.args.get('year_input'))
    cliente_input   = (request.args.get('cliente_input'))
    
    #Validación parametros URL
    trimestre_input, year_input = validarParametros(trimestre_input, year_input, Trimestres, Years)
    
    #Show Table
    if cliente_input is None or cliente_input=="Todos":
        
        #Nota: Se necesitan que esten ordenados?
        kpi_clients = db.collection('CDC_KPIS').order_by("Cliente").get()  #where('Trimestre','==',int(trimestre_input))
        
        #Tabla dinamica
        kpi_q1, kpi_q2, kpi_q3, kpi_q4 = tablaDinamica(kpi_clients)
       
        #Promedio Q's
        avg_q1 = promedioQuarter(kpi_q1)
        avg_q2 = promedioQuarter(kpi_q2)
        avg_q3 = promedioQuarter(kpi_q3)
        avg_q4 = promedioQuarter(kpi_q4)
    
    #Show speedmeter  
    else:
        
        #GET ALL KPI's CDC FROM A SPECIFIC YEAR ALL Q
        kpis_client = db.collection('CDC_KPIS').where('Year','==',int(year_input)).where('Cliente','==',cliente_input).get()
        #KPI's CDC FROM A SPECIFIC Q
        kpi_client, kpi_delta = [], []
        #ONLY ONE CLIENT
        cliente_unico = True
               
        #CALCULATE DELTA     
        for i in kpis_client:
            #GET KPI SPECIFIC QUARTER 
            if(i.to_dict()['Trimestre'] == int(trimestre_input)):
                kpi_client.append(i)
            
            #GET KPI PREVIUS
            if(int(trimestre_input) != 1 and (i.to_dict()['Trimestre'] == (int(trimestre_input)-1))):
                kpi_delta.append(i)
                    
        #SHOW GRAFICOS          
        if len(kpi_client) > 0:
            
            kpi_total = float(kpi_client[0].to_dict()["kpi_total"])
            
            print("Delta")
            print(kpi_delta)
                        
            if(len(kpi_delta) > 0):
                fig_esfuerzo     = speedmeter("Customer Effort Score (CES)",     float(kpi_client[0].to_dict()["kpi_esfuerzo"])    ,kpi_delta[0].to_dict()['kpi_esfuerzo'],7.1,8.2)
                fig_satisfaccion = speedmeter("Customer Satisfaction Score (CSAT)", float(kpi_client[0].to_dict()["kpi_satisfaccion"]),kpi_delta[0].to_dict()['kpi_satisfaccion'],7.4, 8.5)
                fig_lealtad      = speedmeter("Net Promoter Score (NPS)",      float(kpi_client[0].to_dict()["kpi_lealtad"])     ,kpi_delta[0].to_dict()['kpi_lealtad'], 6.9, 9)
                fig_valor        = speedmeter("Valor Añadido (VA)",        float(kpi_client[0].to_dict()["kpi_valor"])       ,kpi_delta[0].to_dict()['kpi_valor'], 6.4, 7.5)
            else:
                fig_esfuerzo     = speedmeter("Customer Effort Score (CES)",     float(kpi_client[0].to_dict()["kpi_esfuerzo"])    , None, 7.1,8.2)
                fig_satisfaccion = speedmeter("Customer Satisfaction Score (CSAT)", float(kpi_client[0].to_dict()["kpi_satisfaccion"]), None, 7.4, 8.5)
                fig_lealtad      = speedmeter("Net Promoter Score (NPS)",      float(kpi_client[0].to_dict()["kpi_lealtad"])     , None, 6.9, 9)
                fig_valor        = speedmeter("Valor Añadido (VA)",        float(kpi_client[0].to_dict()["kpi_valor"])       , None, 6.4, 7.5)
            
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
                           avg_q1 = round(avg_q1,2), 
                           avg_q2 = round(avg_q2,2), 
                           avg_q3 = round(avg_q3,2), 
                           avg_q4 = round(avg_q4,2))


