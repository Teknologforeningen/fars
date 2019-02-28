function updateTime() {
  const hours = new Date().getHours();
  $(".hours").html(( hours < 10 ? "0" : "" ) + hours);
  const minutes = new Date().getMinutes();
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
  const start = new Date(Date.parse(booking.start)),  // Create start and end strings
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

function updateBookings() {
  const bookable = $('#hidden-data').data('bookable'),
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
      var vacant = true;
      for(booking in data) {
        $('#bookingbox').append(createBooking(data[booking]));
        if(Date.parse(data[booking].start) <= now && Date.parse(data[booking].end) >= now) {
          vacant = false;
        }
      }
      if (!vacant) {
        $('#vacancyindicator').removeClass('vacant').addClass('occupied');
      } else {
        $('#vacancyindicator').addClass('vacant').removeClass('occupied');
      }
      updateBookformInfo(now, data);
    }
  });
}

function updateBookformInfo(now, bookings) {
  const day = ("0" + now.getDate()).slice(-2),
      month = ("0" + (now.getMonth() + 1)).slice(-2),
      today = now.getFullYear()+"-"+(month)+"-"+(day),
      now_h = now.getHours(),
      now_m = now.getMinutes();

  // TODO change to 1h or till next booking starts
  var defaultTimes = findDefaultTime(bookings);
  $('#id_start_0').val(today);
  $('#id_start_1').val(zeropad(now_h) + ":" + zeropad(now_m));
  $('#id_end_0').val(today);
  $('#id_end_1').val(zeropad(now_h+1) + ":" + zeropad(now_m));
}

$(document).ready(function() {
  updateTime();
  updateBookings();
  setInterval(updateTime, 1000);
  setInterval(updateBookings, 60000);

  if($('#bookform').data('errors')) {
    $('#book-modal').modal('show');
  }

  $("#bookbtn").click(function(event) {
    $('#book-modal').modal('show');
    // updateBookformInfo(new Date());
  });
});
