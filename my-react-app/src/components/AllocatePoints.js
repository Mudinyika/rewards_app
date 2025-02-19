import React, { useState } from 'react';

const AllocatePoints = () => {
    const [userId, setUserId] = useState('');
    const [points, setPoints] = useState('');
    const [transactionType, setTransactionType] = useState('add');  // 'add' or 'remove'

    const handleSubmit = (e) => {
        e.preventDefault();

        // POST request to allocate points (add or remove)
        fetch('http://127.0.0.1:5000/api/allocate-points', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ user_id: userId, points, transaction_type: transactionType })
        })
            .then(response => response.json())
            .then(data => alert(data.message || 'Points updated'))
            .catch(error => console.error('Error:', error));
    };

    return (
        <div>
            <h3>Allocate Points</h3>
            <form onSubmit={handleSubmit}>
                <div>
                    <label>User ID:</label>
                    <input
                        type="number"
                        value={userId}
                        onChange={(e) => setUserId(e.target.value)}
                        required
                    />
                </div>
                <div>
                    <label>Points:</label>
                    <input
                        type="number"
                        value={points}
                        onChange={(e) => setPoints(e.target.value)}
                        required
                    />
                </div>
                <div>
                    <label>Transaction Type:</label>
                    <select value={transactionType} onChange={(e) => setTransactionType(e.target.value)}>
                        <option value="add">Add Points</option>
                        <option value="remove">Remove Points</option>
                    </select>
                </div>
                <button type="submit">Allocate Points</button>
            </form>
        </div>
    );
};

export default AllocatePoints;
