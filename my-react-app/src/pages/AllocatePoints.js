import React, { useState, useEffect } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import axios from "axios";
import "./AllocatePoints.css"; // ✅ Import the CSS file

console.log("✅ API Base URL:", process.env.REACT_APP_API_BASE_URL);


const BASE_URL = process.env.REACT_APP_API_BASE_URL || "http://127.0.0.1:5000";

const AllocatePoints = () => {
  const [userId, setUserId] = useState("");
  const [points, setPoints] = useState("");
  const [adminKey, setAdminKey] = useState("");
  const [transactionType, setTransactionType] = useState("add");
  const [tillNumber, setTillNumber] = useState("");
  const [operatorName, setOperatorName] = useState("");
  const [role, setRole] = useState("");
  const [userInfo, setUserInfo] = useState({
    name: "N/A",
    totalPoints: "N/A",
    lastTransaction: "N/A",
  });
  const availableTills = ["001", "002", "003", "004", "005"];

  const [showModal, setShowModal] = useState(false);
  const [modalMessage, setModalMessage] = useState("");


  useEffect(() => {
    fetchOperatorInfo();
  }, []);

  const fetchOperatorInfo = async () => {
    try {
      const response = await axios.get(`${BASE_URL}/api/operator_info`, {
        withCredentials: true, // ✅ Ensures session cookies are sent
      });

      setOperatorName(response.data.operator_name || "N/A");
      setRole(response.data.role);
      setTillNumber(response.data.till_number || "");
    } catch (error) {
      console.error("Error fetching operator info:", error.response || error);
    }
  };

  const fetchUserDetails = async () => {
    if (!userId) return;
    try {
      const response = await axios.get(`${BASE_URL}/api/users/${userId}`, {
        withCredentials: true, // ✅ Ensures session authentication
      });

      setUserInfo({
        name: response.data.name,
        totalPoints: response.data.points,
        lastTransaction: response.data.last_transaction || "N/A",
      });
    } catch (error) {
      console.error("Error fetching user details:", error.response || error);
      resetUserInfo();
    }
  };

  const resetUserInfo = () => {
    setUserInfo({ name: "N/A", totalPoints: "N/A", lastTransaction: "N/A" });
  };

  const allocatePoints = async () => {
    if (!userId || !points || !adminKey || (!tillNumber && role !== "till_operator")) {
      alert("Please enter all required fields.");
      return;
    }

    const parsedPoints = parseFloat(points);
    const availablePoints = parseFloat(userInfo.totalPoints); // ✅ Get from DB

    // ✅ Restriction: Prevent removing more points than available
    if (transactionType === "remove" && parsedPoints > availablePoints) {
      setModalMessage(`❌ Error: Cannot remove more points than the user has (${availablePoints} points available).`);
      setShowModal(true);
      return;
    }
  
    try {
      const payload = {
        user_id: userId,
        points: parseFloat(points).toFixed(2),  // ✅ Ensures two decimal places (e.g., 1.50)
        admin_key: adminKey,
        transaction_type: transactionType,
        till_number: tillNumber,
        allocated_by: operatorName || "Admin",
      };

      console.log("🔍 Sending Payload:", payload);  // ✅ Debug log
  
      const response = await axios.post("/api/allocate-points", payload, {
        headers: { "Content-Type": "application/json" },
        withCredentials: true,  // ✅ Ensures cookies (session) are sent
      });

      // ✅ Calculate the new balance based on transaction type
      const availablePoints = parseFloat(userInfo.totalPoints);
      const pointsChange = parseFloat(points);
      const newBalance = transactionType === "add" 
        ? availablePoints + pointsChange 
        : availablePoints - pointsChange;
    
      
      // ✅ Set modal message dynamically
      setModalMessage(
        transactionType === "add"
          ? `✅ Points Added! \n\nAmount: ${points} \nNew Balance: ${newBalance.toFixed(2)}`
          : `❌ Points Removed! \n\nAmount: ${points} \nRemaining Balance: ${newBalance.toFixed(2)}`
      );


      setShowModal(true);

      // Reset Fields
      setUserId("");
      setPoints("");
      setAdminKey("");
      resetUserInfo();
    } catch (error) {
      console.error("❌ Error allocating points:", error.response || error);
      setModalMessage(`❌ Error: ${error.response?.data?.error || "Failed to allocate points"}`);
      setShowModal(true);
    }
  };
  
  return (
    <div className="container">
      <h1>Point Allocation System</h1>
      
      {role !== "till_operator" && (
        <div className="form-group">
          <label>Select Till Number</label>
          <select value={tillNumber} onChange={(e) => setTillNumber(e.target.value)}>
            <option value="">Select Till</option>
            {availableTills.map((till) => (
              <option key={till} value={till}>Till {till}</option>
            ))}
          </select>
        </div>
      )}
      

      <div className="allocate-container">
        {/* Left: Form Section */}
        <div className="allocate-form">
          <label>User ID</label>
          <input type="text" value={userId} onChange={(e) => setUserId(e.target.value)} onBlur={fetchUserDetails} placeholder="Enter User ID" />

          <label>Points</label>
          <input type="number" value={points} onChange={(e) => setPoints(e.target.value)} placeholder="Enter Points" />

          <label>Admin Key</label>
          <input type="text" value={adminKey} onChange={(e) => setAdminKey(e.target.value)} placeholder="Enter Admin Key" />

          <label>Transaction Type</label>
          <div className="radio-group">
            <input type="radio" value="add" checked={transactionType === "add"} onChange={() => setTransactionType("add")} /> Add Points
            <input type="radio" value="remove" checked={transactionType === "remove"} onChange={() => setTransactionType("remove")} /> Remove Points
          </div>

          <button className="allocate-button" onClick={allocatePoints}>Allocate Points</button>
        </div>

        {/* Right: User Info Section */}
        <div className="user-info-box">
          <h2>User Information</h2>
          <p><strong>Name:</strong> {userInfo.name}</p>
          <p><strong>Total Points:</strong> {userInfo.totalPoints}</p>
          <p><strong>Last Transaction:</strong> {userInfo.lastTransaction}</p>
        </div>
      </div>

      {/* ✅ Radix Modal for Errors & Messages */}
            <Dialog.Root open={showModal} onOpenChange={setShowModal}>
              <Dialog.Overlay className="dialog-overlay" />
              <Dialog.Content className="dialog-content">
                <Dialog.Title>Notification</Dialog.Title>
                <Dialog.Description>{modalMessage}</Dialog.Description>
                <button onClick={() => setShowModal(false)}>OK</button>
              </Dialog.Content>
            </Dialog.Root>
    </div>
  );
};

export default AllocatePoints;
