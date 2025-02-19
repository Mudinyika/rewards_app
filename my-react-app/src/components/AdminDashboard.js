import React from 'react';
import UserList from './UserList';
import AddPoints from './AddPoints';
import CardManagement from './CardManagement';

function AdminDashboard() {
  return (
    <div>
      <h1>Admin Dashboard</h1>
      <UserList />
      <AddPoints />
      <CardManagement />
    </div>
  );
}

export default AdminDashboard;
