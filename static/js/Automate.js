$("#automate").addClass("active");
$(document).ready(function(){
    namespace = '/automate/test';
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + namespace);

    $('#bt_connect').click(function(event){
        socket.emit("automate_cmd", {"cmd":"bt_connect,Beoplay M3_28155630"});
    });
    $('#bt_disconnect').click(function(event){
        socket.emit("automate_cmd", {"cmd":"bt_disconnect,Beoplay M3_28155630"});
    });
});