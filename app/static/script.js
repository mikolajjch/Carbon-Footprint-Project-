console.log("working...");
document.getElementById("carbon-form").addEventListener("submit", async (e) => {
    e.preventDefault();

    const category = document.getElementById("category").value;
    const activity = document.getElementById("activity").value;
    const value = document.getElementById("value").value;

    try {
        const response = await fetch('/api/emissions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ activity_type: category, choice: activity, value: parseFloat(value) }),
        });

        if (!response.ok) {
            throw new Error("Failed to calculate emissions. Please try again.");
        }

        const data = await response.json();
        document.getElementById("emission-result").textContent = data.activity.emission.toFixed(2);
    } catch (error) {
        alert("Error: " + error.message);
    }
});
