

$(document).ready(function(){
    $("#btn_generate").click(function(event){
        qr_content = $("#qr-content").val();
        if (qr_content == "") {
            alert("Please input your text first!");
            return;
        }
        $("#qrimage").remove();
        $.ajax({url: "QR_Code/generate", type: "POST", dataType: "json", data: {"txt": qr_content}})
            .done(function(data){
                var $img = $( "<img />" );
                $img.attr({"id": "qrimage",
                           "src": "static/images/"+data['pic']});
                $("#code_pic").append($img);
                $("#qr-content").val("");
            });
    });

});


