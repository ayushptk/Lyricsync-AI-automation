import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  withCredentials: true, // For HttpOnly cookies
  headers: {
    'Content-Type': 'application/json',
  },
});

export default api;
