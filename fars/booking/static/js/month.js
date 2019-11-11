$(document).ready(function() {
  var calendar = $('#calendar'),
    bookable = calendar.data('bookable'),
    bookablestr = calendar.data('bookablestr'),
    locale = calendar.data('locale'),
    user = calendar.data('user');
  calendar.fullCalendar({
      height: 'auto',
      aspectRatio: 2,
      // header
      header: {
        left: '',
        center: '',
        right: 'title today prev,next'
      },
      // header: false,
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
            $('div.fc-left').html(`<h2>${bookablestr}</h2>`);
          }
        });
      }
  });
  var Key = {
    LEFT:   37,
    RIGHT:  39,
    D: 68
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
      case Key.D:
        bookable = calendar.data('bookable')
        window.location.href = '/booking/' + bookable + '/' + moment().format("YYYY-MM-DD");
        break;
    }
  }

  _addEventListener('keydown', document, handleKeyboardEvent);
});
