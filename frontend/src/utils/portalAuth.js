/**
 * Portal Authentication Utility
 * Handles JWT token storage and retrieval for client portal
 *
 * Token is stored in sessionStorage (clears when browser closes)
 * User data is stored in localStorage (persists across sessions)
 * Activity tracking uses localStorage to monitor idle time
 */

const TOKEN_KEY = 'portal_auth_token';
const USER_KEY = 'portal_user';
const ACTIVITY_KEY = 'portal_last_activity';

/**
 * Store JWT token in sessionStorage (clears when browser closes)
 * @param {string} token - JWT token
 */
export const setPortalToken = (token) => {
  if (token) {
    sessionStorage.setItem(TOKEN_KEY, token);
  }
};

/**
 * Get JWT token from sessionStorage
 * @returns {string|null} JWT token or null if not found
 */
export const getPortalToken = () => {
  return sessionStorage.getItem(TOKEN_KEY);
};

/**
 * Remove JWT token from sessionStorage
 */
export const removePortalToken = () => {
  sessionStorage.removeItem(TOKEN_KEY);
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
  removeLastActivity();
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

/**
 * Update last activity timestamp
 */
export const updateLastActivity = () => {
  localStorage.setItem(ACTIVITY_KEY, Date.now().toString());
};

/**
 * Get last activity timestamp
 * @returns {number|null} Timestamp or null if not found
 */
export const getLastActivity = () => {
  const activity = localStorage.getItem(ACTIVITY_KEY);
  return activity ? parseInt(activity, 10) : null;
};

/**
 * Remove last activity timestamp
 */
export const removeLastActivity = () => {
  localStorage.removeItem(ACTIVITY_KEY);
};

/**
 * Check if user has been idle for more than specified minutes
 * @param {number} minutes - Idle timeout in minutes (default: 15)
 * @returns {boolean} True if idle time exceeded
 */
export const isIdleTimeoutExceeded = (minutes = 15) => {
  const lastActivity = getLastActivity();
  if (!lastActivity) {
    return false;
  }

  const idleTime = Date.now() - lastActivity;
  const idleMinutes = idleTime / (1000 * 60);

  return idleMinutes >= minutes;
};
