import React from 'react';
import { Alert, AlertTitle, Button, Container, Box, Typography } from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import BugReportIcon from '@mui/icons-material/BugReport';
import logger from '../utils/logger';

/**
 * Error Boundary Component
 *
 * Catches JavaScript errors anywhere in the child component tree,
 * logs those errors, and displays a fallback UI.
 *
 * Features:
 * - Automatic error logging to logger utility
 * - User-friendly error display
 * - Reset/retry functionality
 * - Development vs Production error details
 *
 * Usage:
 *   <ErrorBoundary>
 *     <App />
 *   </ErrorBoundary>
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorCount: 0,
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log the error to our logging utility
    logger.error(
      'React Error Boundary Caught Error',
      error,
      {
        componentStack: errorInfo.componentStack,
        errorCount: this.state.errorCount + 1,
      }
    );

    // Update state with error details
    this.setState({
      error,
      errorInfo,
      errorCount: this.state.errorCount + 1,
    });

    // If error persists, warn user
    if (this.state.errorCount >= 3) {
      logger.warn('Multiple errors caught in Error Boundary', {
        count: this.state.errorCount + 1,
      });
    }
  }

  handleReset = () => {
    logger.info('User reset Error Boundary');
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  handleReload = () => {
    logger.info('User reloading page from Error Boundary');
    window.location.reload();
  };

  handleExportLogs = () => {
    logger.info('User exporting logs from Error Boundary');
    logger.exportLogs();
  };

  render() {
    if (this.state.hasError) {
      const isDevelopment = process.env.NODE_ENV === 'development';

      return (
        <Container maxWidth="md">
          <Box sx={{ mt: 8 }}>
            <Alert severity="error" icon={<BugReportIcon fontSize="large" />}>
              <AlertTitle>
                <Typography variant="h5">Something Went Wrong</Typography>
              </AlertTitle>

              <Typography variant="body1" sx={{ mb: 2 }}>
                We're sorry, but the application encountered an unexpected error.
                The error has been logged and will be investigated.
              </Typography>

              {/* Show error details in development */}
              {isDevelopment && this.state.error && (
                <Box sx={{ mt: 2, mb: 2 }}>
                  <Typography variant="subtitle2" color="error">
                    Error Details (Development Mode):
                  </Typography>
                  <Box
                    component="pre"
                    sx={{
                      p: 2,
                      bgcolor: '#f5f5f5',
                      borderRadius: 1,
                      overflow: 'auto',
                      maxHeight: 200,
                      fontSize: '0.85rem',
                    }}
                  >
                    {this.state.error.toString()}
                    {this.state.errorInfo && (
                      <>
                        {'\n\n'}
                        {this.state.errorInfo.componentStack}
                      </>
                    )}
                  </Box>
                </Box>
              )}

              {/* Action buttons */}
              <Box sx={{ mt: 3, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={this.handleReset}
                  startIcon={<RefreshIcon />}
                >
                  Try Again
                </Button>

                <Button variant="outlined" onClick={this.handleReload}>
                  Reload Page
                </Button>

                {isDevelopment && (
                  <Button variant="outlined" onClick={this.handleExportLogs}>
                    Export Logs
                  </Button>
                )}
              </Box>

              {/* Multiple error warning */}
              {this.state.errorCount >= 3 && (
                <Box sx={{ mt: 2 }}>
                  <Alert severity="warning">
                    This error has occurred {this.state.errorCount} times.
                    You may want to reload the page or contact support.
                  </Alert>
                </Box>
              )}
            </Alert>

            {/* Help text */}
            <Box sx={{ mt: 4 }}>
              <Typography variant="body2" color="text.secondary">
                If this problem persists:
              </Typography>
              <ul>
                <li>
                  <Typography variant="body2" color="text.secondary">
                    Try clearing your browser cache and cookies
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2" color="text.secondary">
                    Make sure you're using a supported browser
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2" color="text.secondary">
                    Contact support with the error details above
                  </Typography>
                </li>
              </ul>
            </Box>
          </Box>
        </Container>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
