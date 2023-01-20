function getBusinesshours(currentTime, date) {
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

function createCalendar(calendar, date, bookable, locale, user, timezone, timeslots) {
  let currentTime = moment();
  let hasTimeslots = timeslots.length !== 0;
  if (hasTimeslots) {
    calendar.addClass('fars-timeslots');
  } else {
    calendar.addClass('fars-freeselect');
  }
  calendar.fullCalendar({
    height: 'parent',
    aspectRatio: 2,
    // header
    header: {
      left: 'today prev,next title',
      center: '',
      right: ''
    },
    views: {},
    firstDay: 1,
    locale: locale,
    timezone: timezone,
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
    businessHours: getBusinesshours(currentTime, date),
    selectable: !hasTimeslots,
    selectLongPressDelay: 300,
    selectAllow: function(selectInfo) {
      let min = moment();
      const remainder = min.minute() % 30;
      min.subtract(remainder, 'minutes').startOf('minute');
      return selectInfo.start >= min;
    },
    // If a time is selected it opens the modal for booking
    select: function(start, end, jsEvent, view) {
      let now = moment();
      if (start < now) {
        start = now;
      }
      let modal = $('#modalBox');
      let params = {'st': start.format(), 'et': end.format()};
      $.get(
        '/booking/book/' +  bookable + '?' + $.param(params),
        function(data){
          modal.find('.modal-content').html(data)
        }
      ).fail(function(data){
        modal.find('.modal-content').html(data.responseText)
      });
      modal.modal('show');
    },
    events: function(start, end, eventTimezone, callback) {
      // Fill booking slots
      let now = moment();
      let slotEvents = [];

      if (hasTimeslots) {
        // Fill the requested time range with timeslots, week by week. Stop when cursor's week is later than end.
        // Important to pay attention to the distinction between year and week-year here.
        for (let cursor = moment(start); (cursor.isoWeekYear() == end.isoWeekYear() && cursor.isoWeek() <= end.isoWeek()) || cursor.isoWeekYear() < end.isoWeekYear(); cursor.add(1, 'weeks')) {
          let year = cursor.isoWeekYear();
          let week = cursor.isoWeek();
          timeslots.forEach(function(timeslot) {
            let slotStart = moment([year, String(week).padStart(2, '0'), timeslot.start_weekday, timeslot.start_time].join(' '), 'GGGG WW E HH:mm:ss')
            let slotEnd = moment([year, String(week).padStart(2, '0'), timeslot.end_weekday, timeslot.end_time].join(' '), 'GGGG WW E HH:mm:ss')
            // If end time is before the cursor and the start time, the end time should be moved to the next week.
            if (slotStart > slotEnd && slotEnd < cursor) {
              slotEnd.add(1, 'weeks');
            }
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
        {bookable: bookable, after: start.toISOString(), before: end.toISOString()},
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
    eventClick: function(calEvent, jsEvent, view) {
      let modal = $('#modalBox');
      if (calEvent.hasOwnProperty('id')) {
        $.get(
          '/booking/booking/' + calEvent.id,
          function(data){
            modal.find('.modal-content').html(data)
          }
        );
      } else {
        // This is a timeslot event
        let params = {'st': calEvent.start.format(), 'et': calEvent.end.format()};
        $.get(
          '/booking/book/' +  bookable + '?' + $.param(params),
          function(data){
            modal.find('.modal-content').html(data)
          }
        ).fail(function(data){
          modal.find('.modal-content').html(data.responseText)
        });
      }
      modal.modal('show');
    },
  })
}


$(document).ready(function() {
  let calendar = $('#calendar'),
    date = calendar.data('date'),
    bookable = calendar.data('bookable'),
    locale = calendar.data('locale'),
    user = calendar.data('user'),
    timezone = calendar.data('timezone')
  $.get(
    '/api/timeslots',
    {bookable: bookable},
    function(timeslots) {
      createCalendar(calendar, date, bookable, locale, user, timezone, timeslots);
    }
  );

  let Key = {
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
    let keycode = evt.keyCode || evt.which; // also for cross-browser compatible
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
