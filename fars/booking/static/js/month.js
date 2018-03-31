$(document).ready(function() {
  var calendar = $('#calendar'),
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
        month: {
          titleFormat: 'MMMM YYYY'
        }
      },
      firstDay: 1,
      locale: 'fi',
      timeFormat: 'H:mm',
      displayEventEnd: true,
      // If a day is clicked it opens the day-view at that date
      dayClick: function(date, jsEvent, view) {
        window.location.href = '/booking/' + bookable + '/' + date.toISOString();
      },
  });
});
