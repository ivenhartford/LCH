import React, { useState, useEffect, Suspense, lazy } from 'react';
import { BrowserRouter, Route, Routes, Navigate } from 'react-router-dom';
import { CircularProgress, Box, Typography } from '@mui/material';
import ErrorBoundary from './components/ErrorBoundary';
import QueryProvider from './providers/QueryProvider';
import MainLayout from './components/layout/MainLayout';
import LoadingFallback from './components/common/LoadingFallback';
import logger from './utils/logger';
import { initPerformanceMonitoring } from './utils/performanceMonitoring';
import { NotificationProvider } from './contexts/NotificationContext';
import './App.css';

// Lazy load route components for code splitting
// Critical routes loaded immediately
import Login from './components/Login';
import ClientPortalLogin from './components/ClientPortalLogin';

// Lazy-loaded route components
const Dashboard = lazy(() => import('./components/Dashboard'));
const Appointments = lazy(() => import('./components/Appointments'));
const Clients = lazy(() => import('./components/Clients'));
const ClientDetail = lazy(() => import('./components/ClientDetail'));
const ClientForm = lazy(() => import('./components/ClientForm'));
const Patients = lazy(() => import('./components/Patients'));
const PatientDetail = lazy(() => import('./components/PatientDetail'));
const PatientForm = lazy(() => import('./components/PatientForm'));
const AppointmentDetail = lazy(() => import('./components/AppointmentDetail'));
const AppointmentForm = lazy(() => import('./components/AppointmentForm'));
const Visits = lazy(() => import('./components/Visits'));
const VisitDetail = lazy(() => import('./components/VisitDetail'));
const Medications = lazy(() => import('./components/Medications'));
const Services = lazy(() => import('./components/Services'));
const Invoices = lazy(() => import('./components/Invoices'));
const InvoiceDetail = lazy(() => import('./components/InvoiceDetail'));
const FinancialReports = lazy(() => import('./components/FinancialReports'));
const InventoryDashboard = lazy(() => import('./components/InventoryDashboard'));
const Products = lazy(() => import('./components/Products'));
const Vendors = lazy(() => import('./components/Vendors'));
const PurchaseOrders = lazy(() => import('./components/PurchaseOrders'));
const Staff = lazy(() => import('./components/Staff'));
const StaffSchedule = lazy(() => import('./components/StaffSchedule'));
const LabTests = lazy(() => import('./components/LabTests'));
const LabResults = lazy(() => import('./components/LabResults'));
const Reminders = lazy(() => import('./components/Reminders'));
const NotificationTemplates = lazy(() => import('./components/NotificationTemplates'));
const Documents = lazy(() => import('./components/Documents'));
const ProtocolLibrary = lazy(() => import('./components/ProtocolLibrary'));
const TreatmentPlanBuilder = lazy(() => import('./components/TreatmentPlanBuilder'));
const AnalyticsDashboard = lazy(() => import('./components/AnalyticsDashboard'));
const Settings = lazy(() => import('./components/Settings'));
const ClientPortalLayout = lazy(() => import('./components/ClientPortalLayout'));
const ClientPortalDashboard = lazy(() => import('./components/ClientPortalDashboard'));
const ClientPatients = lazy(() => import('./components/ClientPatients'));
const ClientAppointmentHistory = lazy(() => import('./components/ClientAppointmentHistory'));
const ClientInvoices = lazy(() => import('./components/ClientInvoices'));
const AppointmentRequestForm = lazy(() => import('./components/AppointmentRequestForm'));

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
  const [portalUser, setPortalUser] = useState(() => {
    // Load portal user from localStorage on mount
    const saved = localStorage.getItem('portalUser');
    return saved ? JSON.parse(saved) : null;
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    logger.info('App component mounted');

    // Initialize performance monitoring
    initPerformanceMonitoring();

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
        <NotificationProvider>
          <BrowserRouter
            future={{
              v7_startTransition: true,
              v7_relativeSplatPath: true,
            }}
          >
          <Routes>
            {/* Staff Login Route - No layout */}
            <Route
              path="/login"
              element={user ? <Navigate to="/" replace /> : <Login setUser={setUser} />}
            />

            {/* Client Portal Login Route - No layout */}
            <Route
              path="/portal/login"
              element={
                portalUser ? (
                  <Navigate to="/portal/dashboard" replace />
                ) : (
                  <ClientPortalLogin setPortalUser={setPortalUser} />
                )
              }
            />

            {/* Client Portal Protected Routes - With portal layout */}
            <Route
              path="/portal/*"
              element={
                portalUser ? (
                  <ClientPortalLayout portalUser={portalUser} setPortalUser={setPortalUser}>
                    <Suspense fallback={<LoadingFallback />}>
                      <Routes>
                        <Route path="/dashboard" element={<ClientPortalDashboard portalUser={portalUser} />} />
                        <Route path="/patients" element={<ClientPatients portalUser={portalUser} />} />
                        <Route path="/appointments" element={<ClientAppointmentHistory portalUser={portalUser} />} />
                        <Route path="/invoices" element={<ClientInvoices portalUser={portalUser} />} />
                        <Route path="/request-appointment" element={<AppointmentRequestForm portalUser={portalUser} />} />
                      </Routes>
                    </Suspense>
                  </ClientPortalLayout>
                ) : (
                  <Navigate to="/portal/login" replace />
                )
              }
            />

            {/* Staff Protected Routes - With layout */}
            <Route
              path="/*"
              element={
                user ? (
                  <MainLayout user={user} onLogout={handleLogout}>
                    <Suspense fallback={<LoadingFallback />}>
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
                        <Route path="/appointments" element={<Appointments />} />
                        <Route path="/appointments/new" element={<AppointmentForm />} />
                        <Route path="/appointments/:id" element={<AppointmentDetail />} />
                        <Route path="/appointments/:id/edit" element={<AppointmentForm />} />
                        <Route path="/medications" element={<Medications />} />
                        <Route path="/services" element={<Services />} />
                        <Route path="/invoices" element={<Invoices />} />
                        <Route path="/invoices/:invoiceId" element={<InvoiceDetail />} />
                        <Route path="/reports" element={<FinancialReports />} />
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
                        <Route path="/inventory" element={<InventoryDashboard />} />
                        <Route path="/products" element={<Products />} />
                        <Route path="/vendors" element={<Vendors />} />
                        <Route path="/purchase-orders" element={<PurchaseOrders />} />
                        <Route path="/staff" element={<Staff />} />
                        <Route path="/staff-schedule" element={<StaffSchedule />} />
                        <Route path="/lab-tests" element={<LabTests />} />
                        <Route path="/lab-results" element={<LabResults />} />
                        <Route path="/reminders" element={<Reminders />} />
                        <Route path="/notification-templates" element={<NotificationTemplates />} />
                        <Route path="/documents" element={<Documents />} />
                        <Route path="/protocols" element={<ProtocolLibrary />} />
                        <Route path="/treatment-plans/:patientId" element={<TreatmentPlanBuilder />} />
                        <Route path="/analytics" element={<AnalyticsDashboard />} />
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
                    </Suspense>
                  </MainLayout>
                ) : (
                  <Navigate to="/login" replace />
                )
              }
            />
          </Routes>
        </BrowserRouter>
        </NotificationProvider>
      </QueryProvider>
    </ErrorBoundary>
  );
}

export default App;
