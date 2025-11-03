/**
 * Portal API Utility
 * Handles API calls with JWT authentication for client portal
 */

import { getAuthHeader, clearPortalAuth } from './portalAuth';

/**
 * Base API URL
 */
const API_BASE_URL = '/api/portal';

/**
 * Make authenticated API request
 * @param {string} endpoint - API endpoint (without /api/portal prefix)
 * @param {object} options - Fetch options
 * @returns {Promise} Fetch response
 */
export const portalFetch = async (endpoint, options = {}) => {
  const url = `${API_BASE_URL}${endpoint}`;

  const defaultHeaders = {
    'Content-Type': 'application/json',
    ...getAuthHeader(),
  };

  const config = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };

  try {
    const response = await fetch(url, config);

    // If unauthorized, clear auth and redirect to login
    if (response.status === 401) {
      clearPortalAuth();
      window.location.href = '/portal/login';
      throw new Error('Unauthorized - Please log in again');
    }

    return response;
  } catch (error) {
    console.error('Portal API Error:', error);
    throw error;
  }
};

/**
 * GET request with authentication
 */
export const portalGet = async (endpoint) => {
  const response = await portalFetch(endpoint, {
    method: 'GET',
  });
  return response.json();
};

/**
 * POST request with authentication
 */
export const portalPost = async (endpoint, data) => {
  const response = await portalFetch(endpoint, {
    method: 'POST',
    body: JSON.stringify(data),
  });
  return response.json();
};

/**
 * PUT request with authentication
 */
export const portalPut = async (endpoint, data) => {
  const response = await portalFetch(endpoint, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
  return response.json();
};

/**
 * DELETE request with authentication
 */
export const portalDelete = async (endpoint) => {
  const response = await portalFetch(endpoint, {
    method: 'DELETE',
  });
  return response.json();
};

/**
 * API Methods for specific portal endpoints
 */
export const portalApi = {
  // Dashboard
  getDashboard: (clientId) => portalGet(`/dashboard/${clientId}`),

  // Patients
  getPatients: (clientId) => portalGet(`/patients/${clientId}`),
  getPatient: (clientId, patientId) => portalGet(`/patients/${clientId}/${patientId}`),

  // Appointments
  getAppointments: (clientId) => portalGet(`/appointments/${clientId}`),

  // Invoices
  getInvoices: (clientId) => portalGet(`/invoices/${clientId}`),
  getInvoice: (clientId, invoiceId) => portalGet(`/invoices/${clientId}/${invoiceId}`),

  // Appointment Requests
  createAppointmentRequest: (data) => portalPost('/appointment-requests', data),
  getAppointmentRequests: (clientId) => portalGet(`/appointment-requests/${clientId}`),
  getAppointmentRequest: (clientId, requestId) =>
    portalGet(`/appointment-requests/${clientId}/${requestId}`),
  cancelAppointmentRequest: (clientId, requestId) =>
    portalPost(`/appointment-requests/${clientId}/${requestId}/cancel`, {}),
};
