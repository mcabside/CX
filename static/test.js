

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
            clientes_input.push([document.getElementById(-1*i).value,false]);
        }else{ 
            clientes_input.push([document.getElementById(i).value,true]);
        }

    }
    const request = new XMLHttpRequest()
    request.open('POST', `/SaveClients/${JSON.stringify(clientes_input)}`)
    request.send();
    
}