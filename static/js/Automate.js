$("#automate").addClass("active");
get_automation_info();
sessionStorage.setItem("loaded_step_name", "");

$(document).ready(function(){
    var ticker;
    namespace = '/automate/test';
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + namespace);

    socket.on('print_msg', function(msg) {
        printLog3(msg.data, msg.color);
    });

    $('#bt_connect').click(function(event){
        socket.emit("automate_cmd", {"cmd":"bt_connect,Beoplay M3_28155630"});
    });
    $('#bt_disconnect').click(function(event){
        socket.emit("automate_cmd", {"cmd":"bt_disconnect,Beoplay M3_28155630"});
    });


    /********************************
        Automation
    ********************************/
	$(".btn_edit_action").click(function(event){
        popup_window_setting(""+$(this).attr('id'));
	});

	$(".btn_save").click(function(event){
	    var automation_info = {};
        $(".input_edit_action").each(function(){
            automation_info[$(this).attr("id")] = $(this).val();
        });
        $.ajax({url: "automate/save_automation_info", type: "POST", dataType: "JSON", data: automation_info})
        .done(function(){
            get_automation_info();
        });
        cancel_popup_setting();
	});

	$(".btn_add_action").click(function(event){
	    $('#start_run_automation').attr("disabled", false);
        $('#start_run_automation').css("background-color", "black");
		var name = $(this).attr("id");
		var text = $("#text_"+name).text();
		var number = $(".action").length+1;
        create_steps(number, name, text);
        $("#show_steps").scrollTop($("#show_steps").get(0).scrollHeight);
	});

	$(".move").click(function(event){
	    var selectItem = $("#show_steps").find("option:selected");
	    if ( selectItem.text() == "") {return;}
	    if ($(this).attr('id') == 'move_up') {
	        move_item(selectItem, 'move_up');
	    }
	    else {
	        move_item(selectItem, 'move_down');
	    }
	});

	$("#remove_all").click(function(event){
		$("#show_steps").empty();
		$('#start_run_automation').attr("disabled", true);
        $('#start_run_automation').css("background-color", "gray");
	});

	$("#save_steps").click(function(event){
	    if ($('.action').length == 0) {return;}
		popup_window_setting('save_steps');
		$('#input_save_name').val(sessionStorage.getItem("loaded_step_name"));
		$('#input_save_name').focus();
	});

	$("#btn_save_steps_ok").click(function(event){
        var dict_steps = {};
        var info = {};
        info['file_name'] = $('#input_save_name').val();
		if (info['file_name'] == ''){
		    $('#input_save_name').focus();
		    return;
		}
		$('.action').each(function(){
		    var num = $(this).children('.step_number').text();
            dict_steps[num] = get_action_info(this);
		});
		cancel_popup_setting();
		info['steps'] = dict_steps;
		socket.emit('save_steps', info);
		sessionStorage.setItem("loaded_step_name", info['file_name']);
		$('#steps_name').text(info['file_name']);
	});

    socket.on('save_success', function(msg){
        var text = [];
        text[0] = 'Save steps ['+msg['file_name']+'] successfully!';
        popup_window_info(text);
    });

	$("#load_steps").click(function(event){
		popup_window_setting('load_steps');

		$.ajax({url: 'automate/load_steps', type: 'GET', dataType: 'json'})
		.done(function(data){
		    var i=0;
		    if (data.length == 0){return;}
		    var files_name = data['files_name'];
		    $('#select_saved_steps').empty();
		    for (d in files_name) {
		        i += 1;
                $option = $( "<option />");
                $option.text(files_name[d]);
                $option.attr({"id": files_name[d]+"__"+i, "style": "cursor:pointer; border-bottom: gray dashed thin;"});
                //$li.attr({"id":i,"style":"list-style-type:none"});
                $('#select_saved_steps').append($option);
		    }
		});

	});

    $("#select_saved_steps").click(function(event){
        var selectItem = $("#select_saved_steps").find("option:selected");
        if ( selectItem.text() != "") {
            $('#btn_delete_file').attr("disabled", false);
            $('#btn_delete_file').css("background-color", "black");
        }
	});

    $("#btn_delete_file").click(function(event){
        var selectItem = $("#select_saved_steps").find("option:selected");
        if ( selectItem.text() == "") {return;}
        var file_id = selectItem.attr('id');
        $.ajax({url: 'automate/remove_saved_list', type: 'POST', dataType:'json', data:{'name':file_id}})
        .done(function(){
            $('#'+file_id).remove();
            $('#btn_delete_file').attr("disabled", true);
            $('#btn_delete_file').css("background-color", "gray");
        });

	});

	$("#start_run_automation").click(function(event){
	    var steps_info = {};
	    var i = 0;
	    steps_info["total_times"] = $("#total_times").val();
	    if (steps_info["total_times"] == "") {
	        $("#total_times").focus();
	        return;
	    }
	    var reg = /^\d+$/; // time_interval must be integer
	    if (reg.test(steps_info["total_times"]) == false) {
	        $("#total_times").val("");
	        $("#total_times").focus();
	        return;
	    }
		$(".action_step_text").each(function(){
		    i += 1;
		    var tmp = {}
		    tmp[$(this).attr("name")] = $(this).text()
		    //steps_info[i] = {$(this).attr("name"): $(this).text()};
		    steps_info[i] = tmp
		});
		if (i == 0) {
		    return;
		}
		var start_time = (new Date).getTime();
		ticker = self.setInterval(function() {
            $('#elapsed_time').text(tick(start_time));
        }, 1000);
		$("#stop_automation_running").css('background-color', 'black');
        $("#stop_automation_running").attr('disabled', false);
        $("#back").css('background-color', 'gray');
        $("#back").attr('disabled', true);
		$("#automation_running_state").children("h1").text("Running");
		$("#show_total_times").text(steps_info["total_times"]);
		$("#automation_setting").hide();
		$("#automation_running_state").show();
	    $("div#div-log").show();
		socket.emit("start_run_automation", steps_info);
	});

    socket.on('running_over', function() {
        printLog3("**************Finished**************", 'white');
        $("#automation_running_state").children("h1").text("Over");
        $("#stop_automation_running").css('background-color', 'gray');
        $("#stop_automation_running").attr('disabled', true);
        $("#back").css('background-color', 'black');
        $("#back").attr('disabled', false);
        ticker = window.clearInterval(ticker);
    });

	$("#stop_automation_running").click(function(event){
	    $(this).text("Stopping");
        $.ajax({url: 'automate/stop_automation_running', type: 'POST', dataType: 'JSON'})
        .done(function(){
            $("#stop_automation_running").css('background-color', 'gray');
            $("#stop_automation_running").attr('disabled', true);
        })
	});

	socket.on('stop_confirm', function(){
        printLog3('You stopped running!!!', 'red')
        $("#stop_automation_running").text("Stop");
        $("#automation_running_state").children("h1").text("Stopped");
        $("#stop_automation_running").css('background-color', 'gray');
        $("#stop_automation_running").attr('disabled', true);
        $("#back").css('background-color', 'black');
        $("#back").attr('disabled', false);
        ticker = window.clearInterval(ticker);
	});

	socket.on('run_stopped', function(){
        $("#stop_automation_running").text("Stop");
        $("#automation_running_state").children("h1").text("Stopped");
        $("#stop_automation_running").css('background-color', 'gray');
        $("#stop_automation_running").attr('disabled', true);
        $("#back").css('background-color', 'black');
        $("#back").attr('disabled', false);
        ticker = window.clearInterval(ticker);
	});

    socket.on('show_running_info', function(msg) {
        for (i in msg) {
            $('#'+i).text(msg[i]);
        }
    });

	$("#back").click(function(event){
        $("#automation_setting").show();
		$("#automation_running_state").hide();
	    $("div#div-log").hide();
	});
    /*************************************************************/



});

