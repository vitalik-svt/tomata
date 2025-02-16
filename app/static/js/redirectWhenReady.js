async function redirectWhenReady(checkUrl, newTab = false) {

    document.getElementById("loading-spinner").style.display = "block";

    try {
        const response = await fetch(checkUrl);
        if (response.ok) {
            // Если открываем в текущем окне
            if (!newTab) {
                window.addEventListener("beforeunload", () => {
                    document.getElementById("loading-spinner").style.display = "block";
                });
                window.location.href = checkUrl;
            } else {
                window.open(checkUrl, '_blank');
                setTimeout(() => {
                    document.getElementById("loading-spinner").style.display = "none";
                }, 2000); // Отключаем спиннер через 2 секунды в старом окне
            }
        } else {
            setTimeout(() => redirectWhenReady(checkUrl, newTab), 1000);
        }
    } catch (error) {
        console.error("Error on checking readiness:", error);
        setTimeout(() => redirectWhenReady(checkUrl, newTab), 1000);
    }
}

// Убираем спиннер, когда новая страница загрузилась
window.addEventListener("load", () => {
    document.getElementById("loading-spinner").style.display = "none";
});
