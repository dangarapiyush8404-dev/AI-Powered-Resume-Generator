let token = "";

async function login() {
    const res = await fetch("http://127.0.0.1:5000/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            email: document.getElementById("email").value,
            password: document.getElementById("password").value,
        }),
    });

    const data = await res.json();

    if (data.access_token) {
        token = data.access_token;
        document.getElementById("auth-box").style.display = "none";
        document.getElementById("profile-box").style.display = "block";
    } else {
        alert("Login failed");
    }
}

async function registerDemo() {
    await fetch("http://127.0.0.1:5000/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            name: "Demo User",
            email: "demo@gmail.com",
            password: "1234",
            role: "Student",
        }),
    });

    alert("Demo User Created! Now login.");
}

async function updateProfile() {
    const res = await fetch("http://127.0.0.1:5000/api/student/profile", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            Authorization: "Bearer " + token,
        },
        body: JSON.stringify({
            phone: document.getElementById("phone").value,
            degree: document.getElementById("degree").value,
            branch: document.getElementById("branch").value,
            cgpa: document.getElementById("cgpa").value,
            skills: document.getElementById("skills").value,
        }),
    });

    const data = await res.json();
    document.getElementById("domain-result").innerText =
        "Predicted Domain: " + data.domain;
}