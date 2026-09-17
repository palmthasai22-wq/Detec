import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'
import axios from 'axios'
import { API_BASE_URL } from './config/api.ts'

axios.defaults.baseURL = API_BASE_URL;

// Cache-buster interceptor to bypass Chrome's stubborn 307 redirect cache
axios.interceptors.request.use(config => {
    if (config.method === 'get') {
        config.params = { ...config.params, _t: Date.now() };
    }
    return config;
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
