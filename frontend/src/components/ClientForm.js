import React, { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  Box,
  Paper,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Grid,
  TextField,
  MenuItem,
  FormControlLabel,
  Switch,
  IconButton,
  Divider,
} from '@mui/material';
import { ArrowBack as ArrowBackIcon, Save as SaveIcon } from '@mui/icons-material';
import logger from '../utils/logger';

// Validation schema using Zod
const clientSchema = z.object({
  first_name: z.string().min(1, 'First name is required').max(100),
  last_name: z.string().min(1, 'Last name is required').max(100),
  email: z.string().email('Invalid email').or(z.literal('')).optional(),
  phone_primary: z.string().min(1, 'Primary phone is required').max(20),
  phone_secondary: z.string().max(20).optional(),
  address_line1: z.string().max(200).optional(),
  address_line2: z.string().max(200).optional(),
  city: z.string().max(100).optional(),
  state: z.string().max(50).optional(),
  zip_code: z.string().max(20).optional(),
  preferred_contact: z.enum(['email', 'phone', 'sms']).optional(),
  email_reminders: z.boolean().optional(),
  sms_reminders: z.boolean().optional(),
  notes: z.string().optional(),
  alerts: z.string().optional(),
});

/**
 * Client Form Component
 *
 * Handles both creating new clients and editing existing ones.
 * Features:
 * - Comprehensive validation with Zod
 * - React Hook Form integration
 * - Material-UI fields
 * - Comprehensive logging
 * - Loading and error states
 */
