
function deleteUser(userId) {

    if (!userId) {
        alert("Error: userId is required!");
        return;
    }

    if (confirm("Are you sure you want to delete this user?")) {
        fetch(`/user/delete/${userId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        }).then(response => response.json())
        .then(data => {
            alert(data.message);
            window.location.href = "/user/list";
        });
    }
}

