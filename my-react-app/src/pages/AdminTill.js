import React, { useState, useEffect } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import "./AdminTill.css";

const BASE_URL = process.env.REACT_APP_API_BASE_URL || "http://127.0.0.1:5000";

const AdminTill = () => {
  const [formData, setFormData] = useState({
    action: "add",
    user_type: "admin",
    admin_name: "",
    admin_surname: "",
    admin_phone_number: "",
    admin_id_number: "",
    password: "",
    role: "",
    till_number: "",
    operator_name: "",
    id: null,
  });

  const [users, setUsers] = useState([]);
  const [error, setError] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [modalMessage, setModalMessage] = useState("");
  const [selectedUser, setSelectedUser] = useState(null);
  const [showUserModal, setShowUserModal] = useState(false); // ✅ Controls user details modal
  const [editing, setEditing] = useState(false); // ✅ Tracks if user is in edit mode
  const [editData, setEditData] = useState({}); // ✅ Stores edited user data
  const [loggedInRole, setLoggedInRole] = useState(null);

  const [currentPage, setCurrentPage] = useState(1);
  const usersPerPage = 5;

  useEffect(() => {
    const storedRole = localStorage.getItem("role");
    setLoggedInRole(storedRole);
  }, []);

  useEffect(() => {
    fetchUsers(formData.user_type);
  }, [formData.user_type]);

  const fetchUsers = async (userType) => {
    try {
      const response = await fetch(
        `${BASE_URL}/api/manage_user?action=fetch&user_type=${userType}`,
        { credentials: "include" }
      );
      const data = await response.json();
      setUsers(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Fetch error:", err);
      setError(err.message);
    }
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleEditChange = (e) => {
    setEditData({ ...editData, [e.target.name]: e.target.value });
  };
  
  const handleSaveEdit = async () => {
    try {
      const response = await fetch(`${BASE_URL}/api/manage_user`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ ...editData, action: "edit", user_type: formData.user_type }),
      });
  
      if (!response.ok) throw new Error("Failed to update user");
  
      alert("✅ User updated successfully!");
      setShowUserModal(false);
      fetchUsers(formData.user_type); // Refresh list
    } catch (error) {
      alert("❌ Error updating user");
    }
  };
  
  const handleDeleteUser = async () => {
    if (!window.confirm("⚠ Are you sure you want to delete this user?")) return;
  
    try {
      const response = await fetch(`${BASE_URL}/api/manage_user`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ id: selectedUser.id, action: "delete", user_type: formData.user_type }),
      });
  
      if (!response.ok) throw new Error("Failed to delete user");
  
      alert("✅ User deleted successfully!");
      setShowUserModal(false);
      fetchUsers(formData.user_type); // Refresh list
    } catch (error) {
      alert("❌ Error deleting user");
    }
  };
  

  const handleSubmit = async (e) => {
    e.preventDefault();
  
    if (!formData.admin_name && formData.user_type === "admin") {
      alert("⚠ Admin Name is required!");
      return;
    }
  
    if (!formData.operator_name && formData.user_type === "till_operator") {
      alert("⚠ Operator Name is required!");
      return;
    }
  
    const requestBody = {
      action: formData.action,
      user_type: formData.user_type,
      ...(formData.user_type === "admin"
        ? {
            admin_name: formData.admin_name,
            admin_surname: formData.admin_surname,
            admin_phone_number: formData.admin_phone_number,
            admin_id_number: formData.admin_id_number,
            password: formData.password,
            role: formData.role,
          }
        : {
            operator_name: formData.operator_name,
            password: formData.password,
            role: "till_operator",
          }),
    };
  
    if (formData.action === "edit") {
      requestBody.id = formData.id;
    }
  
    try {
      const response = await fetch(`${BASE_URL}/api/manage_user`, {
        method: formData.action === "edit" ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
        credentials: "include",
      });
  
      const data = await response.json(); // ✅ Get API response message
  
      if (!response.ok) {
        throw new Error(data.error || "Failed to update");
      }
  
      setModalMessage(
        `✅ ${formData.user_type === "admin" ? "Admin" : "Till Operator"} ${
          formData.action === "edit" ? "updated" : "created"
        } successfully!`
      );
      setShowModal(true);
      fetchUsers(formData.user_type);
      resetForm();
    } catch (err) {
      setModalMessage(`❌ Error: ${err.message}`);
      setShowModal(true);
    }
  };
  
  const resetForm = () => {
    setFormData({
      action: "add",
      user_type: formData.user_type,
      admin_name: "",
      admin_surname: "",
      admin_phone_number: "",
      admin_id_number: "",
      password: "",
      role: "",
      till_number: "",
      operator_name: "",
      id: null,
    });
  };

  // Open modal when clicking a user
  const handleUserClick = (user) => {
    setSelectedUser(user);
    setEditData(user); // ✅ Pre-fill edit fields
    setShowUserModal(true);
    setEditing(false); // ✅ Start in view mode
  };
  

  // Pagination Controls
  const totalPages = Math.ceil(users.length / usersPerPage);
  const paginatedUsers = users.slice(
    (currentPage - 1) * usersPerPage,
    currentPage * usersPerPage
  );

  
  

  return (
    <div className="admin-till-container">
      <div className="admin-form">
        <h2>Manage {formData.user_type === "admin" ? "Admins" : "Till Operators"}</h2>
        
        <label>
          Select User Type:
          <select name="user_type" value={formData.user_type} onChange={handleChange}>
            <option value="admin">Admin</option>
            <option value="till_operator">Till Operator</option>
          </select>
        </label>

        <form onSubmit={handleSubmit}>
          {formData.user_type === "admin" ? (
            <>
              <input type="text" name="admin_name" placeholder="Admin Name" value={formData.admin_name} onChange={handleChange} required />
              <input type="text" name="admin_surname" placeholder="Admin Surname" value={formData.admin_surname} onChange={handleChange} required />
              <input type="text" name="admin_phone_number" placeholder="Phone Number" value={formData.admin_phone_number} onChange={handleChange} required />
              <input type="text" name="admin_id_number" placeholder="ID Number" value={formData.admin_id_number} onChange={handleChange} required />
              <input type="password" name="password" placeholder="Password" value={formData.password} onChange={handleChange} required />
              <input type="text" name="role" placeholder="Role (super, admin, manager)" value={formData.role} onChange={handleChange} required />
            </>
          ) : (
            <>
              <input type="text" name="operator_name" placeholder="Operator Name" value={formData.operator_name} onChange={handleChange} required />
              <input type="password" name="password" placeholder="Password" value={formData.password} onChange={handleChange} required />
            </>
          )}

          <button type="submit" className="submit-button">
            {formData.action === "edit" ? "Update" : "Add"} {formData.user_type}
          </button>
        </form>
      </div>

      {/* ✅ User List with Clickable Users */}
      <div className="user-list">
        <h3>Existing {formData.user_type === "admin" ? "Admins" : "Till Operators"}</h3>
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Role</th>
            </tr>
          </thead>
          <tbody>
            {paginatedUsers.map((user) => (
              <tr key={user.id} onClick={() => handleUserClick(user)} className="clickable-row">
                <td>{user.admin_name || user.operator_name}</td>
                <td>{user.role}</td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* Pagination Controls */}
        <div className="pagination">
          <button onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 1))} disabled={currentPage === 1}>⬅ Previous</button>
          <span>Page {currentPage} of {totalPages}</span>
          <button onClick={() => setCurrentPage((prev) => Math.min(prev + 1, totalPages))} disabled={currentPage === totalPages}>Next ➡</button>
        </div>
      </div>
      {/* ✅ User Details Modal */}
      {selectedUser && (
        <Dialog.Root open={showUserModal} onOpenChange={setShowUserModal}>
          <Dialog.Overlay className="dialog-overlay" />
          <Dialog.Content className="dialog-content user-details-modal">
            <Dialog.Title>User Details</Dialog.Title>

            {/* ✅ Define Permissions */}
            {(() => {
              const isSuperUser = selectedUser.role === "super";
              const canEditOrDelete = loggedInRole === "super" || (loggedInRole === "admin" && !isSuperUser);

              return (
                <>
                  {/* ✅ Show edit icon only if Super User or Admin */}
                  {canEditOrDelete && !editing && (
                    <button className="edit-icon" onClick={() => setEditing(true)}>✏️</button>
                  )}
                  <p><strong>Name:</strong> 
                    {editing ? (
                      <input 
                        type="text" 
                        value={editData.admin_name || editData.operator_name} 
                        onChange={(e) => setEditData({
                          ...editData, 
                          [formData.user_type === "admin" ? "admin_name" : "operator_name"]: e.target.value
                        })} 
                      />
                    ) : (selectedUser.admin_name || selectedUser.operator_name)}
                  </p>

                  <p><strong>Surname:</strong> 
                    {editing ? (
                      <input 
                        type="text" 
                        value={editData.admin_surname} 
                        onChange={(e) => setEditData({ ...editData, admin_surname: e.target.value })} 
                      />
                    ) : selectedUser.admin_surname}
                  </p>

                  <p><strong>Phone Number:</strong> 
                    {editing ? (
                      <input 
                        type="text" 
                        value={editData.admin_phone_number} 
                        onChange={(e) => setEditData({ ...editData, admin_phone_number: e.target.value })} 
                      />
                    ) : selectedUser.admin_phone_number}
                  </p>

                  <p><strong>ID Number:</strong> {selectedUser.admin_id_number}  {/* 🚫 Not Editable */}</p>
                  {/* ✅ Show "Save" and "Delete" buttons only if editing is enabled */}
                  {canEditOrDelete && editing && (
                    <div className="modal-buttons">
                      <button className="save-button" onClick={handleSaveEdit}>Save</button>
                      <button className="delete-button" onClick={handleDeleteUser}>Delete</button>
                    </div>
                  )}

                  <button onClick={() => setShowUserModal(false)} className="modal-close">Close</button>
                </>
              );
            })()}
          </Dialog.Content>
        </Dialog.Root>
      )}
    </div>
  );
};

export default AdminTill;
