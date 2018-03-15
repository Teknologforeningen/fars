$(document).ready(function() {
  $('#calendar').fullCalendar({
      aspectRatio: 2,
      // header
      header: {
        left: 'prev,next today',
        center: 'title',
        right: 'month,agendaWeek,agendaDay'
      },
      views: {
        month: {
          titleFormat: 'MMMM YYYY'
        }
      },
      firstDay: 1,
      locale: 'fi',
      timeFormat: 'H:mm',
      displayEventEnd: true,
      // If a day is clicked it opens the day-view at that date
      dayClick: function(date, jsEvent, view) {
        $('#calendar').fullCalendar('changeView', 'agendaDay');
        $('#calendar').fullCalendar('gotoDate', date);
      },
  });
  $.ajax({
    url: "/bookings/2018/03",
    success: function(data) {
      for(i=0;i<data.length;i++) {
        $('#calendar').fullCalendar('renderEvent', data[i], true);
      }
    }
  });
});
