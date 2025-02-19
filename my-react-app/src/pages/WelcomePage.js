import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "./WelcomePage.css"; // ✅ Import the CSS file

const WelcomePage = ({ setLoggedIn }) => {
    console.log("✅ WelcomePage is rendering...");

    const [role, setRole] = useState("super");
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [errorMessage, setErrorMessage] = useState("");
    const navigate = useNavigate();

    // ✅ Check login status on page load
    useEffect(() => {
        console.log("🔍 Checking login status...");
        const apiUrl = window.location.origin.replace("/admin", "") + "/api/check-login";
        console.log("🔍 Checking login status at:", apiUrl);

        fetch(apiUrl, { method: "GET", credentials: "include" })
            .then((res) => res.json())
            .then((data) => {
                console.log("🔍 Auto Login Check Response:", data);
                if (data.success) {
                    if (data.user_type === "admin") {
                        console.log("✅ Admin logged in. Redirecting to Dashboard...");
                        setLoggedIn(true);
                        navigate("/dashboard"); // Redirect admins
                    } else {
                        console.log("⚠️ Till Operator detected. Redirecting to Flask...");
                        window.location.href = "/allocate"; // Redirect till operators
                    }
                }
            })
            .catch((err) => console.error("❌ Error checking login:", err));
    }, [setLoggedIn, navigate]);

    // ✅ Handle Login Submission
    const handleLogin = async (e) => {
        e.preventDefault();
        setErrorMessage("");
        console.log("🛠️ Attempting Login...");

        try {
            const apiUrl = window.location.origin.replace("/admin", "") + "/api/admin-login";
            console.log("🔍 Sending login request to:", apiUrl);

            const response = await fetch(apiUrl, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                credentials: "include",
                body: JSON.stringify({ username, password, role }),
            });

            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`);
            }

            const data = await response.json();
            console.log("🔍 Login Response:", data);

            if (data.success) {
                console.log("✅ Login successful! Storing session...");
                localStorage.setItem("loggedIn", "true");
                localStorage.setItem("role", data.role);
                setLoggedIn(true);

                // ✅ Re-check session after login
                setTimeout(async () => {
                    const checkUrl = window.location.origin.replace("/admin", "") + "/api/check-login";
                    console.log("🔍 Re-checking login status at:", checkUrl);

                    const checkResponse = await fetch(checkUrl, { method: "GET", credentials: "include" });
                    const checkData = await checkResponse.json();
                    console.log("🔍 After Login - Check Login Status:", checkData);

                    if (checkData.success) {
                        if (checkData.user_type === "admin") {
                            console.log("✅ Admin session confirmed. Redirecting...");
                            navigate("/dashboard"); // Redirect admins
                        } else {
                            console.log("⚠️ Till Operator detected after login. Ignoring in React.");
                        }
                    } else {
                        setErrorMessage("Login successful, but session not detected.");
                    }
                }, 500);
            } else {
                setErrorMessage(data.error || "Login failed.");
            }
        } catch (error) {
            console.error("❌ Login Error:", error);
            setErrorMessage("An error occurred: " + error.message);
        }
    };

    return (
        <div className="welcome-container">
            <h1>Welcome to the System</h1>
            {errorMessage && <p className="error-message">{errorMessage}</p>}
            <form onSubmit={handleLogin}>
                <input
                    type="text"
                    placeholder="Username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                />
                <input
                    type="password"
                    placeholder="Password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                />
                <button type="submit">Login</button>
            </form>
        </div>
    );
};

export default WelcomePage;
