import React, { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Paper,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Grid,
  Card,
  CardContent,
  CardHeader,
  Chip,
  Divider,
  IconButton,
} from '@mui/material';
import {
  Edit as EditIcon,
  ArrowBack as ArrowBackIcon,
  Email as EmailIcon,
  Phone as PhoneIcon,
  LocationOn as LocationIcon,
  AttachMoney as MoneyIcon,
  Pets as PetsIcon,
} from '@mui/icons-material';
import logger from '../utils/logger';

/**
 * Client Detail Component
 *
 * Displays full details of a single client (cat owner).
 * Features:
 * - Complete client information
 * - Account balance display
 * - Notes and alerts
 * - Edit functionality
 * - Comprehensive logging
 */
function ClientDetail() {
  const { clientId } = useParams();
  const navigate = useNavigate();

  useEffect(() => {
    logger.logLifecycle('ClientDetail', 'mounted', { clientId });

    return () => {
      logger.logLifecycle('ClientDetail', 'unmounted');
    };
  }, [clientId]);

  // Fetch client data
  const {
    data: client,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ['client', clientId],
    queryFn: async () => {
      const startTime = performance.now();
      logger.logAction('Fetching client details', { clientId });

      const response = await fetch(`/api/clients/${clientId}`, {
        credentials: 'include',
      });

      const duration = performance.now() - startTime;

      if (!response.ok) {
        logger.logAPICall('GET', `/api/clients/${clientId}`, response.status, duration, 'Fetch failed');
        throw new Error(`Failed to fetch client: ${response.status}`);
      }

      const data = await response.json();
      logger.logAPICall('GET', `/api/clients/${clientId}`, response.status, duration);
      logger.info('Client details fetched', {
        clientId,
        name: `${data.first_name} ${data.last_name}`,
      });

      return data;
    },
    staleTime: 30000,
    retry: 2,
  });

  // Handle navigation
  const handleBack = () => {
    logger.logAction('Navigate back to client list');
    navigate('/clients');
  };

  const handleEdit = () => {
    logger.logAction('Navigate to edit client', { clientId });
    navigate(`/clients/${clientId}/edit`);
  };

  // Loading state
  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
        <Typography variant="body1" sx={{ ml: 2 }}>
          Loading client details...
        </Typography>
      </Box>
    );
  }

  // Error state
  if (isError) {
    logger.error('Error loading client details', error);
    return (
      <Box p={3}>
        <Alert severity="error" onClose={() => refetch()}>
          Error loading client: {error.message}. Click to retry.
        </Alert>
        <Button startIcon={<ArrowBackIcon />} onClick={handleBack} sx={{ mt: 2 }}>
          Back to Clients
        </Button>
      </Box>
    );
  }

  if (!client) {
    return (
      <Box p={3}>
        <Alert severity="warning">
          Client not found.
        </Alert>
        <Button startIcon={<ArrowBackIcon />} onClick={handleBack} sx={{ mt: 2 }}>
          Back to Clients
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box mb={3} display="flex" justifyContent="space-between" alignItems="center">
        <Box display="flex" alignItems="center">
          <IconButton onClick={handleBack} sx={{ mr: 1 }}>
            <ArrowBackIcon />
          </IconButton>
          <Typography variant="h4" component="h1">
            {client.first_name} {client.last_name}
          </Typography>
          {!client.is_active && (
            <Chip label="Inactive" color="default" size="small" sx={{ ml: 2 }} />
          )}
        </Box>
        <Button
          variant="contained"
          startIcon={<EditIcon />}
          onClick={handleEdit}
        >
          Edit
        </Button>
      </Box>

      <Grid container spacing={3}>
        {/* Contact Information */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="Contact Information" />
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <EmailIcon sx={{ mr: 1, color: 'text.secondary' }} />
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Email
                  </Typography>
                  <Typography variant="body1">
                    {client.email || 'Not provided'}
                  </Typography>
                </Box>
              </Box>

              <Box display="flex" alignItems="center" mb={2}>
                <PhoneIcon sx={{ mr: 1, color: 'text.secondary' }} />
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Primary Phone
                  </Typography>
                  <Typography variant="body1">{client.phone_primary}</Typography>
                </Box>
              </Box>

              {client.phone_secondary && (
                <Box display="flex" alignItems="center" mb={2}>
                  <PhoneIcon sx={{ mr: 1, color: 'text.secondary' }} />
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Secondary Phone
                    </Typography>
                    <Typography variant="body1">{client.phone_secondary}</Typography>
                  </Box>
                </Box>
              )}

              <Divider sx={{ my: 2 }} />

              <Box display="flex" alignItems="flex-start">
                <LocationIcon sx={{ mr: 1, color: 'text.secondary', mt: 0.5 }} />
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Address
                  </Typography>
                  {client.address_line1 || client.city ? (
                    <>
                      {client.address_line1 && (
                        <Typography variant="body1">{client.address_line1}</Typography>
                      )}
                      {client.address_line2 && (
                        <Typography variant="body1">{client.address_line2}</Typography>
                      )}
                      {(client.city || client.state || client.zip_code) && (
                        <Typography variant="body1">
                          {[client.city, client.state, client.zip_code]
                            .filter(Boolean)
                            .join(', ')}
                        </Typography>
                      )}
                    </>
                  ) : (
                    <Typography variant="body1" color="text.secondary">
                      Not provided
                    </Typography>
                  )}
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Account Information */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="Account Information" />
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <MoneyIcon sx={{ mr: 1, color: 'text.secondary' }} />
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Account Balance
                  </Typography>
                  <Typography variant="h6" color={parseFloat(client.account_balance || 0) > 0 ? 'error.main' : 'success.main'}>
                    ${parseFloat(client.account_balance || 0).toFixed(2)}
                  </Typography>
                </Box>
              </Box>

              {client.credit_limit > 0 && (
                <Box mb={2}>
                  <Typography variant="caption" color="text.secondary">
                    Credit Limit
                  </Typography>
                  <Typography variant="body1">
                    ${parseFloat(client.credit_limit).toFixed(2)}
                  </Typography>
                </Box>
              )}

              <Divider sx={{ my: 2 }} />

              <Box>
                <Typography variant="caption" color="text.secondary">
                  Communication Preferences
                </Typography>
                <Typography variant="body2" mt={1}>
                  Preferred Contact: <strong>{client.preferred_contact || 'email'}</strong>
                </Typography>
                <Box mt={1}>
                  <Chip
                    label={client.email_reminders ? 'Email Reminders: Yes' : 'Email Reminders: No'}
                    size="small"
                    color={client.email_reminders ? 'success' : 'default'}
                    sx={{ mr: 1, mb: 1 }}
                  />
                  <Chip
                    label={client.sms_reminders ? 'SMS Reminders: Yes' : 'SMS Reminders: No'}
                    size="small"
                    color={client.sms_reminders ? 'success' : 'default'}
                  />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Patients (Cats) */}
        <Grid item xs={12}>
          <Card>
            <CardHeader
              title="Patients (Cats)"
              avatar={<PetsIcon />}
              action={
                <Button size="small" variant="outlined">
                  Add Patient
                </Button>
              }
            />
            <CardContent>
              <Alert severity="info">
                Patient management coming soon (Phase 1.2)
              </Alert>
            </CardContent>
          </Card>
        </Grid>

        {/* Notes and Alerts */}
        {(client.notes || client.alerts) && (
          <>
            {client.alerts && (
              <Grid item xs={12}>
                <Card>
                  <CardHeader title="Alerts" />
                  <CardContent>
                    <Alert severity="warning">{client.alerts}</Alert>
                  </CardContent>
                </Card>
              </Grid>
            )}

            {client.notes && (
              <Grid item xs={12}>
                <Card>
                  <CardHeader title="Notes" />
                  <CardContent>
                    <Typography variant="body1" style={{ whiteSpace: 'pre-wrap' }}>
                      {client.notes}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            )}
          </>
        )}

        {/* Metadata */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
            <Typography variant="caption" color="text.secondary">
              Created: {new Date(client.created_at).toLocaleString()} |
              Last Updated: {new Date(client.updated_at).toLocaleString()}
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}

export default ClientDetail;
