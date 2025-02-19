import React, { useState, useEffect } from "react";
import axios from "axios";
import "./ViewUser.css"; // ✅ Import CSS

const BASE_URL = process.env.REACT_APP_API_BASE_URL || "http://127.0.0.1:5000";

const ViewUser = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [userDetails, setUserDetails] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  // ✅ Fetch users dynamically based on input
  useEffect(() => {
    if (searchQuery.trim() === "" || selectedUser) {
      setSearchResults([]); // Clears results if no input or user is selected
      return;
    }

    const delaySearch = setTimeout(() => {
      fetchUsers();
    }, 500); // ✅ Debounced API Call

    return () => clearTimeout(delaySearch);
  }, [searchQuery, selectedUser]);

  // ✅ Fetch Users API Call
  const fetchUsers = async () => {
    try {
      setLoading(true);
      const response = await axios.get(
        `${BASE_URL}/api/search-users?query=${searchQuery}&limit=10`
      ); // ✅ Limits to 10 results
      setSearchResults(response.data.users);
      setLoading(false);
    } catch (error) {
      setError("Error fetching search results.");
      setLoading(false);
    }
  };

  // ✅ Handle User Selection & Hide Search Results
  const handleUserSelect = async (userId) => {
    try {
      setLoading(true);
      const response = await axios.get(`${BASE_URL}/api/users/${userId}`);
      setUserDetails(response.data);
      setSelectedUser(userId);
      setSearchResults([]); // ✅ Clear search results after selection
      setLoading(false);
    } catch (error) {
      setError("Error fetching user details.");
      setLoading(false);
    }
  };

  // ✅ Reset View - Allows user to search again
  const resetView = () => {
    setSelectedUser(null);
    setUserDetails(null);
    setSearchQuery(""); // Clears input field
  };

  return (
    <div className="view-user-container">
      {/* ✅ Left Column (Search) */}
      <div className="search-container">
        <h2>Search Users</h2>
        <input
          type="text"
          placeholder="Search by user ID or name"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          disabled={selectedUser} // ✅ Disables input when a user is selected
        />
        {loading && <p>Loading...</p>}
        {selectedUser && (
          <button className="reset-button" onClick={resetView}>
            🔄 Reset Search
          </button>
        )}
      </div>

      {/* ✅ Right Column (Results & Details) */}
      <div className="results-container">
        {error && <p className="error">{error}</p>}

        {/* 🔹 Show Search Results Only If No User Selected */}
        {!selectedUser && searchResults.length > 0 && (
          <div className="search-results">
            <h3>Search Results:</h3>
            <ul>
              {searchResults.map((user) => (
                <li key={user.id}>
                  <button onClick={() => handleUserSelect(user.id)}>
                    {user.name} (ID: {user.id})
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* 🔹 Display Selected User Details */}
        {userDetails && (
          <div className="user-details">
            <h3>User Details:</h3>
            <p>
              <strong>Name:</strong> {userDetails.name}
            </p>
            <p>
              <strong>Points:</strong> {userDetails.points}
            </p>
            <p>
              <strong>Last Transaction:</strong>{" "}
              {userDetails.last_transaction || "No transactions found"}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ViewUser;
