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
      themeSystem: 'bootstrap4',
      // If a day is clicked it opens the day-view at that date
      dayClick: function(date, jsEvent, view) {
        var modal = $('#modalBox');
        $.get(
          '/booking/book/' + bookable + '?t=' + date.toISOString(),
          function(data){
            modal.find('.modal-content').html(data)
          }
        );
        modal.modal("show");
      },
      events: function(start, end, timezone, callback) {
        $.ajax({
          url: '/api/bookings',
          data: {
            bookable: bookable,
            after: start.toISOString(),
            before: end.toISOString(),
          },
          success: function(data) {
            var events = [];
            $(data).each(function() {
              events.push({
                id: $(this).attr('id'),
                title: $(this).attr('comment'),
                start: $(this).attr('start'),
                end: $(this).attr('end'),
              });
            });
            callback(events);
          }
        });
      },
      eventClick: function(calEvent, jsEvent, view) {
        var modal = $('#modalBox');
        $.get(
          '/booking/unbook/' + calEvent.id,
          function(data){
            modal.find('.modal-content').html(data)
          }
        );
        modal.modal("show");
      }
  });
});
