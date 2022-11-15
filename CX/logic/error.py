from   flask import render_template
from   CX import app

#Delete Page
@app.route('/delete', methods=['GET', 'POST'])
def delete():
    return render_template('error.html')

    
    


