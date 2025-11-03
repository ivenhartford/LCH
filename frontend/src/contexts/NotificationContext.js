import React, { createContext, useContext, useState, useCallback } from 'react';
import { Snackbar, Alert, Slide } from '@mui/material';

/**
 * Notification Context
 *
 * Provides a unified toast notification system for the application.
 * Replaces inconsistent error handling patterns (inline alerts, window.alert, console.log).
 *
 * Features:
 * - Success, error, warning, and info notifications
 * - Auto-dismiss after 6 seconds
 * - Manual dismiss option
 * - Queue support (shows notifications one at a time)
 * - Slide-up animation
 * - Material-UI themed
 *
 * Usage:
 * ```jsx
 * const { showNotification } = useNotification();
 *
 * // Success
 * showNotification('Client created successfully', 'success');
 *
 * // Error
 * showNotification('Failed to save changes', 'error');
 *
 * // Warning
 * showNotification('Session will expire soon', 'warning');
 *
 * // Info
 * showNotification('Loading data...', 'info');
 * ```
 */

const NotificationContext = createContext();

export const useNotification = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within NotificationProvider');
  }
  return context;
};

function SlideTransition(props) {
  return <Slide {...props} direction="up" />;
}

export const NotificationProvider = ({ children }) => {
  const [notification, setNotification] = useState({
    open: false,
    message: '',
    severity: 'info', // 'success' | 'error' | 'warning' | 'info'
  });

  const [queue, setQueue] = useState([]);

  const showNotification = useCallback((message, severity = 'info') => {
    // If a notification is already showing, add to queue
    setQueue((prevQueue) => {
      if (notification.open) {
        return [...prevQueue, { message, severity }];
      }
      // Otherwise show immediately
      setNotification({ open: true, message, severity });
      return prevQueue;
    });
  }, [notification.open]);

  const handleClose = (event, reason) => {
    // Don't close on clickaway - only on explicit close or timeout
    if (reason === 'clickaway') {
      return;
    }

    setNotification((prev) => ({ ...prev, open: false }));
  };

  const handleExited = () => {
    // When notification is fully closed, show next in queue if any
    if (queue.length > 0) {
      const [next, ...rest] = queue;
      setNotification({ open: true, message: next.message, severity: next.severity });
      setQueue(rest);
    }
  };

  return (
    <NotificationContext.Provider value={{ showNotification }}>
      {children}
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={handleClose}
        TransitionComponent={SlideTransition}
        TransitionProps={{
          onExited: handleExited,
        }}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'center',
        }}
        sx={{
          // Ensure toast is above everything
          zIndex: (theme) => theme.zIndex.snackbar,
        }}
      >
        <Alert
          onClose={handleClose}
          severity={notification.severity}
          variant="filled"
          elevation={6}
          sx={{
            width: '100%',
            minWidth: { xs: '90vw', sm: '400px' },
            maxWidth: { xs: '90vw', sm: '600px' },
          }}
        >
          {notification.message}
        </Alert>
      </Snackbar>
    </NotificationContext.Provider>
  );
};

export default NotificationContext;
