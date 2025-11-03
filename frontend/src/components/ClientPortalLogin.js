import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  Alert,
  Tabs,
  Tab,
  Container,
  Link,
} from '@mui/material';
import { Login as LoginIcon, PersonAdd as RegisterIcon } from '@mui/icons-material';
import { setPortalToken, setPortalUser as savePortalUser } from '../utils/portalAuth';

// Validation schemas
const loginSchema = z.object({
  username: z.string().min(1, 'Username or email is required'),
  password: z.string().min(1, 'Password is required'),
});

const registerSchema = z.object({
  client_id: z.number().min(1, 'Client ID is required'),
  username: z.string().min(3, 'Username must be at least 3 characters').max(50),
  email: z.string().email('Invalid email address').max(120),
  password: z.string().min(8, 'Password must be at least 8 characters').max(100),
  password_confirm: z.string().min(8, 'Password confirmation is required'),
}).refine((data) => data.password === data.password_confirm, {
  message: "Passwords don't match",
  path: ['password_confirm'],
});

function TabPanel({ children, value, index }) {
  return (
    <div role="tabpanel" hidden={value !== index}>
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

/**
 * Client Portal Login Component
 *
 * Provides both login and registration for client portal access.
 * Separate from staff login - clients access their own portal to:
 * - View their pets
 * - See appointment history
 * - View invoices
 * - Submit appointment requests
 */
function ClientPortalLogin({ setPortalUser }) {
  const navigate = useNavigate();
  const [tabValue, setTabValue] = useState(0);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Login form
  const {
    control: loginControl,
    handleSubmit: handleLoginSubmit,
    formState: { errors: loginErrors },
  } = useForm({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      username: '',
      password: '',
    },
  });

  // Registration form
  const {
    control: registerControl,
    handleSubmit: handleRegisterSubmit,
    formState: { errors: registerErrors },
  } = useForm({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      client_id: '',
      username: '',
      email: '',
      password: '',
      password_confirm: '',
    },
  });

  const handleLogin = async (data) => {
    setError('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/portal/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      const result = await response.json();

      if (response.ok) {
        // Store JWT token and user info
        if (result.token) {
          setPortalToken(result.token);
        }
        savePortalUser(result.user);
        setPortalUser(result.user);
        navigate('/portal/dashboard');
      } else {
        setError(result.error || 'Login failed');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async (data) => {
    setError('');
    setSuccess('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/portal/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      const result = await response.json();

      if (response.ok) {
        setSuccess('Registration successful! Please log in.');
        setTabValue(0); // Switch to login tab
      } else {
        setError(result.error || 'Registration failed');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Container maxWidth="sm">
      <Box sx={{ mt: 8, mb: 4 }}>
        <Paper elevation={3} sx={{ p: 4 }}>
          <Typography variant="h4" align="center" gutterBottom>
            Client Portal
          </Typography>
          <Typography variant="body2" align="center" color="text.secondary" sx={{ mb: 3 }}>
            Access your pets' medical records and appointment history
          </Typography>

          <Tabs
            value={tabValue}
            onChange={(e, newValue) => {
              setTabValue(newValue);
              setError('');
              setSuccess('');
            }}
            variant="fullWidth"
            sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}
          >
            <Tab icon={<LoginIcon />} label="Login" />
            <Tab icon={<RegisterIcon />} label="Register" />
          </Tabs>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
              {error}
            </Alert>
          )}

          {success && (
            <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>
              {success}
            </Alert>
          )}

          {/* Login Tab */}
          <TabPanel value={tabValue} index={0}>
            <form onSubmit={handleLoginSubmit(handleLogin)}>
              <Controller
                name="username"
                control={loginControl}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Username or Email"
                    fullWidth
                    margin="normal"
                    error={!!loginErrors.username}
                    helperText={loginErrors.username?.message}
                    autoFocus
                  />
                )}
              />

              <Controller
                name="password"
                control={loginControl}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Password"
                    type="password"
                    fullWidth
                    margin="normal"
                    error={!!loginErrors.password}
                    helperText={loginErrors.password?.message}
                  />
                )}
              />

              <Button
                type="submit"
                variant="contained"
                fullWidth
                size="large"
                disabled={isLoading}
                startIcon={<LoginIcon />}
                sx={{ mt: 3, mb: 2 }}
              >
                {isLoading ? 'Logging in...' : 'Login'}
              </Button>

              <Typography variant="body2" align="center" color="text.secondary">
                Don't have an account?{' '}
                <Link
                  component="button"
                  type="button"
                  onClick={() => setTabValue(1)}
                  sx={{ cursor: 'pointer' }}
                >
                  Register here
                </Link>
              </Typography>
            </form>
          </TabPanel>

          {/* Registration Tab */}
          <TabPanel value={tabValue} index={1}>
            <form onSubmit={handleRegisterSubmit(handleRegister)}>
              <Alert severity="info" sx={{ mb: 2 }}>
                You'll need your Client ID (available from your clinic) to register.
              </Alert>

              <Controller
                name="client_id"
                control={registerControl}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Client ID"
                    type="number"
                    fullWidth
                    margin="normal"
                    error={!!registerErrors.client_id}
                    helperText={registerErrors.client_id?.message || 'Provided by the clinic'}
                    autoFocus
                  />
                )}
              />

              <Controller
                name="username"
                control={registerControl}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Username"
                    fullWidth
                    margin="normal"
                    error={!!registerErrors.username}
                    helperText={registerErrors.username?.message}
                  />
                )}
              />

              <Controller
                name="email"
                control={registerControl}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Email"
                    type="email"
                    fullWidth
                    margin="normal"
                    error={!!registerErrors.email}
                    helperText={registerErrors.email?.message}
                  />
                )}
              />

              <Controller
                name="password"
                control={registerControl}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Password"
                    type="password"
                    fullWidth
                    margin="normal"
                    error={!!registerErrors.password}
                    helperText={registerErrors.password?.message || 'Minimum 8 characters'}
                  />
                )}
              />

              <Controller
                name="password_confirm"
                control={registerControl}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Confirm Password"
                    type="password"
                    fullWidth
                    margin="normal"
                    error={!!registerErrors.password_confirm}
                    helperText={registerErrors.password_confirm?.message}
                  />
                )}
              />

              <Button
                type="submit"
                variant="contained"
                fullWidth
                size="large"
                disabled={isLoading}
                startIcon={<RegisterIcon />}
                sx={{ mt: 3, mb: 2 }}
              >
                {isLoading ? 'Registering...' : 'Register'}
              </Button>

              <Typography variant="body2" align="center" color="text.secondary">
                Already have an account?{' '}
                <Link
                  component="button"
                  type="button"
                  onClick={() => setTabValue(0)}
                  sx={{ cursor: 'pointer' }}
                >
                  Login here
                </Link>
              </Typography>
            </form>
          </TabPanel>
        </Paper>

        <Typography variant="body2" align="center" color="text.secondary" sx={{ mt: 4 }}>
          Need help? Contact Lenox Cat Hospital at (555) 123-4567
        </Typography>
      </Box>
    </Container>
  );
}

export default ClientPortalLogin;
