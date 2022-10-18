from   CX import app
from   flask import render_template,request
from   CX.logic.functions import OrderClientsRankings
from   firebase_admin import firestore



@app.route('/ranking_general', methods=['GET', 'POST'])
def ranking_general():
    
    if request.method == 'GET':
        
        return render_template('rankings.html')
    
    
    if request.method == 'POST':
        Trimestres, Years, lista_KPIS = [], [], []
        
        kpi_clients = db.collection(request.form.get('area')).get()
        Trimestres, Years,lista_KPIS = OrderClientsRankings(kpi_clients)
        
        
        return render_template('rankings.html')

@app.route('/ranking_lealtad', methods=['GET', 'POST'])
def ranking_lealtad():
    db = firestore.client()
   
    if request.method == 'GET':
        if request.form.get('area') is None:
            area = "CDC_KPIS"
        else:
            area = request.form.get('area')
            print('entro')
        
        print(area)
        Periodos = []        
        kpi_clients = db.collection(area).get()
        Periodos = OrderClientsRankings(kpi_clients)
        print(Periodos)
        return render_template('rankings.html',Periodos=Periodos)
    
    if request.method == 'POST': 
        return render_template('rankings.html')