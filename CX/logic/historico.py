from   pickle import TRUE
from   CX import app
from   flask import render_template,request
from   CX.logic.functions import saveSelectData, getHistorico, unificarClientes
from   firebase_admin import firestore
import plotly
import json

@app.route('/historico', methods=['GET', 'POST'])
def historico():
    db = firestore.client()
    Area, KPI, client = "CDC", "kpi_total", ""
    Trimestres, Years, lista_clientes, kpi_clients, historico_graph = [], [], [], [], []
    list_clients_cdc, list_clients_con, list_clients_pcs, list_clients_pcd = [], [], [], []
    hayData = False
    
    #Check area
    if(request.form.get('area_input') is not None):
        Area   = request.form.get('area_input')
        
    kpi_clients_cdc = db.collection('CDC_KPIS').get()
    kpi_clients_con = db.collection('Consultoria_KPIS').get()
    kpi_clients_pcs = db.collection('PCS_KPIS').get()
    kpi_clients_pcd = db.collection('PCD_KPIS').get()
        
    Trimestres, Years, list_clients_cdc = saveSelectData(kpi_clients_cdc)
    Trimestres, Years, list_clients_con = saveSelectData(kpi_clients_con)
    Trimestres, Years, list_clients_pcs = saveSelectData(kpi_clients_pcs)
    Trimestres, Years, list_clients_pcd = saveSelectData(kpi_clients_pcd)
    
    if(Area == "Todas"):
        #Unificar lista de clientes
        lista_clientes = unificarClientes(lista_clientes, list_clients_cdc)
        lista_clientes = unificarClientes(lista_clientes, list_clients_con)
        lista_clientes = unificarClientes(lista_clientes, list_clients_pcs)
        lista_clientes = unificarClientes(lista_clientes, list_clients_pcd)
        lista_clientes.sort()
    else:
        if (Area == "CDC"):
            kpi_clients = db.collection('CDC_KPIS').order_by("Cliente").get() #Get All CDC KPI's
        elif (Area == "Consultoria"):
            kpi_clients = db.collection('Consultoria_KPIS').order_by("Cliente").get() #Get All Consultoria KPI's
        elif (Area == "PCS"):
            kpi_clients = db.collection('PCS_KPIS').order_by("Cliente").get() #Get All PCS KPI's
        elif (Area == "PCD"):
            kpi_clients = db.collection('PCD_KPIS').order_by("Cliente").get() #Get All PCD KPI's

        #Guardar Listas Trimestres y años de la DB
        Trimestres, Years, lista_clientes = saveSelectData(kpi_clients)
        
    #Validar parametros
    if(request.form.get('cliente_input') is not None):
        client = request.form.get('cliente_input')
    else:
        client = lista_clientes[0]
        
    if(request.form.get('kpi_input') is not None):
        KPI    = request.form.get('kpi_input')
        
    #GET/POST
    if request.method == 'GET':
        return render_template('historico.html',
                               lista_clientes=lista_clientes, 
                               list_clients_cdc = list_clients_cdc,
                               list_clients_con = list_clients_con,
                               list_clients_pcs = list_clients_pcs,
                               list_clients_pcd = list_clients_pcd,
                               Area=Area)
    
    if request.method == 'POST':
        collection = Area + "_KPIS"
        kpi_client = db.collection(collection).where('Cliente', '==', client).get()
        
        if(len(kpi_client) > 0):    
            historico_graph = getHistorico(kpi_client, client, KPI, Area)
            historico_graph = json.dumps(historico_graph,  cls=plotly.utils.PlotlyJSONEncoder)
            hayData = True
        
        return render_template('historico.html',
                               lista_clientes   = lista_clientes,
                               list_clients_cdc = list_clients_cdc,
                               list_clients_con = list_clients_con,
                               list_clients_pcs = list_clients_pcs,
                               list_clients_pcd = list_clients_pcd,
                               cliente_input    = client,
                               kpi_input        = KPI,
                               historico_graph  = historico_graph,
                               busqueda         = True,
                               Area             = Area,
                               hayData          = hayData)
        
    return True

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
        

