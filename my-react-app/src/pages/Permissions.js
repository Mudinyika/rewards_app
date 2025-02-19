import React, { useEffect, useState } from "react";
import "./Permissions.css";

const BASE_URL = process.env.REACT_APP_API_BASE_URL || "http://127.0.0.1:5000";

const Permissions = () => {
  const [admins, setAdmins] = useState([]);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [selectedAdmin, setSelectedAdmin] = useState(null);
  const [newRole, setNewRole] = useState("");
  const [superUserPassword, setSuperUserPassword] = useState("");
  const [isSuperUser, setIsSuperUser] = useState(null);

  // Pagination State
  const [currentPage, setCurrentPage] = useState(0);
  const adminsPerPage = 5; // ✅ Show 5 admins per page


  useEffect(() => {
    fetch(`${BASE_URL}/api/check-superuser`, {
      credentials: "include",
    })
      .then((res) => res.json())
      .then((data) => {
        console.log("🔍 Superuser check result:", data);
        setIsSuperUser(data.is_superuser);
      })
      .catch((err) => {
        console.error("❌ Error checking superuser:", err);
        setError("Error checking permissions.");
        setIsSuperUser(false);
      });
  }, []);

  useEffect(() => {
    if (isSuperUser) {
      fetch(`${BASE_URL}/api/admins`)
        .then((res) => res.json())
        .then((data) => setAdmins(data.admins))
        .catch((err) => setError(err.message));
    }
  }, [isSuperUser]);

  useEffect(() => {
    console.log("🛠️ Modal State Updated:", showModal);
  }, [showModal]);

  if (isSuperUser === null) {
    return <p>Checking permissions...</p>;
  }

  if (!isSuperUser) {
    return <p>You do not have permission to access this page.</p>;
  }

  const handleRoleChange = (adminId, newRole) => {
    console.log(`🔍 Role Change Triggered: Admin ID = ${adminId}, New Role = ${newRole}`);
    setSelectedAdmin(adminId);
    setNewRole(newRole);
    setShowModal(true);
    console.log("🛠️ Updated State:", { selectedAdmin: adminId, newRole, showModal: true });
  };

  const handleConfirm = async () => {
    if (!superUserPassword) {
      alert("Please enter the superuser password.");
      return;
    }

    console.log("🚀 Sending Role Update Request...");

    try {
      const response = await fetch(`${BASE_URL}/api/update-admin-role`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          admin_id: selectedAdmin,
          new_role: newRole,
          superuser_password: superUserPassword,
        }),
      });

      const data = await response.json();
      console.log("🔄 Role Update API Response:", data);

      if (response.ok) {
        alert("✅ Role updated successfully.");
        setShowModal(false);
        setSuperUserPassword("");

        // 🔄 Refresh admin list to reflect new role
        fetch(`${BASE_URL}/api/admins`)
          .then((res) => res.json())
          .then((data) => setAdmins(data.admins))
          .catch((err) => setError(err.message));
      } else {
        alert(`❌ Error: ${data.error}`);
      }
    } catch (error) {
      console.error("❌ Error updating role:", error);
      alert("Something went wrong.");
    }
  };

  const handleCancel = () => {
    setShowModal(false);
    setSuperUserPassword("");
  };

  // Pagination Logic
  const totalPages = Math.ceil(admins.length / adminsPerPage);
  const paginatedAdmins = admins.slice(currentPage * adminsPerPage, (currentPage + 1) * adminsPerPage);


  return (
    <div className="permissions-container">
      <h2>Manage Admin Permissions</h2>
      {error && <p className="error-message">{error}</p>}

      <table className="permissions-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Current Role</th>
            <th>Change Role</th>
          </tr>
        </thead>
        <tbody>
          {paginatedAdmins.map((admin) => (
            <tr key={admin.id}>
              <td>{admin.admin_name} {admin.admin_surname}</td>
              <td>{admin.role}</td>
              <td>
               <select value={admin.id === selectedAdmin ? newRole : admin.role} onChange={(e) => handleRoleChange(admin.id, e.target.value)}>
                  <option value="admin">Admin</option>
                  <option value="manager">Manager</option>
                  <option value="super">Super User</option>
                </select>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {/* ✅ Pagination Controls */}
      <div className="pagination-controls">
        <button onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 0))} disabled={currentPage === 0}>
          ⬅️ Previous
        </button>
        <span>Page {currentPage + 1} of {totalPages}</span>
        <button onClick={() => setCurrentPage((prev) => Math.min(prev + 1, totalPages - 1))} disabled={currentPage === totalPages - 1}>
          Next ➡️
        </button>
      </div>
      {/* ✅ Centered Modal with Dimming Background */}
      {showModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3>Confirm Role Change</h3>
            <p>Please enter the superuser password to confirm the role change.</p>
            <input
              type="password"
              value={superUserPassword}
              onChange={(e) => setSuperUserPassword(e.target.value)}
              placeholder="Superuser Password"
              required
            />
            <div>
              <button onClick={handleConfirm}>Confirm</button>
              <button onClick={handleCancel} className="modal-close">Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Permissions;
