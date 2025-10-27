import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  Container,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  Box,
  Alert,
  CircularProgress,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  FormHelperText,
} from '@mui/material';
import { ArrowBack as ArrowBackIcon, Save as SaveIcon } from '@mui/icons-material';
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';

// Validation schema
const appointmentSchema = z.object({
  title: z.string().min(1, 'Title is required').max(200, 'Title must be less than 200 characters'),
  start_time: z.date({ required_error: 'Start time is required' }),
  end_time: z.date({ required_error: 'End time is required' }),
  description: z.string().optional(),
  client_id: z.number({ required_error: 'Client is required' }).positive('Client is required'),
  patient_id: z.number().positive().optional().nullable(),
  appointment_type_id: z.number().positive().optional().nullable(),
  assigned_staff_id: z.number().positive().optional().nullable(),
  room: z.string().max(50).optional(),
  notes: z.string().optional(),
  status: z.enum(['scheduled', 'confirmed', 'checked_in', 'in_progress', 'completed', 'cancelled', 'no_show']).optional(),
}).refine((data) => data.end_time > data.start_time, {
  message: 'End time must be after start time',
  path: ['end_time'],
});

// Fetch functions
const fetchAppointment = async (id) => {
  const response = await fetch(`/api/appointments/${id}`);
  if (!response.ok) throw new Error('Failed to fetch appointment');
  return response.json();
};

const fetchClients = async () => {
  const response = await fetch('/api/clients?per_page=1000&active_only=true');
  if (!response.ok) throw new Error('Failed to fetch clients');
  const data = await response.json();
  return data.clients || [];
};

const fetchPatients = async (clientId) => {
  if (!clientId) return [];
  const response = await fetch(`/api/patients?owner_id=${clientId}&per_page=1000`);
  if (!response.ok) throw new Error('Failed to fetch patients');
  const data = await response.json();
  return data.patients || [];
};

const fetchAppointmentTypes = async () => {
  const response = await fetch('/api/appointment-types?active_only=true');
  if (!response.ok) throw new Error('Failed to fetch appointment types');
  return response.json();
};

const fetchStaff = async () => {
  const response = await fetch('/api/users');
  if (!response.ok) throw new Error('Failed to fetch staff');
  return response.json();
};

