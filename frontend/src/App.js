import React, { useState, useEffect } from 'react';
import { BrowserRouter, Route, Routes, Navigate } from 'react-router-dom';
import { CircularProgress, Box, Typography } from '@mui/material';
import ErrorBoundary from './components/ErrorBoundary';
import QueryProvider from './providers/QueryProvider';
import MainLayout from './components/layout/MainLayout';
import Dashboard from './components/Dashboard';
import Login from './components/Login';
import Clients from './components/Clients';
import ClientDetail from './components/ClientDetail';
import ClientForm from './components/ClientForm';
import Patients from './components/Patients';
import PatientDetail from './components/PatientDetail';
import PatientForm from './components/PatientForm';
import AppointmentDetail from './components/AppointmentDetail';
import AppointmentForm from './components/AppointmentForm';
import Visits from './components/Visits';
import VisitDetail from './components/VisitDetail';
import Medications from './components/Medications';
import Services from './components/Services';
import Invoices from './components/Invoices';
import InvoiceDetail from './components/InvoiceDetail';
import Settings from './components/Settings';
import logger from './utils/logger';
import './App.css';

/**
 * Main Application Component
 *
 * Features:
 * - Error boundary for global error catching
 * - React Query provider for server state
 * - Authentication state management
 * - Responsive layout with sidebar
 * - Comprehensive logging
 * - Protected routes
 */
function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    logger.info('App component mounted');

    const checkSession = async () => {
      logger.debug('Checking user session');

      try {
        const startTime = Date.now();
        const response = await fetch('/api/check_session');
        const duration = Date.now() - startTime;

        logger.logAPICall(
          'GET',
          '/api/check_session',
          response.status,
          duration,
          !response.ok ? new Error('Session check failed') : null
        );

        if (response.ok) {
          const userData = await response.json();
          setUser(userData);
          logger.info('User session restored', {
            username: userData.username,
            role: userData.role,
          });
        } else {
          logger.info('No active user session found');
        }
      } catch (error) {
        logger.error('Session check failed', error);
      } finally {
        setLoading(false);
      }
    };

    checkSession();

    return () => {
      logger.debug('App component unmounted');
    };
  }, []);

  const handleLogout = async () => {
    logger.info('Logout initiated', { username: user?.username });

    try {
      const startTime = Date.now();
      const response = await fetch('/api/logout');
      const duration = Date.now() - startTime;

      logger.logAPICall(
        'GET',
        '/api/logout',
        response.status,
        duration,
        !response.ok ? new Error('Logout failed') : null
      );

      if (response.ok) {
        setUser(null);
        logger.info('Logout successful');
      }
    } catch (error) {
      logger.error('Logout failed', error);
    }
  };

  // Loading state
  if (loading) {
    logger.debug('App in loading state');
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '100vh',
          gap: 2,
        }}
      >
        <CircularProgress size={60} />
        <Typography variant="h6" color="text.secondary">
          Loading...
        </Typography>
      </Box>
    );
  }

  return (
    <ErrorBoundary>
      <QueryProvider>
        <BrowserRouter
          future={{
            v7_startTransition: true,
            v7_relativeSplatPath: true,
          }}
        >
          <Routes>
            {/* Login Route - No layout */}
            <Route
              path="/login"
              element={user ? <Navigate to="/" replace /> : <Login setUser={setUser} />}
            />

            {/* Protected Routes - With layout */}
            <Route
              path="/*"
              element={
                user ? (
                  <MainLayout user={user} onLogout={handleLogout}>
                    <Routes>
                      <Route path="/" element={<Dashboard />} />
                      <Route path="/calendar" element={<Dashboard />} />
                      <Route path="/clients" element={<Clients />} />
                      <Route path="/clients/new" element={<ClientForm />} />
                      <Route path="/clients/:clientId" element={<ClientDetail />} />
                      <Route path="/clients/:clientId/edit" element={<ClientForm />} />
                      <Route path="/patients" element={<Patients />} />
                      <Route path="/patients/new" element={<PatientForm />} />
                      <Route path="/patients/:patientId" element={<PatientDetail />} />
                      <Route path="/patients/:patientId/edit" element={<PatientForm />} />
                      <Route path="/visits" element={<Visits />} />
                      <Route path="/visits/new" element={<VisitDetail />} />
                      <Route path="/visits/:visitId" element={<VisitDetail />} />
                      <Route path="/appointments" element={<Dashboard />} />
                      <Route path="/appointments/new" element={<AppointmentForm />} />
                      <Route path="/appointments/:id" element={<AppointmentDetail />} />
                      <Route path="/appointments/:id/edit" element={<AppointmentForm />} />
                      <Route path="/medications" element={<Medications />} />
                      <Route path="/services" element={<Services />} />
                      <Route path="/invoices" element={<Invoices />} />
                      <Route path="/invoices/:invoiceId" element={<InvoiceDetail />} />
                      <Route
                        path="/invoices/old-placeholder"
                        element={
                          <Box>
                            <Typography variant="h4">Invoices</Typography>
                            <Typography color="text.secondary">
                              Invoicing coming soon (Phase 2)
                            </Typography>
                          </Box>
                        }
                      />
                      <Route
                        path="/inventory"
                        element={
                          <Box>
                            <Typography variant="h4">Inventory</Typography>
                            <Typography color="text.secondary">
                              Inventory management coming soon (Phase 3)
                            </Typography>
                          </Box>
                        }
                      />
                      <Route
                        path="/staff"
                        element={
                          <Box>
                            <Typography variant="h4">Staff</Typography>
                            <Typography color="text.secondary">
                              Staff management coming soon (Phase 3)
                            </Typography>
                          </Box>
                        }
                      />
                      <Route
                        path="/reports"
                        element={
                          <Box>
                            <Typography variant="h4">Reports</Typography>
                            <Typography color="text.secondary">
                              Reports coming soon (Phase 4)
                            </Typography>
                          </Box>
                        }
                      />
                      <Route path="/settings" element={<Settings user={user} />} />
                      <Route
                        path="/profile"
                        element={
                          <Box>
                            <Typography variant="h4">Profile</Typography>
                            <Typography color="text.secondary">User: {user?.username}</Typography>
                            <Typography color="text.secondary">Role: {user?.role}</Typography>
                          </Box>
                        }
                      />
                    </Routes>
                  </MainLayout>
                ) : (
                  <Navigate to="/login" replace />
                )
              }
            />
          </Routes>
        </BrowserRouter>
      </QueryProvider>
    </ErrorBoundary>
  );
}

export default App;
