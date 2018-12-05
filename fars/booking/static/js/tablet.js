$(document).ready(function() {
  function updateTime() {
    var hours = new Date().getHours();
    $(".hours").html(( hours < 10 ? "0" : "" ) + hours);
    var minutes = new Date().getMinutes();
    $(".min").html(( minutes < 10 ? "0" : "" ) + minutes);
  }
  updateTime();
  setInterval(updateTime, 1000);
});
