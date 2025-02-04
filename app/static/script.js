const socket = io();

document.getElementById("login-form").addEventListener("submit", async (e) => {
    e.preventDefault();

    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();
        if (response.ok) {
            localStorage.setItem("token", data.token);
            alert("Login successful!");
            location.reload();
        } else {
            throw new Error(data.error || "Login failed");
        }
    } catch (error) {
        console.error("Error:", error);
        alert("Error: " + error.message);
    }
});


document.getElementById("carbon-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const token = localStorage.getItem("token");
    if (!token) {
        alert("Please log in first");
        return;
    }
    const category = document.getElementById("category").value;
    const activity = document.getElementById("activity").value;
    const value = document.getElementById("value").value;
    try {
        const response = await fetch('/api/emissions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ activity_type: category, choice: activity, value: parseFloat(value) })
        });

        console.log("Response status:", response.status);

        if (!response.ok) {
            throw new Error("Failed to calculate emissions. Please try again.");
        }

        const data = await response.json();
        console.log("Response data:", data);

        if (data.activity && data.activity.emission !== undefined) {
            document.getElementById("emission-result").textContent = data.activity.emission.toFixed(2);
            loadUserActivities(); 
        } else {
            console.error("Invalid response format:", data);
            alert("Error: Invalid response from server.");
        }
    } catch (error) {
        console.error("Error:", error);
        alert("Error: " + error.message);
    }
});

document.getElementById("logout-btn").addEventListener("click", () => {
    localStorage.removeItem("token");
    alert("Logged out successfully");
    location.reload();
});

//////////////////////////////////// klient aktywnosc dla uzytkownikow i admina osobne panele
async function loadUserActivities() {
    const token = localStorage.getItem("token");
    if (!token) return;

    try {
        const response = await fetch('/api/emissions', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        const data = await response.json();
        const activities = data.daily_activities;
        const tableBody = document.querySelector("#activities-table tbody");
        tableBody.innerHTML = activities.map((activity, index) => `
            <tr>
                <td>${index}</td>
                <td>${activity.date}</td>
                <td>${activity.activity_type}</td>
                <td>${activity.choice}</td>
                <td>${activity.value}</td>
                <td>${activity.emission}</td>
                <td><button onclick="deleteActivity(${index})">Delete</button></td>
            </tr>
        `).join("");
    } catch (error) {
        console.error("Error loading activities:", error);
    }
}

async function loadAllActivities() {
    const token = localStorage.getItem("token");
    if (!token) return;

    try {
        const response = await fetch('/api/emissions', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        const data = await response.json();
        const activities = data.daily_activities;
        const tableBody = document.querySelector("#all-activities-table tbody");
        tableBody.innerHTML = activities.map((activity, index) => `
            <tr>
                <td>${index}</td>
                <td>${activity.date}</td>
                <td>${activity.activity_type}</td>
                <td>${activity.choice}</td>
                <td>${activity.value}</td>
                <td>${activity.emission}</td>
                <td><button onclick="deleteActivity(${index})">Delete</button></td>
            </tr>
        `).join("");
    } catch (error) {
        console.error("Error loading all activities:", error);
    }
}

async function deleteActivity(activityId) {
    const token = localStorage.getItem("token");
    if (!token) return;

    try {
        const response = await fetch(`/api/emissions/${activityId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (response.ok) {
            alert("Activity deleted successfully!");
            loadUserActivities(); 
            if (document.getElementById("admin-panel").style.display === "block") {
                loadAllActivities(); 
            }
        } else {
            throw new Error("Failed to delete activity");
        }
    } catch (error) {
        console.error("Error deleting activity:", error);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const token = localStorage.getItem("token");
    if (token) {
        const decodedToken = JSON.parse(atob(token.split('.')[1]));
        document.getElementById("login-form").style.display = "none";
        document.getElementById("carbon-form").style.display = "block";
        document.getElementById("logout-btn").style.display = "block";

        if (decodedToken.role === "admin") {
            document.getElementById("admin-panel").style.display = "block";
            loadAllActivities();
        } else {
            document.getElementById("user-panel").style.display = "block";
            loadUserActivities();
        }
    }
});

socket.on("update_visit_count", (data) => {
    document.getElementById("visit-count").textContent = data.count;
    document.getElementById("active-users").textContent = data.active_users;
});
//////////////////////////////////////


