function getBusinesshours(date) {
  var currentTime = moment();
  if (currentTime.isSame(date, 'day')) {
    start = currentTime.format('HH:mm');
  } else if (currentTime.isAfter(date)) {
    start = '24:00';
  } else {
    start = '00:00';
  }

  return {
    'start': start,
    'end': '24:00',
    'dow': [0, 1, 2, 3, 4, 5, 6]
  }
};


$(document).ready(function() {
  var calendar = $('#calendar'),
      date = calendar.data('date'),
      bookable = calendar.data('bookable');

  calendar.fullCalendar({
      height: 'parent',
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
      eventBackgroundColor: '#6c757d',
      eventBorderColor: 'grey',
      agendaEventMinHeight: 20,
      businessHours: getBusinesshours(date),
      selectable: true,
      selectLongPressDelay: 300,
      selectAllow: function(selectInfo) {
        var min = moment();
        const remainder = min.minute() % 30;
        min.subtract(remainder, 'minutes').startOf('minute');
        return selectInfo.start >= min;
      },
      // If a time is selected it opens the modal for booking
      select: function(start, end, jsEvent, view) {
        var now = moment();
        if (start < now) {
          start = now;
        }
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
        modal.modal('show');
      },
  });
});
