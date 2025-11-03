import React, { useState } from 'react';
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
import { Lock as LockIcon } from '@mui/icons-material';
import { portalFetch } from '../utils/portalApi';

/**
 * PIN Setup Component
 *
 * Allows users to set up a 4-6 digit PIN for quick re-authentication
 * after idle timeout (15 minutes). This prevents having to log in
 * repeatedly while still maintaining security.
 */
function PinSetup({ open, onClose, onSuccess }) {
  const [pin, setPin] = useState('');
  const [confirmPin, setConfirmPin] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Validate PIN
    if (!pin || pin.length < 4 || pin.length > 6) {
      setError('PIN must be 4-6 digits');
      return;
    }

    if (!/^\d+$/.test(pin)) {
      setError('PIN must contain only numbers');
      return;
    }

    if (pin !== confirmPin) {
      setError('PINs do not match');
      return;
    }

    setLoading(true);

    try {
      const response = await portalFetch('/set-pin', {
        method: 'POST',
        body: JSON.stringify({ pin }),
      });

      if (response.ok) {
        if (onSuccess) {
          onSuccess();
        }
        handleClose();
      } else {
        const data = await response.json();
        setError(data.error || 'Failed to set PIN');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setPin('');
    setConfirmPin('');
    setError('');
    if (onClose) {
      onClose();
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="xs" fullWidth>
      <DialogTitle>
        <Box display="flex" alignItems="center" gap={1}>
          <LockIcon />
          <span>Set Up PIN</span>
        </Box>
      </DialogTitle>

      <form onSubmit={handleSubmit}>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Set up a 4-6 digit PIN for quick re-authentication after 15 minutes of
            inactivity. This keeps you logged in for up to 8 hours without requiring
            your full password.
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
              {error}
            </Alert>
          )}

          <TextField
            label="PIN"
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
            helperText="Enter 4-6 digits"
            autoFocus
            required
          />

          <TextField
            label="Confirm PIN"
            type="password"
            value={confirmPin}
            onChange={(e) => setConfirmPin(e.target.value)}
            fullWidth
            margin="normal"
            inputProps={{
              maxLength: 6,
              inputMode: 'numeric',
              pattern: '[0-9]*',
            }}
            helperText="Re-enter your PIN"
            required
          />
        </DialogContent>

        <DialogActions>
          <Button onClick={handleClose} disabled={loading}>
            Skip for Now
          </Button>
          <Button
            type="submit"
            variant="contained"
            disabled={loading}
            startIcon={<LockIcon />}
          >
            {loading ? 'Setting PIN...' : 'Set PIN'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}

export default PinSetup;
