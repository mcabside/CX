import firebase_admin
from   firebase_admin import credentials, firestore, storage
import json
from   flask import Flask, flash, request, redirect, url_for,render_template, jsonify, send_from_directory
from   werkzeug.utils import secure_filename
import os
import pandas as pd
import math
from   CX.logic.functions import mappingValues, SearchClients, addKPIRange, updateKPIRange
from   flask_toastr import Toastr

app = Flask(__name__)
toastr = Toastr(app)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

#Credenciales Firebase
cred = credentials.Certificate("CX/FirebaseKey/customer-experience-53371-firebase-adminsdk-wcb7p-879b654887.json")
firebase_admin.initialize_app(cred, { 'storageBucket' : 'customer-experience-53371.appspot.com'})

UPLOAD_FOLDER      = 'CX\\static\\files'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xlsm'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#CHECK FILE TYPE
def allowed_file(filename): 
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
        
#Icon
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),'favicon.ico', mimetype='img/icon.png')
            
#Home Page / upload file page
@app.route('/', methods=['GET', 'POST'])
def upload_file():
    
    if request.method == "GET":
        return render_template('upload_file.html')
    
    if request.method == 'POST':
        
        # check if the post request has the file part
        if 'file' not in request.files:
            flash("Debe ingresar un archivo", 'error')
            return redirect(request.url)
        
        # If the user does not select a file, the browser submits an
        file = request.files['file']                  
        
        # Empty file without a filename.
        if file.filename == '':                         
            flash('Debe ingresar un archivo', 'error')
            return redirect(request.url)
        
        # Verificar si existe el archivo y si tiene el formato correcto
        if file and allowed_file(file.filename):
            
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            results  = pd.read_excel(UPLOAD_FOLDER + "\\" + filename)
            results  = mappingValues(results)
            os.remove(UPLOAD_FOLDER + "\\" + filename)
            
            #Variables aux
            not_found_list, found_list, lista_clientes = [], [], []
                
            #Firebase
            try:
                #Check clients
                db = firestore.client()
                Clientes_Data = db.collection("Clientes").get()
                for doc in Clientes_Data:
                    lista_clientes.append(doc.to_dict()['Cliente'])
                    
                #Sort clients list
                lista_clientes.sort()
            
                #Get trimestre and year from file
                Trimestre = math.ceil(int(str(results.loc[0,"Marca temporal"])[5:7])/3)
                Year      = int(str(results.loc[0,"Marca temporal"])[0:4])
                
                #verify client in DB
                found_list, not_found_list, results = SearchClients(results,not_found_list,found_list,Clientes_Data)
            
                #Si se consiguen todos los clientes        
                if len(not_found_list) == 0:
                                    
                    #Get area
                    area = request.form.get('area')
                    
                    if(str(area) == "CDC"):
                        cargaRespuestasArea(db, Year, Trimestre, results, found_list, "CDC")
                        return redirect(url_for('chart'))
                    
                    elif str(area) == "Consultoria Corta" or str(area) =="Consultoria Larga":
                        cargaRespuestasArea(db, Year,Trimestre, results, found_list, area, "Consultoria")
                        return redirect(url_for('chart'))
                    
                    elif str(area) == "Proceso Comercial Satisfacción":
                        cargaRespuestasArea(db, Year,Trimestre, results, found_list, "PCS")
                        return redirect(url_for('chart'))
                    
                    elif str(area) == "Proceso Comercial Declinación":
                        cargaRespuestasArea(db, Year,Trimestre, results, found_list,area, "PCD")
                        return redirect(url_for('chart'))
                else:
                    flash("No se han encontrado estos cliente en la base de datos", 'info')
                    return render_template('clients_form.html', your_list=not_found_list,lista_clientes=lista_clientes)
                            
            except:
                flash("Error al cargar el archivo",'error')
        
        else:
            flash("Error formato del archivo erroneo", "error") 
            
    return render_template('upload_file.html')

#SAVE NEW CLIENTS IN FIREBASE
@app.route('/SaveClients',methods=["GET", "POST"]) 
def SaveClients():
    
    if request.method == 'POST':
        
        try:
            db = firestore.client()
            Clientes_Ref = db.collection("Clientes")
            
            if request.is_json:

                output = json.dumps(request.json)
                result  = json.loads(output) #this converts the json output to a python dictionary

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
                flash("Error en el formato del archivo", 'error')
        except:
            flash("Error al cargar los clientes","error")
           
#Save KPI's and Percents
@app.route('/SaveKPISPercents',methods=["GET", "POST"]) 
def SaveKPISPercents():
    
    if request.method == 'POST':
        
        db = firestore.client()
        Kpis_Ref = db.collection("Rangos_Ponderaciones")
        
        if request.is_json:

            output2 = json.dumps(request.json)
            result  = json.loads(output2)       #this converts the json output to a python dictionary
            
            #Check if exists KPI ranges
            kpi_q = db.collection('Rangos_Ponderaciones').where('year', '==', int(result[0]['dateInput'][:4])).get()
            
            try:
                if(len(kpi_q) == 0):
                    #Agregar KPI
                    addKPIRange(Kpis_Ref, "Net Promoter Score (NPS)", result[0]['min_nps'], result[0]['max_nps'], result[0]['ponde_nps'], result[0]['dateInput'])
                    addKPIRange(Kpis_Ref, "Customer Satisfaction Score (CSAT)", result[0]['min_csat'], result[0]['max_csat'], result[0]['ponde_csat'], result[0]['dateInput'])
                    addKPIRange(Kpis_Ref, "Valor Añadido (VA)", result[0]['min_va'], result[0]['max_va'], result[0]['ponde_va'], result[0]['dateInput'])
                    addKPIRange(Kpis_Ref, "Customer Effort Score (CES)", result[0]['min_ces'], result[0]['max_ces'], result[0]['ponde_ces'], result[0]['dateInput'])
                    flash("Información cargada correctamente", 'success')
                else:
                    # Actualizar campos
                    updateKPIRange(Kpis_Ref, kpi_q, result)
                    flash("Información actualizada correctamente", 'success')
                    
            except:
                flash("Error al actualizar/agregar rangos y ponderaciones")
           
            return jsonify(success=True)        
            
        else:
            flash("Error en el formato del archivo", 'error')
            
#from CX.logic.respaldo.cdc import cargaRespuestasCDC

#from CX.logic.respaldo.consultoria import cargaRespuestasConsultoria

#from CX.logic.respaldo.pc_satisfaccion import cargaRespuestasPCS

#from CX.logic.respaldo.pc_declinacion import cargaRespuestasPCD

from CX.logic.reporte_area import cargaRespuestasArea

from CX.logic.general import reporteGeneral

from CX.logic.reporte_area import chart

from CX.logic.delete import delete

from CX.logic.config import config_ranges_pond, clients_images

#from CX.logic.rankings import ranking_general,ranking_lealtad

from CX.logic.historico import *