
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

