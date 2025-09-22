const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

export const API_ENDPOINTS = {
  BASE_URL: API_BASE_URL,
  AUTH: {
    LOGIN: '/api/v1/auth/login',
    REGISTER: '/api/v1/auth/register',
    LOGOUT: '/api/v1/auth/logout',
    REFRESH: '/api/v1/auth/refresh',
    PROFILE: '/api/v1/auth/profile',
    CHANGE_PASSWORD: '/api/v1/auth/change-password',
    VERIFY: '/api/v1/auth/verify-token',
    ME: '/api/v1/auth/me'
  },
  REPORTS: '/api/v1/auth/profile/reports',
  HEALTH: '/health'
};

export default API_ENDPOINTS;