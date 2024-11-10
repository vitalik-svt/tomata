
function saveExistingAssignment(assignmentId) {
    const formData = new FormData(document.getElementById("assignment-form"));
    const data = Object.fromEntries(formData);

    fetch(`/assignment/${assignmentId}`, {  // Use the assignmentId variable here
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    }).then(response => {
        if (response.ok) {
            alert("Assignment saved successfully!");
            window.location.href = `/assignment/${assignmentId}`;  // Redirect to the same assignment page
        } else {
            alert("Error saving assignment!");
        }
    }).catch(error => alert("Error: " + error));
}


function createNewAssignment() {
    const formData = new FormData(document.getElementById("assignment-form"));
    const data = Object.fromEntries(formData);

    fetch(`/assignment/new`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    }).then(response => {
        if (response.ok) {
            response.json().then(data => {
                alert("New assignment created successfully!");
                // Redirect to the new assignment page using the returned ID
                window.location.href = `/assignment/${data.id}`;
            });
        } else {
            alert("Error creating assignment!");
        }
    }).catch(error => alert("Error: " + error));
}


// Unified delete function
function deleteAssignment(assignmentId) {
    const confirmation = confirm("Are you sure you want to delete this assignment?");
    if (confirmation) {
        fetch(`/assignment/${assignmentId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            },
        })
        .then(response => {
            if (response.ok) {
                alert("Assignment deleted successfully");
                window.location.href = "/assignments";  // Redirect to assignments list page
            } else {
                alert("Error deleting the assignment");
            }
        })
        .catch(error => {
            alert("Error: " + error);
        });
    }
}

// Print function (currently just prints the page)
function printAssignment(id) {
    window.print();
}