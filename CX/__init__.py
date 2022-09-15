import firebase_admin
from   firebase_admin import credentials, firestore
import json
from   flask import Flask, flash, request, redirect, url_for,render_template, jsonify
from   werkzeug.utils import secure_filename
import os
import pandas as pd
import math
from   CX.logic.functions import mappingValues,SearchClients

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

#Credenciales Firebase
cred = credentials.Certificate("CX/FirebaseKey/customer-experience-53371-firebase-adminsdk-wcb7p-879b654887.json")
firebase_admin.initialize_app(cred)

UPLOAD_FOLDER      = 'CX\\static\\files'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xlsm'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#CHECK FILE TYPE
def allowed_file(filename): 
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
            
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
            results = pd.read_excel(UPLOAD_FOLDER + "\\" + filename)
            results = mappingValues(results) 
            
        not_found_list, found_list, lista_clientes = [], [], []
        
        #Firebase
        db = firestore.client()
        Clientes_Data = db.collection("Clientes").get()
        for doc in Clientes_Data:
            lista_clientes.append(doc.to_dict()['Cliente'])
            
        #Sort clients
        lista_clientes.sort()
        
        #Get trimestre from file
        Trimestre = math.ceil(int(str(results.loc[0,"Marca temporal"])[5:7])/3)
        
        #Get trimestre from year
        Year = int(str(results.loc[0,"Marca temporal"])[0:4])
        
        #verify client in DB
        print(results)
        found_list,not_found_list,results = SearchClients(results,not_found_list,found_list,Clientes_Data)
        print(found_list)
        print(not_found_list)
        
        #Si vacio        
        if len(not_found_list) == 0:
            
            #Get area
            area = request.form.get('area')
            
            if(str(area) == "CDC"):
                cargaRespuestasCDC(db, Year, Trimestre, results, found_list)
                return redirect(url_for('chart_cdc'))
            
            elif str(area) == "Consultoria Corta" or str(area) =="Consultoria Larga":
                cargaRespuestasConsultoria(db, Year,Trimestre, results, found_list, area)
                return redirect(url_for('chart_consultoria'))
            
            elif str(area) == "Proceso Comercial Satisfacción":
                cargaRespuestasPCS(db, Year,Trimestre, results, found_list)
                return redirect(url_for('chart_pcs'))
            
            elif str(area) == "Proceso Comercial Declinación":
                cargaRespuestasPCD(db, Year,Trimestre, results, found_list,area)
                return redirect(url_for('chart_pcd'))
            
            else:
                return redirect(url_for('upload_file'))
            
        else:
             return render_template('clients_form.html', your_list=not_found_list,lista_clientes=lista_clientes)

    return render_template('home.html')

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
            
@app.route('/SaveKPISPercents',methods=["GET", "POST"]) 
def SaveKPISPercents():
    
    if request.method == 'POST':
        
        db = firestore.client()
        Kpis_Ref = db.collection("Rangos_Ponderaciones")
        
        if request.is_json:

            output  = request.json
            output2 = json.dumps(output)
            result  = json.loads(output2) #this converts the json output to a python dictionary
            
            Kpis_Ref.add({
                        'kpi_name': "Net Promoter Score (NPS)",
                        'min': result[0]['min_nps'],
                        'max': result[0]['max_nps'],
                        'ponderacion': result[0]['ponde_nps'],
                        'fecha':result[0]['dateInput'],
                        'year': int(result[0]['dateInput'][:4])
                    })
            Kpis_Ref.add({
                        'kpi_name': "Customer Satisfaction Score (CSAT)",
                        'min': result[0]['min_csat'],
                        'max': result[0]['max_csat'],
                        'ponderacion': result[0]['ponde_csat'],
                        'fecha':result[0]['dateInput'],
                        'year':int(result[0]['dateInput'][:4])
                    })
            Kpis_Ref.add({
                        'kpi_name': "Valor Añadido (VA)",
                        'min': result[0]['min_va'],
                        'max': result[0]['max_va'],
                        'ponderacion': result[0]['ponde_va'],
                        'fecha':result[0]['dateInput'],
                        'year':int(result[0]['dateInput'][:4])
                    })
            Kpis_Ref.add({
                        'kpi_name': "Customer Effort Score (CES)",
                        'min': result[0]['min_ces'],
                        'max': result[0]['max_ces'],
                        'ponderacion': result[0]['ponde_ces'],
                        'fecha':result[0]['dateInput'],
                        'year':int(result[0]['dateInput'][:4])
                    })
            
            return jsonify(success=True)        
            
        else:
            print("no es json")
            
from CX.logic.cdc import cargaRespuestasCDC

from CX.logic.consultoria import cargaRespuestasConsultoria

from CX.logic.pc_satisfaccion import cargaRespuestasPCS

from CX.logic.pc_declinacion import cargaRespuestasPCD

from CX.logic.general import reporteGeneral

from CX.logic.delete import delete

from CX.logic.config import config_ranges_pond