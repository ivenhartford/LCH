import React from 'react';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import { Breadcrumbs as MuiBreadcrumbs, Link, Typography, Box } from '@mui/material';
import { NavigateNext as NavigateNextIcon, Home as HomeIcon } from '@mui/icons-material';

/**
 * Breadcrumbs Component
 *
 * Displays navigation breadcrumbs based on current route.
 * Automatically generates breadcrumb trail from URL path.
 */

const routeLabels = {
  dashboard: 'Dashboard',
  calendar: 'Calendar',
  clients: 'Clients',
  patients: 'Patients',
  appointments: 'Appointments',
  'medical-records': 'Medical Records',
  invoices: 'Invoices',
  inventory: 'Inventory',
  staff: 'Staff',
  reports: 'Reports',
  settings: 'Settings',
  profile: 'Profile',
  new: 'New',
  edit: 'Edit',
};

const Breadcrumbs = () => {
  const location = useLocation();
  const pathnames = location.pathname.split('/').filter((x) => x);

  // Don't show breadcrumbs on home page
  if (pathnames.length === 0) {
    return null;
  }

  return (
    <Box sx={{ mb: 2 }}>
      <MuiBreadcrumbs separator={<NavigateNextIcon fontSize="small" />} aria-label="breadcrumb">
        {/* Home link */}
        <Link
          component={RouterLink}
          to="/"
          underline="hover"
          sx={{ display: 'flex', alignItems: 'center' }}
          color="inherit"
        >
          <HomeIcon sx={{ mr: 0.5 }} fontSize="small" />
          Home
        </Link>

        {/* Dynamic path segments */}
        {pathnames.map((value, index) => {
          const last = index === pathnames.length - 1;
          const to = `/${pathnames.slice(0, index + 1).join('/')}`;

          // Skip numeric IDs and "edit" on the same level
          const isNumeric = !isNaN(Number(value));
          const label =
            routeLabels[value] ||
            (isNumeric ? `#${value}` : value.charAt(0).toUpperCase() + value.slice(1));

          return last ? (
            <Typography color="text.primary" key={to}>
              {label}
            </Typography>
          ) : (
            <Link component={RouterLink} underline="hover" color="inherit" to={to} key={to}>
              {label}
            </Link>
          );
        })}
      </MuiBreadcrumbs>
    </Box>
  );
};

export default Breadcrumbs;
