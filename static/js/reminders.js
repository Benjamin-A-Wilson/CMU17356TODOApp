const enableButton = document.getElementById("enable-reminders");
const dueTodayData = document.getElementById("due-today-data");

function getDueTodayTasks() {
    if (!dueTodayData) {
        return [];
    }
    return JSON.parse(dueTodayData.textContent);
}

function showMorningReminder(tasks) {
    if (!("Notification" in window)) {
        return;
    }
    if (Notification.permission !== "granted") {
        return;
    }

    const now = new Date();
    const hour = now.getHours();
    const dateKey = now.toISOString().slice(0, 10);
    const shownForDay = localStorage.getItem("lastReminderDate");

    if (hour < 5 || shownForDay === dateKey) {
        return;
    }

    const count = tasks.length;
    const body = count > 0
        ? `You have ${count} task(s) due today.`
        : "No tasks due today. Keep up the good work.";

    new Notification("CMU TODO Morning Reminder", { body });
    localStorage.setItem("lastReminderDate", dateKey);
}

if (enableButton) {
    enableButton.addEventListener("click", async () => {
        if (!("Notification" in window)) {
            alert("Your browser does not support notifications.");
            return;
        }

        const permission = await Notification.requestPermission();
        if (permission === "granted") {
            alert("Morning reminders are enabled.");
            showMorningReminder(getDueTodayTasks());
            return;
        }

        alert("Notification permission was not granted.");
    });
}

if (dueTodayData) {
    showMorningReminder(getDueTodayTasks());
}
