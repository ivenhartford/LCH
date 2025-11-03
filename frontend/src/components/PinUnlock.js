import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Typography,
  Alert,
  Box,
} from '@mui/material';
import { LockClock as LockIcon } from '@mui/icons-material';
import { portalFetch } from '../utils/portalApi';
import { clearPortalAuth } from '../utils/portalAuth';

/**
 * PIN Unlock Component
 *
 * Appears after 15 minutes of inactivity to require PIN re-authentication.
 * If PIN verification fails or session has expired, redirects to login.
 */
function PinUnlock({ open, onUnlock, onSessionExpired }) {
  const [pin, setPin] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Clear PIN field when dialog opens
  useEffect(() => {
    if (open) {
      setPin('');
      setError('');
    }
  }, [open]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!pin) {
      setError('Please enter your PIN');
      return;
    }

    setLoading(true);

    try {
      const response = await portalFetch('/verify-pin', {
        method: 'POST',
        body: JSON.stringify({ pin }),
      });

      const data = await response.json();

      if (response.ok) {
        setPin('');
        if (onUnlock) {
          onUnlock();
        }
      } else if (data.session_expired) {
        // Session has expired, redirect to login
        setError('Session expired. Redirecting to login...');
        setTimeout(() => {
          clearPortalAuth();
          if (onSessionExpired) {
            onSessionExpired();
          }
        }, 2000);
      } else {
        setError(data.error || 'Invalid PIN');
        setPin('');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    clearPortalAuth();
    if (onSessionExpired) {
      onSessionExpired();
    }
  };

  return (
    <Dialog
      open={open}
      disableEscapeKeyDown
      maxWidth="xs"
      fullWidth
      PaperProps={{
        sx: { bgcolor: 'background.paper' },
      }}
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" gap={1}>
          <LockIcon />
          <span>Session Locked</span>
        </Box>
      </DialogTitle>

      <form onSubmit={handleSubmit}>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Your session has been locked due to inactivity. Please enter your PIN to
            continue, or log out to return to the login page.
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          <TextField
            label="Enter PIN"
            type="password"
            value={pin}
            onChange={(e) => setPin(e.target.value)}
            fullWidth
            margin="normal"
            inputProps={{
              maxLength: 6,
              inputMode: 'numeric',
              pattern: '[0-9]*',
            }}
            helperText="Enter your 4-6 digit PIN"
            autoFocus
            required
            disabled={loading}
          />
        </DialogContent>

        <DialogActions>
          <Button onClick={handleLogout} color="error" disabled={loading}>
            Log Out
          </Button>
          <Button
            type="submit"
            variant="contained"
            disabled={loading}
            startIcon={<LockIcon />}
          >
            {loading ? 'Verifying...' : 'Unlock'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}

export default PinUnlock;
