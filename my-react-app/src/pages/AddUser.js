import React, { useState } from 'react';
import axios from 'axios';
import "./AddUser.css"; // ✅ Import the CSS file

const BASE_URL = process.env.REACT_APP_API_BASE_URL || "http://127.0.0.1:5000";

const AddUser = () => {
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [password, setPassword] = useState('');
  const [adminKey, setAdminKey] = useState('');
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState(""); // ✅ New state for styling

  const handleAddUser = async () => {
    try {
      const response = await axios.post(`${BASE_URL}/api/manage_user`, {
        action: "add",  // Required action
        user_type: "user",  // Specify this is a regular user
        email,
        name,
        password,
        admin_key: adminKey,
      });
      setMessage(response.data.message);
      setMessageType("success"); // ✅ Set message type to success
      setEmail('');
      setName('');
      setPassword('');
      setAdminKey('');
    } catch (error) {
      setMessage(error.response?.data?.error || 'Error adding user');
      setMessageType("error"); // ✅ Set message type to error
    }
  };

  return (
<div className="add-user-container">
      <div className="add-user-form">
        <h1>Add User</h1>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Enter user email"
        />
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Enter user name"
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Enter user password"
        />
        <input
          type="text"
          value={adminKey}
          onChange={(e) => setAdminKey(e.target.value)}
          placeholder="Enter admin key"
        />
        <button className="add-user-button" onClick={handleAddUser}>
          Add User
        </button>

        {/* ✅ Message Section */}
        {message && <p className={`message ${messageType}`}>{message}</p>}
      </div>
    </div>
  );
};

export default AddUser;
