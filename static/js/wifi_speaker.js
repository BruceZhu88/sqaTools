$("#wifi_speaker").addClass("active");
$().ready(function() {
    $("#commentForm").validate();
});

$(document).ready(function(){
    var ticker;
    /*
	$.ajax({url:'ase_ota_status',type:'GET',dataType:'json'})
	.done(function(data){
		if (data["aseOtaUpdate"]=="1") {
			var startDate = new Date()
			var int=self.setInterval(function(){
				var elapsed_time = tick(startDate)
				$.ajax({url:'ase_ota_status_refresh', type:'GET', dataType:'json'})
				.done(function(data){
					for (d in data){
						$("td#"+d).text(data[d]);
					}
				});
			},5000)
		}
		else{
			int=window.clearInterval(int);
			//$('div#div-left').show();
			//$('div#start_ota').hide();
		}
	});
	*/
	/*		$('a#'+data["page"]).css({"font-size":"35px", "text-decoration":"underline"});
		$('a#'+data["page"]+'>span').css({
    	"content": "url('{{url_for('static', filename='images/circledDot16x16.png')}}')",
		"padding-right": "4px",
		"position": "relative",
		"top": "4px",
		"left": "-0px",
		});
	.fail(function(){console.log("fail")})
	.always(function(){console.log("complete")});
	*/

    namespace = '/wifi_speaker/test';
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + namespace);

    scan_devices(socket);

    socket.on('print_msg', function(msg) {
        printLog([[msg.data, msg.color]]);
    });

    socket.on('get_scan_devices', function(msg) {
        var $select = $("#select-device");
        $option = $("<option />");
        $option.css("margin-bottom","5px");
        $option.text(msg.data).appendTo($select);
    });

    socket.on('stop_scan_devices', function(msg) {
        $('button#scan-devices').text("Scan Devices");
        //$('button#scan-devices:hover').css("cursor", "pointer");
        $('button#scan-devices').attr("disabled", false)
        $('button#scan-devices').css("background-color", "black")
    });

    socket.on('refresh_update_status', function(msg) {
        for (name in msg){
            $('#'+name).text(msg[name]);
        }
    });

    socket.on('stop_ase_auto_update', function() {
        $('#ota_status h1').text('Over');
        ticker = window.clearInterval(ticker);
    });

    socket.on('stop_auto_setup_wifi', function() {
        $('#wifi_setup_status h1').text('Over');
        ticker = window.clearInterval(ticker);
    });

	$('button#ota-auto-update').click(function(event) {
		popup_window_setting("ota");
		$.ajax({url:'get_ota_setting', type:'GET', dataType:'json'})
		.done(function(data){
			for (name in data) {
				$('#set_'+name).val(data[name]);
			}
		});
	});

    socket.on('wifi_setup_pass_ratio', function(msg) {
        $('#pass_wifi_setup').text(msg.data);
    });

    socket.on('ota_check_over', function(msg) {
        $('#one_tap_ota').attr("disabled", false);
        //$('#one_tap_ota').text("OTA")
        $('#one_tap_ota').css("background-color", "black");
        printLog("Update over! Please check device version!");
        $('button#refresh').click();
    });

    $('button#one_tap_ota').click(function(event){
        popup_window_setting('one_tap_ota');
    });

    $('button#start_one_tap_ota').click(function(event){
        var file_path = $('#set_ota_path').val();
        if ( file_path == ""){
            $('#set_ota_path').focus();
            //popup_window_info(["OTA path is required!"]);
            return
        }
        cancel_popup_setting();
        printLog("Uploading file...");
        $('button#one_tap_ota').attr("disabled", true);
        $("button#one_tap_ota").css("background-color", "grey");
	    $.ajax({url:'one_tap_ota', type:'post', dataType:'json',
	            data:{"ip":sessionStorage.getItem("ip"), "file_path": file_path,}})
	    .done(function(data){
            if (data['status'] == 200){
                printLog("Upload file successful!");
                printLog("Starting burn...");
                //$('#one_tap_ota').text("Updating...")
                //socket.emit("ota_status_check", {"ip": sessionStorage.getItem("ip")});
                //return
            }
            else if (data['status'] == "file error"){
                $('#set_ota_path').focus();
                printLog([["OTA file does not exist! Please check OTA path!", "red"]]);
                //popup_window_info(["OTA file does not exist! Please check OTA path!"]);
            }
            else if (data['status'] == "device disconnect"){
                printLog([["Your device seems disconnected!", "red"]]);
                //popup_window_info(["Your device seems disconnected!"]);
            }
            else {
                printLog([["Upload ASE OTA file failed!", "red"]]);
            }
            $('button#one_tap_ota').attr("disabled", false);
            $("button#one_tap_ota").css("background-color", "black");
	    })
	});

	$('button#auto-setup-wifi').click(function(event) {
		popup_window_setting("wifisetup");
		$.ajax({url:'wifi_setup_setting', type:'GET', dataType:'json'})
		.done(function(data){
		    var dhcp_mode = data["dhcp"];
			for (name in data) {
			    if (name=="total_times"){
			        $('#set_total_times_wifi_setup').val(data[name]);
			    }
				$('#set_'+name).val(data[name]);
			}
			if (dhcp_mode == "True"){$(".dhcp_false").hide();}
            else{$(".dhcp_false").show();}
		});
	});

    $('button#ase_log').click(function(event) {
		popup_window_setting("ase_log");
	});

	$('button#go-ip').click(function(event){
		var ip = $("input[name='input-ip']").val();
		if (isValidIP(ip)) {
		    get_info({"text":ip});
			$('div#device-scan').hide();
			$('#info-show').show();
			$("div#log").show();
			$("p#ip-error").hide();
			var text = {"text":ip};
		}
		else{
			$("p#ip-error").show();
		}
	});

	$('button#clear_print').click(function(event){
	    $('#EventsLog').empty();
	});

	$('button#back').click(function(event){
	    scan_devices(socket);
	});

	$("#set_dhcp").change(function(){
	    var dhcp_mode = $(this).val();
	    if (dhcp_mode == "True"){$(".dhcp_false").hide();}
	    else{$(".dhcp_false").show();}
	});

	$("#bt_reconnect_mode").change(function(){
	    var bt_mode = $(this).val();
	    printLog("Change bluetooth reconnect mode to " + bt_mode);
		text = {"ip": sessionStorage.getItem("ip"),"mode": bt_mode};
		$.ajax({url:'ase_set_bt_reconnect_mode',type:'POST',dataType:'json', data:text});
	});

	$('button#factory_reset').click(function(event){
		var text = {"ip":sessionStorage.getItem("ip")};
		$.ajax({url:'ase_reset', type:'POST',dataType:'json', data:text});
		button_back();
	});

	$('button#go_web_setting').click(function(event){
	    //window.location.href='http://'+sessionStorage.getItem("ip")
	    window.open('http://'+sessionStorage.getItem("ip"))
	});

    $('input#bt_open').click(function(event){
        if ($(this).prop('checked') == true) {
            printLog("Enable BT always open");
            $('.bt_pair').hide();
            socket.emit("bt_open", {"enable": true});
        }
        else {
            printLog("Disable BT always open");
            $('.bt_pair').show();
            socket.emit("bt_open", {"enable": false});
        }
	});

    $('button#bt_pair').click(function(event){
        printLog("Trigger BT pairing");
	    socket.emit("bt_pair", {"cmd": "pair"});
	});

    $('button#bt_cancel_pair').click(function(event){
        printLog("Cancel BT pairing");
	    socket.emit("bt_pair", {"cmd": "cancel"});
	});

    $('button#get_current_source').click(function(event){
        printLog("Refresh current source");
        $.ajax({url:'get_current_source',type:'GET', dataType:'json'})
		.done(function(data){
		    $('td#current_source').text(data['source'])
		});
	});

    socket.on('check_standby', function(msg) {
        if (msg['status'] == 'Standby') {
            printLog("Your product enter Standby! Elapsed Time: "+msg['elapsed_time']);
        }
        else {
            printLog('Timeout to detect Standby');
        }
        $('#detect_standby').attr("disabled", false);
        $('#detect_standby').text("Detect Standby")
        $('#detect_standby').css("background-color", "black");
    });

    $('button#detect_standby').click(function(event){
        printLog('Start detect Standby');
        socket.emit('detect_standby');
        $('#detect_standby').attr("disabled", true);
        $('#detect_standby').text("Detecting");
        $('#detect_standby').css("background-color", "gray");
	});

	$('button#refresh').click(function(event){
	    printLog('Refresh info list');
		$(this).attr("disabled", true);
		$(this).css("background-color", "gray");
		$(this).text("Refreshing");
		get_info({"text":sessionStorage.getItem("ip")});
	});

	$('button#exit_ase_ota').click(function(event){
		$.ajax({url:'exit_ase_ota',type:'POST',dataType:'json'})
		.done(function(){console.log("done")});
		int=window.clearInterval(int);
	});

	$('button#log_submit_server').click(function(event){
	    printLog("Start submit log files..");
		$(this).attr("disabled", true);
		$(this).css("background-color", "gray");
		$(this).text("Submitting");
		cancel_popup_setting();
		var ip = {"ip":sessionStorage.getItem("ip")};
		$.ajax({url:'log_submit_server',type:'POST', dataType:'json', data:ip})
		.done(function(data){
		    if (data["status"]==200){
                printLog("Log files submitted successfully!");
		    }
		    else{
		        printLog([["Log files submitted failed!", "red"]]);
		    }
		})
		.always(function(){
            $("button#log_submit_server").attr("disabled", false);
            $("button#log_submit_server").css("background-color", "black");
            $("button#log_submit_server").text("Submit Log (Server)");
		});
	});

    $('button#log_download_local').click(function(event) {
        printLog("Start zip and download log files..");
		$(this).attr("disabled", true);
		$(this).css("background-color", "gray");
		$(this).text("Downloading log");
		cancel_popup_setting();
		var ip = {"ip":sessionStorage.getItem("ip")};
		$.ajax({url:'log_download_local',type:'POST', dataType:'json', data:ip})
		.done(function(data){
		    if (data["path"]!=""){
                printLog([["Download log files successfully!"], [data["log_path"], "blue"]]);
		    }
		    else{
		        printLog([["Download log files failed!", "red"]]);
		    }
		})
		.always(function(){
            $("button#log_download_local").attr("disabled", false);
            $("button#log_download_local").css("background-color", "black");
            $("button#log_download_local").text("Download Log (Local)");
		});
	});

    $('button#log_get').click(function(event) {
        printLog("Start get log files..");
		$(this).attr("disabled", true);
		$(this).css("background-color", "gray");
		$(this).text("Getting log");
		cancel_popup_setting();
		var ip = {"ip":sessionStorage.getItem("ip")};
		$.ajax({url:'log_get',type:'POST', dataType:'json', data:ip})
		.done(function(data){
		    if (data["log_path"]!=""){
                printLog([["Get log files successfully!"], [data["log_path"], "blue"]]);
		    }
		    else{
		        printLog([["Get log files failed!", "red"]]);
		    }
		})
		.always(function(){
            $("button#log_get").attr("disabled", false);
            $("button#log_get").css("background-color", "black");
            $("button#log_get").text("Get Log file (log-nSDK)");
		});
	});

    $('button#log_clear').click(function(event) {
	    printLog("Start clear log files..");
		$(this).attr("disabled", true);
		$(this).css("background-color", "gray");
		$(this).text("Clearing");
		cancel_popup_setting();
		var ip = {"ip":sessionStorage.getItem("ip")};
		$.ajax({url:'log_clear',type:'POST', dataType:'json', data:ip})
		.done(function(data){
		    if (data["status"]==200){
                printLog("Clear log files successfully!");
		    }
		    else{
		        printLog([["Clear log files failed!", "red"]]);
		    }
		})
		.always(function(){
            $("button#log_clear").attr("disabled", false);
            $("button#log_clear").css("background-color", "black");
            $("button#log_clear").text("Clear Log files");
		});
	});

	$('button#unblock').click(function(event){
		$(this).attr("disabled", true);
		$(this).css("background-color", "gray");
		$(this).text("Unblocking");
		var text = {"ip":sessionStorage.getItem("ip")};
		$.ajax({url: 'unblock',type:'POST',dataType:'json',data: text})
		.done(function(data){
			if (data["status"]=="successful"){
			    printLog("Unblock successfully!");
			    popup_window_info(["Unblock successfully!"]);
			}
			else{
			    printLog([["Unblock Failed!", "red"]]);
			    popup_window_info(["Unblock failed!"]);
			}
		})
		.fail(function(){console.log("fail");})
		.always(function(){
			$('button#unblock').attr("disabled", false);
			$('button#unblock').css("background-color", "black");
			$('button#unblock').text("Unblock");
		});
	});

	$('button#scan-devices').click(function(event){
        scan_devices(socket);
	});

    //$('form#ota-auto-update-setting').submit(function(event) {})
    //$('form#wifi-setup-setting').submit(function(event) {})
	$("#ota-auto-update-setting-form").validate({
			rules: {
				set_total_times: {required:true,digits:true},
				set_low_version: "required",
				set_low_version_path: "required",
				set_high_version: "required",
				set_high_version_path: "required",
			},
			messages: {
				set_low_version: "Enter low version",
			},
			// specifying a submitHandler prevents the default submit, good for the demo
			submitHandler: function() {
			    text = {'low_version_path': $('#set_low_version_path').val(),
                        'high_version_path': $('#set_high_version_path').val()}
			    $.ajax({url:'check_ota_path',type:'POST',dataType:'json',data:text})
			        .done(function(data){
                        if (data['status'] == 'error') {
                            alert("Please check your "+data['name']+": "+text[data['name']]);
                            $('#set_'+data['name']).focus();
                        }
                        else{
                            $(".window_popup").hide();
                            $("#info-show").hide();
                            $("div#ota_status").show();
                            socket.emit('ota_auto_update',
                                        {'total_times': $('#set_total_times').val(),
                                        'ip': sessionStorage.getItem("ip"),
                                        'low_version': $('#set_low_version').val(),
                                        'low_version_path': $('#set_low_version_path').val(),
                                        'high_version': $('#set_high_version').val(),
                                        'high_version_path': $('#set_high_version_path').val(),
                            });
                            $('#start_time').text(getNowFormatDate());
                            $('#total_times').text($('#set_total_times').val());
                            $('#high_version').text($('#set_high_version').val());
                            $('#low_version').text($('#set_low_version').val());
                            start_time = (new Date).getTime();
                            ticker = self.setInterval(function() {
                                    $('#elapsed_time').text(tick(start_time));
                            }, 1000);
                        }
			     });
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

    $.mockjax({
        url: "set_static_ip.action",
        response: function(settings) {
            ip = settings.data.set_static_ip;
            this.responseText = "true";
            if (isValidIP(ip) == false) {this.responseText = "false";}
        },
        responseTime: 500
	});

    $.mockjax({
        url: "set_gateway.action",
        response: function(settings) {
            ip = settings.data.set_gateway;
            this.responseText = "true";
            if (isValidIP(ip) == false) {this.responseText = "false";}
        },
        responseTime: 500
	});

	$.mockjax({
        url: "set_netmask.action",
        response: function(settings) {
            ip = settings.data.set_netmask;
            this.responseText = "true";
            if (isValidIP(ip) == false) {this.responseText = "false";}
        },
        responseTime: 500
	});
    $("#wifi-setup-setting-form").validate({
            rules: {
                set_total_times_wifi_setup: {required:true,digits:true},
                set_time_reset: {required:true,digits:true},
                set_ssid: "required",
                //set_password: "required",
                set_static_ip: {required: true, remote: "set_static_ip.action"},
                set_gateway: {required: true, remote: "set_gateway.action"},
                set_netmask: {required: true, remote: "set_netmask.action"},
            },
            messages: {
                set_static_ip:{
                    required: "Please enter a valid ip address",
                    remote: jQuery.validator.format("Invalid ip address")
                },
                set_gateway:{
                    required: "Please enter a valid gateway address",
                    remote: jQuery.validator.format("Invalid gateway address")
                    //remote: jQuery.validator.format("{0} is invalid")
                },
                set_netmask:{
                    required: "Please enter a valid netmask address",
                    remote: jQuery.validator.format("Invalid netmask address")
                },

            },
            // specifying a submitHandler prevents the default submit, good for the demo
            submitHandler: function() {
                $(".window_popup").hide();
                $("#info-show").hide();
                $("div#wifi_setup_status").show();

                socket.emit('auto_setup_wifi',
                            {'total_times': $('#set_total_times_wifi_setup').val(),
                            'time_reset': $('#set_time_reset').val(),
                            'ssid': $('#set_ssid').val(),
                            'password': $('#set_password').val(),
                            'dhcp': $('#set_dhcp').val(),
                            'static_ip': $('#set_static_ip').val(),
                            'gateway': $('#set_gateway').val(),
                            'netmask': $('#set_netmask').val(),
                });

                $('#start_time_wifi_setup').text(getNowFormatDate());
                $('#total_times_wifi_setup').text($('#set_total_times_wifi_setup').val());
                $('#time_reset').text($('#set_time_reset').val());
                $('#ssid').text($('#set_ssid').val());
                $('#dhcp').text($('#set_dhcp').val());
                start_time = (new Date).getTime();
                ticker = self.setInterval(function() {
                        $('#elapsed_time_wifi_setup').text(tick(start_time));
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

$(document).on('dblclick', '.bt_devices', function() {
    var bt_name = $(this).text();
    if (bt_name.indexOf("connected") != -1){
        bt_name = bt_name.replace(" [connected]", "");
    }
    var value = {"bt_mac": $(this).attr("id"),
                 "ip": sessionStorage.getItem("ip")};
    printLog("Removing bluetooth [" + bt_name + "]");
    $.ajax({url:'bt_remove', type:'POST', dataType:'json', data:value})
    .done(function(){
        printLog("Removed bluetooth [" + bt_name + "] successfully!");
        get_info({"text":value["ip"]});
    });
});

/*
function submitSetting(){
	var t = $('#ota-auto-update-setting').serializeArray();
	var values = {};
     for( x in params ){
        values[params[x].name] = params[x].value;
     }
	$.each(t, function() {
	  values[this.name] = this.value;
	});
	values["ip"] = sessionStorage.getItem("ip");
	var setting_values = JSON.stringify(values);
	$.ajax({
		url:'/otaAutoUpdate',
		type:'POST',
		dataType: 'json',
		data: values,
	})
	.done(function(data){
		console.log("done");
			console.log(xhr);
            var json=$.parseJSON(response);
	});
}

function nav_selected(id) {
    //$('#'+id).attr("class","active");
    $("#" + id).addClass("active");
    $("#" + id).parent("ul").children("li").not("#" + id).removeClass("active");
}
*/

function button_back(){
    $('div#device-scan').show();
    $('#info-show').hide();
    $('#select-device').empty();
    $('div#log').hide();
}

function scan_devices(socket){
    $('button#scan-devices').text("Scanning ...");
    //$('button#scan-devices:hover').css("cursor", "wait");
    $('#select-device').empty();
    $('button#scan-devices').attr("disabled", true);
    $('button#scan-devices').css("background-color", "gray");
    socket.emit("scan_devices");
/*    $.ajax({
        url: 'scan_devices',
        type: 'GET',
        dataType:'json',
    })
    .done(function(data){
        for (var text in data){
            if (text=="error"){
                var text=new Array()
                text[0] = "Please install Bonjour and ensure service is running!"
                popup_window_info(text);
            }
            else{
                var $select = $("#select-device");
                $option = $("<option />");
                $option.css("margin-bottom","5px");
                $option.text(data[text]).appendTo($select);
            }
        }

    })
    .fail(function(){console.log("error");})
    .always(function(){
        $('button#scan-devices').text("Scan Devices");
        $('button#scan-devices').attr("disabled", false)
        $('button#scan-devices').css("background-color", "black")
    });
*/
}

function SelectDevice() {
    var selectText = $("#select-device").find("option:selected").text();
    if (selectText == ""){return;}
  	get_info({"text": selectText});
	$('div#device-scan').hide();
	$('#info-show').show();
	$("div#log").show();
    //$.post("/get_info", data, function(){
    //	alert("success")
    //});
}

function get_info(ip){
    $.ajax({
    	url: 'get_info',
       	type: 'GET',
       	dataType: 'json',
       	data: ip,})
    .done(function(data){
        //console.log(response);
        for (d in data){
            if (d=="error"){
                var text=new Array()
                text[0] = "Sorry, cannot connect to "+data["ip"]+"!";
                text[1] = "Maybe you need to check your device!";
                printLog([[text[0], "red"]]);
                popup_window_info(text);
                return;
            }
            else if (d=="bt_reconnect"){
                $("#bt_reconnect_mode").val(data[d]);
            }
            else if (d=="deviceName") {
                $('#device_name_input').val(data[d]);
            }
            else if (d=="bt_open") {
                $('#bt_open').attr('checked', data[d]);
                if (data[d]==true) {
                    $('.bt_pair').hide();
                }
                else {
                    $('.bt_pair').show();
                }

            }
            else if (d=="bt_devices"){
                $('#bt_paired').empty();
                var devices = data[d]["rows"]
                if (devices.length==0) {
                    $li = $( "<li />");
                    $li.text("<None>");
                    $('#bt_paired').append($li);
                    $li.attr("disabled", true);
                }
                else{
                    for (var i in devices){
                        bt = devices[i];
                        if (bt[2] != ''){
                            bt_name = bt[0] + ' [' + bt[2] + ']';
                        }
                        else{
                            bt_name = bt[0];
                        }
                        bt_mac = bt[1];
                        $li = $( "<li />");
                        $li.text(bt_name);
                        $li.addClass("bt_devices");
                        $li.attr({"id":bt_mac,"style":"border-bottom-color: #222222;border-bottom-width: 1px;border-bottom-style: solid;"});
                        //$li.attr({"id":i,"style":"list-style-type:none"});
                        $('#bt_paired').append($li);
                    }
                }

            }
            else{
                $('td#'+d).text(data[d]);
            }
        }
        sessionStorage.setItem("ip",data["ip"]);
        $('button#refresh').attr("disabled", false);
        $('button#refresh').css("background-color", "black");
        $('button#refresh').text("Refresh");
    })
    .always(function(){
        $('button#refresh').attr("disabled", false);
        $('button#refresh').css("background-color", "black");
        $('button#refresh').text("Refresh");
    });
}
function change_device_name(name){
    printLog("Change product name to " + name);
    text = {"name":name, "ip":sessionStorage.getItem("ip")};
    $.ajax({url:'change_product_name', type:'POST', dataType:'json', data:text})
    .done(function(){
        get_info({"text":text["ip"]});
    });
}
/********************************
	Log print
********************************/
function printLog() {
    var msg = arguments[0] ? arguments[0] : "Print Nothing!";
    //var color = arguments[1] ? arguments[1] : "white";
	var time = getNowFormatDate();
    var sn = $('#sn').text();
	var $li = $( "<li />" );
	$( "<span />" ).text( time + " ["+ sn +"]").addClass( "lowlighted" ).appendTo( $li );
	$( "<br />").appendTo( $li );
	$( "<span />" ).text( "* " ).appendTo( $li );
	if ($.isArray(msg)) {
        for (i in msg) {
            var $span = $( "<span />" );
            if ($.isArray(msg[i]) == true && msg[i].length == 2) {
                $span.css("color", msg[i][1]);
                $span.text( msg[i][0] );
            }
            else {
                $span.text( msg[i] );
            }
            $span.appendTo( $li );
            if (i < msg.length-1) {
                $( "<br />").appendTo( $li );
            }
        }
	}
	else {
	    $( "<span />" ).text( msg ).appendTo( $li );
	}
    //$li.css("color", color);
	var $log = $('#EventsLog');
	//$log.prepend($li)
	$log.append($li);
	//$("#EventsLog").height();
	$("#EventsLog").scrollTop($("#EventsLog").get(0).scrollHeight);
}
/********************************
	Verify IP
********************************/
function isValidIP(ip) {
	var reg = /^(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])$/
	return reg.test(ip);
}










