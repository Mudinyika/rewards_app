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
  const [currentPage, setCurrentPage] = useState(1);
  const usersPerPage = 5;

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

  const handleSubmit = async (e) => {
    e.preventDefault();
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

      if (!response.ok) {
        throw new Error("Failed to update");
      }

      setModalMessage(
        `✅ ${formData.user_type === "admin" ? "Admin" : "Till Operator"} ${
          formData.action === "edit" ? "updated" : "created"
        } successfully!`
      );
      setShowModal(true);
      fetchUsers(formData.user_type);
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
    } catch (err) {
      setModalMessage(`❌ Error: ${err.message}`);
      setShowModal(true);
    }
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

      {/* ✅ User List with Pagination */}
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
              <tr key={user.id}>
                <td>{user.admin_name || user.operator_name}</td>
                <td>{user.role}</td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* Pagination Controls */}
        <div className="pagination">
          <button
            onClick={() => setCurrentPage((prev) => Math.max(prev - 1, 1))}
            disabled={currentPage === 1}
          >
            ⬅ Previous
          </button>
          <span>Page {currentPage} of {totalPages}</span>
          <button
            onClick={() => setCurrentPage((prev) => Math.min(prev + 1, totalPages))}
            disabled={currentPage === totalPages}
          >
            Next ➡
          </button>
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

export default AdminTill;
