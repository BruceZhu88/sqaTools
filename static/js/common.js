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

	$('button#clear_print').click(function(event){
	    $('#EventsLog').empty();
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

/********************************
	Log print for WifiSpeaker
********************************/
function printLog() {
    /*
       e.g. printLog('some text');
            printLog([['/n'], [some text]);
            printLog([['some text', 'red']]);
            printLog([['some text', 'red', 'indent'], [...]]);
    */
    var msg = arguments[0] ? arguments[0] : "Print Nothing!";
    //var color = arguments[1] ? arguments[1] : "white";
	var time = getNowFormatDate();
    //var sn = $('#sn').text();
	var sn = sessionStorage.getItem("sn");
	var $li = $( "<li />" );
	$( "<span />" ).text( time + " ["+ sn +"]").addClass( "time_print" ).appendTo( $li );
	$( "<br />").appendTo( $li );
	$( "<span />" ).text( "* " ).appendTo( $li );
	var content;
	if ($.isArray(msg)) {
        for (i in msg) {
            var $span = $( "<span />" );
            if ($.isArray(msg[i]) == true && msg[i].length >= 2) {
                $span.css("color", msg[i][1]);
                content = msg[i][0];
                if (msg[i].length == 3) {
                    $span.addClass("indent");
                }
            }
            else {
                content = msg[i];
            }

            if (content == '/n') {
                $( "<br />" ).appendTo( $li );
            }
            else {
                $span.text(content).appendTo( $li );
                $( "<br />").appendTo( $li );
            }
        }
	}
	else {
	    content = msg;
        $( "<span />" ).text(content).appendTo( $li );
	}
	//$('#log').append('<br>' + $('<div/>').text('Received #' + msg.count + ': ' + msg.data).html());
    //$li.css("color", color);
	var $log = $('#EventsLog');
	//$log.prepend($li)
	$log.append($li);
	//$("#EventsLog").height();
	$("#EventsLog").scrollTop($("#EventsLog").get(0).scrollHeight);
}

/********************************
	Log print2 for Power Cycle
********************************/
function printLog2() {
    var msg = arguments[0] ? arguments[0] : "Print Nothing!";
    var color = arguments[1] ? arguments[1] : "white";
	var time = getNowFormatDate();

	var $li = $( "<li />" );
	$( "<span />" ).text( time ).addClass( "lowlighted" ).appendTo( $li );
	$( "<span />" ).text( " " ).appendTo( $li );
	$( "<span />" ).text( msg ).appendTo( $li );

    $li.css("color", color);
	var $log = $('#power_cycle-print');
	//$log.prepend($li)
	$log.append($li);
	$("#power_cycle-print").scrollTop($("#power_cycle-print").get(0).scrollHeight);
}

/********************************
	Log print3 for Automate
********************************/
function printLog3() {
    var msg = arguments[0] ? arguments[0] : "Print Nothing!";
    var color = arguments[1] ? arguments[1] : "white";
	var time = getNowFormatDate();

	var $li = $( "<li />" );
	$( "<span />" ).text( time ).addClass( "lowlighted" ).appendTo( $li );
	$( "<span />" ).text( " " ).appendTo( $li );
	$( "<span />" ).text( msg ).appendTo( $li );

    $li.css("color", color);
	var $log = $('#EventsLog');
	//$log.prepend($li)
	$log.append($li);
	$("#EventsLog").scrollTop($("#EventsLog").get(0).scrollHeight);
}