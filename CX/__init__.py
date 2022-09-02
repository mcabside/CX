import firebase_admin
from   firebase_admin import credentials, firestore
import json
from   flask import Flask, flash, request, redirect, url_for,render_template, jsonify
from   werkzeug.utils import secure_filename
import os
import pandas as pd
import math
from   CX.functions import mappingValues,SearchClients

app = Flask(__name__)

#Credenciales Firebase
cred = credentials.Certificate("CX/FirebaseKey/customer-experience-53371-firebase-adminsdk-wcb7p-879b654887.json")
firebase_admin.initialize_app(cred)

UPLOAD_FOLDER      = 'CX'
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
            results = pd.read_excel(filename)
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
        found_list,not_found_list,results = SearchClients(results,not_found_list,found_list,Clientes_Data)
        
        #Si vacio        
        if len(not_found_list) == 0:
            
            #Get area
            area = request.form.get('area')
            
            if(str(area) == "CDC"):
                print(str(area))
                cargaRespuestasCDC(db, Year, Trimestre, results, found_list)
                return redirect(url_for('chart_cdc'))
            else:
                return redirect(url_for('chart_consultoria'))
        
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
            
from CX.cdc import cargaRespuestasCDC

import CX.consultoria