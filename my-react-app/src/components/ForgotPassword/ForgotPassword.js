import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

const ForgotPassword = () => {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleForgotPassword = (e) => {
    e.preventDefault();
  
    fetch("http://localhost:5000/api/forgot-password", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          setMessage("Check your email for the reset link!");
          setTimeout(() => {
            navigate("/welcome"); // Redirect to Welcome page after success
          }, 2000);
        } else {
          setError(data.error || "Failed to send reset link.");
        }
      })
      .catch((err) => {
        setError("An error occurred: " + err.message);
      });
  };

  const handleCancel = () => {
    navigate("/welcome"); // Navigate to the Welcome page if user clicks Cancel
  };

  return (
    <div className="forgot-password-container">
      <h1>Forgot Password</h1>
      {message && <p>{message}</p>}
      {error && <p>{error}</p>}
      <form onSubmit={handleForgotPassword}>
        <input
          type="email"
          placeholder="Enter your email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <button type="submit">Request Reset Link</button>
      </form>
      <button onClick={handleCancel}>Cancel</button> {/* Cancel button */}
    </div>
  );
};

export default ForgotPassword;