function create_steps(number, name, text){
    var remove_step_id = name+"_"+number;
    var action_step_id = "action_"+remove_step_id;
    var $steps = $("#show_steps");
    var $option = $("<option id=\""+action_step_id+"\" value=\""+action_step_id+"\" style=\"border-bottom: gray dashed thin;\"></option>").addClass("action");
    var $sequence = $("<div>"+number+"</div>").addClass("step_number");
    var $space = $("<div>.&nbsp</div>");
    var $action_text = $("<div name=\""+name+"\">"+text+"</div>").addClass("action_step_text");
    //var $move_up = $("<div class=move_up>▲</div>");
    //var $move_down = $("<div class=move_down>▼</div>");
    //var $remove_item = $("<div class=\"remove_item\" id=\""+remove_step_id+"\">―</div>");
    $option.append($sequence);
    $option.append($space);
    $option.append($action_text);
    //$option.append($remove_item);
    $steps.append($option);
}

function get_automation_info() {
    $.ajax({url:"automate/get_automation_info", type:"GET", dataType:"JSON"})
    .done(function(data){
        for (k in data['info1']){
            $("#text_"+k).text(data['info1'][k]);
        }
        for (k in data['info2']){
            $("#"+k).val(data['info2'][k]);
        }
    });
}


function get_action_info(selector){
    var tmp = [];
    tmp.push($(selector).attr('id'));
    tmp.push($(selector).children('.action_step_text').attr('name'));
    tmp.push($(selector).children('.action_step_text').text());
    return tmp;
}

