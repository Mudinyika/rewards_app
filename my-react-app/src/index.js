import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css'; // Ensure this matches your CSS file path

console.log("🚀 React is trying to mount...");

const rootElement = document.getElementById('root');
if (!rootElement) {
    console.error("❌ ERROR: No #root element found in HTML!");
} else {
    console.log("✅ Found #root element, mounting React...");
    const root = ReactDOM.createRoot(rootElement);
    root.render(
        <React.StrictMode>
            <App />
        </React.StrictMode>
    );
}
