import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'
import axios from 'axios'

// Use VITE_API_URL for production, fallback to relative path (Vite proxy) for local dev
let apiUrl = import.meta.env.VITE_API_URL || '';
if (apiUrl && apiUrl.startsWith('http://') && window.location.protocol === 'https:') {
    apiUrl = apiUrl.replace('http://', 'https://');
}
axios.defaults.baseURL = apiUrl;

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
