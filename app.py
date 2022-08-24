import os
from flask import Flask, flash, request, redirect, url_for,render_template,jsonify
from werkzeug.utils import secure_filename
import pandas as pd
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import json
import threading
import math
from aux_functions import carga_preguntas,carga_kpi

cred = credentials.Certificate("FirebaseKey/customer-experience-53371-firebase-adminsdk-wcb7p-879b654887.json")
firebase_admin.initialize_app(cred)


UPLOAD_FOLDER = 'C:\\Users\Abside User\Desktop\customer experience'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xlsm'}
#CLIENTES_FILE = "Nombres_Cliente.xlsx"

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename): #check file type
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/SaveClients',methods=["GET", "POST"]) #save new clients in firebase
def SaveClients():
    
    if request.method == 'POST':
        
        db = firestore.client()
        Clientes_Ref = db.collection("Clientes")
        
        if request.is_json:

            
            output = request.json
            output2 = json.dumps(output)
            

            result = json.loads(output2) #this converts the json output to a python dictionary

            
        
            for cliente in result:
                
                if cliente['Es_nuevo'] == "True": 
                    Clientes_Ref.add({
                        'Cliente': cliente['Input'],
                        'Encuestas': [cliente['Excel']]
                    })

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

        not_found=0
        found=0
        not_found_list = []
        found_list = []
        lista_clientes = []
        
        db = firestore.client()
        Clientes_Data = db.collection("Clientes").get()
        CDC_Respuestas_Ref = db.collection("CDC_Respuestas")
        for doc in Clientes_Data:
            lista_clientes.append(doc.to_dict()['Cliente'])
        lista_clientes.sort()
        Trimestre = math.ceil(int(str(results.loc[0,"Marca temporal"])[5:7])/3)
        Year = int(str(results.loc[0,"Marca temporal"])[0:4])
        print(Trimestre)
        print(Year)
        for index, row in results.iterrows():

            Found = False
            Nombre_Cliente = row["Nombre de la empresa a la que pertenece"]
            for doc in Clientes_Data:
                if row["Nombre de la empresa a la que pertenece"] == doc.to_dict()['Cliente']:
                    Found = True
                    break
                else:
                    for cliente_encuesta in doc.to_dict()['Encuestas']:
                        if (row["Nombre de la empresa a la que pertenece"].lower() == cliente_encuesta.lower() or 
                            row["Nombre de la empresa a la que pertenece"].lower() in cliente_encuesta.lower() or 
                            cliente_encuesta.lower() in row["Nombre de la empresa a la que pertenece"].lower()  or 
                            row["Nombre de la empresa a la que pertenece"].lower().replace(",","").replace(".","").replace("á",'a').replace("é",'e').replace("í",'i').replace("ó",'o').replace("ú",'u') == cliente_encuesta.lower().replace(",","").replace(".","").replace("á",'a').replace("é",'e').replace("í",'i').replace("ó",'o').replace("ú",'u') or 
                            row["Nombre de la empresa a la que pertenece"].lower().replace(",","").replace(".","").replace("á",'a').replace("é",'e').replace("í",'i').replace("ó",'o').replace("ú",'u') in cliente_encuesta.lower().replace(",","").replace(".","").replace("á",'a').replace("é",'e').replace("í",'i').replace("ó",'o').replace("ú",'u') )  :
                            
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

        print("# encontrados : " + str(found))
        print("# no encontrados : " + str(not_found))
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
                    kpi_esfuerzo = 0
                    kpi_satisfaccion = 0
                    kpi_lealtad = 0
                    kpi_valor = 0
                    numero_de_respuestas = 0
                    query_kpi = db.collection('CDC_Respuestas').where('Year', '==',str(Year) ).where('Trimestre', '==', str(Trimestre)).where("Nombre_de_la_empresa_a_la_que_pertenece", '==', cliente).get()
                    
                    for doc in query_kpi:
                        
                        kpi_esfuerzo += (float(doc.to_dict()['kpi_esfuerzo']))
                        kpi_satisfaccion += (float(doc.to_dict()['kpi_satisfaccion']))
                        kpi_lealtad += (float(doc.to_dict()['kpi_lealtad']))
                        kpi_valor += (float(doc.to_dict()['kpi_valor']))
                        
                        numero_de_respuestas += 1
                        
                        
                        
                    kpi_esfuerzo = kpi_esfuerzo/numero_de_respuestas
                    kpi_satisfaccion = kpi_satisfaccion/numero_de_respuestas
                    kpi_lealtad = kpi_lealtad/numero_de_respuestas
                    kpi_valor = kpi_valor/numero_de_respuestas
                    
                    kpi_total = (kpi_esfuerzo*0.20) + (kpi_satisfaccion*0.35) + (kpi_lealtad*0.35) + (kpi_valor*0.10)
                    
                    
                    carga_kpi(cliente,CDC_KPI_Ref,Trimestre,Year,kpi_esfuerzo,kpi_satisfaccion,kpi_lealtad,kpi_valor,kpi_total) 
                
            
            
            return render_template('simple.html',  tables=[results.to_html(classes='data', header="true")])
        
        else:
             return render_template('clients_form.html', your_list=not_found_list,lista_clientes=lista_clientes)

    return render_template('home.html')


@app.route('/chart', methods=['GET', 'POST'])
def chart():
    
    if request.method == 'POST':
        output = request.json
        output2 = json.dumps(output)    
        result = json.loads(output2) #this converts the json output to a python dictionary
        
        db = firestore.client()
        kpi_clients = db.collection('CDC_KPIS').where('Year','==',2022).where('Trimestre','==',2).get()
        x = []
        y = []
        
        for doc in kpi_clients:
            x.append(doc.to_dict()['Cliente'])
            y.append(float(doc.to_dict()[result['kpi']]))
            
        return render_template('chart.html',x=x,y=y)
    else:
    
        db = firestore.client()
        kpi_clients = db.collection('CDC_KPIS').where('Year','==',2022).where('Trimestre','==',2).get()
        x = []
        y = []
        
        for doc in kpi_clients:
            x.append(doc.to_dict()['Cliente'])
            y.append(float(doc.to_dict()['kpi_total']))
                
        return render_template('chart.html',x=x,y=y)
