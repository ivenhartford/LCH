import React from 'react';
import { Box, Typography, Grid, Card, CardContent, CardActions, Button } from '@mui/material';
import {
  CalendarMonth as CalendarIcon,
  People as PeopleIcon,
  Pets as PetsIcon,
  Receipt as ReceiptIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

/**
 * Dashboard Component
 *
 * Main dashboard with quick links to major sections.
 */
function Dashboard() {
  const navigate = useNavigate();

  const quickLinks = [
    {
      title: 'Appointments',
      description: 'View and manage appointments',
      icon: <CalendarIcon sx={{ fontSize: 48 }} />,
      path: '/appointments',
      color: 'primary.main',
    },
    {
      title: 'Clients',
      description: 'Manage client information',
      icon: <PeopleIcon sx={{ fontSize: 48 }} />,
      path: '/clients',
      color: 'secondary.main',
    },
    {
      title: 'Patients',
      description: 'View patient records',
      icon: <PetsIcon sx={{ fontSize: 48 }} />,
      path: '/patients',
      color: 'success.main',
    },
    {
      title: 'Invoices',
      description: 'Billing and invoices',
      icon: <ReceiptIcon sx={{ fontSize: 48 }} />,
      path: '/invoices',
      color: 'warning.main',
    },
  ];

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Welcome to Lenox Cat Hospital
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Select a section to get started
      </Typography>

      <Grid container spacing={3} mt={2}>
        {quickLinks.map((link) => (
          <Grid item xs={12} sm={6} md={3} key={link.path}>
            <Card
              sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                cursor: 'pointer',
                '&:hover': {
                  boxShadow: 4,
                  transform: 'translateY(-4px)',
                  transition: 'all 0.2s ease-in-out',
                },
              }}
              onClick={() => navigate(link.path)}
            >
              <CardContent sx={{ flexGrow: 1, textAlign: 'center' }}>
                <Box sx={{ color: link.color, mb: 2 }}>{link.icon}</Box>
                <Typography variant="h6" component="h2" gutterBottom>
                  {link.title}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {link.description}
                </Typography>
              </CardContent>
              <CardActions sx={{ justifyContent: 'center', pb: 2 }}>
                <Button size="small" onClick={() => navigate(link.path)}>
                  Go to {link.title}
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}

export default Dashboard;
