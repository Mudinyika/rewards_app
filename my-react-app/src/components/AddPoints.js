import React, { useState } from 'react';

function AddPoints() {
  const [userId, setUserId] = useState('');
  const [points, setPoints] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    fetch('http://127.0.0.1:5000/api/points', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, points: parseInt(points) }),
    })
      .then((response) => response.json())
      .then((data) => alert('Points added successfully!'))
      .catch((error) => console.error('Error adding points:', error));
  };

  return (
    <div>
      <h2>Add Points</h2>
      <form onSubmit={handleSubmit}>
        <label>
          User ID:
          <input
            type="text"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            required
          />
        </label>
        <label>
          Points:
          <input
            type="number"
            value={points}
            onChange={(e) => setPoints(e.target.value)}
            required
          />
        </label>
        <button type="submit">Add Points</button>
      </form>
    </div>
  );
}

export default AddPoints;
