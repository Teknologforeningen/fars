function updateTime() {
  var hours = new Date().getHours();
  $(".hours").html(( hours < 10 ? "0" : "" ) + hours);
  var minutes = new Date().getMinutes();
  $(".min").html(( minutes < 10 ? "0" : "" ) + minutes);
}

function zeropad(num) {
  if(num < 10) {
    return '0' + num;
  } else {
    return num.toString();
  }
}

function createBooking(booking) {
  var start = new Date(Date.parse(booking.start)),
      start_str = zeropad(start.getHours()) + ':' + zeropad(start.getMinutes()),
      end = new Date(Date.parse(booking.end)),
      end_str = zeropad(end.getHours()) + ':' + zeropad(end.getMinutes()),
      htmlstr = '';
  htmlstr += '<div class="row pt-4"><h2 class="col-6 timebox pt-3">' + start_str + ' - ' + end_str + '</h2>';
  htmlstr += '<div class="col-6"><h2 class="col-12">' + booking.comment + '</h2><p class="col-12">' + booking.user + '</p></div></div>';
  // TODO: Change user to actual get the users name and not the ID
  return htmlstr;
}

function getBookings() {
  var bookable = $('#hidden-data').data('bookable'),
      now = new Date(),
      eod = new Date(
        now.getFullYear(),
        now.getMonth(),
        now.getDate(),
        23, 59, 59
      );
  $.ajax({
    url: '/api/bookings',
    data: {
      bookable: bookable,
      after: now.toISOString(),
      before: eod.toISOString(),
    },
    success: function(data) {
      $('#bookingbox').html('');
      for(booking in data) {
        $('#bookingbox').append(createBooking(data[booking]));
      }
    }
  });
}

$(document).ready(function() {
  updateTime();
  getBookings();
  setInterval(updateTime, 1000);
  setInterval(getBookings, 60000);
});
