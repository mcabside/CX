from   flask import render_template
from   CX import app

#Chart Page
@app.route('/config_ranges_pond', methods=['GET', 'POST'])
def config_ranges_pond():
    return render_template('config_ran_pond.html')