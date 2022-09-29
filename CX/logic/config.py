from   flask import render_template,request,flash,redirect
from   CX import app,firestore,storage,UPLOAD_FOLDER
from   werkzeug.utils import secure_filename
import os
import tempfile
from uuid import uuid4
import json


ALLOWED_EXTENSIONS = {'JPEG', 'JPG', 'PNG','jpeg','jpg','png'}
bucket = storage.bucket()

def allowed_file(filename): 
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
           
           
#Chart Page
@app.route('/config_ranges_pond', methods=['GET', 'POST'])
def config_ranges_pond():
    return render_template('config_ran_pond.html')

@app.route('/clients_images', methods=['GET', 'POST'])
def clients_images():
    db = firestore.client()
    
    Clientes_Ref = db.collection("Clientes")
    Clientes_Data = Clientes_Ref.order_by("Cliente").get()
    if request.method == 'GET':
        
        return render_template('clients_images.html',Clientes_Data = Clientes_Data)
    #print(Clientes_Data)
    if request.method == 'POST':
        
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
            
            
                
            #Firebase
            try:
                
                #firebase.storage().put('Imagenes_Cliente/' + temp.name)
                
                # Create new token
                new_token = uuid4()
                
                cliente = json.loads((request.form.get('cliente_input')).replace("'",'"'))
                print(cliente)
                
                # Create new dictionary with the metadata
                metadata  = {"firebaseStorageDownloadTokens": new_token}

                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                
                blob = bucket.blob(UPLOAD_FOLDER + "\\" + filename)
                
                # Set metadata to blob
                blob.metadata = metadata
                
                
                blob.upload_from_filename(filename=UPLOAD_FOLDER + "\\" + filename)
                blob.make_public()
                img_url = blob.public_url
                
                docs = Clientes_Ref.where("Cliente","==", cliente['Cliente']).get()
                for doc in docs:
                    id = doc.id
                Clientes_Ref.document(id).update({'Imagen':blob.public_url})
                # Clean-up temp image
                os.remove(UPLOAD_FOLDER + "\\" + filename)
            except Exception as e:
                print(e)
                flash("Error al cargar el archivo",'error')
        
        else:
            flash("Error formato del archivo erroneo", "error") 
            
        
        
        return render_template('clients_images.html',Clientes_Data = Clientes_Data)