function change_div(id, set_num, set_name, step_text){
    //$('#'+id).children('.step_number').text(set_num);
    $('#'+id).children('.action_step_text').attr('name', set_name);
    $('#'+id).children('.action_step_text').text(step_text);
    $('#'+id).attr('id', 'action_'+set_name+'_'+set_num);
}

function change_option_content(id, set_num, set_name, step_text){
    //$('#'+id).children('.step_number').text(set_num);
    //$('#'+id).children('.action_step_text').attr('name', set_name);
    //$('#'+id).children('.action_step_text').text(step_text);
    var value = 'action_'+set_name+'_'+set_num;
    $('#'+id).empty();
    var $sequence = $("<div>"+set_num+"</div>").addClass("step_number");
    var $space = $("<div>.&nbsp</div>");
    var $action_text = $("<div name=\""+set_name+"\">"+step_text+"</div>").addClass("action_step_text");
    $('#'+id).append($sequence);
    $('#'+id).append($space);
    $('#'+id).append($action_text)
    $('#'+id).val(value);
    $('#'+id).attr('id', value);
    return value;
}

$(document).on('click', '#remove_item', function() {
    var selectItem = $("#show_steps").find("option:selected");
    if (selectItem.text() == ""){return;}
    selectItem.remove();
    var i=0;
    $(".action").each(function(){
        i += 1;
        var tmp = get_action_info(this);
        change_option_content($(this).attr("id"), i, tmp[1], tmp[2]);
        /*
        new_id = origin_id.replace(/(\d+)/, i);
        $(this).children(".step_number").text(i);
        $("#"+origin_id).attr("id", new_id);
        $("#action_"+origin_id).children(".step_number").text(i);
        $("#action_"+origin_id).attr("id", "action_"+new_id);
        */
    })
});

function move_item(option, type){
    var move_id_a = option.attr('id');
    if (move_id_a == ''){return;}
    var num_a = $('#'+move_id_a).children('.step_number').text();
    var num_b;
    if (type == 'move_up') {
        if (num_a == '1'){return;}
        num_b = Number(num_a) - 1;
    }
    else {
        if (num_a == $('.action').length){return;}
        num_b = Number(num_a) + 1;
    }
    $('#'+move_id_a).attr('selected', false);
    var info_a = get_action_info('#'+move_id_a);
    var name_b = '';
    var text_b = '';
    var moved_val_a;
    $(".step_number").each(function(){
        if ($(this).text() == num_b){
            name_b = $(this).siblings('.action_step_text').attr('name');
            text_b = $(this).siblings('.action_step_text').text();
            var move_id_b = $(this).parent().attr('id');
            moved_val_a = change_option_content(move_id_b, num_b, info_a[1], info_a[2]);
            return;
        }
    })
    change_option_content(move_id_a, num_a, name_b, text_b);
    $("#show_steps").val(moved_val_a);
}

/*
$(document).on('click', '.move_up', function() {
    move_item(this, 'move_up')
});

$(document).on('click', '.move_down', function() {
    move_item(this, 'move_down')
});
*/
function SelectSteps() {
    var selectItem = $("#select_saved_steps").find("option:selected");
    var file_name = selectItem.text();
    if (file_name == ""){return;}
    var file_id = selectItem.attr('id');
    $.ajax({url: 'automate/load_step', type: 'POST', dataType:'json', data:{'name':file_id}})
    .done(function(data){
        if (data.length == 0){return;}
        $('#show_steps').empty();
        var i = 0;
        for (d in data) {
            i += 1;
            create_steps(i, data[i][1], data[i][2]);
        }
        cancel_popup_setting();
        sessionStorage.setItem("loaded_step_name", file_name);
        $('#steps_name').text(file_name);
        $('#start_run_automation').attr("disabled", false);
        $('#start_run_automation').css("background-color", "black");
    });
}

