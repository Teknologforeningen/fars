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
      bookable = calendar.data('bookable'),
      locale = calendar.data('locale'),
      user = calendar.data('user');

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
      locale: locale,
      timezone: 'local',
      timeFormat: 'H:mm',
      slotLabelFormat: 'H:mm',
      displayEventEnd: true,
      nowIndicator: true,
      defaultView: 'agendaDay',
      defaultDate: date,
      allDaySlot: false,
      themeSystem: 'bootstrap4',
      agendaEventMinHeight: 20,
      scrollTime: '08:00:00',
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
              var event = {
                id: $(this).attr('id'),
                title: $(this).attr('comment'),
                start: $(this).attr('start'),
                end: $(this).attr('end'),
              };
              var today = moment();
              var classNames = [];
              if (moment(event.end) < today) {
                classNames.push("past-event");
              }
              if ($(this).attr('user') === user) {
                classNames.push('bg-own');
              }
              event.className = classNames;
              events.push(event);
            });
            callback(events);
          }
        });
      },
      eventClick: function(calEvent, jsEvent, view) {
        var modal = $('#modalBox');
        $.get(
          '/booking/booking/' + calEvent.id,
          function(data){
            modal.find('.modal-content').html(data)
          }
        );
        modal.modal('show');
      },
  });
  var Key = {
    LEFT:   37,
    RIGHT:  39,
    M: 77
  };

  /**
   * old IE: attachEvent
   * Firefox, Chrome, or modern browsers: addEventListener
   */
  function _addEventListener(evt, element, fn) {
    if (window.addEventListener) {
      element.addEventListener(evt, fn, false);
    }
    else {
      element.attachEvent('on'+evt, fn);
    }
  }

  function handleKeyboardEvent(evt) {
    if (!evt) {evt = window.event;} // for old IE compatible
    var keycode = evt.keyCode || evt.which; // also for cross-browser compatible
    if (!$('#modalBox').hasClass('show')) {
      switch (keycode) {
        case Key.LEFT:
          calendar.fullCalendar('prev');
          break;
        case Key.RIGHT:
          calendar.fullCalendar('next');
          break;
        case Key.M:
          bookable = calendar.data('bookable')
          window.location.href = '/booking/' + bookable;
          break;
      }
    }
  }

  _addEventListener('keydown', document, handleKeyboardEvent);
});
