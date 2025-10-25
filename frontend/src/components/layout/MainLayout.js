import React, { useState } from 'react';
import { Box, Toolbar, CssBaseline } from '@mui/material';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import Header from './Header';
import Sidebar, { drawerWidth } from './Sidebar';
import logger from '../../utils/logger';

/**
 * MainLayout Component
 *
 * Main application layout with responsive sidebar and header.
 *
 * Props:
 * - user: Current user object
 * - onLogout: Logout handler function
 * - children: Child components to render in main content area
 *
 * Features:
 * - Responsive design (mobile-friendly)
 * - Persistent sidebar on desktop
 * - Temporary drawer on mobile
 * - Material-UI theme integration
 * - Comprehensive logging
 */

// Create Material-UI theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2', // Blue
    },
    secondary: {
      main: '#dc004e', // Pink/Red
    },
  },
  typography: {
    fontFamily: [
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none', // Disable uppercase
        },
      },
    },
  },
});

const MainLayout = ({ user, onLogout, children }) => {
  const [mobileOpen, setMobileOpen] = useState(false);

  React.useEffect(() => {
    logger.logLifecycle('MainLayout', 'mounted', {
      user: user?.username,
      viewport: `${window.innerWidth}x${window.innerHeight}`,
    });

    // Log viewport changes
    const handleResize = () => {
      logger.debug('Viewport resized', {
        width: window.innerWidth,
        height: window.innerHeight,
      });
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      logger.logLifecycle('MainLayout', 'unmounted');
    };
  }, [user]);

  const handleDrawerToggle = () => {
    logger.logAction('Mobile drawer toggled', { open: !mobileOpen });
    setMobileOpen(!mobileOpen);
  };

  const handleDrawerClose = () => {
    logger.logAction('Mobile drawer closed');
    setMobileOpen(false);
  };

  return (
    <ThemeProvider theme={theme}>
      <Box sx={{ display: 'flex' }}>
        <CssBaseline />

        {/* Header */}
        <Header
          user={user}
          onMenuToggle={handleDrawerToggle}
          onLogout={onLogout}
        />

        {/* Sidebar */}
        <Sidebar
          open={mobileOpen}
          onClose={handleDrawerClose}
        />

        {/* Main content area */}
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            p: 3,
            width: { sm: `calc(100% - ${drawerWidth}px)` },
            minHeight: '100vh',
            backgroundColor: (theme) =>
              theme.palette.mode === 'light'
                ? theme.palette.grey[100]
                : theme.palette.grey[900],
          }}
        >
          <Toolbar /> {/* Spacer for AppBar */}
          {children}
        </Box>
      </Box>
    </ThemeProvider>
  );
};

export default MainLayout;
