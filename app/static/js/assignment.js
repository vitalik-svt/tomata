
function editAssignment(assignmentId) {
    redirectWhenReady(`/assignment/${assignmentId}`);
}


function saveExistingAssignment(assignmentId) {

    if (!assignmentId) {
        alert("Error: assignmentId is required!");
        return;
    }

    document.getElementById("loading-spinner").style.display = "block"; // show spinner
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
            redirectWhenReady(`/assignment/${assignmentId}`);  // Redirect to the same assignment page
            alert("Assignment saved successfully! You will be redirected to page with updated data.");
        } else {
            alert("Error saving assignment!");
        }
    })
    .catch(error => alert("Error: " + error));
}


function createNewAssignment() {

    fetch(`/assignment/new`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (response.ok) {
            response.json().then(data => {
                window.location.href = `/assignment/${data.id}`;
            });
        } else {
            alert("Error creating assignment!");
        }
    })
    .catch(error => alert("Error: " + error));
}


function createNewVersion(assignmentId) {

    if (!assignmentId) {
        alert("Error: assignmentId is required!");
        return;
    }

    fetch(`/fork_modal`)  // Загружаем HTML модального окна
        .then(response => response.text())
        .then(html => {
            document.body.insertAdjacentHTML('beforeend', html);
            // Сохраняем ID задания в модальном окне (чтобы использовать при подтверждении)
            document.getElementById('confirmationModal').dataset.assignmentId = assignmentId;
        });
}


// Подтверждение создания новой версии
function confirmNewVersion() {
    const modal = document.getElementById('confirmationModal');
    const assignmentId = modal.dataset.assignmentId;
    const useNewSchema = document.getElementById('useNewSchema').checked;

    console.log("Collected assignmentId:", assignmentId);
    console.log("Collected useNewSchema:", useNewSchema);

    closeModal();
    document.getElementById("loading-spinner").style.display = "block";

    fetch(`/assignment/${assignmentId}/create_new_version?use_new_schema=${useNewSchema}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .catch(error => alert("Error: " + error))
    .then(response => response.json())
    .then(data => {
        redirectWhenReady(`/assignment/${data.id}`);
    });
    ;
}


function closeModal() {
    const modal = document.getElementById('confirmationModal');
    if (modal) {
        modal.style.transition = 'opacity 0.1s ease-out';
        modal.style.opacity = '0';
        setTimeout(() => {
            modal.remove();
        }, 100);
    }
}


function deleteAssignment(assignmentId) {

    if (!assignmentId) {
        alert("Error: assignmentId is required!");
        return;
    }

    const confirmation = confirm("Are you sure you want to delete this assignment?");
    if (confirmation) {
        document.getElementById("loading-spinner").style.display = "block";
        fetch(`/assignment/${assignmentId}`, {
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


function viewAssignment(assignmentId) {

    if (!assignmentId) {
        alert("Error: assignmentId is required!");
        return;
    }

    const confirmation = confirm("Last saved version will be viewed. Make sure you saved progress!");
    if (confirmation) {
        document.getElementById("loading-spinner").style.display = "block";
        redirectWhenReady(`/assignment/${assignmentId}/view`, true);
    }
}

