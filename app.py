import os
from pickle import NONE
from flask import Flask, flash, request, redirect, url_for,render_template,jsonify
from werkzeug.utils import secure_filename
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore
import json
#import threading
import math
from aux_functions import carga_preguntas, carga_kpi, speedmeter
from datetime import date
import plotly
#import plotly.graph_objects as go
#import plotly.express as px
#from plotly.subplots import make_subplots


cred = credentials.Certificate("FirebaseKey/customer-experience-53371-firebase-adminsdk-wcb7p-879b654887.json")
firebase_admin.initialize_app(cred)

UPLOAD_FOLDER = 'C:\\Users\Abside User\Desktop\customer experience'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xlsm'}

app = Flask(__name__)
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

            output = request.json
            output2 = json.dumps(output)
            result = json.loads(output2) #this converts the json output to a python dictionary

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

        not_found, found = 0, 0
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
                found+=1
                found_list.append(Nombre_Cliente)
                print("se encontro : " + Nombre_Cliente)
            else:
                not_found+=1
                not_found_list.append(Nombre_Cliente)
                print("no se encontro : " + Nombre_Cliente)

        Area = str(request.form["area"])
        
        if not_found == 0:
            
            query_trimestre = db.collection('CDC_Respuestas').where('Year', '==',str(Year) ).where('Trimestre', '==', str(Trimestre)).get()
        
            if len(query_trimestre)>0:
                print("ya se ingreso el archivo")
            else:
                carga_preguntas(results, CDC_Respuestas_Ref,Trimestre,Year)
                CDC_KPI_Ref = db.collection("CDC_KPIS")
                found_set = set(found_list)
                found_list_unique = list(found_set)
                for cliente in found_list_unique:
                    kpi_esfuerzo, kpi_satisfaccion, kpi_lealtad, kpi_valor, numero_de_respuestas = 0, 0, 0, 0, 0
                    query_kpi = db.collection('CDC_Respuestas').where('Year', '==',str(Year) ).where('Trimestre', '==', str(Trimestre)).where("Nombre_de_la_empresa_a_la_que_pertenece", '==', cliente).get()
                    
                    for doc in query_kpi:
                        
                        kpi_esfuerzo += (float(doc.to_dict()['kpi_esfuerzo']))
                        kpi_satisfaccion += (float(doc.to_dict()['kpi_satisfaccion']))
                        kpi_lealtad += (float(doc.to_dict()['kpi_lealtad']))
                        kpi_valor += (float(doc.to_dict()['kpi_valor']))
                        
                        numero_de_respuestas += 1
                        
                    kpi_esfuerzo = round(kpi_esfuerzo/numero_de_respuestas, 2)
                    kpi_satisfaccion = round(kpi_satisfaccion/numero_de_respuestas,2)
                    kpi_lealtad = round(kpi_lealtad/numero_de_respuestas,2)
                    kpi_valor = round(kpi_valor/numero_de_respuestas,2)
                    
                    kpi_total = round((kpi_esfuerzo*0.20) + (kpi_satisfaccion*0.35) + (kpi_lealtad*0.35) + (kpi_valor*0.10), 2)
                    
                    carga_kpi(cliente,CDC_KPI_Ref,Trimestre,Year,kpi_esfuerzo,kpi_satisfaccion,kpi_lealtad,kpi_valor,kpi_total) 
                            
            return redirect(url_for('chart'))
        
        else:
             return render_template('clients_form.html', your_list=not_found_list,lista_clientes=lista_clientes)

    return render_template('home.html')


