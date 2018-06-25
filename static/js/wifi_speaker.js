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
		    $(this).text('Checking...');
		    $(this).attr("disabled", true);
            $(this).css("background-color", "gray");
            $.ajax({url: 'check_wifi', type: 'GET', dataType: 'json', data: {'ip': ip}})
            .done(function(data){
                if (data['status'] == 'ok') {
                    $('div#device-scan').hide();
                    $('#info-show').show();
                    $("div#div-log").show();
                    $("p#ip-error").hide();
                    get_info(ip);
                    socket.emit('save_ip', {'ip': ip});
                }
                else{
                    var text=[];
                    text[0] = 'Sorry, cannot connect to '+ip+'  !';
                    text[1] = "Please check device ip and try again!";
                    popup_window_info(text);
                }
            })
            .always(function(){
                $('#go-ip').text('Go');
                $('#go-ip').attr("disabled", false);
                $('#go-ip').css("background-color", "black");
            });
		}
		else{
			$("p#ip-error").show();
		}
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
		text = {"mode": bt_mode};
		$.ajax({url:'ase_set_bt_reconnect_mode',type:'POST',dataType:'json', data:text})
		.done(function(data){
            if (refresh_info(data['status'], true) == true) {
                printLog("Changed bluetooth reconnect mode to " + bt_mode);
            }
		});
	});

	$('button#factory_reset').click(function(event){
		// var text = {"ip":sessionStorage.getItem("ip")};
		$.ajax({url:'ase_reset', type:'POST',dataType:'json'})
		.done(function(data){
		    if (refresh_info(data['status'], false) == true) {
		        button_back();
		    }
		});
	});

	$('button#go_web_setting').click(function(event){
	    //window.location.href='http://'+sessionStorage.getItem("ip")
	    window.open('http://'+sessionStorage.getItem("ip"));
	});

    $('input#bt_open_set').click(function(event){
        if ($(this).prop('checked') == true) {
            $.ajax({url:'bt_open_set',type:'POST',dataType:'json', data:{"enable": true}})
            .done(function(data){
                if (refresh_info(data['status'], true) == true) {
                    printLog("Enabled BT always open");
                    $('.bt_pair').hide();
                }
            });
        }
        else {
            $.ajax({url:'bt_open_set',type:'POST',dataType:'json', data:{"enable": false}})
            .done(function(data){
                if (refresh_info(data['status'], true) == true) {
                    printLog("Disabled BT always open");
                    $('.bt_pair').show();
                }
            });
        }
	});

    $('button#bt_pair').click(function(event){
        $.ajax({url:'bt_pair',type:'POST',dataType:'json', data:{"cmd": "pair"}})
        .done(function(data){
            if (refresh_info(data['status'], true) == true) {
                printLog("Trigger BT pairing");
            }
        });
	});

    $('button#bt_cancel_pair').click(function(event){
	    $.ajax({url:'bt_pair',type:'POST',dataType:'json', data:{"cmd": "cancel"}})
        .done(function(data){
            if (refresh_info(data['status'], true) == true) {
                printLog("Cancel BT pairing");
            }
        });
	});

    $('button#get_product_status').click(function(event){
        printLog("Refresh product status");
        $(this).attr("disabled", true);
        $(this).css("background-color", "grey");
        $.ajax({url:'get_product_status',type:'GET', dataType:'json'})
		.done(function(data){
		    $('td#product_status').empty();
		    for (name in data) {
		        if (data[name] != 'error') {
		            $li = $( "<li />");
                    $li.text(name+": "+ data[name]);
                    $li.appendTo($('td#product_status'));
		        }
                else {
                    prompt_error();
                    return
                }
		    }
		})
		.always(function(){
            $('#get_product_status').attr("disabled", false);
            $('#get_product_status').css("background-color", "black");
		});
	});

    $('button#get_volume').click(function(event){
        $(this).attr("disabled", true);
        $(this).css("background-color", "grey");
        $.ajax({url:'get_volume',type:'GET', dataType:'json'})
		.done(function(data){
            if ('error' in data) {
                    prompt_error();
                    return;
            }
            var info = [];
            info[0] = 'Sound volume:';
            info[1] = '/n';
            var i = 2;
            for (d in data) {
                info[i] = [d+': '+data[d], 'white', 'indent'];
                i ++;
            }
            info[i] = '/n';
            printLog(info);
		})
		.always(function(){
            $('#get_volume').attr("disabled", false);
            $('#get_volume').css("background-color", "black");
		});
	});

    $('button#get_other_info').click(function(event){
        $(this).attr("disabled", true);
        $(this).css("background-color", "grey");
        $.ajax({url:'get_other_info',type:'GET', dataType:'json'})
		.done(function(data){
            if ('error' in data) {
                prompt_error();
                return;
            }
            var info = [];
            info[0] = 'Other info:';
            info[1] = '/n';
            var i = 2;
            for (d in data) {
                info[i] = ['*'+d+'*', 'white', 'indent'];
                for (d1 in data[d]) {
                    i ++;
                    info[i] = [d1+': '+data[d][d1], 'white', 'indent'];
                }
                i ++;
                info[i] = '/n';
                i ++;
            }
            printLog(info);
		})
		.always(function(){
            $('#get_other_info').attr("disabled", false);
            $('#get_other_info').css("background-color", "black");
		});
	});

    socket.on('check_standby', function(msg) {
        if (msg['status'] == 'Standby') {
            printLog("Your product enter Standby! Elapsed Time: "+msg['elapsed_time']);
            get_info(sessionStorage.getItem('ip'));
        }
        else if (msg['status'] == 'error'){
            printLog([['Seems disconnected with your product!', 'red']])
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
        $('#detect_standby').attr("disabled", true);
        $('#detect_standby').text("Detecting");
        $('#detect_standby').css("background-color", "gray");
        socket.emit('detect_standby');
	});

	$('button#get_network_settings').click(function(event){
	    printLog('Scanning...');
		$(this).attr("disabled", true);
		$(this).css("background-color", "gray");
		$(this).text("Scanning");
        $.ajax({url:'get_network_settings',type:'GET', dataType:'json'})
		.done(function(data){
		    if ('error' in data) {
		        printLog([['Sorry! Something wrong! Try again!', 'red']]);
		        return;
		    }
            var info = [];
            info[0] = 'Network Settings:';
            info[1] = '/n';
            var i = 2;
            for (d in data) {
                info[i] = [d+': '+data[d], 'white', 'indent'];
                i ++;
            }
            info[i] = '/n';
            printLog(info);
		})
		.always(function(){
            $('#get_network_settings').attr("disabled", false);
            $('#get_network_settings').css("background-color", "black");
            $('#get_network_settings').text("Network Scan");
		});
	});

	$('button#refresh').click(function(event){
	    printLog('Refresh info list');
		$(this).attr("disabled", true);
		$(this).css("background-color", "gray");
		$(this).text("Refreshing");
		get_info(sessionStorage.getItem("ip"));
	});

	$('button#auto_refresh').click(function(event){
	    if ( $(this).text() == 'Stop' ){
	        $.ajax({url: 'stop_auto_refresh', type: 'POST', dataType: 'json'})
	        .done(function(){
                $("button#auto_refresh").text('Auto Refresh');
	            $("button#auto_refresh").css("background-color", "black");
	        });
	    }
	    else {
	        popup_window_setting("auto_refresh");
	    }
	});

	$('button#start_auto_refresh').click(function(event){
	    var checked = [];
	    var time_interval = $('#time_interval').val();
	    checked[0] = $('#product_status_check').prop('checked');
	    checked[1] = $('#volume_check').prop('checked');
	    var reg = /^\d+$/; // time_interval must be integer
	    if (reg.test(time_interval) == false) {
            $('#time_interval').focus();
            $('#time_interval').val('');
            return;
	    }
	    for (i in checked) {
	        if (checked[i] == true) {
	        	$('#auto_refresh').text('Stop');
                cancel_popup_setting();
                printLog("Start auto refresh");
                $("button#auto_refresh").css("background-color", "red");
                socket.emit('auto_refresh', {'time_interval': time_interval,
                                             'items': {'get_product_status': checked[0],
                                                       'volume': checked[1]}
                                             });
                break;
	        }
	    }

	});

    socket.on('start_auto_refresh', function(data) {
        $('#EventsLog').empty();
        var info = [];
        var i = 2;
        info[0] = 'Info: ';
        info[1] = '/n';
        if ('volume' in data) {
            if ('error' in data['volume']) {
                prompt_error();
                return;
            }
            info[i] = ['Current volume: '+data['volume']['Current Level'], 'white', 'indent'];
            i += 1;
        }
        if ('get_product_status' in data) {
            if ('error' in data['get_product_status']) {
                prompt_error();
                return;
            }
            for (d in data['get_product_status']) {
                info[i] = [d+': '+data['get_product_status'][d], 'white', 'indent'];
                i ++;
            }
        }
        info[i] = '/n';
        printLog(info);

        /*
        if ($('#product_status_check').prop('checked') == true) {
            $('#get_product_status').click();
        }
        if ($('#volume_check').prop('checked') == true) {
            $('#get_volume').click();
        }*/

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
    var value = {"bt_mac": $(this).attr("id")};
    printLog("Removing BT device [" + bt_name + "]");
    $.ajax({url:'bt_remove', type:'POST', dataType:'json', data:value})
    .done(function(data){
        if (refresh_info(data['status'], true) == true) {
            printLog("Removed BT device [" + bt_name + "] successfully!");
        }
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

function prompt_error(){
    var text = [];
    text[0] = 'Seems disconnected with your product!';
    text[1] = "Please check your connection and try again!";
    printLog([[text[0], "red"]]);
    popup_window_info(text);
}

function refresh_info(status, refresh){
    var ip = sessionStorage.getItem('ip');
    if (status != 200) {
        prompt_error();
        return false;
    }
    if (refresh == true){
        get_info(ip);
    }
    return true;
}

function button_back(){
    $('div#device-scan').show();
    $('#info-show').hide();
    $('#select-device').empty();
    $('div#div-log').hide();
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
  	get_info(selectText);
	$('div#device-scan').hide();
	$('#info-show').show();
	$("div#div-log").show();
    //$.post("/get_info", data, function(){
    //	alert("success")
    //});
}

function get_info(ip_text){
    var status = false;
    $.ajax({
    	url: 'get_info',
       	type: 'GET',
       	dataType: 'json',
       	data: {'ip': ip_text}})
    .done(function(data){
        //console.log(response);
        for (d in data){
            if (d=="error"){
                var text=new Array()
                text[0] = "Sorry, cannot connect to "+data["ip"]+"!";
                text[1] = "Maybe you need to check your device!";
                printLog([[text[0], "red"]]);
                popup_window_info(text);
                return false;
            }
            else if (d=="deviceName") {
                $('#device_name_input').val(data[d]);
            }
            else if (d=="product_status") {
                $('td#product_status').empty();
                for (name in data["product_status"]) {
		            $li = $( "<li />");
                    $li.text(name+": "+ data["product_status"][name]);
                    $li.appendTo($('td#product_status'));
		        }
            }
            else if (d=="bluetoothSettings"){
                $('#bt_paired').empty();
                //always open
                var bt_open = data[d]['bt_open']
                $('#bt_open_set').attr('checked', bt_open);
                if (bt_open==true) {
                    $('.bt_pair').hide();
                }
                else {
                    $('.bt_pair').show();
                }
                //bt reconnect mode
                $("#bt_reconnect_mode").val(data[d]['bt_reconnect_mode']);
                //bt paired devices
                var devices = data[d]["bt_devices"]
                if (devices.length==0) {
                    $li = $( "<li />");
                    $li.text("<None>");
                    $('#bt_paired').append($li);
                    $li.attr("disabled", true);
                }
                else{
                    for (var i in devices){
                        bt = devices[i];
                        if (bt['connected'] == true){
                            bt_name = bt['deviceName'] + ' [connected]';
                        }
                        else{
                            bt_name = bt['deviceName'];
                        }
                        bt_mac = bt['deviceAddress'];
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
        status = true;
        sessionStorage.setItem("ip", data["ip"]);
        sessionStorage.setItem("sn", data["sn"]);
        $('button#refresh').attr("disabled", false);
        $('button#refresh').css("background-color", "black");
        $('button#refresh').text("Refresh");
    })
    .always(function(){
        $('button#refresh').attr("disabled", false);
        $('button#refresh').css("background-color", "black");
        $('button#refresh').text("Refresh");
    });
    return status;
}
function change_device_name(name){
    text = {"name":name};
    $.ajax({url:'change_product_name', type:'POST', dataType:'json', data:text})
    .done(function(data){
        if (refresh_info(data['status'], true) == true) {
            printLog("Changed product name to " + name);
        }
    });
}

/********************************
	Verify IP
********************************/
function isValidIP(ip) {
	var reg = /^(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])$/;
	return reg.test(ip);
}




















