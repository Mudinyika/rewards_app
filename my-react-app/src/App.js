import React, { useState, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import WelcomePage from "./pages/WelcomePage";
import ViewUser from "./pages/ViewUser";
import AddUser from "./pages/AddUser";
import DeleteUser from "./pages/DeleteUser";
import EditUser from "./pages/EditUser";
import Analytics from "./pages/Analytics";
import AllocatePoints from "./pages/AllocatePoints";
import AdminTill from "./pages/AdminTill";
import Search from "./pages/Search";
import Permissions from "./pages/Permissions";
import ForgotPassword from "./components/ForgotPassword/ForgotPassword";
import ResetPassword from "./components/ResetPassword/ResetPassword";
import "./index.css"; // Ensure modal styles are globally applied



function ProtectedLayout({ children, handlePermissionsClick, role, setLoggedIn }) {
  return (
    <div className="app-container">
      {/* ✅ Sidebar remains fixed */}
      <Sidebar handlePermissionsClick={handlePermissionsClick} setLoggedIn={setLoggedIn} />

      {/* ✅ Only this part updates */}
      <div className="main-content">{children}</div>
    </div>
  );
}


function App() {
  const [loggedIn, setLoggedIn] = useState(localStorage.getItem("loggedIn") === "true");
  const [role, setRole] = useState(localStorage.getItem("role") || null);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    const handleStorageChange = () => {
      if (localStorage.getItem("showModal") === "true") {
        setShowModal(true);
      }
    };
  
    window.addEventListener("storage", handleStorageChange);
    return () => window.removeEventListener("storage", handleStorageChange);
  }, []);
  

  useEffect(() => {
    const checkLoginStatus = async () => {
      try {
        const response = await fetch("/api/check-login", {
          method: "GET",
          credentials: "include", // ✅ Ensures cookies are sent
        });

        const data = await response.json();
        console.log("🔍 Login Check Response:", data);

        if (data.success) {
          localStorage.setItem("loggedIn", "true");
          localStorage.setItem("role", data.role);
          setLoggedIn(true);
          setRole(data.role);
        } else {
          localStorage.removeItem("loggedIn");
          localStorage.removeItem("role");
          setLoggedIn(false);
          setRole(null);
        }
      } catch (error) {
        console.error("❌ Error checking login status:", error);
      }
    };

    checkLoginStatus(); // ✅ Run once when app loads
  }, []);

  const handleManagePermissionsClick = (event) => {
    console.log("🔍 User Role:", role);
  
    if (role !== "super") {
      event.preventDefault(); // ⛔ Prevents navigation
      setShowModal(true); 
    }
  };
  
  
  return (
    <Router basename="/admin"> {/* ✅ Router is at the highest level */}
      <Routes>
        {!loggedIn ? (
          <>
            <Route path="/" element={<WelcomePage setLoggedIn={setLoggedIn} />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password/:token" element={<ResetPassword />} />
          </>
        ) : (
          <>
            <Route
              path="/"
              element={
                <ProtectedLayout role={role} setLoggedIn={setLoggedIn} handlePermissionsClick={handleManagePermissionsClick}>
                  <Dashboard />
                </ProtectedLayout>
              }
            />
            <Route
              path="/view-user"
              element={
                <ProtectedLayout role={role} setLoggedIn={setLoggedIn} handlePermissionsClick={handleManagePermissionsClick}>
                  <ViewUser />
                </ProtectedLayout>
              }
            />
            <Route
              path="/add-user"
              element={
                <ProtectedLayout role={role} setLoggedIn={setLoggedIn} handlePermissionsClick={handleManagePermissionsClick}>
                  <AddUser />
                </ProtectedLayout>
              }
            />
            <Route
              path="/delete-user"
              element={
                <ProtectedLayout role={role} setLoggedIn={setLoggedIn} handlePermissionsClick={handleManagePermissionsClick}>
                  <DeleteUser />
                </ProtectedLayout>
              }
            />
            <Route
              path="/edit-user"
              element={
                <ProtectedLayout role={role} setLoggedIn={setLoggedIn} handlePermissionsClick={handleManagePermissionsClick}>
                  <EditUser />
                </ProtectedLayout>
              }
            />
            <Route
              path="/analytics"
              element={
                <ProtectedLayout role={role} setLoggedIn={setLoggedIn} handlePermissionsClick={handleManagePermissionsClick}>
                  <Analytics />
                </ProtectedLayout>
              }
            />
            <Route
              path="/allocate-points"
              element={
                <ProtectedLayout role={role} setLoggedIn={setLoggedIn} handlePermissionsClick={handleManagePermissionsClick}>
                  <AllocatePoints />
                </ProtectedLayout>
              }
            />
            <Route
              path="/till-operators"
              element={
                <ProtectedLayout role={role} setLoggedIn={setLoggedIn} handlePermissionsClick={handleManagePermissionsClick}>
                  <AdminTill />
                </ProtectedLayout>
              }
            />
            <Route
              path="/search"
              element={
                <ProtectedLayout role={role} setLoggedIn={setLoggedIn} handlePermissionsClick={handleManagePermissionsClick}>
                  <Search />
                </ProtectedLayout>
              }
            />
            <Route
              path="/manage-permissions"
              element={
                <ProtectedLayout role={role} setLoggedIn={setLoggedIn} handlePermissionsClick={handleManagePermissionsClick}>
                  <Permissions />
                </ProtectedLayout>
              }
            />
          </>
        )}

        <Route path="/*" element={<Navigate to="/" />} />
      </Routes>

      {/* Unauthorized Access Modal */}
      {showModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <p> Access Denied! Only the Super User can Manage Permissions.</p>
            <button  
              onClick={() => {
                setShowModal(false);
                localStorage.removeItem("showModal"); // ✅ Reset trigger after closing
              }}
              className="modal-close"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </Router>
  );
}

export default App;
