import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  TextField,
  Button,
  Typography,
  Container,
  Paper,
  CircularProgress,
  InputAdornment,
  IconButton
} from '@mui/material';
import { Visibility, VisibilityOff } from '@mui/icons-material';
import { useNotification } from '../contexts/NotificationContext';

function Login({ setUser }) {
  const { showNotification } = useNotification();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const usernameRef = React.useRef(null);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Basic validation
    if (!username.trim()) {
      showNotification('Username is required', 'error');
      if (usernameRef.current) {
        usernameRef.current.focus();
      }
      return;
    }

    if (!password) {
      showNotification('Password is required', 'error');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      if (response.ok) {
        const user = await fetch('/api/check_session').then((res) => res.json());
        setUser(user);
        showNotification('Login successful', 'success');
        navigate('/');
      } else {
        const data = await response.json();
        showNotification(data.message || 'Login failed. Please check your credentials.', 'error');
        // Focus username field for retry
        if (usernameRef.current) {
          usernameRef.current.focus();
        }
      }
    } catch (err) {
      showNotification('Network error. Please try again.', 'error');
      // Focus username field for retry
      if (usernameRef.current) {
        usernameRef.current.focus();
      }
    } finally {
      setLoading(false);
    }
  };

  const handleTogglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Paper
          elevation={3}
          sx={{
            p: 4,
            width: '100%',
            borderRadius: 2,
          }}
        >
          <Typography
            variant="h4"
            component="h1"
            gutterBottom
            align="center"
            sx={{ mb: 3, fontWeight: 600 }}
          >
            Lenox Cat Hospital
          </Typography>

          <Typography
            variant="h6"
            component="h2"
            gutterBottom
            align="center"
            color="text.secondary"
            sx={{ mb: 4 }}
          >
            Staff Login
          </Typography>

          <Box component="form" onSubmit={handleSubmit} noValidate>
            <TextField
              id="username"
              label="Username"
              variant="outlined"
              fullWidth
              required
              margin="normal"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={loading}
              autoComplete="username"
              autoFocus
              inputRef={usernameRef}
              sx={{ mb: 2 }}
            />

            <TextField
              id="password"
              label="Password"
              type={showPassword ? 'text' : 'password'}
              variant="outlined"
              fullWidth
              required
              margin="normal"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
              autoComplete="current-password"
              sx={{ mb: 3 }}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      aria-label={showPassword ? 'Hide password' : 'Show password'}
                      onClick={handleTogglePasswordVisibility}
                      edge="end"
                      disabled={loading}
                    >
                      {showPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />

            <Button
              type="submit"
              variant="contained"
              fullWidth
              size="large"
              disabled={loading}
              sx={{
                mt: 2,
                py: 1.5,
                textTransform: 'none',
                fontSize: '1rem',
                fontWeight: 600,
              }}
            >
              {loading ? (
                <>
                  <CircularProgress size={20} sx={{ mr: 1 }} color="inherit" />
                  Logging in...
                </>
              ) : (
                'Login'
              )}
            </Button>
          </Box>

          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              Authorized staff only
            </Typography>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
}

export default Login;
