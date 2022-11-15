from   CX import app
from   flask import render_template,request
from   CX.logic.functions import OrderClientsRankings, reporteGeneral, tablaReporteGeneral
from   firebase_admin import firestore
import datetime

CON_KPIS, PCS_KPIS, CDC_KPIS, year_cargados = [], [], [], []
year_cargados = []

@app.route('/ranking_general', methods=['GET', 'POST'])
def ranking_general():
    
    #Global variables
    global CON_KPIS, PCS_KPIS, CDC_KPIS, year_cargados
    
    #Local variables
    trimestre, year, area = "Todos",  int(datetime.date.today().year), "Todas"
    
    #Guardar Parametros URL
    year_input      = request.form.get('year_input')
    trimestre_input = request.form.get('trimestre_input')
    area_input      = request.form.get('area_input')
    
    #Validar inputs
    if(trimestre_input != None):
        trimestre = str(trimestre_input)
        
    if(year_input != None):
        year = int(year_input)
        
    if(area_input != None):
        area = int(area_input)
    
    #Conexion con la DB - KPI's CDC/Consultaria/Proceso Comercial Satisfacción from one specific year
    db = firestore.client()
    
    #KPI's USE variables
    CON_KPIS_USE, CDC_KPIS_USE, PCS_KPIS_USE = [], [], []
    
    if request.method == 'GET':
        
        #Get KPI's from one year 
        CON_KPIS = db.collection('Consultoria_KPIS').where('Year','==', year).get()
        CDC_KPIS = db.collection('CDC_KPIS').where('Year','==', year).get()
        PCS_KPIS = db.collection('PCS_KPIS').where('Year','==', year).get()
        
        CON_KPIS_USE = CON_KPIS
        CDC_KPIS_USE = CDC_KPIS
        PCS_KPIS_USE = PCS_KPIS
        
        year_cargados.append(year)
            
    if request.method == 'POST':
       
        if(year in year_cargados):
            #Fitrar por cliente
            if(area_input == "Todas"): 
                for i in CON_KPIS:
                    if(i.to_dict()['Year'] == year):  
                        CON_KPIS_USE.append(i)
                        
                for i in CDC_KPIS:
                    if(i.to_dict()['Year'] == year):  
                        CDC_KPIS_USE.append(i)
                        
                for i in PCS_KPIS:
                    if(i.to_dict()['Year'] == year):  
                        PCS_KPIS_USE.append(i)                                    
                
        else: #ADD NEW DATA 
            
            CON_KPIS_NEW_DATA    = db.collection('Consultoria_KPIS').where('Year','==',year).get()
            CDC_KPIS_NEW_DATA    = db.collection('CDC_KPIS').where('Year','==',year).get()
            PCS_KPIS_NEW_DATA    = db.collection('PCS_KPIS').where('Year','==', year).get()
            year_cargados.append(year)
            
            #Validacion, Add data 
            if(len(CON_KPIS_NEW_DATA) > 0):
                CON_KPIS = CON_KPIS + CON_KPIS_NEW_DATA
                
            if(len(CDC_KPIS_NEW_DATA) > 0):
                CDC_KPIS = CON_KPIS + CDC_KPIS_NEW_DATA
                
            if(len(PCS_KPIS_NEW_DATA) > 0):
                PCS_KPIS = CON_KPIS + PCS_KPIS_NEW_DATA
            
            #Unificar
            if(client_input != "Todos"): 
                #Fitrar por cliente
                for i in CON_KPIS_NEW_DATA:
                    if(i.to_dict()['Cliente'] == client_input):  
                        CON_KPIS_USE.append(i)
                        
                for i in CDC_KPIS_NEW_DATA:
                    if(i.to_dict()['Cliente'] == client_input):  
                        CDC_KPIS_USE.append(i)
                        
                for i in PCS_KPIS_NEW_DATA:
                    if(i.to_dict()['Cliente'] == client_input):  
                        PCS_KPIS_USE.append(i)     
            else:
                CON_KPIS_USE = CON_KPIS_NEW_DATA
                CDC_KPIS_USE = CDC_KPIS_NEW_DATA
                PCS_KPIS_USE = PCS_KPIS_NEW_DATA
       
    # Variables
    #["Esfuerzo", "Satisfacción","Lealtad", "Valor, "General"] 
    c_q1, c_q2, c_q3, c_q4          = reporteGeneral(CON_KPIS_USE) #KPI's Consultoria
    cdc_q1, cdc_q2, cdc_q3, cdc_q4  = reporteGeneral(CDC_KPIS_USE) #KPI's CDC
    pc_q1, pc_q2, pc_q3, pc_q4      = reporteGeneral(PCS_KPIS_USE) #KPI's Proceso comercial satisfacción
    
    print(c_q1)
    print(cdc_q1)
        
    avg_general, avg_lealtad, avg_satisfaccion, avg_esfuerzo, avg_valor = 0, 0, 0, 0, 0
    hayDatos = False
    
    if(trimestre == "Todos"):
        cont = 4
        avg_general_q1, avg_lealtad_q1, avg_satisfaccion_q1, avg_esfuerzo_q1, avg_valor_q1 = tablaReporteGeneral(c_q1, cdc_q1, pc_q1)    
        avg_general_q2, avg_lealtad_q2, avg_satisfaccion_q2, avg_esfuerzo_q2, avg_valor_q2 = tablaReporteGeneral(c_q2, cdc_q2, pc_q2)   
        avg_general_q3, avg_lealtad_q3, avg_satisfaccion_q3, avg_esfuerzo_q3, avg_valor_q3 = tablaReporteGeneral(c_q3, cdc_q3, pc_q3)   
        avg_general_q4, avg_lealtad_q4, avg_satisfaccion_q4, avg_esfuerzo_q4, avg_valor_q4 = tablaReporteGeneral(c_q4, cdc_q4, pc_q4)

        #Trimestres vacios
        if(avg_general_q1 == 0):
            cont = cont - 1
        if(avg_general_q2 == 0):
            cont = cont - 1
        if(avg_general_q3 == 0):
            cont = cont - 1
        if(avg_general_q4 == 0):
            cont = cont - 1
        
        if(cont > 0):
            avg_general = (avg_general_q1 + avg_general_q2 + avg_general_q3 + avg_general_q4) / cont
          
    elif(trimestre == "Q1"):
        avg_general, avg_lealtad, avg_satisfaccion, avg_esfuerzo, avg_valor = tablaReporteGeneral(c_q1, cdc_q1, pc_q1)           
    elif(trimestre == "Q2"):
        avg_general, avg_lealtad, avg_satisfaccion, avg_esfuerzo, avg_valor = tablaReporteGeneral(c_q2, cdc_q2, pc_q2)
    elif(trimestre == "Q3"):
        avg_general, avg_lealtad, avg_satisfaccion, avg_esfuerzo, avg_valor = tablaReporteGeneral(c_q3, cdc_q3, pc_q3) 
    elif(trimestre == "Q4"):
        avg_general, avg_lealtad, avg_satisfaccion, avg_esfuerzo, avg_valor = tablaReporteGeneral(c_q4, cdc_q4, pc_q4) 
        
    if(avg_general != 0):
        hayDatos = True
        
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