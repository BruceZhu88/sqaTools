$(document).ready(function(){
    // Use a "/test" namespace.
    // An application can open a connection on multiple namespaces, and
    // Socket.IO will multiplex all those connections on a single
    // physical channel. If you don't care about multiple channels, you
    // can set the namespace to an empty string.
    namespace = '/test';

    // Connect to the Socket.IO server.
    // The connection URL has the following format:
    //     http[s]://<domain>:<port>[/<namespace>]
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + namespace);

    $("button#popup_button_ok").click(function () {
        $(".window_popup").hide();
        $(".window_popup_info").hide();
        $("body").css("overflow", "auto");
    });
    $('#About').click(function (){
        popup_window_info(["Author: Bruce.Zhu", "Email: bruce.zhu@tymphany.com"]);
    });
    $('#qr_code').click(function (){
        $("#window_popup").css("top",0).css("left",0).show();
        $("#window_popup_setting").hide();
        $("#window_popup_qr").show();

        $("body").css("overflow", "hidden");
    });
    $('#WinSCP').click(function (){
        socket.emit("WinSCP");
    });

    $('.close_popup_setting').click(function (){
        cancel_popup_setting();
    });

});

/********************************
	Popup Window
********************************/
var windowHeight;
var windowWidth;
var popWidth;
var popHeight;
function init(){
   windowHeight=$(window).height();
   windowWidth=$(window).width();
   popHeight=$(".window").height();
   popWidth=$(".window").width();
}
function closeWindow(){
    $(".title img").click(function(){
        $(this).parent().parent().hide("slow");
        });
}
/********************************
	Popup error window
********************************/
function popup_window_info(text){
	$('#error_text').text(text);
	$('#error_text').empty();
	for (i=0; i<text.length; i++){
		$('#error_text').append($( "<span />" ).text(text[i]));
		$('#error_text').append($( "<br />" ));
	}
    $("#window_popup").css("top",0).css("left",0).show();
    $("#window_popup_setting").hide();
    $("#window_popup_info").show();

    $("body").css("overflow", "hidden");
}
/********************************
	Popup setting Window
********************************/
function popup_window_setting(type){
    //init();
    //var popY=(windowHeight-popHeight/2);
    //var popX=(windowWidth-popWidth/2);
    //$("#center").css("top",popY).css("left",popX).slideToggle("slow");
    $("#window_popup").css("top",0).css("left",0).show();
    $("#window_popup_setting_"+type).show();
    //closeWindow();
    $("body").css("overflow", "hidden");
}

function cancel_popup_setting(){
    $(".window_popup").hide();
    $(".window_popup_setting").hide();
    $("body").css("overflow", "auto");
}

/********************************
	Timer
********************************/
var one_second = 1000
  , one_minute = one_second * 60
  , one_hour = one_minute * 60
  , one_day = one_hour * 24
function tick(startTime){
	var now = new Date()
	, elapsed = now - startTime
	, parts = [];

	parts[0] = '' + Math.floor( elapsed / one_hour );
	parts[1] = '' + Math.floor( (elapsed % one_hour) / one_minute );
	parts[2] = '' + Math.floor( ( (elapsed % one_hour) % one_minute ) / one_second );

	parts[0] = (parts[0].length == 1) ? '0' + parts[0] : parts[0];
	parts[1] = (parts[1].length == 1) ? '0' + parts[1] : parts[1];
	parts[2] = (parts[2].length == 1) ? '0' + parts[2] : parts[2];
	var elapsed_time = parts.join(':');
	return elapsed_time
}
/********************************
	Get Current Time
********************************/
function getNowFormatDate() {
    var date = new Date();
    var strTime = {
        "month": (date.getMonth() + 1).toString(),
        "date": date.getDate().toString(),
        "hours": date.getHours().toString(),
        "minutes": date.getMinutes().toString(),
        "seconds": date.getSeconds().toString(),
    };
    for (s in strTime){
        strTime[s] = (strTime[s].length == 1) ? '0' + strTime[s] : strTime[s];
    }
    return date.getFullYear() + "-" + strTime["month"] + "-" + strTime["date"]
            + " " + strTime["hours"] + ":" + strTime["minutes"]
            + ":" + strTime["seconds"];
}

/********************************
	Tooltips
********************************/
 $(function() {
    $( document ).tooltip({
      position: {
        my: "center bottom-20",
        at: "center top",
        using: function( position, feedback ) {
          $( this ).css( position );
          $( "<div>" )
            .addClass( "arrow" )
            .addClass( feedback.vertical )
            .addClass( feedback.horizontal )
            .appendTo( this );
        }
      }
    });
  });