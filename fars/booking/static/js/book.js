function makeUL(array) {
  // Create the list element:
  var list = document.createElement('ul');
  for (var i = 0; i < array.length; i++) {
      // Create the list item:
      var item = document.createElement('li');
      // Set its contents:
      item.appendChild(document.createTextNode(array[i]));
      // Add it to the list:
      list.appendChild(item);
  }

  // Finally, return the constructed list:
  return list;
}


$(document).ready(function() {
  $('#repeat-toggle').change(function() {
    $('#repeat-form-wrapper').toggleClass('disabled');
  });
  $('#bookform').submit(function(event) {
    if($('#repeat-toggle').prop('checked')) {
      var postdata = $(this).serialize()+'&repeat=1&'+$('#repeatform').serialize();
    } else {
      var postdata = $(this).serialize();
    }
    $.post($(this).data('url'), postdata)
      .done(function(data) {
        $('#calendar').fullCalendar('refetchEvents');
        if (data.skipped_bookings.length > 0) {
          $('#modalBox').find('.modal-title').html(
            '<strong>Booking succeeded with the following exceptions:</strong>'
          );
          $('#modalBox').find('.modal-body').html(
            'Following bookings were skipped because of overlaps:'
          );
          $('#modalBox').find('.modal-body').append(makeUL(data.skipped_bookings));
        } else {
          $('#modalBox').modal('hide');
        }
      }).fail(function(data){
        $('#modalBox').find('.modal-content').html(data.responseText);
      });
    event.preventDefault();
  });
  $('#nowbutton').click(function() {
    let now = moment();
    $('#id_start_0').val(now.format('YYYY-MM-DD'));
    $('#id_start_1').val(now.format('HH:mm'));
    let then = now.add(1, 'hours')
    $('#id_end_0').val(then.format('YYYY-MM-DD'));
    $('#id_end_1').val(then.format('HH:mm'));
  });
});
