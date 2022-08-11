console.log("esta")


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