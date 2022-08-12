import os
from flask import Flask, flash, request, redirect, url_for,render_template,jsonify
from werkzeug.utils import secure_filename
import pandas as pd
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import json
import threading

cred = credentials.Certificate("FirebaseKey/customer-experience-53371-firebase-adminsdk-wcb7p-879b654887.json")
firebase_admin.initialize_app(cred)









UPLOAD_FOLDER = 'C:\\Users\Abside User\Desktop\customer experience'
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xlsm'}
#CLIENTES_FILE = "Nombres_Cliente.xlsx"

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/SaveClients',methods=["GET", "POST"])
def SaveClients():
    
    if request.method == 'POST':
        
        db = firestore.client()
        Clientes_Ref = db.collection("Clientes")
        
        if request.is_json:
            print("es json")
            
            #output = request.form.get('json_data')
            output = request.json
            output2 = json.dumps(output)
            
            print(output2) # This is the output that was stored in the JSON within the browser
            print(type(output2))
            result = json.loads(output2) #this converts the json output to a python dictionary
            print(result) # Printing the new dictionary
            print(type(result))#this shows the json converted as a python dictionary
            
        
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
            
            
    #return render_template('home.html')

        

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

        #clientes = pd.read_excel("assets\\"+CLIENTES_FILE)
        
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            results = pd.read_excel(filename) 
            results.replace(["No satisfecho","Ningún Valor","En Desacuerdo"],2,inplace=True)
            results.replace(["Baja Satisfacción","Poco Valor","Casi Nunca"],4,inplace=True)
            results.replace(["Satisfacción Promedio","Valor Promedio","Normalmente de Acuerdo"],6,inplace=True)
            results.replace(["Buena Satisfacción","Gran Valor","Totalmente de Acuerdo"],8,inplace=True)
            results.replace(["Supera las Expectativas"],10,inplace=True)

        not_found=0
        found=0
        not_found_list = []
        lista_clientes = []
        
        db = firestore.client()
        Clientes_Data = db.collection("Clientes").get()
        for doc in Clientes_Data:
            lista_clientes.append(doc.to_dict()['Cliente'])
        lista_clientes.sort()
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
                            
                            break

            
            if Found:
                found+=1
                print("se encontro : " + Nombre_Cliente)
            else:
                not_found+=1
                not_found_list.append(Nombre_Cliente)
                print("no se encontro : " + Nombre_Cliente)

        print("# encontrados : " + str(found))
        print("# no encontrados : " + str(not_found))

        
        if not_found == 0:
            return render_template('simple.html',  tables=[results.to_html(classes='data', header="true")])
        else:
             return render_template('your_view.html', your_list=not_found_list,lista_clientes=lista_clientes)

    return render_template('home.html')