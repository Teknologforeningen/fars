$(document).ready(function() {
  var calendar = $('#calendar'),
    bookable = calendar.data('bookable');
  calendar.fullCalendar({
      height: 'auto',
      aspectRatio: 2,
      // header
      header: {
        left: 'today prev,next title',
        center: '',
        right: ''
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
      eventBackgroundColor: "#6c757d",
      // If a day is clicked it opens the day-view at that date
      dayClick: function(date, jsEvent, view) {
        window.location.href = '/booking/' + bookable + '/' + date.toISOString();
      },
      events: function(start, end, timezone, callback) {
        $.ajax({
          url: '/api/bookings',
          data: {
            bookable: bookable,
            after: start.toISOString() + 'T00:00:00',
            before: end.toISOString() + 'T23:59:59',
          },
          success: function(data) {
            var events = [];
            $(data).each(function() {
              events.push({
                title: $(this).attr('comment'),
                start: $(this).attr('start'),
                end: $(this).attr('end'),
              });
            });
            callback(events);
          }
        });
      }
  });
});
