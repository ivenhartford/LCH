import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Typography,
  Grid,
  Paper,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  List,
  ListItem,
  ListItemText,
  CircularProgress,
  Alert,
  Divider,
} from '@mui/material';
import {
  Pets as PetsIcon,
  Event as EventIcon,
  Receipt as ReceiptIcon,
  RequestPage as RequestIcon,
  ArrowForward as ArrowForwardIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { portalApi } from '../utils/portalApi';

/**
 * Client Portal Dashboard Component
 *
 * Main dashboard for client portal showing:
 * - Summary cards (pets, upcoming appointments, balance due)
 * - Upcoming appointments list
 * - Recent invoices list
 * - Pending appointment requests
 */
function ClientPortalDashboard({ portalUser }) {
  const navigate = useNavigate();

  const { data, isLoading, error } = useQuery({
    queryKey: ['portalDashboard', portalUser?.client_id],
    queryFn: () => portalApi.getDashboard(portalUser.client_id),
    enabled: !!portalUser?.client_id,
  });

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mt: 2 }}>
        Error loading dashboard: {error.message}
      </Alert>
    );
  }

  const { patients, upcoming_appointments, recent_invoices, pending_requests, account_balance } = data || {};

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Welcome, {portalUser?.client_name}!
      </Typography>
      <Typography variant="body1" color="text.secondary" gutterBottom>
        Manage your pets' healthcare from your dashboard
      </Typography>

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <PetsIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">My Pets</Typography>
              </Box>
              <Typography variant="h3">{patients?.length || 0}</Typography>
              <Typography variant="body2" color="text.secondary">
                Active pets
              </Typography>
            </CardContent>
            <CardActions>
              <Button size="small" onClick={() => navigate('/portal/patients')}>
                View All
              </Button>
            </CardActions>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <EventIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Upcoming</Typography>
              </Box>
              <Typography variant="h3">{upcoming_appointments?.length || 0}</Typography>
              <Typography variant="body2" color="text.secondary">
                Appointments
              </Typography>
            </CardContent>
            <CardActions>
              <Button size="small" onClick={() => navigate('/portal/appointments')}>
                View All
              </Button>
            </CardActions>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <ReceiptIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Balance</Typography>
              </Box>
              <Typography variant="h3">${account_balance || '0.00'}</Typography>
              <Typography variant="body2" color="text.secondary">
                Current balance
              </Typography>
            </CardContent>
            <CardActions>
              <Button size="small" onClick={() => navigate('/portal/invoices')}>
                View Invoices
              </Button>
            </CardActions>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <RequestIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Requests</Typography>
              </Box>
              <Typography variant="h3">{pending_requests?.length || 0}</Typography>
              <Typography variant="body2" color="text.secondary">
                Pending requests
              </Typography>
            </CardContent>
            <CardActions>
              <Button size="small" onClick={() => navigate('/portal/request-appointment')}>
                New Request
              </Button>
            </CardActions>
          </Card>
        </Grid>
      </Grid>

      {/* Upcoming Appointments */}
      <Paper sx={{ mt: 4, p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">Upcoming Appointments</Typography>
          <Button
            size="small"
            endIcon={<ArrowForwardIcon />}
            onClick={() => navigate('/portal/appointments')}
          >
            View All
          </Button>
        </Box>
        {upcoming_appointments && upcoming_appointments.length > 0 ? (
          <List>
            {upcoming_appointments.map((apt) => (
              <React.Fragment key={apt.id}>
                <ListItem>
                  <ListItemText
                    primary={apt.title}
                    secondary={
                      <>
                        {format(new Date(apt.start_time), 'PPp')}
                        <Chip
                          label={apt.status}
                          size="small"
                          color="primary"
                          sx={{ ml: 1 }}
                        />
                      </>
                    }
                  />
                </ListItem>
                <Divider />
              </React.Fragment>
            ))}
          </List>
        ) : (
          <Typography color="text.secondary">No upcoming appointments</Typography>
        )}
        <Box sx={{ mt: 2 }}>
          <Button
            variant="contained"
            startIcon={<RequestIcon />}
            onClick={() => navigate('/portal/request-appointment')}
          >
            Request New Appointment
          </Button>
        </Box>
      </Paper>

      {/* Recent Invoices */}
      <Paper sx={{ mt: 4, p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">Recent Invoices</Typography>
          <Button
            size="small"
            endIcon={<ArrowForwardIcon />}
            onClick={() => navigate('/portal/invoices')}
          >
            View All
          </Button>
        </Box>
        {recent_invoices && recent_invoices.length > 0 ? (
          <List>
            {recent_invoices.map((invoice) => (
              <React.Fragment key={invoice.id}>
                <ListItem>
                  <ListItemText
                    primary={`Invoice ${invoice.invoice_number}`}
                    secondary={
                      <>
                        {format(new Date(invoice.invoice_date), 'PP')} - ${invoice.total_amount}
                        <Chip
                          label={invoice.status}
                          size="small"
                          color={invoice.status === 'paid' ? 'success' : 'warning'}
                          sx={{ ml: 1 }}
                        />
                      </>
                    }
                  />
                  {invoice.balance_due !== '0.00' && (
                    <Typography variant="body2" color="error">
                      Balance: ${invoice.balance_due}
                    </Typography>
                  )}
                </ListItem>
                <Divider />
              </React.Fragment>
            ))}
          </List>
        ) : (
          <Typography color="text.secondary">No recent invoices</Typography>
        )}
      </Paper>

      {/* Pending Appointment Requests */}
      {pending_requests && pending_requests.length > 0 && (
        <Paper sx={{ mt: 4, p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Pending Appointment Requests
          </Typography>
          <List>
            {pending_requests.map((request) => (
              <React.Fragment key={request.id}>
                <ListItem>
                  <ListItemText
                    primary={`${request.patient_name} - ${request.reason}`}
                    secondary={
                      <>
                        Requested: {format(new Date(request.requested_date), 'PP')}
                        <Chip
                          label={request.priority}
                          size="small"
                          color={request.priority === 'urgent' ? 'error' : 'default'}
                          sx={{ ml: 1 }}
                        />
                      </>
                    }
                  />
                </ListItem>
                <Divider />
              </React.Fragment>
            ))}
          </List>
        </Paper>
      )}
    </Box>
  );
}

export default ClientPortalDashboard;
