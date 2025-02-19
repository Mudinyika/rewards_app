import React from "react";

export default function AdminDashboard() {
  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-800 text-white p-4">
        <h2 className="text-xl font-bold mb-4">Admin Dashboard</h2>
        <nav>
          <ul className="space-y-4">
            <li>
              <a href="#dashboard" className="block hover:bg-gray-700 p-2 rounded">
                Dashboard
              </a>
            </li>
            <li>
              <a href="#manage-users" className="block hover:bg-gray-700 p-2 rounded">
                Manage Users
              </a>
            </li>
            <li>
              <a href="#settings" className="block hover:bg-gray-700 p-2 rounded">
                Settings
              </a>
            </li>
          </ul>
        </nav>
      </aside>

      {/* Main Content */}
      <div className="flex-1 bg-gray-100 p-6">
        {/* Header */}
        <header className="flex justify-between items-center bg-white p-4 rounded shadow mb-6">
          <h1 className="text-2xl font-bold">Welcome, Admin</h1>
          <div className="flex items-center space-x-4">
            <span className="text-gray-600">Admin Name</span>
            <button className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600">
              Logout
            </button>
          </div>
        </header>

        {/* Main Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Analytics Cards */}
          <div className="bg-white p-4 rounded shadow">
            <h2 className="text-lg font-bold">Total Users</h2>
            <p className="text-3xl mt-2">120</p>
          </div>
          <div className="bg-white p-4 rounded shadow">
            <h2 className="text-lg font-bold">Active Sessions</h2>
            <p className="text-3xl mt-2">35</p>
          </div>
          <div className="bg-white p-4 rounded shadow">
            <h2 className="text-lg font-bold">Pending Tasks</h2>
            <p className="text-3xl mt-2">8</p>
          </div>
        </div>
      </div>
    </div>
  );
}
