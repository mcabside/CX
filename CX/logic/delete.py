from   flask import request, flash, render_template, redirect,url_for
from   firebase_admin import firestore
from   CX import app

def delete_collection(coll_ref, batch_size):
    docs = coll_ref.limit(batch_size).stream()
    deleted = 0
    for doc in docs:
        print(f'Deleting doc {doc.id} => {doc.to_dict()}')
        doc.reference.delete()
        deleted = deleted + 1

    if deleted >= batch_size:
        return delete_collection(coll_ref, batch_size)

#Delete Page
@app.route('/delete', methods=['GET', 'POST'])
def delete():
    
    if request.method == 'POST':
        
        try:
            #Guardar Parametros URL
            trimestre_delete = request.form.get('trimestre_delete')
            year_delete      = request.form.get('year_delete')
            area_delete      = request.form.get('area_delete')
            
            db = firestore.client()
        
            if(str(area_delete) == "CDC"):
                delete_collection(db.collection('CDC_Respuestas').where('Year', '==',str(year_delete) ).where('Trimestre', '==', str(trimestre_delete)),32)
                delete_collection(db.collection('CDC_KPIS').where('Year', '==',int(year_delete) ).where('Trimestre', '==', int(trimestre_delete)),32)
                flash("Se borro " + area_delete + " Q"+ trimestre_delete + " " + year_delete, "success")
                return redirect(url_for('chart_cdc'))
                
            elif str(area_delete) == "Consultoria":
                delete_collection(db.collection('Consultoria_Respuestas').where('Year', '==',str(year_delete) ).where('Trimestre', '==', str(trimestre_delete)),32)
                delete_collection(db.collection('Consultoria_KPIS').where('Year', '==',int(year_delete) ).where('Trimestre', '==', int(trimestre_delete)),32)
                flash("Se borro " + area_delete + " Q"+ trimestre_delete + " " + year_delete, "success")
                return redirect(url_for('chart_consultoria'))
            
            elif str(area_delete) == "Proceso Comercial Satisfacción":
                delete_collection(db.collection('PCS_Respuestas').where('Year', '==',str(year_delete) ).where('Trimestre', '==', str(trimestre_delete)),32)
                delete_collection(db.collection('PCS_KPIS').where('Year', '==',int(year_delete) ).where('Trimestre', '==', int(trimestre_delete)),32)
                flash("Se borro " + area_delete + " Q"+ trimestre_delete + " " + year_delete, "success")
                return redirect(url_for('chart_pcs'))
            
            elif str(area_delete) == "Proceso Comercial Declinación":
                delete_collection(db.collection('PCD_Respuestas').where('Year', '==',str(year_delete) ).where('Trimestre', '==', str(trimestre_delete)),32)
                delete_collection(db.collection('PCD_KPIS').where('Year', '==',int(year_delete) ).where('Trimestre', '==', int(trimestre_delete)),32)
                flash("Se borro " + area_delete + " Q"+ trimestre_delete + " " + year_delete, "success")
                return redirect(url_for('chart_pcd'))
            
            else:
                return redirect(url_for('upload_file'))
        except:
            flash("Error al eliminar info", "error")
            
    return render_template('delete.html')
    
    


