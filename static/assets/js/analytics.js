var myChart = null;
$(function() {

  $("#resetChart").on("click", function () {
    $("#xAxisSelect").selectpicker('deselectAll');
    $('#xAxisSelect').selectpicker('render');
    $("#yAxisSelect").selectpicker('deselectAll');
    $('#yAxisSelect').selectpicker('render');
    $("#chartType").val('barChart')
    window.location.reload()
  })

  var generateChartFunc = function () {
    let fileId = $("#fileId").val()
    let xAxisSelect = $("#xAxisSelect").val()
    let yAxisSelect = $("#yAxisSelect").val()
    console.log('fileId', fileId)
    console.log('xAxisSelect', xAxisSelect)
    console.log('xAxisSelect', typeof xAxisSelect)
    console.log('yAxisSelect', yAxisSelect)
    console.log('yAxisSelect', typeof yAxisSelect)
    if (!fileId) {
      alert('Select a data first.');
      return
    }
    if (!xAxisSelect || !xAxisSelect.length) {
      alert('Select a column for x-axis');
      return
    }
    let chartType = $("#chartType").val()
    if (chartType !== 'pieChart' && (!yAxisSelect || !yAxisSelect.length)) {
      alert('Select a column for y-axis');
      return
    }
    var postData = {
      'fileId': fileId,
      'xAxisSelect': xAxisSelect,
      'yAxisSelect': yAxisSelect
    }
    $.ajax({
      url: '/getAnalyticsData',
      type: 'POST',
      contentType: 'application/json',
      data: JSON.stringify(postData),
      success: function(resp) {
        if (resp && resp.reqData && resp.respData) {
          // 展示
          let respData = resp.respData
          if (typeof resp.respData === 'string') {
            respData = JSON.parse(resp.respData)
          }
          console.log('respData', respData)
          console.log('respData', typeof respData)
          let chartType = $("#chartType").val()
          if (chartType === 'pieChart') {

          } else {
            $("#bar_chart").width(respData.length * 50);
          }
          if (chartType === 'barChart') {
            displayBarChart(resp.reqData, respData)
          }
          if (chartType === 'lineChart') {
            displayLineChart(resp.reqData, respData)
          }
          if (chartType === 'pieChart') {
            displayPieChart(resp.reqData, respData)
          }
        }
      },
      error: function(error) {
        console.error('There was an error!', error);
        alert('Failed to retrieve data.')
      }
    });
  };

  // 获取数据
  $("#generateChart").on("click", generateChartFunc);

  $("#saveChart").on("click", function() {
    if (!myChart) {
      alert('Please generate the chart first.')
      return
    }
    var name = prompt("Please enter the name.","")
    if (!name || $.trim(name) === '') {
      alert('Please output the name.')
      return
    }
    var imgData = myChart.getDataURL({
      type: 'jpeg',
      pixelRatio: 2 // 图片清晰度
    });
    console.log('imgData', imgData);

    let postData = {
      "name": name,
      "xAxis": $("#xAxisSelect").val(),
      "yAxis": $("#yAxisSelect").val(),
      "type": $("#chartType").val(),
      "content": imgData
    }
    $.ajax({
      url: '/saveAnalyticsData',
      type: 'POST',
      contentType: 'application/json',
      data: JSON.stringify(postData),
      success: function(resp) {
        console.log('resp', resp)
        alert('Data saved successfully.')
      },
      error: function(error) {
        console.error('There was an error!', error);
        alert('Failed to save data')
      }
    });
  })

  // displayBarChart();

  // $("#exportChart").on("click", function() {
  //   const src = myChart.getDataURL({
  //       pixelRatio: 2,
  //       backgroundColor: '#fff'
  //   });
  //   const a = document.createElement('a');
  //   a.href = src;
  //   a.download = 'chart';
  //   document.body.appendChild(a);
  //   a.click();
  //   document.body.removeChild(a);
  // });
});



function displayBarChart(reqData, respData) {
  let xAxisSelect = reqData.xAxisSelect
  let yAxisSelect = reqData.yAxisSelect
  console.log('xAxisSelect', xAxisSelect)
  console.log('yAxisSelect', yAxisSelect)
  console.log('respData', respData)
  xData = []
  yData = []
  for (let rd of respData) {
    let arr = []
    for (let k of xAxisSelect) {
      arr.push(rd[k])
    }
    xData.push(arr.join(':'))
    for (let i = 0; i < yAxisSelect.length; i=i+1) {
      if (yData.length === i) {
        yData[i] = []
      }
      yData[i].push(rd[yAxisSelect[i]])
    }
  }
  
  console.log('xData', xData)
  console.log('yData', yData)
  let mySeries = []
  for (let i = 0; i < yData.length; i=i+1) {
    mySeries.push({
      name: yAxisSelect[i],
      type: 'bar',
      emphasis: {
        focus: 'series'
      },
      data: yData[i]
    })
  }
  console.log('mySeries', mySeries)

  var chartDom = document.getElementById('bar_chart');
  myChart = echarts.init(chartDom);
  var option;

  option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    legend: {},
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: [
      {
        type: 'category',
        data: xData,
        axisLabel: {
          interval: 0,  // 显示所有标签
          rotate: 45,   // 旋转 45 度
          fontSize: 12  // 设置字体大小
        }
      }
    ],
    yAxis: [
      {
        type: 'value'
      }
    ],
    series: mySeries
  };

  option && myChart.setOption(option);
}

function displayLineChart(reqData, respData) {
  
  let xAxisSelect = reqData.xAxisSelect
  let yAxisSelect = reqData.yAxisSelect
  console.log('xAxisSelect', xAxisSelect)
  console.log('yAxisSelect', yAxisSelect)
  console.log('respData', respData)
  xData = []
  yData = []
  for (let rd of respData) {
    let arr = []
    for (let k of xAxisSelect) {
      arr.push(rd[k])
    }
    xData.push(arr.join(':'))
    for (let i = 0; i < yAxisSelect.length; i=i+1) {
      if (yData.length === i) {
        yData[i] = []
      }
      yData[i].push(rd[yAxisSelect[i]])
    }
  }
  console.log('xData', xData)
  console.log('yData', yData)
  let mySeries = []
  for (let i = 0; i < yData.length; i=i+1) {
    mySeries.push({
      name: yAxisSelect[i],
      type: 'line',
      stack: 'Total',
      data: yData[i]
    })
  }
  console.log('mySeries', mySeries)

  var chartDom = document.getElementById('bar_chart');
  myChart = echarts.init(chartDom);
  var option;
  
  option = {
    title: {
      text: 'Stacked Line'
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    toolbox: {
      feature: {
        saveAsImage: {}
      }
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: xData,
      axisLabel: {
        interval: 0,  // 显示所有标签
        rotate: 45,   // 旋转 45 度
        fontSize: 12  // 设置字体大小
      }
    },
    yAxis: {
      type: 'value'
    },
    series: mySeries
  };
  
  option && myChart.setOption(option);
}

function displayPieChart(reqData, respData) {
  let xAxisSelect = reqData.xAxisSelect
  let yAxisSelect = reqData.yAxisSelect
  console.log('xAxisSelect', xAxisSelect)
  console.log('yAxisSelect', yAxisSelect)
  console.log('respData', respData)

  var chartDom = document.getElementById('bar_chart');
  myChart = echarts.init(chartDom);
  var option;

  option = {
    title: {
      text: 'Pie Chart',
      subtext: 'Data',
      left: 'center'
    },
    tooltip: {
      trigger: 'item'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        name: 'Access From',
        type: 'pie',
        radius: '50%',
        data: respData,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  };

  option && myChart.setOption(option);
}