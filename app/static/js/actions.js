function saveExistingAssignment(assignmentId) {
    // Получаем данные из JSON Editor
    const data = editor.getValue();

    fetch(`/assignment/${assignmentId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (response.ok) {
            alert("Assignment saved successfully!");
            window.location.href = `/assignment/${assignmentId}`;  // Redirect to the same assignment page
        } else {
            alert("Error saving assignment!");
        }
    })
    .catch(error => alert("Error: " + error));
}

function createNewAssignment() {
    const data = editor.getValue();

    fetch(`/assignment/new`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (response.ok) {
            response.json().then(data => {
                alert("New assignment created successfully!");
                // Redirect to the new assignment page using the returned ID
                window.location.href = `/assignment/${data.id}`;
            });
        } else {
            alert("Error creating assignment!");
        }
    })
    .catch(error => alert("Error: " + error));
}

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


function printAssignment(assignmentId) {
    const confirmation = confirm("Last saved version will be printed. Make sure you saved progress!");
    if (confirmation) {
        fetch(`/assignment/${assignmentId}/print`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        })
        .then(response => {
            if (response.ok) {
                window.open(`/assignment/${assignmentId}/print`, '_blank');
            } else {
                alert("Error printing the assignment");
            }
        })
        .catch(error => {
            alert("Error: " + error);
        });
    };
}


