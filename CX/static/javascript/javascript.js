function func(index) {
    if(document.getElementById(index).value === "")
        document.getElementById(-1*index).disabled = false;
    else
        document.getElementById(-1*index).disabled = true;
}

function submitfunc(list){
    const clientes_input = []
    for (var i = 1; i <= list.length; i++){
        if(document.getElementById(i).value === ""){
            clientes_input.push([list[i-1],document.getElementById(-1*i).value,"False"]);
        }else
            clientes_input.push([list[i-1],document.getElementById(i).value,"True"]);
    }
    var data = []
    for (i = 0; i < clientes_input.length; i++) {
        var dict = {}
        dict["Excel"] = clientes_input[i][0]
        dict["Input"] = clientes_input[i][1]
        dict["Es_nuevo"] = clientes_input[i][2]
        data[i] = dict   
    }
    aux = "{"
    json_data=aux.concat(JSON.stringify(data).slice(1, -1),"}")
    $.ajax({
        url: '/SaveClients',
        type: 'POST',
        //url: "{{ url_for('app.SaveClients')}}",
        contentType: "application/json",
        data: JSON.stringify(data),
        dataType: "json",
        success: function(response) {
            console.log("success",response)
            goHome();
          },
        error: function(err) {
            console.log("error",err);
        }
        
    });
    
}

function goHome(){
    window.location.href="http://127.0.0.1:5000/"
}

function changeSelect(){
    var cliente_input = document.getElementById("cliente_input").value
    if(cliente_input != "Todos")
        document.getElementById("kpi").disabled = true;
    else
        document.getElementById("kpi").disabled = false;
}

function validarkpipond(){
    var min_nps = parseFloat(document.getElementById("min_nps").value)
    var max_nps = parseFloat(document.getElementById("max_nps").value)
    var ponde_nps = parseInt(document.getElementById("ponde_nps").value)

    var min_csat = parseFloat(document.getElementById("min_csat").value)
    var max_csat = parseFloat(document.getElementById("max_csat").value)
    var ponde_csat = parseInt(document.getElementById("ponde_csat").value)

    var min_va = parseFloat(document.getElementById("min_va").value)
    var max_va = parseFloat(document.getElementById("max_va").value)
    var ponde_va = parseInt(document.getElementById("ponde_va").value)

    var min_ces = parseFloat(document.getElementById("min_ces").value)
    var max_ces = parseFloat(document.getElementById("max_ces").value)
    var ponde_ces = parseInt(document.getElementById("ponde_ces").value)
    
    var dateInput = document.getElementById('date_kpi');

    if((ponde_nps + ponde_csat + ponde_va +  ponde_ces != 100) || (max_ces<=min_ces) || (max_va<=min_va) || 
    (max_csat<=min_csat) || (max_nps<=min_nps) || (!dateInput.value)){
        document.getElementById("boton_kpis").disabled = true;
    }else{
        document.getElementById("boton_kpis").disabled = false;
    }
}

function submitfunckpi(){

    var min_nps = parseFloat(document.getElementById("min_nps").value)
    var max_nps = parseFloat(document.getElementById("max_nps").value)
    var ponde_nps = parseInt(document.getElementById("ponde_nps").value)

    var min_csat = parseFloat(document.getElementById("min_csat").value)
    var max_csat = parseFloat(document.getElementById("max_csat").value)
    var ponde_csat = parseInt(document.getElementById("ponde_csat").value)

    var min_va = parseFloat(document.getElementById("min_va").value)
    var max_va = parseFloat(document.getElementById("max_va").value)
    var ponde_va = parseInt(document.getElementById("ponde_va").value)

    var min_ces = parseFloat(document.getElementById("min_ces").value)
    var max_ces = parseFloat(document.getElementById("max_ces").value)
    var ponde_ces = parseInt(document.getElementById("ponde_ces").value)
    
    var dateInput = document.getElementById('date_kpi').value;

    var data = []
    
    var dict = {}
    dict["min_nps"] = min_nps
    dict["max_nps"] = max_nps
    dict["ponde_nps"] = ponde_nps

    dict["min_csat"] = min_csat
    dict["max_csat"] = max_csat
    dict["ponde_csat"] = ponde_csat

    dict["min_va"] = min_va
    dict["max_va"] = max_va
    dict["ponde_va"] = ponde_va

    dict["min_ces"] = min_ces
    dict["max_ces"] = max_ces
    dict["ponde_ces"] = ponde_ces

    dict["dateInput"] = dateInput
    data[0] = dict   
    
    aux = "{"
    json_data=aux.concat(JSON.stringify(data).slice(1, -1),"}")
    $.ajax({
        url: '/SaveKPISPercents',
        type: 'POST',
        //url: "{{ url_for('app.SaveClients')}}",
        contentType: "application/json",
        data: JSON.stringify(data),
        dataType: "json",
        success: function(response) {
            console.log("success",response)
            goHome();
          },
          error: function(err) {
            console.log("error",err);
          }
        
    });
    
}

//Show Loader
function hidden_func() {
    document.getElementById("loading").style.display = 'block';
    document.getElementById("div_form").style.display = 'none';
}