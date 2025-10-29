import React from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Divider,
  Box,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  People as PeopleIcon,
  Pets as PetsIcon,
  CalendarMonth as CalendarIcon,
  MedicalServices as MedicalIcon,
  Medication as MedicationIcon,
  Receipt as ReceiptIcon,
  Inventory as InventoryIcon,
  Category as CategoryIcon,
  LocalShipping as LocalShippingIcon,
  ShoppingCart as ShoppingCartIcon,
  Group as GroupIcon,
  Science as ScienceIcon,
  Biotech as BiotechIcon,
  Notifications as NotificationsIcon,
  Email as EmailIcon,
  Assessment as AssessmentIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import logger from '../../utils/logger';

/**
 * Sidebar Component
 *
 * Navigation sidebar with all main application routes.
 *
 * Props:
 * - open: Boolean - Whether drawer is open (mobile)
 * - onClose: Function - Handle drawer close (mobile)
 * - drawerWidth: Number - Width of drawer in pixels
 *
 * Features:
 * - Responsive drawer (permanent on desktop, temporary on mobile)
 * - Active route highlighting
 * - Icon-based navigation
 * - Comprehensive logging of navigation
 */

const drawerWidth = 240;

const Sidebar = ({ open, onClose }) => {
  const navigate = useNavigate();
  const location = useLocation();

  React.useEffect(() => {
    logger.logLifecycle('Sidebar', 'mounted');
    return () => {
      logger.logLifecycle('Sidebar', 'unmounted');
    };
  }, []);

  // Navigation items organized by section
  const navigationItems = [
    {
      section: 'Main',
      items: [
        { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
        { text: 'Calendar', icon: <CalendarIcon />, path: '/calendar' },
      ],
    },
    {
      section: 'Management',
      items: [
        { text: 'Clients', icon: <PeopleIcon />, path: '/clients' },
        { text: 'Patients', icon: <PetsIcon />, path: '/patients' },
      ],
    },
    {
      section: 'Clinical',
      items: [
        { text: 'Visits', icon: <MedicalIcon />, path: '/visits' },
        { text: 'Appointments', icon: <CalendarIcon />, path: '/appointments' },
        { text: 'Medications', icon: <MedicationIcon />, path: '/medications' },
        { text: 'Services', icon: <InventoryIcon />, path: '/services' },
      ],
    },
    {
      section: 'Financial',
      items: [{ text: 'Invoices', icon: <ReceiptIcon />, path: '/invoices' }],
    },
    {
      section: 'Inventory',
      items: [
        { text: 'Dashboard', icon: <InventoryIcon />, path: '/inventory' },
        { text: 'Products', icon: <CategoryIcon />, path: '/products' },
        { text: 'Vendors', icon: <LocalShippingIcon />, path: '/vendors' },
        { text: 'Purchase Orders', icon: <ShoppingCartIcon />, path: '/purchase-orders' },
      ],
    },
    {
      section: 'Staff',
      items: [
        { text: 'Staff Directory', icon: <GroupIcon />, path: '/staff' },
        { text: 'Schedule', icon: <CalendarIcon />, path: '/staff-schedule' },
      ],
    },
    {
      section: 'Laboratory',
      items: [
        { text: 'Lab Tests', icon: <ScienceIcon />, path: '/lab-tests' },
        { text: 'Lab Results', icon: <BiotechIcon />, path: '/lab-results' },
      ],
    },
    {
      section: 'Reminders',
      items: [
        { text: 'Reminders', icon: <NotificationsIcon />, path: '/reminders' },
        { text: 'Templates', icon: <EmailIcon />, path: '/notification-templates' },
      ],
    },
    {
      section: 'Reports',
      items: [{ text: 'Reports', icon: <AssessmentIcon />, path: '/reports' }],
    },
  ];

  const handleNavigation = (path, text) => {
    logger.logAction('Navigation clicked', { from: location.pathname, to: path, item: text });
    navigate(path);
    if (onClose) {
      onClose();
    }
  };

  const isSelected = (path) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  const drawerContent = (
    <Box>
      <Toolbar /> {/* Spacer for AppBar */}
      {navigationItems.map((section, sectionIndex) => (
        <Box key={section.section}>
          {sectionIndex > 0 && <Divider sx={{ my: 1 }} />}

          {/* Section Header */}
          <ListItem>
            <ListItemText
              primary={section.section}
              primaryTypographyProps={{
                variant: 'caption',
                color: 'text.secondary',
                fontWeight: 'bold',
                sx: { pl: 2 },
              }}
            />
          </ListItem>

          {/* Section Items */}
          <List disablePadding>
            {section.items.map((item) => (
              <ListItem key={item.text} disablePadding>
                <ListItemButton
                  selected={isSelected(item.path)}
                  onClick={() => handleNavigation(item.path, item.text)}
                  sx={{
                    '&.Mui-selected': {
                      backgroundColor: 'primary.light',
                      '&:hover': {
                        backgroundColor: 'primary.light',
                      },
                    },
                  }}
                >
                  <ListItemIcon
                    sx={{
                      color: isSelected(item.path) ? 'primary.main' : 'inherit',
                    }}
                  >
                    {item.icon}
                  </ListItemIcon>
                  <ListItemText
                    primary={item.text}
                    primaryTypographyProps={{
                      fontWeight: isSelected(item.path) ? 'bold' : 'normal',
                    }}
                  />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        </Box>
      ))}
      <Divider sx={{ my: 1 }} />
      {/* Settings at bottom */}
      <List>
        <ListItem disablePadding>
          <ListItemButton
            selected={isSelected('/settings')}
            onClick={() => handleNavigation('/settings', 'Settings')}
          >
            <ListItemIcon>
              <SettingsIcon />
            </ListItemIcon>
            <ListItemText primary="Settings" />
          </ListItemButton>
        </ListItem>
      </List>
    </Box>
  );

  return (
    <>
      {/* Mobile drawer */}
      <Drawer
        variant="temporary"
        open={open}
        onClose={onClose}
        ModalProps={{
          keepMounted: true, // Better mobile performance
        }}
        sx={{
          display: { xs: 'block', sm: 'none' },
          '& .MuiDrawer-paper': {
            boxSizing: 'border-box',
            width: drawerWidth,
          },
        }}
      >
        {drawerContent}
      </Drawer>

      {/* Desktop drawer */}
      <Drawer
        variant="permanent"
        sx={{
          display: { xs: 'none', sm: 'block' },
          width: drawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
          },
        }}
        open
      >
        {drawerContent}
      </Drawer>
    </>
  );
};

export default Sidebar;
export { drawerWidth };
