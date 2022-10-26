from   CX import app
from   flask import render_template,request
from   CX.logic.functions import saveSelectData,getHistorico
from   firebase_admin import firestore
import plotly
import json



@app.route('/historico_cdc', methods=['GET', 'POST'])
def historico_cdc():
    db = firestore.client()
    Area = "CDC"
    kpi_input = "kpi_lealtad"
    Trimestres, Years, lista_clientes = [], [], []
    kpi_clients = db.collection('CDC_KPIS').order_by("Cliente").get() #Get All CDC KPI's
    #Guardar Listas Trimestres y años de la DB
    Trimestres, Years, lista_clientes = saveSelectData(kpi_clients)
    
    if request.method == 'GET':
        return render_template('historico.html',lista_clientes=lista_clientes,Area=Area)
    
    if request.method == 'POST':
        cliente_input   = (request.form.get('cliente_input'))
        kpi_input = (request.form.get('kpi_input'))
        historico_graph = getHistorico(kpi_clients,cliente_input,kpi_input,Area)
        historico_graph  = json.dumps(historico_graph,  cls=plotly.utils.PlotlyJSONEncoder)
        return render_template('historico.html',
                               lista_clientes=lista_clientes,
                               cliente_input=cliente_input,
                               kpi_input=kpi_input,
                               historico_graph=historico_graph,
                               busqueda=True,
                               Area=Area)
        
@app.route('/historico_consultoria', methods=['GET', 'POST'])
def historico_consultoria():
    db = firestore.client()
    Area = "Consultoria"
    kpi_input = "kpi_lealtad"
    Trimestres, Years, lista_clientes = [], [], []
    kpi_clients = db.collection('Consultoria_KPIS').order_by("Cliente").get() #Get All CDC KPI's
    
    #Guardar Listas Trimestres y años de la DB
    Trimestres, Years, lista_clientes = saveSelectData(kpi_clients)
    if request.method == 'GET':
        return render_template('historico.html',lista_clientes=lista_clientes,Area=Area)
    
    if request.method == 'POST':
        cliente_input   = (request.form.get('cliente_input'))
        kpi_input = (request.form.get('kpi_input'))
        print("KPI")
        print(kpi_input)
        historico_graph = getHistorico(kpi_clients,cliente_input,kpi_input,Area)
        historico_graph  = json.dumps(historico_graph,  cls=plotly.utils.PlotlyJSONEncoder)
        return render_template('historico.html',
                               lista_clientes=lista_clientes,
                               cliente_input=cliente_input,
                               kpi_input=kpi_input,
                               historico_graph=historico_graph,
                               busqueda=True,
                               Area=Area)

@app.route('/historico_pcd', methods=['GET', 'POST'])
def historico_pcd():
    db = firestore.client()
    Trimestres, Years, lista_clientes = [], [], []
    Area = "Proceso Comercial Declinación"
    kpi_input = "kpi_lealtad"
    kpi_clients = db.collection('PCD_KPIS').order_by("Cliente").get() #Get All CDC KPI's
    
    #Guardar Listas Trimestres y años de la DB
    Trimestres, Years, lista_clientes = saveSelectData(kpi_clients)
    
    if request.method == 'GET':
        return render_template('historico.html',lista_clientes=lista_clientes,Area=Area)
    
    if request.method == 'POST':
        cliente_input   = (request.form.get('cliente_input'))
        kpi_input = (request.form.get('kpi_input'))
        historico_graph = getHistorico(kpi_clients,cliente_input,kpi_input,Area)
        historico_graph  = json.dumps(historico_graph,  cls=plotly.utils.PlotlyJSONEncoder)
        return render_template('historico.html',
                               lista_clientes=lista_clientes,
                               cliente_input=cliente_input,
                               kpi_input=kpi_input,
                               historico_graph=historico_graph,
                               busqueda=True,
                               Area=Area)

@app.route('/historico_pcs', methods=['GET', 'POST'])
def historico_pcs():
    db = firestore.client()
    Trimestres, Years, lista_clientes = [], [], []
    Area = "Proceso Comercial Satisfacción"
    kpi_input = "kpi_lealtad"
    kpi_clients = db.collection('PCS_KPIS').order_by("Cliente").get() #Get All CDC KPI's
    
    #Guardar Listas Trimestres y años de la DB
    Trimestres, Years, lista_clientes = saveSelectData(kpi_clients)
    
    if request.method == 'GET':
        return render_template('historico.html',lista_clientes=lista_clientes,Area=Area)
    
    if request.method == 'POST':
        cliente_input   = (request.form.get('cliente_input'))
        kpi_input = (request.form.get('kpi_input'))
        historico_graph = getHistorico(kpi_clients,cliente_input,kpi_input,Area)
        historico_graph  = json.dumps(historico_graph,  cls=plotly.utils.PlotlyJSONEncoder)
        return render_template('historico.html',
                               lista_clientes=lista_clientes,
                               cliente_input=cliente_input,
                               kpi_input=kpi_input,
                               historico_graph=historico_graph,
                               busqueda=True,
                               Area=Area)
        

