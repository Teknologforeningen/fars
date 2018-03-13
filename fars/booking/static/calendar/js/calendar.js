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
      locale: 'fi',

      events: [
        // all day event
        {
          title  : 'Meeting',
          start  : '2018-03-12'
        },
        // long-term event
        {
          title  : 'Conference',
          start  : '2018-03-13',
          end    : '2018-03-15'
        },
        // short term event
        {
          title  : 'Dentist',
          start  : '2018-03-09T11:30:00',
          end  : '2018-03-09T012:30:00',
          allDay : false // will make the time show
        }
      ]
  });
});
