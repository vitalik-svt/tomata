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
    // Получаем данные из JSON Editor
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

//
// function printAssignment() {
//     const data = editor.getValue();
//
//     console.log(JSON.stringify(data));
//
//     fetch("/print", {
//         method: "POST",  // Use POST method
//         headers: {
//             "Content-Type": "application/json"
//         },
//         body: JSON.stringify(data)
//     })
//     .then(response => {
//         if (response.ok) {
//             return response.text();  // Получаем ответ от сервера
//         } else {
//             alert("Error printing the assignment");
//         }
//     })
//     .then(responseText => {
//         console.log("Backend response: ", responseText);
//         window.location.href = '/print';
//     })
//     .catch(error => {
//             alert("Error: " + error);
//     });
// }


function printAssignment() {
    const data = editor.getValue();  // Получаем данные из редактора

    console.log("Sending data:", JSON.stringify(data));

    fetch("/print", {
        method: "POST",  // Используем метод POST
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data)  // Отправляем данные в теле запроса
    })
    .then(response => {
        if (response.ok) {
            return response.text();  // Получаем HTML-ответ от сервера
        } else {
            alert("Error printing the assignment");
        }
    })
    .then(responseText => {
        console.log("Backend response:", responseText);

        // Здесь ты можешь сделать что-то с HTML, например, открыть его в новом окне
        const printWindow = window.open();
        printWindow.document.write(responseText);  // Пишем HTML в новое окно
        printWindow.document.close();  // Закрываем документ для рендеринга
    })
    .catch(error => {
        alert("Error: " + error);
    });
}


