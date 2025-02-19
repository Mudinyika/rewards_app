import React, { useState, useEffect } from 'react';

const UserList = () => {
    const [users, setUsers] = useState([]);

    useEffect(() => {
        // Fetch users from the backend
        fetch('http://127.0.0.1:5000/api/users')
            .then(response => response.json())
            .then(data => setUsers(data.users))
            .catch(error => console.error('Error fetching users:', error));
    }, []); // Empty array to run only once on component mount

    return (
        <div>
            <h2>User List</h2>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Created At</th>
                    </tr>
                </thead>
                <tbody>
                    {users.length > 0 ? (
                        users.map(user => (
                            <tr key={user.id}>
                                <td>{user.id}</td>
                                <td>{user.name}</td>
                                <td>{user.email}</td>
                                <td>{user.created_at}</td>
                            </tr>
                        ))
                    ) : (
                        <tr>
                            <td colSpan="4">No users found</td>
                        </tr>
                    )}
                </tbody>
            </table>
        </div>
    );
};

export default UserList;
