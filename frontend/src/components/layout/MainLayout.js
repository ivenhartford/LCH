import React, { useState, useEffect } from 'react';
import { Box, Toolbar, CssBaseline } from '@mui/material';
import { ThemeProvider } from '@mui/material/styles';
import Header from './Header';
import Sidebar, { drawerWidth } from './Sidebar';
import GlobalSearch from '../GlobalSearch';
import theme from '../../theme';
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
 * - Global search (Ctrl/Cmd+K)
 * - Keyboard shortcuts
 * - Clean, modern Material-UI theme
 * - Comprehensive logging
 */

const MainLayout = ({ user, onLogout, children }) => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);

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

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event) => {
      // Ctrl/Cmd + K: Open global search
      if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
        event.preventDefault();
        logger.logAction('Global search opened via keyboard shortcut');
        setSearchOpen(true);
      }

      // ESC: Close search
      if (event.key === 'Escape' && searchOpen) {
        setSearchOpen(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [searchOpen]);

  return (
    <ThemeProvider theme={theme}>
      <Box sx={{ display: 'flex' }}>
        <CssBaseline />

        {/* Header */}
        <Header
          user={user}
          onMenuToggle={handleDrawerToggle}
          onLogout={onLogout}
          onSearchClick={() => setSearchOpen(true)}
        />

        {/* Sidebar */}
        <Sidebar
          open={mobileOpen}
          onClose={handleDrawerClose}
        />

        {/* Global Search */}
        <GlobalSearch
          open={searchOpen}
          onClose={() => setSearchOpen(false)}
        />

        {/* Main content area */}
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            p: 3,
            width: { sm: `calc(100% - ${drawerWidth}px)` },
            minHeight: '100vh',
            backgroundColor: 'background.default',
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
