// Function to add a new action
function addAction() {
    const container = document.getElementById('actions-container');
    const index = container.children.length;

    const actionHTML = `
        <div class="action-item" data-index="${index}">
            <div class="form-group">
                <label for="action_name_${index}">Action Name</label>
                <input type="text" class="form-control" id="action_name_${index}" name="actions[${index}][name]" required>
            </div>
            <div class="form-group">
                <label for="action_description_${index}">Description</label>
                <textarea class="form-control" id="action_description_${index}" name="actions[${index}][description]"></textarea>
            </div>

            <div id="events-container_${index}">
                <h6>Events</h6>
            </div>
            <button type="button" class="btn btn-primary btn-sm add-event" onclick="addEvent(${index})">Add Event</button>

            <button type="button" class="btn btn-danger btn-sm remove-action" onclick="removeAction(${index})">Remove Action</button>
            <hr>
        </div>
    `;
    container.insertAdjacentHTML('beforeend', actionHTML);
}

// Function to add a new event to a specific action
function addEvent(actionIndex) {
    const actionContainer = document.getElementById(`events-container_${actionIndex}`);
    const eventIndex = actionContainer.children.length;

    const eventHTML = `
        <div class="event-item" data-action-index="${actionIndex}" data-event-index="${eventIndex}">
            <div class="form-group">
                <label for="event_type_${actionIndex}_${eventIndex}">Event Type</label>
                <input type="text" class="form-control" id="event_type_${actionIndex}_${eventIndex}" name="actions[${actionIndex}][events][${eventIndex}][type]" required>
            </div>
            <div class="form-group">
                <label for="event_description_${actionIndex}_${eventIndex}">Event Description</label>
                <textarea class="form-control" id="event_description_${actionIndex}_${eventIndex}" name="actions[${actionIndex}][events][${eventIndex}][description]"></textarea>
            </div>
            <button type="button" class="btn btn-danger btn-sm remove-event" onclick="removeEvent(${actionIndex}, ${eventIndex})">Remove Event</button>
        </div>
    `;
    actionContainer.insertAdjacentHTML('beforeend', eventHTML);
}

// Function to remove an event from a specific action
function removeEvent(actionIndex, eventIndex) {
    const eventItem = document.querySelector(`.event-item[data-action-index="${actionIndex}"][data-event-index="${eventIndex}"]`);
    if (eventItem) {
        eventItem.remove();
    }
}

// Function to remove an action and its associated events
function removeAction(actionIndex) {
    const actionItem = document.querySelector(`.action-item[data-index="${actionIndex}"]`);
    if (actionItem) {
        actionItem.remove();
    }
}

// Function to add a new action
function addAction() {
    const container = document.getElementById('actions-container');
    const index = container.children.length;

    const actionHTML = `
        <div class="action-item" data-index="${index}">
            <div class="form-group">
                <label for="action_name_${index}">Action Name</label>
                <input type="text" class="form-control" id="action_name_${index}" name="actions[${index}][name]" required>
            </div>
            <div class="form-group">
                <label for="action_description_${index}">Description</label>
                <textarea class="form-control" id="action_description_${index}" name="actions[${index}][description]"></textarea>
            </div>

            <div id="events-container_${index}">
                <h6>Events</h6>
            </div>
            <button type="button" class="btn btn-primary btn-sm add-event" onclick="addEvent(${index})">Add Event</button>

            <button type="button" class="btn btn-danger btn-sm remove-action" onclick="removeAction(${index})">Remove Action</button>
            <hr>
        </div>
    `;
    container.insertAdjacentHTML('beforeend', actionHTML);
}