@app.route('/chart', methods=['GET', 'POST'])
def chart():
    
    #Lista Nombres KPI
    tipos_kpi_ori = ["kpi_total", "kpi_esfuerzo", "kpi_lealtad","kpi_satisfaccion","kpi_valor"]
    tipos_kpi_nice = ["KPI Total", "KPI Esfuerzo", "KPI Lealtad", "KPI Satisfaccion", "KPI Valor"]
    
    #Conexion con la DB - KPI's CDC
    db = firestore.client()
    CDC_KPIS = db.collection('CDC_KPIS').get()

    #Variables
    cliente_unico, graphJSON_total, graphJSON_esfuerzo, graphJSON_satisfaccion = False, False, False, False
    graphJSON_lealtad, graphJSON_valor = False, False
    Years, Trimestres, lista_clientes = [], [], []
    
    #Guardar Listas Trimestres y años
    for doc in CDC_KPIS:
        if doc.to_dict()["Trimestre"] not in Trimestres:
            Trimestres.append(doc.to_dict()["Trimestre"])
            
        if doc.to_dict()["Year"] not in Years:
            Years.append(doc.to_dict()["Year"])
        
    #Conexión con la DB - Lista clientes
    Clientes_Data = db.collection("Clientes").get()
    for doc in Clientes_Data:
        lista_clientes.append(doc.to_dict()['Cliente'])
    lista_clientes.sort()
     
    #Parametros URL
    kpi_name = (request.args.get('kpi'))
    trimestre_input = (request.args.get('trimestre_input'))
    year_input = (request.args.get('year_input'))
    cliente_input = (request.args.get('cliente_input'))
    
    #Validación parametros
    if kpi_name != "kpi_total" and kpi_name != "kpi_esfuerzo" and kpi_name != "kpi_lealtad" and kpi_name != "kpi_satisfaccion" and kpi_name != "kpi_valor":
        kpi_name = "kpi_total"
    if trimestre_input is None:
        if len(Trimestres) >0:
            trimestre_input = Trimestres[len(Trimestres)-1]
        else:
            trimestre_input = 1
    if year_input is None:
        if len(Years) >0:
            year_input = Years[len(Years)-1]
        else:
            year_input = int(date.today().year)
    
    # Lista Clientes/ Lista KPI
    x, y = [], [] 
    Promedio_total_q = 0
    kpi_clients = None

    if cliente_input is None or cliente_input=="Todos":
        
        kpi_clients = db.collection('CDC_KPIS').where('Trimestre','==',int(trimestre_input)).where('Year','==',int(year_input)).get()
        
        for doc in kpi_clients:
            x.append(doc.to_dict()['Cliente'])
            y.append(float(doc.to_dict()[kpi_name]))
            
        for j in range(len(x)):
            aux_x = x[j]
            aux_x_i = j  
            for i in range(j,len(x)):
                if x[i] < aux_x:
                    aux_x = x[i]
                    aux_x_i = i
            aux_1 = x[j]
            aux_2 = y[j]
            
            x[j] = aux_x
            y[j] = y[aux_x_i]
            
            x[aux_x_i] = aux_1
            y[aux_x_i] = aux_2
        
        for kpi_value in y:
            Promedio_total_q += kpi_value
        Promedio_total_q = Promedio_total_q/len(y)
                
    else:
        
        kpi_client = db.collection('CDC_KPIS').where('Trimestre','==',int(trimestre_input)).where('Year','==',int(year_input)).where('Cliente','==',cliente_input).get()
        cliente_unico = True

        for doc in kpi_client:
            x.append("total")
            x.append("esfuerzo")
            x.append("satisfaccion")
            x.append("lealtad")
            x.append("valor")
            y.append(float(doc.to_dict()["kpi_total"]))
            y.append(float(doc.to_dict()["kpi_esfuerzo"]))
            y.append(float(doc.to_dict()["kpi_satisfaccion"]))
            y.append(float(doc.to_dict()["kpi_lealtad"]))
            y.append(float(doc.to_dict()["kpi_valor"]))
            
        if len(y)>0:
            
            fig_total        = speedmeter("Total", y[0])
            fig_esfuerzo     = speedmeter("Esfuerzo", y[1])
            fig_satisfaccion = speedmeter("Satisfacción", y[2])
            fig_lealtad      = speedmeter("Lealtad", y[3])
            fig_valor        = speedmeter("Valor", y[4])

            graphJSON_total         = json.dumps(fig_total, cls=plotly.utils.PlotlyJSONEncoder)
            graphJSON_esfuerzo      = json.dumps(fig_esfuerzo, cls=plotly.utils.PlotlyJSONEncoder)
            graphJSON_satisfaccion  = json.dumps(fig_satisfaccion, cls=plotly.utils.PlotlyJSONEncoder)
            graphJSON_lealtad       = json.dumps(fig_lealtad, cls=plotly.utils.PlotlyJSONEncoder)
            graphJSON_valor         = json.dumps(fig_valor, cls=plotly.utils.PlotlyJSONEncoder)
        
    return render_template('chart.html',x=x,y=y,kpi_name=kpi_name,Trimestres=Trimestres,
                           Years=Years,lista_clientes=lista_clientes,cliente_unico=cliente_unico,
                           cliente_input=cliente_input,trimestre_input=int(trimestre_input), 
                           tipos_kpi_ori=tipos_kpi_ori,tipos_kpi_nice=tipos_kpi_nice,Promedio_total_q=round(Promedio_total_q,2),
                           graphJSON_total=graphJSON_total,graphJSON_esfuerzo=graphJSON_esfuerzo,
                           graphJSON_satisfaccion=graphJSON_satisfaccion,graphJSON_lealtad=graphJSON_lealtad,
                           graphJSON_valor=graphJSON_valor,
                           kpi_clients=kpi_clients)
