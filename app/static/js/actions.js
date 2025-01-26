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
                window.location.href = "/assignment/list";  // Redirect to assignment list page
            } else {
                alert("Error deleting the assignment");
            }
        })
        .catch(error => {
            alert("Error: " + error);
        });
    };
}

function viewAssignment(assignmentId) {
    const confirmation = confirm("Last saved version will be viewed. Make sure you saved progress!");
    if (confirmation) {
        fetch(`/assignment/${assignmentId}/view`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        })
        .then(response => {
            if (response.ok) {
                window.open(`/assignment/${assignmentId}/view`, '_blank');
            } else {
                alert("Error viewing the assignment");
            }
        })
        .catch(error => {
            alert("Error: " + error);
        });
    }
}

function deleteUser(userId) {
        if (confirm("Are you sure you want to delete this user?")) {
            fetch(`/user/delete/${userId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            }).then(response => {
                if (response.ok) {
                    alert('User deleted successfully');
                    location.reload();  // Reload the page to reflect the changes
                } else {
                    alert('Failed to delete user');
                }
            });
        }
    }