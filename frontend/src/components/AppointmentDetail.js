import React from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Container,
  Paper,
  Typography,
  Grid,
  Button,
  Box,
  Chip,
  CircularProgress,
  Alert,
  Divider,
  Card,
  CardContent,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Edit as EditIcon,
  Cancel as CancelIcon,
  CheckCircle as CheckCircleIcon,
  PlayArrow as PlayArrowIcon,
  Done as DoneIcon,
  EventAvailable as EventAvailableIcon,
  Person as PersonIcon,
  Pets as PetsIcon,
  MedicalServices as MedicalServicesIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';

const fetchAppointment = async (id) => {
  const response = await fetch(`/api/appointments/${id}`);
  if (!response.ok) {
    throw new Error('Failed to fetch appointment');
  }
  return response.json();
};

const updateAppointmentStatus = async ({ id, status, cancellation_reason }) => {
  const response = await fetch(`/api/appointments/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status, cancellation_reason }),
  });

  if (!response.ok) {
    throw new Error('Failed to update appointment status');
  }

  return response.json();
};

const getStatusColor = (status) => {
  const colors = {
    scheduled: 'info',
    confirmed: 'primary',
    checked_in: 'secondary',
    in_progress: 'warning',
    completed: 'success',
    cancelled: 'error',
    no_show: 'default',
  };
  return colors[status] || 'default';
};

const getStatusIcon = (status) => {
  const icons = {
    scheduled: <EventAvailableIcon />,
    confirmed: <CheckCircleIcon />,
    checked_in: <PersonIcon />,
    in_progress: <PlayArrowIcon />,
    completed: <DoneIcon />,
    cancelled: <CancelIcon />,
    no_show: <CancelIcon />,
  };
  return icons[status] || <EventAvailableIcon />;
};

const AppointmentDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: appointment, isLoading, error } = useQuery({
    queryKey: ['appointment', id],
    queryFn: () => fetchAppointment(id),
  });

  const statusMutation = useMutation({
    mutationFn: updateAppointmentStatus,
    onSuccess: () => {
      queryClient.invalidateQueries(['appointment', id]);
      queryClient.invalidateQueries(['appointments']);
    },
  });

  const handleStatusChange = (newStatus) => {
    let cancellation_reason = null;

    if (newStatus === 'cancelled') {
      cancellation_reason = prompt('Please enter a cancellation reason:');
      if (!cancellation_reason) {
        return; // User cancelled
      }
    }

    statusMutation.mutate({ id, status: newStatus, cancellation_reason });
  };

  if (isLoading) {
    return (
      <Container sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  if (error) {
    return (
      <Container sx={{ mt: 4 }}>
        <Alert severity="error">Error loading appointment: {error.message}</Alert>
      </Container>
    );
  }

  const canCheckIn = appointment.status === 'scheduled' || appointment.status === 'confirmed';
  const canStart = appointment.status === 'checked_in';
  const canComplete = appointment.status === 'in_progress';
  const canCancel = !['completed', 'cancelled', 'no_show'].includes(appointment.status);

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate(-1)}
          variant="outlined"
        >
          Back
        </Button>
        <Typography variant="h4" component="h1" sx={{ flexGrow: 1 }}>
          Appointment Details
        </Typography>
        <Button
          startIcon={<EditIcon />}
          variant="contained"
          onClick={() => navigate(`/appointments/${id}/edit`)}
          disabled={appointment.status === 'completed'}
        >
          Edit
        </Button>
      </Box>

      {/* Status Update Buttons */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Status Actions
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          {appointment.status === 'scheduled' && (
            <Button
              variant="outlined"
              color="primary"
              onClick={() => handleStatusChange('confirmed')}
            >
              Confirm
            </Button>
          )}
          {canCheckIn && (
            <Button
              variant="outlined"
              color="secondary"
              startIcon={<PersonIcon />}
              onClick={() => handleStatusChange('checked_in')}
            >
              Check In
            </Button>
          )}
          {canStart && (
            <Button
              variant="outlined"
              color="warning"
              startIcon={<PlayArrowIcon />}
              onClick={() => handleStatusChange('in_progress')}
            >
              Start Appointment
            </Button>
          )}
          {canComplete && (
            <Button
              variant="outlined"
              color="success"
              startIcon={<DoneIcon />}
              onClick={() => handleStatusChange('completed')}
            >
              Complete
            </Button>
          )}
          {canCancel && (
            <Button
              variant="outlined"
              color="error"
              startIcon={<CancelIcon />}
              onClick={() => handleStatusChange('cancelled')}
            >
              Cancel
            </Button>
          )}
          {appointment.status === 'scheduled' && (
            <Button
              variant="outlined"
              onClick={() => handleStatusChange('no_show')}
            >
              Mark No Show
            </Button>
          )}
        </Box>
      </Paper>

      <Grid container spacing={3}>
        {/* Main Information */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
              <Typography variant="h5" component="h2">
                {appointment.title}
              </Typography>
              <Chip
                icon={getStatusIcon(appointment.status)}
                label={appointment.status.replace('_', ' ').toUpperCase()}
                color={getStatusColor(appointment.status)}
                sx={{ textTransform: 'uppercase' }}
              />
            </Box>

            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2" color="text.secondary">
                  Start Time
                </Typography>
                <Typography variant="body1">
                  {format(new Date(appointment.start_time), 'PPpp')}
                </Typography>
              </Grid>

              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2" color="text.secondary">
                  End Time
                </Typography>
                <Typography variant="body1">
                  {format(new Date(appointment.end_time), 'PPpp')}
                </Typography>
              </Grid>

              {appointment.appointment_type_name && (
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Appointment Type
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {appointment.appointment_type_color && (
                      <Box
                        sx={{
                          width: 16,
                          height: 16,
                          borderRadius: '50%',
                          backgroundColor: appointment.appointment_type_color,
                        }}
                      />
                    )}
                    <Typography variant="body1">
                      {appointment.appointment_type_name}
                    </Typography>
                  </Box>
                </Grid>
              )}

              {appointment.room && (
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Room
                  </Typography>
                  <Typography variant="body1">{appointment.room}</Typography>
                </Grid>
              )}

              {appointment.assigned_staff_name && (
                <Grid item xs={12}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Assigned Staff
                  </Typography>
                  <Typography variant="body1">
                    {appointment.assigned_staff_name}
                  </Typography>
                </Grid>
              )}

              {appointment.description && (
                <Grid item xs={12}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Description
                  </Typography>
                  <Typography variant="body1">
                    {appointment.description}
                  </Typography>
                </Grid>
              )}

              {appointment.notes && (
                <Grid item xs={12}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Notes
                  </Typography>
                  <Typography variant="body1">{appointment.notes}</Typography>
                </Grid>
              )}
            </Grid>
          </Paper>
        </Grid>

        {/* Sidebar - Client and Patient Info */}
        <Grid item xs={12} md={4}>
          {/* Client Card */}
          <Card sx={{ mb: 2 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <PersonIcon color="primary" />
                <Typography variant="h6">Client</Typography>
              </Box>
              {appointment.client_name ? (
                <>
                  <Typography variant="body1" gutterBottom>
                    {appointment.client_name}
                  </Typography>
                  <Button
                    component={Link}
                    to={`/clients/${appointment.client_id}`}
                    size="small"
                    variant="outlined"
                    fullWidth
                  >
                    View Client
                  </Button>
                </>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  Client ID: {appointment.client_id}
                </Typography>
              )}
            </CardContent>
          </Card>

          {/* Patient Card */}
          {appointment.patient_id && (
            <Card sx={{ mb: 2 }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <PetsIcon color="primary" />
                  <Typography variant="h6">Patient</Typography>
                </Box>
                {appointment.patient_name ? (
                  <>
                    <Typography variant="body1" gutterBottom>
                      {appointment.patient_name}
                    </Typography>
                    <Button
                      component={Link}
                      to={`/patients/${appointment.patient_id}`}
                      size="small"
                      variant="outlined"
                      fullWidth
                    >
                      View Patient
                    </Button>
                  </>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    Patient ID: {appointment.patient_id}
                  </Typography>
                )}
              </CardContent>
            </Card>
          )}

          {/* Timing Information */}
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <MedicalServicesIcon color="primary" />
                <Typography variant="h6">Timing</Typography>
              </Box>

              {appointment.check_in_time && (
                <Box sx={{ mb: 1 }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Checked In
                  </Typography>
                  <Typography variant="body2">
                    {format(new Date(appointment.check_in_time), 'PPpp')}
                  </Typography>
                </Box>
              )}

              {appointment.actual_start_time && (
                <Box sx={{ mb: 1 }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Started
                  </Typography>
                  <Typography variant="body2">
                    {format(new Date(appointment.actual_start_time), 'PPpp')}
                  </Typography>
                </Box>
              )}

              {appointment.actual_end_time && (
                <Box sx={{ mb: 1 }}>
                  <Typography variant="subtitle2" color="text.secondary">
                    Ended
                  </Typography>
                  <Typography variant="body2">
                    {format(new Date(appointment.actual_end_time), 'PPpp')}
                  </Typography>
                </Box>
              )}

              {appointment.cancelled_at && (
                <>
                  <Divider sx={{ my: 1 }} />
                  <Box sx={{ mb: 1 }}>
                    <Typography variant="subtitle2" color="text.secondary">
                      Cancelled
                    </Typography>
                    <Typography variant="body2">
                      {format(new Date(appointment.cancelled_at), 'PPpp')}
                    </Typography>
                  </Box>
                  {appointment.cancelled_by_name && (
                    <Box sx={{ mb: 1 }}>
                      <Typography variant="subtitle2" color="text.secondary">
                        Cancelled By
                      </Typography>
                      <Typography variant="body2">
                        {appointment.cancelled_by_name}
                      </Typography>
                    </Box>
                  )}
                  {appointment.cancellation_reason && (
                    <Box>
                      <Typography variant="subtitle2" color="text.secondary">
                        Reason
                      </Typography>
                      <Typography variant="body2">
                        {appointment.cancellation_reason}
                      </Typography>
                    </Box>
                  )}
                </>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Metadata */}
      <Paper sx={{ p: 2, mt: 3 }}>
        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
          Metadata
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <Typography variant="body2" color="text.secondary">
              Created: {format(new Date(appointment.created_at), 'PPpp')}
            </Typography>
          </Grid>
          {appointment.updated_at && (
            <Grid item xs={12} sm={6}>
              <Typography variant="body2" color="text.secondary">
                Last Updated: {format(new Date(appointment.updated_at), 'PPpp')}
              </Typography>
            </Grid>
          )}
        </Grid>
      </Paper>
    </Container>
  );
};

export default AppointmentDetail;
