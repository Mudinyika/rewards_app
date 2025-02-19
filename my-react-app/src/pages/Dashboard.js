import React, { useEffect, useState } from 'react';
import "../styles/Dashboard.css"; // Import the Dashboard CSS

const Dashboard = () => {
  const [metrics, setMetrics] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Fetch the metrics data from the backend
    fetch('http://localhost:5000/api/metrics')
      .then(response => response.json())
      .then(data => {
        if (data.error) {
          setError(data.error);  // Set error if any
        } else {
          setMetrics(data);  // Set the metrics data
        }
      })
      .catch(err => {
        setError("Failed to fetch metrics: " + err.message);  // Handle network or other errors
      });
  }, []); // Empty dependency array means this runs once on component mount

  // If there's an error, display it
  if (error) {
    return <div className="error">Error: {error}</div>;
  }

  // If the data is still loading, show a loading message
  if (!metrics) {
    return <div className="loading">Loading...</div>;
  }

  // If the data is ready, render the metrics
  return (
    <div className="dashboard-container">
      <h2>Dashboard Metrics</h2>
      <ul>
        <li>
          <span>Total Users:</span> {metrics.total_users}
        </li>
        <li>
          <span>Till Operators:</span> {metrics.till_operator_count}
        </li>
        <li>
          <span>Admins:</span> {metrics.admin_count}
        </li>
        <li>
          <span>Superusers:</span> {metrics.superuser_count}
        </li>
        <li>
          <span>Total Points Added This Month:</span> {metrics.total_added_points}
        </li>
        <li>
          <span>Total Points Removed This Month:</span> {metrics.total_removed_points}
        </li>
        <li>
          <span>New Users This Month:</span> {metrics.new_users_this_month}
        </li>
      </ul>
    </div>
  );
};

export default Dashboard;
