import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";

console.log("✅ API Base URL:", process.env.REACT_APP_API_BASE_URL);


const BASE_URL = process.env.REACT_APP_API_BASE_URL || "http://127.0.0.1:5000";

const Sidebar = ({ setLoggedIn }) => {
  const [isUsersOpen, setIsUsersOpen] = useState(false);
  const [role, setRole] = useState(null);
  const [showModal, setShowModal] = useState(false); // ✅ State for modal
  const navigate = useNavigate();

  useEffect(() => {
    const storedRole = localStorage.getItem("role");

    fetch(`${BASE_URL}/api/check-superuser`, { credentials: "include" })
      .then((res) => res.json())
      .then((data) => {
        console.log("🔍 Superuser Check:", data); // Debugging

        if (data.is_superuser) {
          setRole("super"); // ✅ Set role as superuser
        } else {
          setRole(storedRole); // Keep stored role if not super
        }
      })
      .catch((err) => {
        console.error("❌ Error fetching superuser status:", err);
        setRole(storedRole); // Fallback in case of error
      });
  }, []);

  const toggleUsers = () => {
    setIsUsersOpen(!isUsersOpen);
  };

  const handleLogout = async () => {
    try {
      const response = await fetch(`${BASE_URL}/api/logout`, {
        method: "POST",
        credentials: "include",
      });

      if (response.ok) {
        console.log("✅ Successfully logged out");

        // ✅ Clear authentication state
        localStorage.removeItem("loggedIn");
        localStorage.removeItem("role");

        setLoggedIn(false);

        // ✅ Redirect to Welcome Page
        navigate("/welcome");
      } else {
        console.error("❌ Logout failed");
      }
    } catch (error) {
      console.error("❌ Logout error:", error);
    }
  };

  const handleManagePermissionsClick = () => {
    console.log("🔄 Manage Permissions Clicked! Role:", role); // Debug log

    if (role === "super") {
      console.log("✅ Navigating to /permissions");
      navigate("/permissions"); // ✅ Should navigate
    } else {
      console.log("❌ Not a superuser - Triggering modal in App.js");
      localStorage.setItem("showModal", "true"); // ✅ Use localStorage to trigger App.js modal
      window.dispatchEvent(new Event("storage")); // ✅ Notify App.js to show modal
    }
  };

  return (
    <div className="sidebar">
      <h1 className="text-2xl font-bold text-center p-4 border-b border-gray-700">
        My App
      </h1>
      <nav className="flex-1 mt-4 space-y-4">
        <Link to="/" className="nav-item">Dashboard</Link>

        <div>
          <button onClick={toggleUsers} className="nav-item">Users</button>
          {isUsersOpen && (
            <ul className="submenu ml-4 mt-2 space-y-2">
              <li><Link to="/add-user" className="block text-gray-300 hover:text-white">Add User</Link></li>
              <li><Link to="/edit-user" className="block text-gray-300 hover:text-white">Edit User</Link></li>
              <li><Link to="/view-user" className="block text-gray-300 hover:text-white">View User</Link></li>
            </ul>
          )}
        </div>

        <Link to="/analytics" className="nav-item">Analytics</Link>
        <Link to="/allocate-points" className="nav-item">Allocate Points</Link>
        <Link to="/till-operators" className="nav-item">Admin & Till</Link>
        <Link to="/search" className="nav-item">Search</Link>

        <button
          onClick={(event) => {
            if (role === "super") {
              navigate("/manage-permissions"); // ✅ Allow navigation for superuser
            } else {
              handleManagePermissionsClick(event); // ⛔ Block non-superusers with modal
            }
          }}
          className={`nav-item ${role === "super" ? "bg-red-500 hover:bg-red-700 text-white" : "text-gray-500 cursor-not-allowed"}`}
        >
          Manage Permissions
        </button>



        <button
          onClick={handleLogout}
          className="nav-item text-red-500 hover:text-red-700"
        >
          Logout
        </button>
      </nav>
    </div>
  );
};

export default Sidebar;
