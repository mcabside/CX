from   flask import request, render_template
from   firebase_admin import firestore
import json
import plotly
from   CX.static.questions.consultoria_questions import Preguntas_esfuerzo,Preguntas_satisfaccion,Preguntas_lealtad,Preguntas_valor
from   CX import app
from   CX.logic.functions import deltaKPI, saveSelectData, speedmeter, promedioQuarter, tablaDinamica, validarParametros, carga_kpi, carga_preguntas, deltaKPI

#Chart Page
@app.route('/config_ranges_pond', methods=['GET', 'POST'])
def config_ranges_pond():
    
    
        
    return render_template('config_ran_pond.html')
    
    


