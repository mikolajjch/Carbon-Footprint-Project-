console.log("working...");
document.getElementById("carbon-form").addEventListener("submit", async (e) => {
    e.preventDefault(); 

    const category = document.getElementById("category").value;
    const activity = document.getElementById("activity").value;
    const value = document.getElementById("value").value;

    console.log("Sending data:", { activity_type: category, choice: activity, value: parseFloat(value) }); 

    try {
        const response = await fetch('/api/emissions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ activity_type: category, choice: activity, value: parseFloat(value) }),
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