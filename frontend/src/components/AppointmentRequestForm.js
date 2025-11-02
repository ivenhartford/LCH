import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  MenuItem,
  FormControlLabel,
  Checkbox,
  CircularProgress,
  Alert,
  Grid,
} from '@mui/material';
import { Send as SendIcon, ArrowBack as ArrowBackIcon } from '@mui/icons-material';
import { format } from 'date-fns';

// Validation schema
const requestSchema = z.object({
  patient_id: z.number().min(1, 'Please select a pet'),
  appointment_type_id: z.number().optional(),
  requested_date: z.string().min(1, 'Please select a date'),
  requested_time: z.string().optional(),
  alternate_date_1: z.string().optional(),
  alternate_date_2: z.string().optional(),
  reason: z.string().min(1, 'Please provide a reason for the appointment'),
  is_urgent: z.boolean(),
  notes: z.string().optional(),
});

/**
 * Appointment Request Form Component
 *
 * Allows clients to submit appointment requests online
 */
function AppointmentRequestForm({ portalUser }) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [submitError, setSubmitError] = useState('');

  // Fetch client's patients
  const { data: patients, isLoading: patientsLoading } = useQuery({
    queryKey: ['portalPatients', portalUser?.client_id],
    queryFn: async () => {
      const response = await fetch(`/api/portal/patients/${portalUser.client_id}`);
      if (!response.ok) throw new Error('Failed to fetch patients');
      return response.json();
    },
    enabled: !!portalUser?.client_id,
  });

  // Fetch appointment types
  const { data: appointmentTypes } = useQuery({
    queryKey: ['appointmentTypes'],
    queryFn: async () => {
      const response = await fetch('/api/appointment_types');
      if (!response.ok) throw new Error('Failed to fetch appointment types');
      return response.json();
    },
  });

  // Form setup
  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(requestSchema),
    defaultValues: {
      patient_id: '',
      appointment_type_id: '',
      requested_date: '',
      requested_time: 'morning',
      alternate_date_1: '',
      alternate_date_2: '',
      reason: '',
      is_urgent: false,
      notes: '',
    },
  });

  // Submit mutation
  const submitMutation = useMutation({
    mutationFn: async (data) => {
      const response = await fetch('/api/portal/appointment-requests', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...data,
          client_id: portalUser.client_id,
        }),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to submit request');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['portalDashboard']);
      navigate('/portal/dashboard');
    },
    onError: (error) => {
      setSubmitError(error.message);
    },
  });

  const onSubmit = (data) => {
    setSubmitError('');
    submitMutation.mutate(data);
  };

  if (patientsLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/portal/dashboard')}
          sx={{ mr: 2 }}
        >
          Back
        </Button>
        <Typography variant="h4">Request Appointment</Typography>
      </Box>

      <Paper sx={{ p: 3 }}>
        <Alert severity="info" sx={{ mb: 3 }}>
          Submit your appointment request and we'll review it shortly. You'll be notified once it's approved.
        </Alert>

        {submitError && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setSubmitError('')}>
            {submitError}
          </Alert>
        )}

        <form onSubmit={handleSubmit(onSubmit)}>
          <Grid container spacing={2}>
            {/* Pet Selection */}
            <Grid item xs={12} md={6}>
              <Controller
                name="patient_id"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    select
                    label="Select Pet"
                    fullWidth
                    required
                    error={!!errors.patient_id}
                    helperText={errors.patient_id?.message}
                    value={field.value || ''}
                    onChange={(e) => field.onChange(parseInt(e.target.value))}
                  >
                    <MenuItem value="">Select a pet</MenuItem>
                    {patients?.map((patient) => (
                      <MenuItem key={patient.id} value={patient.id}>
                        {patient.name} ({patient.species})
                      </MenuItem>
                    ))}
                  </TextField>
                )}
              />
            </Grid>

            {/* Appointment Type */}
            <Grid item xs={12} md={6}>
              <Controller
                name="appointment_type_id"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    select
                    label="Appointment Type"
                    fullWidth
                    error={!!errors.appointment_type_id}
                    helperText={errors.appointment_type_id?.message || 'Optional'}
                    value={field.value || ''}
                    onChange={(e) => field.onChange(e.target.value ? parseInt(e.target.value) : '')}
                  >
                    <MenuItem value="">Any type</MenuItem>
                    {appointmentTypes?.map((type) => (
                      <MenuItem key={type.id} value={type.id}>
                        {type.name}
                      </MenuItem>
                    ))}
                  </TextField>
                )}
              />
            </Grid>

            {/* Requested Date */}
            <Grid item xs={12} md={6}>
              <Controller
                name="requested_date"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    type="date"
                    label="Requested Date"
                    fullWidth
                    required
                    InputLabelProps={{ shrink: true }}
                    error={!!errors.requested_date}
                    helperText={errors.requested_date?.message}
                    inputProps={{
                      min: format(new Date(), 'yyyy-MM-dd'),
                    }}
                  />
                )}
              />
            </Grid>

            {/* Preferred Time */}
            <Grid item xs={12} md={6}>
              <Controller
                name="requested_time"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    select
                    label="Preferred Time"
                    fullWidth
                    error={!!errors.requested_time}
                    helperText={errors.requested_time?.message}
                  >
                    <MenuItem value="morning">Morning (8am-12pm)</MenuItem>
                    <MenuItem value="afternoon">Afternoon (12pm-4pm)</MenuItem>
                    <MenuItem value="evening">Evening (4pm-6pm)</MenuItem>
                  </TextField>
                )}
              />
            </Grid>

            {/* Alternate Dates */}
            <Grid item xs={12} md={6}>
              <Controller
                name="alternate_date_1"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    type="date"
                    label="Alternate Date 1"
                    fullWidth
                    InputLabelProps={{ shrink: true }}
                    helperText="Optional"
                    inputProps={{
                      min: format(new Date(), 'yyyy-MM-dd'),
                    }}
                  />
                )}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <Controller
                name="alternate_date_2"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    type="date"
                    label="Alternate Date 2"
                    fullWidth
                    InputLabelProps={{ shrink: true }}
                    helperText="Optional"
                    inputProps={{
                      min: format(new Date(), 'yyyy-MM-dd'),
                    }}
                  />
                )}
              />
            </Grid>

            {/* Reason */}
            <Grid item xs={12}>
              <Controller
                name="reason"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Reason for Appointment"
                    fullWidth
                    required
                    multiline
                    rows={3}
                    error={!!errors.reason}
                    helperText={errors.reason?.message || 'Please describe the reason for this appointment'}
                  />
                )}
              />
            </Grid>

            {/* Additional Notes */}
            <Grid item xs={12}>
              <Controller
                name="notes"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    label="Additional Notes"
                    fullWidth
                    multiline
                    rows={2}
                    error={!!errors.notes}
                    helperText="Any additional information we should know"
                  />
                )}
              />
            </Grid>

            {/* Urgent Checkbox */}
            <Grid item xs={12}>
              <Controller
                name="is_urgent"
                control={control}
                render={({ field }) => (
                  <FormControlLabel
                    control={
                      <Checkbox
                        {...field}
                        checked={field.value}
                      />
                    }
                    label="This is urgent (requires immediate attention)"
                  />
                )}
              />
            </Grid>

            {/* Submit Button */}
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                <Button
                  variant="outlined"
                  onClick={() => navigate('/portal/dashboard')}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="contained"
                  startIcon={<SendIcon />}
                  disabled={submitMutation.isPending}
                >
                  {submitMutation.isPending ? 'Submitting...' : 'Submit Request'}
                </Button>
              </Box>
            </Grid>
          </Grid>
        </form>
      </Paper>
    </Box>
  );
}

export default AppointmentRequestForm;