const AppointmentForm = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const isEditMode = Boolean(id);

  const [selectedClientId, setSelectedClientId] = useState(null);

  // Fetch data
  const { data: appointment, isLoading: loadingAppointment } = useQuery({
    queryKey: ['appointment', id],
    queryFn: () => fetchAppointment(id),
    enabled: isEditMode,
  });

  const { data: clients = [], isLoading: loadingClients } = useQuery({
    queryKey: ['clients'],
    queryFn: fetchClients,
  });

  const { data: patients = [], isLoading: loadingPatients } = useQuery({
    queryKey: ['patients', selectedClientId],
    queryFn: () => fetchPatients(selectedClientId),
    enabled: Boolean(selectedClientId),
  });

  const { data: appointmentTypes = [], isLoading: loadingTypes } = useQuery({
    queryKey: ['appointmentTypes'],
    queryFn: fetchAppointmentTypes,
  });

  const { data: staff = [], isLoading: loadingStaff } = useQuery({
    queryKey: ['staff'],
    queryFn: fetchStaff,
  });

  // Form setup
  const {
    control,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(appointmentSchema),
    defaultValues: {
      title: '',
      start_time: new Date(),
      end_time: new Date(Date.now() + 60 * 60 * 1000), // 1 hour from now
      description: '',
      client_id: '',
      patient_id: '',
      appointment_type_id: '',
      assigned_staff_id: '',
      room: '',
      notes: '',
      status: 'scheduled',
    },
  });

  const watchClientId = watch('client_id');

  // Update selected client when form value changes
  useEffect(() => {
    if (watchClientId) {
      setSelectedClientId(watchClientId);
    }
  }, [watchClientId]);

  // Populate form when editing
  useEffect(() => {
    if (appointment && isEditMode) {
      setValue('title', appointment.title);
      setValue('start_time', new Date(appointment.start_time));
      setValue('end_time', new Date(appointment.end_time));
      setValue('description', appointment.description || '');
      setValue('client_id', appointment.client_id);
      setValue('patient_id', appointment.patient_id || '');
      setValue('appointment_type_id', appointment.appointment_type_id || '');
      setValue('assigned_staff_id', appointment.assigned_staff_id || '');
      setValue('room', appointment.room || '');
      setValue('notes', appointment.notes || '');
      setValue('status', appointment.status || 'scheduled');
      setSelectedClientId(appointment.client_id);
    }
  }, [appointment, isEditMode, setValue]);

  // Mutation for save
  const saveMutation = useMutation({
    mutationFn: async (data) => {
      const url = isEditMode ? `/api/appointments/${id}` : '/api/appointments';
      const method = isEditMode ? 'PUT' : 'POST';

      // Convert empty strings to null for optional fields
      const payload = {
        ...data,
        patient_id: data.patient_id || null,
        appointment_type_id: data.appointment_type_id || null,
        assigned_staff_id: data.assigned_staff_id || null,
        start_time: data.start_time.toISOString(),
        end_time: data.end_time.toISOString(),
      };

      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to save appointment');
      }

      return response.json();
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries(['appointments']);
      if (isEditMode) {
        queryClient.invalidateQueries(['appointment', id]);
      }
      navigate(isEditMode ? `/appointments/${id}` : `/appointments/${data.id}`);
    },
  });

  const onSubmit = (data) => {
    saveMutation.mutate(data);
  };

  if (loadingAppointment || loadingClients || loadingTypes || loadingStaff) {
    return (
      <Container sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
        {/* Header */}
        <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate(-1)}
            variant="outlined"
          >
            Back
          </Button>
          <Typography variant="h4" component="h1">
            {isEditMode ? 'Edit Appointment' : 'New Appointment'}
          </Typography>
        </Box>

        {/* Error display */}
        {saveMutation.isError && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {saveMutation.error.message}
          </Alert>
        )}

        {/* Form */}
        <Paper sx={{ p: 3 }}>
          <form onSubmit={handleSubmit(onSubmit)}>
            <Grid container spacing={3}>
              {/* Title */}
              <Grid item xs={12}>
                <Controller
                  name="title"
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      label="Title"
                      fullWidth
                      required
                      error={!!errors.title}
                      helperText={errors.title?.message}
                    />
                  )}
                />
              </Grid>

              {/* Start Time */}
              <Grid item xs={12} sm={6}>
                <Controller
                  name="start_time"
                  control={control}
                  render={({ field }) => (
                    <DateTimePicker
                      label="Start Time"
                      value={field.value}
                      onChange={field.onChange}
                      slotProps={{
                        textField: {
                          fullWidth: true,
                          required: true,
                          error: !!errors.start_time,
                          helperText: errors.start_time?.message,
                        },
                      }}
                    />
                  )}
                />
              </Grid>

              {/* End Time */}
              <Grid item xs={12} sm={6}>
                <Controller
                  name="end_time"
                  control={control}
                  render={({ field }) => (
                    <DateTimePicker
                      label="End Time"
                      value={field.value}
                      onChange={field.onChange}
                      slotProps={{
                        textField: {
                          fullWidth: true,
                          required: true,
                          error: !!errors.end_time,
                          helperText: errors.end_time?.message,
                        },
                      }}
                    />
                  )}
                />
              </Grid>

              {/* Client */}
              <Grid item xs={12} sm={6}>
                <Controller
                  name="client_id"
                  control={control}
                  render={({ field }) => (
                    <FormControl fullWidth required error={!!errors.client_id}>
                      <InputLabel>Client</InputLabel>
                      <Select {...field} label="Client">
                        <MenuItem value="">
                          <em>Select Client</em>
                        </MenuItem>
                        {clients.map((client) => (
                          <MenuItem key={client.id} value={client.id}>
                            {client.first_name} {client.last_name}
                          </MenuItem>
                        ))}
                      </Select>
                      <FormHelperText>{errors.client_id?.message}</FormHelperText>
                    </FormControl>
                  )}
                />
              </Grid>

              {/* Patient */}
              <Grid item xs={12} sm={6}>
                <Controller
                  name="patient_id"
                  control={control}
                  render={({ field }) => (
                    <FormControl fullWidth error={!!errors.patient_id} disabled={!selectedClientId || loadingPatients}>
                      <InputLabel>Patient (Optional)</InputLabel>
                      <Select {...field} label="Patient (Optional)">
                        <MenuItem value="">
                          <em>No Patient</em>
                        </MenuItem>
                        {patients.map((patient) => (
                          <MenuItem key={patient.id} value={patient.id}>
                            {patient.name} ({patient.breed || 'Unknown breed'})
                          </MenuItem>
                        ))}
                      </Select>
                      <FormHelperText>
                        {errors.patient_id?.message || (selectedClientId ? 'Select a patient for this appointment' : 'Select a client first')}
                      </FormHelperText>
                    </FormControl>
                  )}
                />
              </Grid>

              {/* Appointment Type */}
              <Grid item xs={12} sm={6}>
                <Controller
                  name="appointment_type_id"
                  control={control}
                  render={({ field }) => (
                    <FormControl fullWidth error={!!errors.appointment_type_id}>
                      <InputLabel>Appointment Type</InputLabel>
                      <Select {...field} label="Appointment Type">
                        <MenuItem value="">
                          <em>None</em>
                        </MenuItem>
                        {appointmentTypes.map((type) => (
                          <MenuItem key={type.id} value={type.id}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Box
                                sx={{
                                  width: 12,
                                  height: 12,
                                  borderRadius: '50%',
                                  backgroundColor: type.color,
                                }}
                              />
                              {type.name}
                            </Box>
                          </MenuItem>
                        ))}
                      </Select>
                      <FormHelperText>{errors.appointment_type_id?.message}</FormHelperText>
                    </FormControl>
                  )}
                />
              </Grid>

              {/* Assigned Staff */}
              <Grid item xs={12} sm={6}>
                <Controller
                  name="assigned_staff_id"
                  control={control}
                  render={({ field }) => (
                    <FormControl fullWidth error={!!errors.assigned_staff_id}>
                      <InputLabel>Assigned Staff</InputLabel>
                      <Select {...field} label="Assigned Staff">
                        <MenuItem value="">
                          <em>Unassigned</em>
                        </MenuItem>
                        {staff.map((member) => (
                          <MenuItem key={member.id} value={member.id}>
                            {member.username} ({member.role})
                          </MenuItem>
                        ))}
                      </Select>
                      <FormHelperText>{errors.assigned_staff_id?.message}</FormHelperText>
                    </FormControl>
                  )}
                />
              </Grid>

              {/* Room */}
              <Grid item xs={12} sm={6}>
                <Controller
                  name="room"
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      label="Room"
                      fullWidth
                      error={!!errors.room}
                      helperText={errors.room?.message}
                    />
                  )}
                />
              </Grid>

              {/* Status (edit mode only) */}
              {isEditMode && (
                <Grid item xs={12} sm={6}>
                  <Controller
                    name="status"
                    control={control}
                    render={({ field }) => (
                      <FormControl fullWidth error={!!errors.status}>
                        <InputLabel>Status</InputLabel>
                        <Select {...field} label="Status">
                          <MenuItem value="scheduled">Scheduled</MenuItem>
                          <MenuItem value="confirmed">Confirmed</MenuItem>
                          <MenuItem value="checked_in">Checked In</MenuItem>
                          <MenuItem value="in_progress">In Progress</MenuItem>
                          <MenuItem value="completed">Completed</MenuItem>
                          <MenuItem value="cancelled">Cancelled</MenuItem>
                          <MenuItem value="no_show">No Show</MenuItem>
                        </Select>
                        <FormHelperText>{errors.status?.message}</FormHelperText>
                      </FormControl>
                    )}
                  />
                </Grid>
              )}

              {/* Description */}
              <Grid item xs={12}>
                <Controller
                  name="description"
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      label="Description"
                      fullWidth
                      multiline
                      rows={3}
                      error={!!errors.description}
                      helperText={errors.description?.message}
                    />
                  )}
                />
              </Grid>

              {/* Notes */}
              <Grid item xs={12}>
                <Controller
                  name="notes"
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      label="Notes"
                      fullWidth
                      multiline
                      rows={3}
                      error={!!errors.notes}
                      helperText={errors.notes?.message}
                    />
                  )}
                />
              </Grid>

              {/* Actions */}
              <Grid item xs={12}>
                <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                  <Button variant="outlined" onClick={() => navigate(-1)}>
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    variant="contained"
                    startIcon={<SaveIcon />}
                    disabled={saveMutation.isPending}
                  >
                    {saveMutation.isPending ? 'Saving...' : 'Save Appointment'}
                  </Button>
                </Box>
              </Grid>
            </Grid>
          </form>
        </Paper>
      </Container>
    </LocalizationProvider>
  );
};

export default AppointmentForm;
