function createCalendar(calendar, bookable, locale, user, timezone, timeslots) {
  let currentTime = moment();
  let hasTimeslots = timeslots.length !== 0;
  if (hasTimeslots) {
    calendar.addClass('fars-timeslots');
  } else {
    calendar.addClass('fars-freeselect');
  }
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
    locale: locale,
    timezone: timezone,
    timeFormat: 'H:mm',
    displayEventEnd: true,
    // If a day is clicked it opens the day-view at that date
    dayClick: function(date, jsEvent, view) {
      window.location.href = '/booking/' + bookable + '/' + date.toISOString();
    },
    events: function(start, end, eventTimezone, callback) {
      // Fill booking slots
      let now = moment();
      let slotEvents = [];
      if (hasTimeslots) {
        // TODO: fix december and january
        // Important to pay attention to the distinction between year and week-year here.
        for (let cursor = moment(start); (cursor.isoWeekYear() == end.isoWeekYear() && cursor.isoWeek() <= end.isoWeek()) || cursor.isoWeekYear() < end.isoWeekYear(); cursor.add(1, 'weeks')) {
          let year = cursor.year();
          let week = cursor.isoWeek();
          timeslots.forEach(function(timeslot) {
            let slotStart = moment([year, String(week).padStart(2, '0'), timeslot.start_weekday, timeslot.start_time].join(' '), 'GGGG WW E HH:mm:ss')
            let slotEnd = moment([year, String(week).padStart(2, '0'), timeslot.end_weekday, timeslot.end_time].join(' '), 'GGGG WW E HH:mm:ss')
            // Start time of a slot may be in the previous week. If start ends up after end, move it back one week.
            if (slotStart > slotEnd) {
              slotStart.subtract(1, 'weeks');
            }
            if (slotEnd > now && slotEnd > start && slotStart < end) {
              slotEvents.push({start: slotStart, end: slotEnd, className: ['fars-timeslot']});
            }
          });
        }
      }

      // Add bookings
      $.get(
        '/api/bookings',
        {
          bookable: bookable,
          after: start.toISOString() + 'T00:00:00',
          before: end.toISOString() + 'T23:59:59',
        },
        function(bookings) {
          let bookingEvents = [];
          bookings.forEach(function(booking) {
            let bookingEvent = {
              id: booking.id,
              title: booking.comment,
              start: moment(booking.start),
              end: moment(booking.end),
            };
            let classNames = [];
            if (bookingEvent.end < now) {
              classNames.push("past-event");
            }
            if (booking.user === user) {
              classNames.push('bg-own');
            }
            bookingEvent.className = classNames;
            bookingEvents.push(bookingEvent);
            // Remove overlapped booking slots
            slotEvents = slotEvents.filter(slot => bookingEvent.end < now || !(bookingEvent.end > slot.start && bookingEvent.start < slot.end));
          });
          callback(slotEvents.concat(bookingEvents));
        }
      );
    },
  })
}


$(document).ready(function() {
  let calendar = $('#calendar'),
    bookable = calendar.data('bookable'),
    locale = calendar.data('locale'),
    user = calendar.data('user'),
    timezone = calendar.data('timezone');
  $.get(
    '/api/timeslots',
    {bookable: bookable},
    function(timeslots) {
      createCalendar(calendar, bookable, locale, user, timezone, timeslots);
    }
  );

  let Key = {
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
    let keycode = evt.keyCode || evt.which; // also for cross-browser compatible
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
