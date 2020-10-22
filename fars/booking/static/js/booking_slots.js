Element.prototype.appendAfter = function (element) {
  element.parentNode.insertBefore(this, element.nextSibling);
}, false;

function updateBookableTimeslotValues(value, id, type) {
  const slots_elem = document.getElementById("id_booking_slots");
  // Need to replace single quotes with double quotes because single quotes are not JSON
  let time_slots = JSON.parse(slots_elem.value.replaceAll("'",'"'));
  const [start_or_end, i] = id.split('_');

  let j;
  switch (start_or_end) {
    case "start":
      j = 0;
      break;
    case "end":
      j = 1;
      break;
    default:
      j = undefined;
  }
  switch (type) {
    case "booking_slot_weekday_":
      if (j !== undefined) time_slots[i][j] = value.target.value + " " + time_slots[i][j].split(' ')[1];
      break
    case "booking_slot_time_":
      if (j !== undefined) time_slots[i][j] = time_slots[i][j].split(' ')[0] + " " + value.target.value;
      break
  }
  slots_elem.value = JSON.stringify(time_slots);
}

function createWeekdaySelectElement(value, id) {
  const selectElement = document.createElement("select");


  const weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

  weekdays.forEach(v => {
    const optionElement = document.createElement("option");
    optionElement.value = v;
    optionElement.text = v;
    selectElement.appendChild(optionElement);

  })

  if (value) { selectElement.value = value }
  else { selectElement.value = weekdays[0] }

  const type = "booking_slot_weekday_";
  selectElement.id = type + id;
  selectElement.onchange = (value) => updateBookableTimeslotValues(value, id, type)
  return selectElement;
}

function createTimeSelectElement(value, id) {
  const input = document.createElement("input");
  input.value = value.split(":").map(n => (n.toString().length < 2 ? '0' : '') + n).join(':');
  input.type = "time";
  const type = "booking_slot_time_";
  input.id = type + id
  input.onchange = (value) => updateBookableTimeslotValues(value, id, type)
  return input;
}

function createWeekdayTimeSelectElement(value, id) {
  const [weekday, time] = value.split(' ');
  return [createWeekdaySelectElement(weekday, id), createTimeSelectElement(time, id)];
}

function renderBookingSlotInput(timespan, i) {
  const [start, end] = timespan;

  const container = document.createElement('div');
  container.classList.add('bookable-timeslot-input')
  const start_span = document.createElement('span');
  start_span.innerText = 'Starts';
  container.appendChild(start_span)
  const [start_weekday, start_time] = createWeekdayTimeSelectElement(start, 'start_' + i)
  container.appendChild(start_weekday);
  container.appendChild(start_time);
  const end_span = document.createElement('span');
  end_span.innerText = 'Ends';
  container.appendChild(end_span)
  const [end_weekday, end_time] = createWeekdayTimeSelectElement(end, 'end_' + i)
  container.appendChild(end_weekday);
  container.appendChild(end_time);

  const delete_btn = document.createElement('button');
  delete_btn.type = "button";
  delete_btn.value = i;
  delete_btn.textContent = "🗑️";
  delete_btn.onclick = () => {
    const mainInput = document.getElementById("id_booking_slots");
    deleteValueAtIndex(mainInput, i)
    refreshBookingSlotInputs(mainInput)
  }
  container.appendChild(delete_btn)

  return container;
}

function renderBookingSlotInputs(mainInput, input_container) {
  // Need to replace single quotes with double quotes because single quotes are not JSON
  const time_slots = JSON.parse(mainInput.value.replaceAll("'",'"'));

  const slot_inputs = time_slots.map((ts, i) => renderBookingSlotInput(ts, i));

  slot_inputs.forEach(e => input_container.appendChild(e));
}

function appendToElementValue(element, value) {
  // The element is assumed to have content in JSON format
  const tmp = JSON.parse(element.value.replaceAll("'",'"')).concat(value);
  element.value = JSON.stringify(tmp);
}

function deleteValueAtIndex(element, id) {
  // The element is assumed to have content in JSON format
  const tmp = JSON.parse(element.value.replaceAll("'",'"'));
  tmp.splice(id, 1);
  element.value = JSON.stringify(tmp);
}

function refreshBookingSlotInputs(element) {
  const input_container = element.parentNode.querySelector('.bookable-timeslots-input-container');
  input_container.textContent = '';
  renderBookingSlotInputs(element, input_container);
}

function addBookingSlotInputs(element) {
  const input_container = document.createElement('div');
  input_container.classList.add('bookable-timeslots-input-container');
  element.parentNode.appendChild(input_container);
  
  refreshBookingSlotInputs(element, input_container);

  const more_timeslots_button = document.createElement('button');
  more_timeslots_button.type = "button";
  more_timeslots_button.textContent = "+";
  more_timeslots_button.onclick = () => {
    const mainInput = document.getElementById("id_booking_slots");
    appendToElementValue(mainInput, [["",""]]);
    refreshBookingSlotInputs(mainInput)
  }
  
  element.parentNode.appendChild(more_timeslots_button);

  // element.style.visibility = "hidden";
}

$(document).ready(function() {
  const slots_elem = document.getElementById("id_booking_slots");
  addBookingSlotInputs(slots_elem);
});