$("#power_cycle").addClass("active");
$(document).ready(function(){
    var ticker;
    namespace = '/power_cycle/test';
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + namespace);

    socket.emit("scan_port");

    socket.on('print_log', function(msg) {
        printLog(msg.msg, msg.color);
    });

    socket.on('add_port', function(msg) {
        var $select = $("#select-port");
        $option = $("<option />");
        $option.css("margin-bottom","5px");
        $option.attr("title", msg.data);
        $option.text(msg.data).appendTo($select);
    });
    socket.on('del_port', function(msg) {
        $("#select-port option").each(function(i){
            if ($(this).text() == msg.data){
                $(this).remove();
            }
        });
    });

    socket.on('port_status', function(msg) {
        if (msg.color == 'red'){
            $("#btn-open_port").text("Open");
            $("#btn-open_port").attr("disabled", true);
            $("#btn-open_port").css("background-color", "gray");
            $('#btn_options').attr("disabled", true);
            $('#btn_options').css("background", "gray");
        }
        $("#port_status").text(msg.msg);
        $("#port_status").css("color", msg.color);
    });

    socket.on('start_auto_power_cycle', function(msg) {
        for (name in msg){
            $('#'+name).text(msg[name]);
        }
    });
    socket.on('stop_auto_power_cycle', function(msg) {
        $('#btn_stop_auto_power_cycle').text("Stopping");
        $('#btn_stop_auto_power_cycle').attr("disabled", true);
        $('#btn_stop_auto_power_cycle').css("background", "gray");
    });
    socket.on('stop_confirm', function(msg) {
        stop_confirm(ticker);
    });

    $('#btn_stop_auto_power_cycle').click(function(event){
        $.ajax({url:'stop_auto_power_cycle',type:'POST',dataType:'json', data:{"power_cycle": "stop"}});
	    //socket.emit("stop_auto_power_cycle");
	});


    $('#clear_power_cycle_log').click(function(event){
	    $('#power_cycle-print').empty();
	});

	$('#btn_options').click(function(event) {
		popup_window_setting("power_cycle");
		$.ajax({url:'power_cycle_options', type:'GET', dataType:'json'})
		.done(function(data){
		    var relay_type = data["relay_type"];
			for (name in data) {
				$('#set_'+name).val(data[name]);
			}
			if (relay_type == "AC"){$(".button_type").hide();}
            else{$(".button_type").show();}
		});
	});

    $("#set_relay_type").change(function(){
	    var relay_type = $(this).val();
	    if (relay_type == "AC"){$(".button_type").hide();}
        else{$(".button_type").show();}
	});

    $("#select-port").click(function(event) {
        var selectText = $("#select-port").find("option:selected").text();
        if (selectText == ""){return;}
        $("#btn-open_port").attr("disabled", false);
        $("#btn-open_port").css("background-color", "black");
    });

    $('#btn-open_port').click(function(event) {
        $(".power_cycle_setting_show").text("");
        if ($("#btn-open_port").text() == "Open"){
            var selectText = $("#select-port").find("option:selected").text();
            if (selectText == ""){return;}
            $("#btn-open_port").text("Close");
            $("#btn-open_port").css("background-color", "red");
            $('#btn_options').attr("disabled", false);
            $('#btn_options').css("background", "black");
            socket.emit("open_port",
                        {"port_info": selectText,
                         "baud_rate": $("#baud_rate").find("option:selected").text(),
                         "parity": $("#parity").find("option:selected").text(),
                         "data_bit": $("#data_bit").find("option:selected").text(),
                         "stop_bit": $("#stop_bit").find("option:selected").text(),}
            );

        }
        else{
            socket.emit("close_port");
            $("#btn-open_port").text("Open");
            $("#btn-open_port").css("background-color", "black");
            $('#btn_options').attr("disabled", true);
            $('#btn_options').css("background", "gray");
        }
    });

    $('#send_msg').click(function(event) {
        socket.emit("send_ser_msg", {"msg": $('#port_message').val()});
        $('#port_message').val("");
    });

    $("#power-cycle-setting-form").validate({
        rules: {
            set_total_count: {required:true,digits:true},
            set_time_on: {required:true,digits:true},
            set_time_off: {required:true,digits:true},
            set_button_press_on: {required:true},
            set_button_press_off: {required:true},
        },
        messages: {},
        // specifying a submitHandler prevents the default submit, good for the demo
        submitHandler: function(data) {
            if (RangeValidate($('#set_button_press_on').val()) == false) {
                $('#set_button_press_on').focus();
                alert("Value range of random delay[button press on] is illegal!\nExample: 0.9 or 1 or 0.8-1.5");
                return;
            }
            if (RangeValidate($('#set_button_press_off').val()) == false) {
                $('#set_button_press_off').focus();
                alert("Value range of random delay[button press off] is illegal!\nExample: 0.9 or 1 or 0.8-1.5");
                return;
            }
            $(".window_popup").hide();
            socket.emit('auto_power_cycle',
                        {'total_count': $('#set_total_count').val(),
                        'time_on': $('#set_time_on').val(),
                        'time_off': $('#set_time_off').val(),
                        'relay_type': $('#set_relay_type').val(),
                        'port_address': $('#set_port_address').val(),
                        'button_press_on': $('#set_button_press_on').val(),
                        'button_press_off': $('#set_button_press_off').val(),
            });
            $('#btn_stop_auto_power_cycle').attr("disabled", false);
            $('#btn_stop_auto_power_cycle').css("background", "black");
            $('#btn_options').attr("disabled", true);
            $('#btn_options').css("background", "gray");
            $('#port_status').text('Running');
            $("#port_status").css({"color":"white", "background":"green"});
            $('#power_cycle_start_time').text(getNowFormatDate());
            start_time = (new Date).getTime();
            ticker = self.setInterval(function() {
                    $('#power_cycle_elapsed_time').text(tick(start_time));
            }, 1000);
            return false;
        },
        // set this class to error-labels to indicate valid fields
        success: function(label) {
            // set &nbsp; as text for IE
            label.html("&nbsp;").addClass("checked");
        },
        highlight: function(element, errorClass) {
            $(element).parent().next().find("." + errorClass).removeClass("checked");
        }
    });
});

function stop_confirm(ticker) {
    $('#port_status').text('Ready');
    $("#port_status").css({"color":"white", "background":"black"});
    $('#btn_options').attr("disabled", false);
    $('#btn_options').css("background", "black");
    $('#btn_stop_auto_power_cycle').text("Stop");
    $('#btn_stop_auto_power_cycle').attr("disabled", true);
    $('#btn_stop_auto_power_cycle').css("background", "gray");
    ticker = window.clearInterval(ticker);
}
/*Remove blank*/
function Trim(str, is_global){
    var result;
    result = str.replace(/(^\s+)|(\s+$)/g, "");
    if (is_global.toLowerCase()=="g") {
        result = result.replace(/\s/g, "");
     }
    return result;
}

function RangeValidate(value) {
    value = Trim(value, "g");
    if (/(\d+)-(\d+)/.test(value) == true){
        nums = value.split("-");
        if (nums.length == 2){
            for (var i=0; i<nums.length; i++){
                if ( isNaN(Number(nums[i])) ){
                    return false;
                }
            }
            return true;
        }
    }
    else if ( !isNaN(value)) {
        return true;
    }
    return false;
}
/********************************
	Log print
********************************/
function printLog() {
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

