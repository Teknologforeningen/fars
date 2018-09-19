$(document).ready(function() {
  var calendar = $('#calendar'),
      date = calendar.data('date'),
      bookable = calendar.data('bookable');
  calendar.fullCalendar({
      height: 'auto',
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
      timezone: 'local',
      timeFormat: 'H:mm',
      slotLabelFormat: 'H:mm',
      displayEventEnd: true,
      nowIndicator: true,
      defaultView: 'agendaDay',
      defaultDate: date,
      allDaySlot: false,
      themeSystem: 'bootstrap4',
      eventBackgroundColor: "#6c757d",
      eventBorderColor: "grey",
      agendaEventMinHeight: 20,
      selectable: true,
      selectAllow: function(selectInfo) {
        return selectInfo.start > moment();
      },
      // If a time is selected it opens the modal for booking
      select: function(start, end, jsEvent, view) {
        var modal = $('#modalBox');
        var params = {'st': start.format(), 'et': end.format()};
        $.get(
          '/booking/book/' +  bookable + '?' + $.param(params),
          function(data){
            modal.find('.modal-content').html(data)
          }
        );
        modal.modal('show');
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
      },
  });
});
