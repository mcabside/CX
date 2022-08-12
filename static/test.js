

function func(index) {
    if(document.getElementById(index).checked){
        document.getElementById(-1*index).disabled = true;
    }else{
        document.getElementById(-1*index).disabled = false;
    }
}

function func2(index) {
    if(document.getElementById(index).value === ""){
        document.getElementById(-1*index).disabled = false;
    }else{
        document.getElementById(-1*index).disabled = true;
    }
}

function submitfunc(list){
    const clientes_input = []
    for (var i = 1; i <= list.length; i++){

        if(document.getElementById(i).value === ""){
            clientes_input.push([list[i-1],document.getElementById(-1*i).value,"False"]);
        }else{ 
            clientes_input.push([list[i-1],document.getElementById(i).value,"True"]);
        }

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
    console.log(aux.concat(JSON.stringify(data).slice(1, -1),"}"))
    json_data=aux.concat(JSON.stringify(data).slice(1, -1),"}")
    console.log(data)
    $.ajax({
        url: '/SaveClients',
        type: 'POST',
        //url: "{{ url_for('app.SaveClients')}}",
        contentType: "application/json",
        data: JSON.stringify(data),
        dataType: "json",
        success: function(response) {
            console.log("success")
            console.log(response);
            goHome();
            
            // The data has now been successfully transferred.
            
            // document.TrialQuestions.submit();
          },
          error: function(err) {
            console.log("error")
            console.log(err);
          }
        
    });
    
}

function goHome(){
    window.location.href="http://127.0.0.1:5000/"

}
