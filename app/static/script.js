console.log("working...");

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

    console.log("Sending data:", { activity_type: category, choice: activity, value: parseFloat(value) });

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

document.addEventListener("DOMContentLoaded", () => {
    const token = localStorage.getItem("token");
    if (token) {
        document.getElementById("login-form").style.display = "none";
        document.getElementById("carbon-form").style.display = "block";
        document.getElementById("logout-btn").style.display = "block";
    }
});
