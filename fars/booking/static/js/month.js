$(document).ready(function() {
  var calendar = $('#calendar'),
    bookable = calendar.data('bookable'),
    locale = calendar.data('locale'),
    user = calendar.data('user');
  calendar.fullCalendar({
      height: 'auto',
      locale: locale,
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
      timezone: 'local',
      timeFormat: 'H:mm',
      displayEventEnd: true,
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
              var event = {
                id: $(this).attr('id'),
                title: $(this).attr('comment'),
                start: $(this).attr('start'),
                end: $(this).attr('end'),
              };
              if ($(this).attr('user') === user) {
                event.className = 'bg-primary';
              }
              events.push(event);
            });
            callback(events);
          }
        });
      }
  });
  var Key = {
    LEFT:   37,
    RIGHT:  39
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
    switch (keycode) {
      case Key.LEFT:
        calendar.fullCalendar('prev');
        break;
      case Key.RIGHT:
        calendar.fullCalendar('next');
        break;
    }
  }

  _addEventListener('keydown', document, handleKeyboardEvent);
});
