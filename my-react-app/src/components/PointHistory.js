import React, { useEffect, useState } from 'react';

const PointHistory = () => {
    const [pointHistory, setPointHistory] = useState([]);

    useEffect(() => {
        // GET request to fetch point history
        fetch('http://127.0.0.1:5000/api/point-history')
            .then(response => response.json())
            .then(data => setPointHistory(data.point_history || []))
            .catch(error => console.error('Error:', error));
    }, []);

    return (
        <div>
            <h3>Point History</h3>
            <table>
                <thead>
                    <tr>
                        <th>User ID</th>
                        <th>Points</th>
                        <th>Transaction Type</th>
                        <th>Timestamp</th>
                    </tr>
                </thead>
                <tbody>
                    {pointHistory.map((transaction, index) => (
                        <tr key={index}>
                            <td>{transaction.user_id}</td>
                            <td>{transaction.points}</td>
                            <td>{transaction.transaction_type}</td>
                            <td>{new Date(transaction.timestamp).toLocaleString()}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default PointHistory;
