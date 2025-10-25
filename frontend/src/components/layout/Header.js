import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Menu,
  MenuItem,
  Avatar,
  Box,
  Divider,
} from '@mui/material';
import {
  Menu as MenuIcon,
  AccountCircle,
  ExitToApp,
  Settings,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import logger from '../../utils/logger';

/**
 * Header Component
 *
 * Top navigation bar with application title, user menu, and mobile menu toggle.
 *
 * Props:
 * - user: Current user object { username, role }
 * - onMenuToggle: Function to toggle mobile drawer
 * - onLogout: Function to handle logout
 *
 * Features:
 * - User profile menu
 * - Logout functionality
 * - Mobile drawer toggle
 * - Comprehensive logging
 */
const Header = ({ user, onMenuToggle, onLogout }) => {
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = React.useState(null);

  React.useEffect(() => {
    logger.logLifecycle('Header', 'mounted', { user: user?.username });
    return () => {
      logger.logLifecycle('Header', 'unmounted');
    };
  }, [user]);

  const handleMenuOpen = (event) => {
    logger.logAction('User menu opened', { username: user?.username });
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    logger.logAction('User menu closed');
    setAnchorEl(null);
  };

  const handleLogout = async () => {
    logger.info('User initiated logout', { username: user?.username });
    handleMenuClose();

    try {
      if (onLogout) {
        await onLogout();
      }
      logger.info('Logout successful');
    } catch (error) {
      logger.error('Logout failed', error);
    }
  };

  const handleSettings = () => {
    logger.logAction('Navigate to settings');
    handleMenuClose();
    navigate('/settings');
  };

  const handleProfile = () => {
    logger.logAction('Navigate to profile');
    handleMenuClose();
    navigate('/profile');
  };

  const getUserInitials = () => {
    if (!user?.username) return '?';
    return user.username.substring(0, 2).toUpperCase();
  };

  const isMenuOpen = Boolean(anchorEl);

  return (
    <AppBar
      position="fixed"
      sx={{
        zIndex: (theme) => theme.zIndex.drawer + 1,
      }}
    >
      <Toolbar>
        {/* Mobile menu toggle */}
        <IconButton
          color="inherit"
          aria-label="open drawer"
          edge="start"
          onClick={onMenuToggle}
          sx={{ mr: 2, display: { sm: 'none' } }}
        >
          <MenuIcon />
        </IconButton>

        {/* Application title */}
        <Typography
          variant="h6"
          noWrap
          component="div"
          sx={{ flexGrow: 1 }}
        >
          Lenox Cat Hospital
        </Typography>

        {/* User info and menu */}
        {user && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="body2" sx={{ display: { xs: 'none', sm: 'block' } }}>
              {user.username}
            </Typography>

            <IconButton
              size="large"
              aria-label="account of current user"
              aria-controls="user-menu"
              aria-haspopup="true"
              onClick={handleMenuOpen}
              color="inherit"
            >
              <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.dark' }}>
                {getUserInitials()}
              </Avatar>
            </IconButton>
          </Box>
        )}

        {/* User menu */}
        <Menu
          id="user-menu"
          anchorEl={anchorEl}
          open={isMenuOpen}
          onClose={handleMenuClose}
          anchorOrigin={{
            vertical: 'bottom',
            horizontal: 'right',
          }}
          transformOrigin={{
            vertical: 'top',
            horizontal: 'right',
          }}
        >
          {user && (
            <Box sx={{ px: 2, py: 1 }}>
              <Typography variant="subtitle2">{user.username}</Typography>
              <Typography variant="caption" color="text.secondary">
                {user.role || 'User'}
              </Typography>
            </Box>
          )}
          <Divider />
          <MenuItem onClick={handleProfile}>
            <AccountCircle sx={{ mr: 1 }} />
            Profile
          </MenuItem>
          <MenuItem onClick={handleSettings}>
            <Settings sx={{ mr: 1 }} />
            Settings
          </MenuItem>
          <Divider />
          <MenuItem onClick={handleLogout}>
            <ExitToApp sx={{ mr: 1 }} />
            Logout
          </MenuItem>
        </Menu>
      </Toolbar>
    </AppBar>
  );
};

export default Header;
