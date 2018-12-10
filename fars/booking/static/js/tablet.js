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
  var start = new Date(Date.parse(booking.start)),  // Create start and end strings
      start_str = zeropad(start.getHours()) + ':' + zeropad(start.getMinutes()),
      end = new Date(Date.parse(booking.end)),
      end_str = zeropad(end.getHours()) + ':' + zeropad(end.getMinutes()),
      time_str = start_str + ' - ' + end_str,
      time = $('<h2 class="col-6 timebox pt-3"></h2>').append(time_str),
      comment = $('<h2 class="col-12"></h2>').append(booking.comment),
      name_str = booking.user.first_name + " " + booking.user.last_name,
      name = $('<p class="col-12"></p>').append(name_str),
      comment_and_name = $('<div class="col-6"></div>'),
      booking_box = $('<div class="row pt-4"></div>');

  comment_and_name.append(comment).append(name);
  booking_box.append(time).append(comment_and_name);

  return booking_box;
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
