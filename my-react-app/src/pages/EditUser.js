import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import "./EditUser.css"; // ✅ Import the CSS file

const BASE_URL = process.env.REACT_APP_API_BASE_URL || "http://127.0.0.1:5000";

const EditUser = () => {
  const [userId, setUserId] = useState("");
  const [userDetails, setUserDetails] = useState({
    name: "",
    email: "",
    password: "",
  });
  const [message, setMessage] = useState("");
  const [messageType, setMessageType] = useState(""); // ✅ Track success/error
  const navigate = useNavigate();

  // Fetch user details based on user ID
  const handleFetchUser = () => {
    if (!userId) {
      setMessage("Please enter a user ID");
      setMessageType("error");
      return;
    }

    axios
      .get(`${BASE_URL}/api/users/${userId}`)
      .then((response) => {
        setUserDetails({
          name: response.data.name,
          email: response.data.email,
          password: "", // Don't prepopulate the password
        });
        setMessage("");
      })
      .catch((err) => {
        setUserDetails({
          name: "",
          email: "",
          password: "",
        });
        setMessage(err.response?.data?.error || "Error fetching user details");
        setMessageType("error");
      });
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setUserDetails((prevDetails) => ({
      ...prevDetails,
      [name]: value,
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    const updatedUser = {
      action: "edit",
      user_type: "user",
      id: userId,
      name: userDetails.name,
      email: userDetails.email,
    };

    // Only include password if it was updated
    if (userDetails.password.trim()) {
      updatedUser.password = userDetails.password;
    }

    axios
      .put(`${BASE_URL}/api/manage_user`, updatedUser)
      .then((response) => {
        setMessage("User updated successfully");
        setMessageType("success");
        setTimeout(() => navigate("/view-user"), 1000); // Redirect after success
      })
      .catch((err) => {
        console.error("Error updating user", err);
        setMessage(err.response?.data?.error || "Failed to update user");
        setMessageType("error");
      });
  };

  return (
    <div className="edit-user-container">
      <div className="edit-user-form">
        <h1>Edit User</h1>

        {/* 🔍 Fetch User Section */}
        <div className="fetch-user-section">
          <input
            type="text"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            placeholder="Enter user ID"
          />
          <button className="edit-user-button" onClick={handleFetchUser}>
            Fetch User
          </button>
        </div>

        {/* ✅ Message Section */}
        {message && <p className={`message ${messageType}`}>{message}</p>}

        {/* 📌 Edit User Form */}
        {userDetails.name && (
          <form onSubmit={handleSubmit}>
            <div>
              <label htmlFor="name">Name</label>
              <input
                type="text"
                id="name"
                name="name"
                value={userDetails.name}
                onChange={handleChange}
                required
              />
            </div>

            <div>
              <label htmlFor="email">Email</label>
              <input
                type="email"
                id="email"
                name="email"
                value={userDetails.email}
                onChange={handleChange}
                required
              />
            </div>

            <div>
              <label htmlFor="password">Password (Leave blank to keep unchanged)</label>
              <input
                type="password"
                id="password"
                name="password"
                value={userDetails.password}
                onChange={handleChange}
              />
            </div>

            <button className="edit-user-button" type="submit">
              Save Changes
            </button>
          </form>
        )}
      </div>
    </div>
  );
};

export default EditUser;
