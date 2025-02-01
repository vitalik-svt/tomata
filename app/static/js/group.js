function viewGroupAssignment(groupId) {

    if (!groupId) {
        alert("Error: groupId is required!");
        return;
    }

    fetch(`/assignment/group/${groupId}/view`, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        },
    })
    .then(response => {
        if (response.ok) {
            window.open(`/assignment/group/${groupId}/view`, '_blank');
        } else {
            alert("Error viewing the assignment");
        }
    })
    .catch(error => {
        alert("Error: " + error);
    });
}


function deleteGroup(groupId) {

    if (!groupId) {
        alert("Error: groupId is required!");
        return;
    }

    const confirmation = confirm("Are you sure you want to delete all this group with all its assignments?");
    if (confirmation) {
        fetch(`/assignment/group/${groupId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            },
        })
        .then(response => {
            if (response.ok) {
                alert("Group with all assignments deleted successfully");
                window.location.href = "/assignment/list";  // Redirect to assignment list page
            } else {
                alert("Error deleting the group");
            }
        })
        .catch(error => {
            alert("Error: " + error);
        });
    };
}

