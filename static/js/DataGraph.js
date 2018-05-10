$("#data_graph").addClass("active");
$("body").css("background-color", "white");
$("html").css("background-color", "white");

$.ajax({url:'get_graph_data', type:'POST', dataType:'json', data:{"filename": $("#data_file").text()}})
    .done(function(data){
        if (data["file_error"] != "") {
            alert(data["file_error"]);
        }
        new_mychart(data);
    });

$(document).ready(function(){
    namespace = '/DataGraph/test';
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port + namespace);

    $('form#graph_data').submit(function(){
        if (document.querySelector("#file_path").files["length"] == 0){
            alert("You need select a file!");
            return false
        }
        //socket.emit('upload_file', {"data": document.querySelector("#file_path").files['file']});
    });
});

var myChart = echarts.init(document.getElementById('main'));

var upColor = '#ec0000';
var upBorderColor = '#8A0000';
var downColor = '#00da3c';
var downBorderColor = '#008F28';


/*var data0 = splitData([
    ['12-04 09:36:21.013', 39.98],
]);

function splitData(rawData) {
    var time = [];
    var values = []
    for (var i = 0; i < rawData.length; i++) {
        time.push(rawData[i].splice(0, 1)[0]);
        values.push(rawData[i][0])
    }
    return {
        time: time,
        values: values
    };
}*/

var option = {
    tooltip: {
        trigger: 'axis',
        axisPointer: {
            type: 'cross'
        }
    },
    legend: {
        data: ['db']
    },
    grid: {
        left: '10%',
        right: '10%',
        bottom: '15%'
    },
    xAxis: {
        type: 'category',
        //data: data0.time,
        scale: true,
    },
    yAxis: {
        scale: true,
        splitArea: {
            show: true
        }
    },
    dataZoom: [
        {
            type: 'inside',
            start: 50,
            end: 100
        },
        {
            show: true,
            type: 'slider',
            y: '90%',
            start: 50,
            end: 100
        }
    ],
    series: [

        {
            name: 'db',
            type: 'line',
            // data: data0.values,
            // smooth: true,
            lineStyle: {
                normal: {opacity: 0.5}
            },
            markPoint: {
                data: [
                    {type: 'max', name: '最大值'},
                    {type: 'min', name: '最小值'}
                ]
            },
            markLine: {
                data: [
                    {type: 'average', name: '平均值'}
                ]
            }
        },
    ]
};
myChart.setOption(option);

var new_mychart = function (res) {
    myChart.setOption({
        title: {
            text: res["title"],
            left: 0
        },
        xAxis: {
            data: res["time"]
        },
        series: [{
            name: res["name"],
            data: res["values"]
        }]
    });
}