import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";

const ResetPassword = () => {
  const { token } = useParams(); // Get token from URL
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    // Validate the token with the backend
    fetch(`http://localhost:5000/api/validate-token/${token}`)
      .then((response) => response.json())
      .then((data) => {
        if (!data.valid) {
          setError("Invalid or expired reset token.");
        }
      })
      .catch(() => {
        setError("An error occurred while validating the token.");
      });
  }, [token]);

  const handleResetPassword = (e) => {
    e.preventDefault();

    fetch("http://localhost:5000/api/reset-password", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ token, password }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          setMessage("Password has been successfully reset.");
          setTimeout(() => navigate("/"), 2000); // Redirect to login after 2 seconds
        } else {
          setError(data.error || "Failed to reset password.");
        }
      })
      .catch(() => {
        setError("An error occurred while resetting the password.");
      });
  };

  return (
    <div>
      <h1>Reset Password</h1>
      {error && <p style={{ color: "red" }}>{error}</p>}
      {message && <p style={{ color: "green" }}>{message}</p>}
      {!error && (
        <form onSubmit={handleResetPassword}>
          <input
            type="password"
            id="new-password" // ✅ Added id
            name="new-password" // ✅ Added name
            placeholder="Enter your new password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <button type="submit">Reset Password</button>
        </form>
      )}
    </div>
  );
};

export default ResetPassword;