function ClientForm() {
  const { clientId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const isEditMode = Boolean(clientId);

  useEffect(() => {
    logger.logLifecycle('ClientForm', 'mounted', {
      mode: isEditMode ? 'edit' : 'create',
      clientId,
    });

    return () => {
      logger.logLifecycle('ClientForm', 'unmounted');
    };
  }, [isEditMode, clientId]);

  // Form setup
  const {
    control,
    handleSubmit,
    reset,
    formState: { errors, isDirty },
  } = useForm({
    resolver: zodResolver(clientSchema),
    defaultValues: {
      first_name: '',
      last_name: '',
      email: '',
      phone_primary: '',
      phone_secondary: '',
      address_line1: '',
      address_line2: '',
      city: '',
      state: '',
      zip_code: '',
      preferred_contact: 'email',
      email_reminders: true,
      sms_reminders: true,
      notes: '',
      alerts: '',
    },
  });

  // Fetch existing client data (edit mode only)
  const {
    isLoading: isLoadingClient,
    isError: isClientError,
    error: clientError,
  } = useQuery({
    queryKey: ['client', clientId],
    queryFn: async () => {
      const startTime = performance.now();
      logger.logAction('Fetching client for edit', { clientId });

      const response = await fetch(`/api/clients/${clientId}`, {
        credentials: 'include',
      });

      const duration = performance.now() - startTime;

      if (!response.ok) {
        logger.logAPICall(
          'GET',
          `/api/clients/${clientId}`,
          response.status,
          duration,
          'Fetch failed'
        );
        throw new Error('Failed to fetch client');
      }

      const data = await response.json();
      logger.logAPICall('GET', `/api/clients/${clientId}`, response.status, duration);

      // Reset form with fetched data
      reset(data);

      return data;
    },
    enabled: isEditMode,
    staleTime: 0, // Always fetch fresh data for editing
  });

  // Create/Update mutation
  const mutation = useMutation({
    mutationFn: async (data) => {
      const url = isEditMode ? `/api/clients/${clientId}` : '/api/clients';
      const method = isEditMode ? 'PUT' : 'POST';

      const startTime = performance.now();
      logger.logAction(isEditMode ? 'Updating client' : 'Creating client', {
        clientId,
        data: { first_name: data.first_name, last_name: data.last_name },
      });

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(data),
      });

      const duration = performance.now() - startTime;

      if (!response.ok) {
        const errorData = await response.json();
        logger.logAPICall(
          method,
          url,
          response.status,
          duration,
          errorData.error || 'Request failed'
        );
        throw new Error(errorData.error || 'Failed to save client');
      }

      const result = await response.json();
      logger.logAPICall(method, url, response.status, duration);
      logger.info(isEditMode ? 'Client updated' : 'Client created', {
        clientId: result.id,
        name: `${result.first_name} ${result.last_name}`,
      });

      return result;
    },
    onSuccess: (data) => {
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: ['clients'] });
      queryClient.invalidateQueries({ queryKey: ['client', data.id] });

      logger.logAction('Navigate to client detail after save', { clientId: data.id });
      navigate(`/clients/${data.id}`);
    },
    onError: (error) => {
      logger.error('Error saving client', error);
    },
  });

  // Handle form submission
  const onSubmit = (data) => {
    // Clean up empty optional fields
    const cleanedData = Object.fromEntries(
      Object.entries(data).filter(([_, value]) => value !== '')
    );

    logger.logAction('Submitting client form', {
      mode: isEditMode ? 'edit' : 'create',
      isDirty,
    });

    mutation.mutate(cleanedData);
  };

  // Handle navigation
  const handleBack = () => {
    if (isDirty) {
      const confirmLeave = window.confirm(
        'You have unsaved changes. Are you sure you want to leave?'
      );
      if (!confirmLeave) {
        logger.logAction('Cancelled navigation with unsaved changes');
        return;
      }
    }

    logger.logAction('Navigate back from client form');
    navigate(isEditMode ? `/clients/${clientId}` : '/clients');
  };

  // Loading state (edit mode)
  if (isEditMode && isLoadingClient) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
        <Typography variant="body1" sx={{ ml: 2 }}>
          Loading client data...
        </Typography>
      </Box>
    );
  }

  // Error state (edit mode)
  if (isEditMode && isClientError) {
    logger.error('Error loading client for edit', clientError);
    return (
      <Box p={3}>
        <Alert severity="error">Error loading client: {clientError.message}</Alert>
        <Button startIcon={<ArrowBackIcon />} onClick={handleBack} sx={{ mt: 2 }}>
          Back
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
            {isEditMode ? 'Edit Client' : 'New Client'}
          </Typography>
        </Box>
      </Box>

      {/* Form */}
      <Paper sx={{ p: 3 }}>
        <form onSubmit={handleSubmit(onSubmit)}>
          {/* Mutation error */}
          {mutation.isError && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {mutation.error.message}
            </Alert>
          )}

          <Grid container spacing={3}>
            {/* Personal Information */}
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Personal Information
              </Typography>
            </Grid>

            <Grid item xs={12} sm={6}>
              <Controller
                name="first_name"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="First Name"
                    required
                    error={!!errors.first_name}
                    helperText={errors.first_name?.message}
                  />
                )}
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <Controller
                name="last_name"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="Last Name"
                    required
                    error={!!errors.last_name}
                    helperText={errors.last_name?.message}
                  />
                )}
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <Controller
                name="email"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="Email"
                    type="email"
                    error={!!errors.email}
                    helperText={errors.email?.message}
                  />
                )}
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <Controller
                name="phone_primary"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="Primary Phone"
                    required
                    error={!!errors.phone_primary}
                    helperText={errors.phone_primary?.message}
                  />
                )}
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <Controller
                name="phone_secondary"
                control={control}
                render={({ field }) => <TextField {...field} fullWidth label="Secondary Phone" />}
              />
            </Grid>

            {/* Address */}
            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Typography variant="h6" gutterBottom>
                Address
              </Typography>
            </Grid>

            <Grid item xs={12}>
              <Controller
                name="address_line1"
                control={control}
                render={({ field }) => <TextField {...field} fullWidth label="Address Line 1" />}
              />
            </Grid>

            <Grid item xs={12}>
              <Controller
                name="address_line2"
                control={control}
                render={({ field }) => <TextField {...field} fullWidth label="Address Line 2" />}
              />
            </Grid>

            <Grid item xs={12} sm={5}>
              <Controller
                name="city"
                control={control}
                render={({ field }) => <TextField {...field} fullWidth label="City" />}
              />
            </Grid>

            <Grid item xs={12} sm={3}>
              <Controller
                name="state"
                control={control}
                render={({ field }) => <TextField {...field} fullWidth label="State" />}
              />
            </Grid>

            <Grid item xs={12} sm={4}>
              <Controller
                name="zip_code"
                control={control}
                render={({ field }) => <TextField {...field} fullWidth label="ZIP Code" />}
              />
            </Grid>

            {/* Communication Preferences */}
            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Typography variant="h6" gutterBottom>
                Communication Preferences
              </Typography>
            </Grid>

            <Grid item xs={12} sm={6}>
              <Controller
                name="preferred_contact"
                control={control}
                render={({ field }) => (
                  <TextField {...field} fullWidth select label="Preferred Contact Method">
                    <MenuItem value="email">Email</MenuItem>
                    <MenuItem value="phone">Phone</MenuItem>
                    <MenuItem value="sms">SMS</MenuItem>
                  </TextField>
                )}
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <Box display="flex" gap={2} mt={1}>
                <Controller
                  name="email_reminders"
                  control={control}
                  render={({ field }) => (
                    <FormControlLabel
                      control={<Switch {...field} checked={field.value} />}
                      label="Email Reminders"
                    />
                  )}
                />
                <Controller
                  name="sms_reminders"
                  control={control}
                  render={({ field }) => (
                    <FormControlLabel
                      control={<Switch {...field} checked={field.value} />}
                      label="SMS Reminders"
                    />
                  )}
                />
              </Box>
            </Grid>

            {/* Notes and Alerts */}
            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Typography variant="h6" gutterBottom>
                Notes and Alerts
              </Typography>
            </Grid>

            <Grid item xs={12}>
              <Controller
                name="alerts"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    multiline
                    rows={2}
                    label="Alerts"
                    helperText="Important alerts or warnings about this client"
                  />
                )}
              />
            </Grid>

            <Grid item xs={12}>
              <Controller
                name="notes"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    multiline
                    rows={4}
                    label="Notes"
                    helperText="General notes about the client"
                  />
                )}
              />
            </Grid>

            {/* Actions */}
            <Grid item xs={12}>
              <Box display="flex" justifyContent="flex-end" gap={2} mt={2}>
                <Button onClick={handleBack} disabled={mutation.isPending}>
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="contained"
                  startIcon={mutation.isPending ? <CircularProgress size={20} /> : <SaveIcon />}
                  disabled={mutation.isPending || !isDirty}
                >
                  {mutation.isPending ? 'Saving...' : 'Save Client'}
                </Button>
              </Box>
            </Grid>
          </Grid>
        </form>
      </Paper>
    </Box>
  );
}

export default ClientForm;
