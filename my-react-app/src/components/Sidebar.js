import React, { useState, useEffect } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";

const BASE_URL = process.env.REACT_APP_API_BASE_URL || "http://127.0.0.1:5000";

const Sidebar = ({ setLoggedIn }) => {
  const [isUsersOpen, setIsUsersOpen] = useState(false);
  const [role, setRole] = useState(null);
  const navigate = useNavigate();
  const location = useLocation(); // ✅ Get current route
  

  useEffect(() => {
    const storedRole = localStorage.getItem("role");

    fetch(`${BASE_URL}/api/check-superuser`, { credentials: "include" })
      .then((res) => res.json())
      .then((data) => {
        if (data.is_superuser) {
          setRole("super");
        } else {
          setRole(storedRole);
        }
      })
      .catch(() => {
        setRole(storedRole);
      });
  }, []);

  const toggleUsers = () => {
    setIsUsersOpen(!isUsersOpen);
  };

  const closeUsersMenu = () => {
    setIsUsersOpen(false);
  };

  const handleLogout = async () => {
    try {
      const response = await fetch(`${BASE_URL}/api/logout`, {
        method: "POST",
        credentials: "include",
      });

      if (response.ok) {
        localStorage.removeItem("loggedIn");
        localStorage.removeItem("role");
        setLoggedIn(false);
        navigate("/welcome");
      }
    } catch (error) {
      console.error("❌ Logout error:", error);
    }
  };

  const isActive = (path) => location.pathname === path;

  return (
    <div className="sidebar">
      <h1 className="text-2xl font-bold text-center p-4 border-b border-gray-700">
        My App
      </h1>
      <nav className="flex-1 mt-4 space-y-4">
        <Link to="/" className={`nav-item ${isActive("/") ? "active" : ""}`} onClick={closeUsersMenu}>
          Dashboard
        </Link>

        <div>
        <button 
          onClick={toggleUsers} 
          className={`nav-button ${isActive("/add-user") || isActive("/edit-user") || isActive("/view-user") ? "active" : ""}`}
        >
          Users
        </button>
        {isUsersOpen && (
          <ul className="submenu ml-4 mt-2 space-y-2">
          <li>
            <Link to="/add-user" className={`block ${isActive("/add-user") ? "active" : ""}`}>
              Add User
            </Link>
          </li>
          <li>
            <Link to="/edit-user" className={`block ${isActive("/edit-user") ? "active" : ""}`}>
              Edit User
            </Link>
          </li>
          <li>
            <Link to="/view-user" className={`block ${isActive("/view-user") ? "active" : ""}`}>
              View User
            </Link>
          </li>
        </ul>
                
        )}  
        </div>

        <Link to="/analytics" className={`nav-item ${isActive("/analytics") ? "active" : ""}`} onClick={closeUsersMenu}>
          Analytics
        </Link>
        <Link to="/allocate-points" className={`nav-item ${isActive("/allocate-points") ? "active" : ""}`} onClick={closeUsersMenu}>
          Allocate Points
        </Link>
        <Link to="/till-operators" className={`nav-item ${isActive("/till-operators") ? "active" : ""}`} onClick={closeUsersMenu}>
          Admin & Till
        </Link>
        <Link to="/search" className={`nav-item ${isActive("/search") ? "active" : ""}`} onClick={closeUsersMenu}>
          Search
        </Link>

        <button
          onClick={() => {
            closeUsersMenu(); // ✅ Close the Users menu
            role === "super" ? navigate("/manage-permissions") : alert("Access Denied");
          }}
          className={`nav-button ${isActive("/manage-permissions") ? "active" : ""}`}
        >
          Manage Permissions
        </button>

        <button onClick={handleLogout} className="nav-button logout-button">
          Logout
        </button>
      </nav>
    </div>
  );
};

export default Sidebar;
