from   CX import app
from   flask import render_template, request
from   CX.logic.functions import saveSelectData, getHistorico, unificarClientes, getHistoricoTodaslasAreas
from   firebase_admin import firestore
import plotly
import json

kpi_clients_cdc, kpi_clients_con, kpi_clients_pcs, kpi_clients_pcd = [], [], [], []
lista_clientes, list_clients_cdc, list_clients_con, list_clients_pcs, list_clients_pcd = [], [], [], [], []

@app.route('/historico', methods=['GET', 'POST'])
def historico():
    
    #Variables
    global kpi_clients_cdc, kpi_clients_con, kpi_clients_pcs, kpi_clients_pcd
    global lista_clientes, list_clients_cdc, list_clients_con, list_clients_pcs, list_clients_pcd
    hayData = False
    
    area_input = "Todas"
    
    if request.method == 'GET':
        #Get KPI's for all areas
        db = firestore.client()
        kpi_clients_cdc = db.collection('CDC_KPIS').get()
        kpi_clients_con = db.collection('Consultoria_KPIS').get()
        kpi_clients_pcs = db.collection('PCS_KPIS').get()
        kpi_clients_pcd = db.collection('PCD_KPIS').get()
        
        #Extract list of clients for all areas    
        list_clients_cdc = saveSelectData(kpi_clients_cdc, "Cliente", True)
        list_clients_con = saveSelectData(kpi_clients_con, "Cliente", True)
        list_clients_pcs = saveSelectData(kpi_clients_pcs, "Cliente", True)
        list_clients_pcd = saveSelectData(kpi_clients_pcd, "Cliente", True)
        
        lista_clientes = unificarClientes(lista_clientes, list_clients_cdc)
        lista_clientes = unificarClientes(lista_clientes, list_clients_con)
        lista_clientes = unificarClientes(lista_clientes, list_clients_pcs)
        lista_clientes = unificarClientes(lista_clientes, list_clients_pcd)
        
        lista_clientes.sort()
        
        #Ordenar

        return render_template('historico.html',
                                lista_clientes   = lista_clientes, 
                                list_clients_cdc = list_clients_cdc,
                                list_clients_con = list_clients_con,
                                list_clients_pcs = list_clients_pcs,
                                list_clients_pcd = list_clients_pcd,
                                hayData          = hayData)

    if request.method == 'POST':
        #Guardar Parametros URL
        kpi_input       = request.form.get('kpi_input')
        cliente_input   = request.form.get('cliente_input')
        area_input      = request.form.get('area_input')
        historico_graph = None
        hayData         = False
        
        #Filter Data
        if(area_input == "CDC"):
            lista_clientes = list_clients_cdc
            if(len(kpi_clients_cdc) > 0):    
                historico_graph = getHistorico(kpi_clients_cdc, cliente_input, kpi_input, area_input)
                hayData = True         
        elif(area_input == "Consultoria"):
            lista_clientes = list_clients_con
            if(len(kpi_clients_con) > 0):    
                historico_graph = getHistorico(kpi_clients_con, cliente_input, kpi_input, area_input)
                hayData = True    
        elif(area_input == "PCS"):
            lista_clientes = list_clients_pcs
            if(len(kpi_clients_pcs) > 0):    
                historico_graph = getHistorico(kpi_clients_pcs, cliente_input, kpi_input, area_input)
                hayData = True 
        elif(area_input == "PCD"):
            lista_clientes = list_clients_pcd
            if(len(kpi_clients_pcd) > 0):    
                historico_graph = getHistorico(kpi_clients_pcd, cliente_input, kpi_input, area_input)
                hayData = True
        elif(area_input == "Todas"):
            if(len(kpi_clients_cdc) > 0 or len(kpi_clients_con) > 0 or len(kpi_clients_pcs) > 0 or len(kpi_clients_pcd) > 0):
                lista_clientes  = []
                lista_clientes  = unificarClientes(lista_clientes, list_clients_cdc)
                lista_clientes  = unificarClientes(lista_clientes, list_clients_con)
                lista_clientes  = unificarClientes(lista_clientes, list_clients_pcs)
                lista_clientes  = unificarClientes(lista_clientes, kpi_clients_pcd)
                historico_graph = getHistoricoTodaslasAreas(kpi_clients_cdc, kpi_clients_con, kpi_clients_pcs, kpi_clients_pcd, cliente_input, kpi_input, area_input)
                hayData = True

        historico_graph = json.dumps(historico_graph,cls=plotly.utils.PlotlyJSONEncoder)
            
        return render_template('historico.html',
                                cliente_input    = cliente_input,
                                area_input       = area_input,
                                kpi_input        = kpi_input,
                                lista_clientes   = lista_clientes, 
                                list_clients_cdc = list_clients_cdc,
                                list_clients_con = list_clients_con,
                                list_clients_pcs = list_clients_pcs,
                                list_clients_pcd = list_clients_pcd,
                                hayData          = hayData,
                                historico_graph  = historico_graph)
    