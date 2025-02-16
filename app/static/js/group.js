function viewGroupAssignment(groupId) {

    if (!groupId) {
        alert("Error: groupId is required!");
        return;
    }

    document.getElementById("loading-spinner").style.display = "block";
    redirectWhenReady(`/assignment/group/${groupId}/view`, true);
}


function deleteGroup(groupId) {

    if (!groupId) {
        alert("Error: groupId is required!");
        return;
    }

    const confirmation = confirm("Are you sure you want to delete all this group with all its assignments?");
    if (confirmation) {
        document.getElementById("loading-spinner").style.display = "block";
        fetch(`/assignment/group/${groupId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            },
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            window.location.href = "/assignment/list";
        })
        .catch(error => {
            alert("Error: " + error);
        });
    };
}

