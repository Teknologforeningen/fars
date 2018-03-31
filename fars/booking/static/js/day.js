$(document).ready(function() {
  var calendar = $('#calendar'),
      date = calendar.data('date'),
      bookable = calendar.data('bookable');
  calendar.fullCalendar({
      aspectRatio: 2,
      // header
      header: {
        left: '',
        center: 'title',
        right: ''
      },
      views: {

      },
      firstDay: 1,
      locale: 'fi',
      timeFormat: 'H:mm',
      displayEventEnd: true,
      defaultView: 'agendaDay',
      defaultDate: date,
      allDaySlot: false,
      // If a day is clicked it opens the day-view at that date
      dayClick: function(date, jsEvent, view) {
        window.location.href = '/booking/book/' + bookable + '?t=' + date.toISOString();
      },
  });
});
