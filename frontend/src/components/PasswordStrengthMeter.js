import React from 'react';
import { Box, LinearProgress, Typography } from '@mui/material';

/**
 * Password Strength Meter Component
 *
 * Displays visual feedback for password strength based on complexity requirements
 */
function PasswordStrengthMeter({ password }) {
  const calculateStrength = (pwd) => {
    if (!pwd) return { score: 0, label: '', color: '' };

    let score = 0;

    // Length check
    if (pwd.length >= 8) score += 1;
    if (pwd.length >= 12) score += 1;

    // Complexity checks
    if (/[A-Z]/.test(pwd)) score += 1; // Uppercase
    if (/[a-z]/.test(pwd)) score += 1; // Lowercase
    if (/\d/.test(pwd)) score += 1; // Number
    if (/[!@#$%^&*()_+\-=\[\]{};':",.<>?/\\|`~]/.test(pwd)) score += 1; // Special char

    // Cap at 5
    score = Math.min(score, 5);

    const strengthLevels = {
      0: { label: '', color: '', value: 0 },
      1: { label: 'Very Weak', color: 'error', value: 20 },
      2: { label: 'Weak', color: 'error', value: 40 },
      3: { label: 'Fair', color: 'warning', value: 60 },
      4: { label: 'Good', color: 'info', value: 80 },
      5: { label: 'Strong', color: 'success', value: 100 },
    };

    return strengthLevels[score];
  };

  const strength = calculateStrength(password);

  if (!password) {
    return null;
  }

  return (
    <Box sx={{ mt: 1, mb: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 0.5 }}>
        <Typography variant="caption" color="text.secondary">
          Password Strength:
        </Typography>
        <Typography variant="caption" color={`${strength.color}.main`} fontWeight="bold">
          {strength.label}
        </Typography>
      </Box>
      <LinearProgress
        variant="determinate"
        value={strength.value}
        color={strength.color}
        sx={{ height: 6, borderRadius: 1 }}
      />
      <Box sx={{ mt: 1 }}>
        <Typography variant="caption" color="text.secondary">
          Password must contain:
        </Typography>
        <Box component="ul" sx={{ mt: 0.5, pl: 2, mb: 0 }}>
          <Typography
            component="li"
            variant="caption"
            color={password.length >= 8 ? 'success.main' : 'text.secondary'}
          >
            At least 8 characters
          </Typography>
          <Typography
            component="li"
            variant="caption"
            color={/[A-Z]/.test(password) ? 'success.main' : 'text.secondary'}
          >
            One uppercase letter
          </Typography>
          <Typography
            component="li"
            variant="caption"
            color={/[a-z]/.test(password) ? 'success.main' : 'text.secondary'}
          >
            One lowercase letter
          </Typography>
          <Typography
            component="li"
            variant="caption"
            color={/\d/.test(password) ? 'success.main' : 'text.secondary'}
          >
            One number
          </Typography>
          <Typography
            component="li"
            variant="caption"
            color={
              /[!@#$%^&*()_+\-=\[\]{};':",.<>?/\\|`~]/.test(password)
                ? 'success.main'
                : 'text.secondary'
            }
          >
            One special character (!@#$%^&*...)
          </Typography>
        </Box>
      </Box>
    </Box>
  );
}

export default PasswordStrengthMeter;
