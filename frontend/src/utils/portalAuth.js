/**
 * Portal Authentication Utility
 * Handles JWT token storage and retrieval for client portal
 */

const TOKEN_KEY = 'portal_auth_token';
const USER_KEY = 'portal_user';

/**
 * Store JWT token in localStorage
 * @param {string} token - JWT token
 */
export const setPortalToken = (token) => {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  }
};

/**
 * Get JWT token from localStorage
 * @returns {string|null} JWT token or null if not found
 */
export const getPortalToken = () => {
  return localStorage.getItem(TOKEN_KEY);
};

/**
 * Remove JWT token from localStorage
 */
export const removePortalToken = () => {
  localStorage.removeItem(TOKEN_KEY);
};

/**
 * Store user info in localStorage
 * @param {object} user - User object
 */
export const setPortalUser = (user) => {
  if (user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }
};

/**
 * Get user info from localStorage
 * @returns {object|null} User object or null if not found
 */
export const getPortalUser = () => {
  const user = localStorage.getItem(USER_KEY);
  return user ? JSON.parse(user) : null;
};

/**
 * Remove user info from localStorage
 */
export const removePortalUser = () => {
  localStorage.removeItem(USER_KEY);
};

/**
 * Check if user is authenticated
 * @returns {boolean} True if token exists
 */
export const isPortalAuthenticated = () => {
  return !!getPortalToken();
};

/**
 * Clear all portal authentication data
 */
export const clearPortalAuth = () => {
  removePortalToken();
  removePortalUser();
};

/**
 * Get Authorization header for API requests
 * @returns {object} Authorization header object
 */
export const getAuthHeader = () => {
  const token = getPortalToken();
  if (token) {
    return {
      Authorization: `Bearer ${token}`,
    };
  }
  return {};
};
