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

      },
      firstDay: 1,
      locale: 'fi',
      timeFormat: 'H:mm',
      displayEventEnd: true,
      defaultView: 'agendaDay',
      // If a day is clicked it opens the day-view at that date
      // dayClick: function(date, jsEvent, view) {
      // },
  });
});
