function updateTime() {
  $(".hours").html(moment().hour());
  $(".min").html(moment().minute());
}

function createBooking(booking) {
  const start = moment(booking.start).format('HH:mm'),
      end = moment(booking.end).format('HH:mm'),
      time_str = start + ' - ' + end,
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
      now = moment(),
      eod = moment().endOf('day');
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
        if(moment(data[booking].start) <= now && moment(data[booking].end) >= now) {
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
  const today = now.format('YYYY-MM-DD');

  // TODO change to 1h or till next booking starts
  var defaultTimes = findDefaultTime(bookings);
  $('#id_start_0').val(today);
  $('#id_start_1').val(now.format('HH:mm'));
  $('#id_end_0').val(today);
  $('#id_end_1').val(now.add(1,'h').format('HH:mm'));
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
  });
});
