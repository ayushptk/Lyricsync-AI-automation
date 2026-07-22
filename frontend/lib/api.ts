import axios from 'axios';
import { useAuthStore } from './store';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  withCredentials: true, // For HttpOnly cookies
  headers: {
    'Content-Type': 'application/json',
  },
});

let isRefreshing = false;
let failedQueue: any[] = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });

  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // Check if error is 401 and we haven't already retried this request
    if (
      error.response?.status === 401 && 
      !originalRequest._retry && 
      originalRequest.url !== '/api/v1/auth/refresh' && 
      originalRequest.url !== '/api/v1/auth/login'
    ) {
      
      if (isRefreshing) {
        return new Promise(function(resolve, reject) {
          failedQueue.push({resolve, reject});
        }).then(token => {
          return api(originalRequest);
        }).catch(err => {
          return Promise.reject(err);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;
      
      try {
        // Attempt to refresh the token
        await api.post('/api/v1/auth/refresh');
        processQueue(null);
        return api(originalRequest); // Retry the original request
      } catch (err) {
        processQueue(err, null);
        // Refresh token failed, user is logged out
        useAuthStore.getState().setUser(null);
        if (typeof window !== 'undefined') {
           window.location.href = '/login';
        }
        return Promise.reject(err);
      } finally {
        isRefreshing = false;
      }
    }
    
    // If it's a 401 on the refresh endpoint itself, clean up and redirect
    if (error.response?.status === 401 && originalRequest.url === '/api/v1/auth/refresh') {
        useAuthStore.getState().setUser(null);
        if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
           window.location.href = '/login';
        }
    }

    return Promise.reject(error);
  }
);

export default api;
