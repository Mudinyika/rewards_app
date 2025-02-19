// src/components/Navbar.js
import React from 'react';
import { Link } from 'react-router-dom';

function Navbar() {
  return (
    <nav className="bg-blue-600 text-white shadow-lg">
      <div className="container mx-auto flex justify-between items-center p-4">
        <h1 className="text-xl font-bold">Admin Dashboard</h1>
        <ul className="flex space-x-4">
          <li>
            <Link to="/" className="hover:text-gray-300">Home</Link>
          </li>
          <li>
            <Link to="/settings" className="hover:text-gray-300">Settings</Link>
          </li>
          <li>
            <button className="hover:text-gray-300">Logout</button>
          </li>
        </ul>
      </div>
    </nav>
  );
}

export default Navbar;
