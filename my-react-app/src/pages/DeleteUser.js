import React, { useState } from 'react';
import axios from 'axios';

const DeleteUser = () => {
  const [userId, setUserId] = useState('');
  const [userDetails, setUserDetails] = useState(null);
  const [error, setError] = useState('');
  const [superuserPassword, setSuperuserPassword] = useState('');
  const [isConfirming, setIsConfirming] = useState(false);

  // Fetch User Details
  const fetchUser = () => {
    axios.get(`http://127.0.0.1:5000/api/users/${userId}`)
      .then(response => {
        setUserDetails(response.data);
        setError('');
      })
      .catch(err => {
        setUserDetails(null);
        setError('User not found or error fetching details');
      });
  };

  // Delete User
  const deleteUser = () => {
    axios.delete(`http://127.0.0.1:5000/api/users/${userId}`, {
      data: { superuser_password: superuserPassword }
    })
    .then(() => {
      alert('User deleted successfully');
      setUserDetails(null);
      setUserId('');
      setIsConfirming(false);
    })
    .catch(err => {
      alert(err.response?.data?.error || 'Failed to delete user');
    });
  };

  return (
    <div>
      <h1>Delete User</h1>

      <div>
        <label>User ID:</label>
        <input
          type="text"
          value={userId}
          onChange={(e) => setUserId(e.target.value)}
        />
        <button onClick={fetchUser}>Fetch User</button>
      </div>

      {error && <p style={{ color: 'red' }}>{error}</p>}

      {userDetails && (
        <div>
          <h2>User Details</h2>
          <p><strong>Name:</strong> {userDetails.name}</p>
          <p><strong>Email:</strong> {userDetails.email}</p>
          <p><strong>Created At:</strong> {userDetails.created_at}</p>
          <p><strong>Points:</strong> {userDetails.points}</p>

          <button onClick={() => setIsConfirming(true)}>Delete User</button>
        </div>
      )}

      {isConfirming && (
        <div className="modal">
          <h3>Confirm Deletion</h3>
          <p>Are you sure you want to delete this user? This action cannot be undone.</p>
          <label>Enter Superuser Password:</label>
          <input
            type="password"
            value={superuserPassword}
            onChange={(e) => setSuperuserPassword(e.target.value)}
          />
          <button onClick={deleteUser}>Confirm</button>
          <button onClick={() => setIsConfirming(false)}>Cancel</button>
        </div>
      )}
    </div>
  );
};

export default DeleteUser;
