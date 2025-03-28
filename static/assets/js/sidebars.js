/* global bootstrap: false */
(function () {
  'use strict'
  var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
  tooltipTriggerList.forEach(function (tooltipTriggerEl) {
    new bootstrap.Tooltip(tooltipTriggerEl)
  })

  var windowHeight = $(window).height();
  var windowWidth = $(window).width();
  $("#main-container").height(windowHeight - 10).width(windowWidth - 320);
})()
