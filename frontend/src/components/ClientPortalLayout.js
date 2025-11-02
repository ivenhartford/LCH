import React from 'react';
import { Outlet, useNavigate, NavLink } from 'react-router-dom';
import {
  Box,
  AppBar,
  Toolbar,
  Typography,
  Button,
  Container,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  Avatar,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Pets as PetsIcon,
  Event as EventIcon,
  Receipt as ReceiptIcon,
  RequestPage as RequestIcon,
  Logout as LogoutIcon,
} from '@mui/icons-material';

const drawerWidth = 240;

const menuItems = [
  { path: '/portal/dashboard', label: 'Dashboard', icon: <DashboardIcon /> },
  { path: '/portal/patients', label: 'My Pets', icon: <PetsIcon /> },
  { path: '/portal/appointments', label: 'Appointments', icon: <EventIcon /> },
  { path: '/portal/invoices', label: 'Invoices', icon: <ReceiptIcon /> },
  { path: '/portal/request-appointment', label: 'Request Appointment', icon: <RequestIcon /> },
];

/**
 * Client Portal Layout Component
 *
 * Provides navigation wrapper for client portal pages.
 * Includes sidebar navigation and top app bar with user info.
 */
function ClientPortalLayout({ portalUser, setPortalUser }) {
  const navigate = useNavigate();

  const handleLogout = () => {
    setPortalUser(null);
    localStorage.removeItem('portalUser');
    navigate('/portal/login');
  };

  if (!portalUser) {
    navigate('/portal/login');
    return null;
  }

  return (
    <Box sx={{ display: 'flex' }}>
      {/* App Bar */}
      <AppBar
        position="fixed"
        sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}
      >
        <Toolbar>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            Lenox Cat Hospital - Client Portal
          </Typography>
          <Typography variant="body2" sx={{ mr: 2 }}>
            {portalUser?.client_name}
          </Typography>
          <Avatar sx={{ bgcolor: 'secondary.main', mr: 2 }}>
            {portalUser?.username?.charAt(0).toUpperCase()}
          </Avatar>
          <Button
            color="inherit"
            startIcon={<LogoutIcon />}
            onClick={handleLogout}
          >
            Logout
          </Button>
        </Toolbar>
      </AppBar>

      {/* Sidebar */}
      <Drawer
        variant="permanent"
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
          },
        }}
      >
        <Toolbar /> {/* Spacer for AppBar */}
        <Box sx={{ overflow: 'auto' }}>
          <List>
            {menuItems.map((item) => (
              <ListItem key={item.path} disablePadding>
                <ListItemButton
                  component={NavLink}
                  to={item.path}
                  sx={{
                    '&.active': {
                      bgcolor: 'action.selected',
                      '& .MuiListItemIcon-root': {
                        color: 'primary.main',
                      },
                    },
                  }}
                >
                  <ListItemIcon>{item.icon}</ListItemIcon>
                  <ListItemText primary={item.label} />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
          <Divider />
          <List>
            <ListItem disablePadding>
              <ListItemButton onClick={handleLogout}>
                <ListItemIcon>
                  <LogoutIcon />
                </ListItemIcon>
                <ListItemText primary="Logout" />
              </ListItemButton>
            </ListItem>
          </List>
        </Box>
      </Drawer>

      {/* Main Content */}
      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        <Toolbar /> {/* Spacer for AppBar */}
        <Container maxWidth="lg">
          <Outlet />
        </Container>
      </Box>
    </Box>
  );
}

export default ClientPortalLayout;
