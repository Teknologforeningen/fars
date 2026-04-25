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
  function isRepeating() {
    return $('#repeat-form-wrapper').hasClass('show');
  }

  function setRepeatToggle(on) {
    const btn = $('#repeat-toggle');
    btn.toggleClass('btn-success', on);
    btn.toggleClass('btn-info', !on);
    btn.text(on ? btn.data('on') : btn.data('off'));
  }

  // Keep track of the repeat toggle state separately
  setRepeatToggle(isRepeating());

  // Toggle class and text of button when clicked
  $('#repeat-toggle').click(() => {
    // Prevent toggling during collapsing animation
    if ($('#repeat-form-wrapper').hasClass('collapsing'))
      return;

    setRepeatToggle(!isRepeating());
  });

  // Do POST request when submitting
  $('#bookform').submit(function(event) {
    const repeating = isRepeating();

    let postdata = $(this).serialize();
    if (repeating) postdata += '&repeat=1&' + $('#repeatform').serialize();

    $.post($(this).data('url'), postdata)
      .done(function(data) {
        // XXX: Return HTML directly instead of JSON?
        // XXX: Translations?

        $('#calendar').fullCalendar('refetchEvents');
        const modal = $('#modalBox');

        if (!repeating) {
          modal.modal('hide');
          return;
        }

        // Possible outcomes when creating repeating bookings:
        //  1. All repetitions were created
        //  2. Some repetitions were created, but not all
        //  3. No repetitions were created (should be impossible since the first should always succeed)
        //  4. No repetitions were created, but none were created either (XXX: currently not impossible, but should eventually be once the form validation is fixed)
        const created = data.created_bookings || [];
        const skipped = data.skipped_bookings || [];

        if (created.length && !skipped.length) {
            // 1.
            modal.modal('hide');
            return;
        }

        const title = modal.find('.modal-title');
        const body =  modal.find('.modal-body');

        if (created.length) {
          // 2.
          title.html('<strong>Booking succeeded with exceptions</strong>');
          body.html(`<p>Successfully created ${created.length} repeating booking(s).</p>`);
        } else {
          // 3. or 4.
          title.html('<strong>Booking failed</strong>');
          body.html('<p>No repeating bookings were created.</p>');
        }

        if (skipped.length) {
          // 2. or 3.
          body.append(`<p>The following ${skipped.length} repetition(s) could not be created due to overlapping with existing bookings:</p>`);
          body.append(makeUL(skipped));
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
