import React from 'react';
import { Box, CircularProgress, Typography } from '@mui/material';

/**
 * LoadingFallback Component
 *
 * Displays while lazy-loaded components are being fetched.
 * Used with React.Suspense for code splitting.
 */
function LoadingFallback({ message = 'Loading...' }) {
  return (
    <Box
      display="flex"
      flexDirection="column"
      justifyContent="center"
      alignItems="center"
      minHeight="400px"
      gap={2}
    >
      <CircularProgress size={48} />
      <Typography variant="body1" color="text.secondary">
        {message}
      </Typography>
    </Box>
  );
}

export default LoadingFallback;
