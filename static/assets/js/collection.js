$(function() {

  $("#overlay").hide()
  $("#image-container").hide()

  // 点击“查看图片”按钮
  $(".view-chart").on('click', function() {
    $('#image').attr('src', $(this).attr('content')).height(600).width(1000);

    // 显示遮罩层和图片容器
    $("#overlay").show()
    $("#image-container").show()
  })

  // 点击“关闭”按钮
  $('#close-btn').on('click', () => {
    $("#overlay").hide()
    $("#image-container").hide()
  });

  // 点击遮罩层也可以关闭
  $('#overlay').on('click', () => {
    $("#overlay").hide()
    $("#image-container").hide()
  });

  $(".export-chart").on("click", function () {
    // 提取 Base64 数据的 MIME 类型和纯数据部分
    const base64Image = $(this).attr('content')
    const mimeType = base64Image.match(/^data:(.*);base64,/)[1]; // 获取 MIME 类型
    const base64Data = base64Image.split(',')[1]; // 获取纯 Base64 数据

    // 将 Base64 数据转换为二进制数据
    const byteCharacters = atob(base64Data); // 解码 Base64
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);

    // 创建 Blob 对象
    const blob = new Blob([byteArray], { type: mimeType });

    // 创建下载链接
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'image.png'; // 下载文件的名称
    document.body.appendChild(a);

    // 触发下载
    a.click();

    // 清理
    URL.revokeObjectURL(url);
    document.body.removeChild(a);
  })

  $(".delete-chart").on("click", function(){
    $.ajax({
      url: '/deletePersonCollection',
      type: 'POST',
      contentType: 'application/json',
      data: JSON.stringify({name: $(this).attr("name")}),
      success: function(resp) {
        alert("Deletion successful.")
        window.location.reload()
      },
      error: function(error) {
        console.error('There was an error!', error);
        alert('Data deletion failed.')
      }
    })
  })
})