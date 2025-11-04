import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  Chip,
  IconButton,
  Tooltip,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  useMediaQuery,
  useTheme,
  Divider,
  Alert,
} from '@mui/material';
import {
  Add as AddIcon,
  Event as EventIcon,
  Person as PersonIcon,
  Pets as PetsIcon,
  Schedule as ScheduleIcon,
  ChevronRight as ChevronRightIcon,
  Today as TodayIcon,
} from '@mui/icons-material';
import { format, parseISO, isToday, isTomorrow, isPast, isFuture } from 'date-fns';
import TableSkeleton from './common/TableSkeleton';
import EmptyState from './common/EmptyState';

/**
 * Appointments List Component
 *
 * Modern MUI-based appointments view optimized for mobile and desktop.
 * Replaces react-big-calendar with a more mobile-friendly interface.
 */
function Appointments() {
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const [statusFilter, setStatusFilter] = useState('upcoming');
  const [dateFilter, setDateFilter] = useState('all');

  // Fetch appointments
  const { data: appointments = [], isLoading, isError, error } = useQuery({
    queryKey: ['appointments'],
    queryFn: async () => {
      const response = await fetch('/api/appointments', {
        credentials: 'include',
      });
      if (!response.ok) {
        throw new Error('Failed to fetch appointments');
      }
      return response.json();
    },
    staleTime: 30000,
  });

  // Helper functions
  const getStatusColor = (status) => {
    switch (status?.toLowerCase()) {
      case 'scheduled':
      case 'confirmed':
        return 'primary';
      case 'completed':
        return 'success';
      case 'cancelled':
        return 'error';
      case 'no-show':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getDateLabel = (dateStr) => {
    try {
      const date = parseISO(dateStr);
      if (isToday(date)) return 'Today';
      if (isTomorrow(date)) return 'Tomorrow';
      return format(date, 'EEEE, MMMM d, yyyy');
    } catch {
      return 'Invalid date';
    }
  };

  const getTimeLabel = (startStr, endStr) => {
    try {
      const start = parseISO(startStr);
      const end = parseISO(endStr);
      return `${format(start, 'h:mm a')} - ${format(end, 'h:mm a')}`;
    } catch {
      return 'Invalid time';
    }
  };

  // Filter appointments
  const filteredAppointments = appointments.filter((apt) => {
    // Status filter
    if (statusFilter === 'upcoming') {
      const aptDate = parseISO(apt.start_time);
      if (isPast(aptDate) && apt.status !== 'scheduled' && apt.status !== 'confirmed') {
        return false;
      }
    } else if (statusFilter === 'past') {
      const aptDate = parseISO(apt.start_time);
      if (isFuture(aptDate)) return false;
    } else if (statusFilter !== 'all') {
      if (apt.status?.toLowerCase() !== statusFilter) return false;
    }

    // Date filter
    if (dateFilter === 'today') {
      if (!isToday(parseISO(apt.start_time))) return false;
    } else if (dateFilter === 'tomorrow') {
      if (!isTomorrow(parseISO(apt.start_time))) return false;
    }

    return true;
  });

  // Sort by start time
  const sortedAppointments = [...filteredAppointments].sort((a, b) => {
    return new Date(a.start_time) - new Date(b.start_time);
  });

  // Loading state
  if (isLoading) {
    return (
      <Box>
        <Typography variant="h4" component="h1" mb={3}>
          <EventIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Appointments
        </Typography>
        <TableSkeleton rows={5} columns={1} showHeaders={false} />
      </Box>
    );
  }

  // Error state
  if (isError) {
    return (
      <Box p={3}>
        <Alert severity="error">Error loading appointments: {error.message}</Alert>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box mb={3} display="flex" justifyContent="space-between" alignItems="center" flexWrap="wrap" gap={2}>
        <Typography variant="h4" component="h1">
          <EventIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Appointments
        </Typography>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={() => navigate('/appointments/new')}
        >
          New Appointment
        </Button>
      </Box>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={4}>
            <FormControl fullWidth size="small">
              <InputLabel>Status</InputLabel>
              <Select
                value={statusFilter}
                label="Status"
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <MenuItem value="all">All</MenuItem>
                <MenuItem value="upcoming">Upcoming</MenuItem>
                <MenuItem value="past">Past</MenuItem>
                <MenuItem value="scheduled">Scheduled</MenuItem>
                <MenuItem value="confirmed">Confirmed</MenuItem>
                <MenuItem value="completed">Completed</MenuItem>
                <MenuItem value="cancelled">Cancelled</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <FormControl fullWidth size="small">
              <InputLabel>Date</InputLabel>
              <Select
                value={dateFilter}
                label="Date"
                onChange={(e) => setDateFilter(e.target.value)}
              >
                <MenuItem value="all">All</MenuItem>
                <MenuItem value="today">Today</MenuItem>
                <MenuItem value="tomorrow">Tomorrow</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>

      {/* Results count */}
      {sortedAppointments.length > 0 && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Showing {sortedAppointments.length} appointment{sortedAppointments.length !== 1 ? 's' : ''}
        </Typography>
      )}

      {/* Empty State or Appointments List */}
      {sortedAppointments.length === 0 ? (
        <EmptyState
          icon={EventIcon}
          title={statusFilter !== 'all' || dateFilter !== 'all' ? 'No Appointments Found' : 'No Appointments Yet'}
          message={
            statusFilter !== 'all' || dateFilter !== 'all'
              ? 'No appointments match your current filters. Try adjusting your filters.'
              : 'Get started by scheduling your first appointment. Track patient visits, procedures, and follow-ups all in one place.'
          }
          actionLabel={statusFilter !== 'all' || dateFilter !== 'all' ? 'Clear Filters' : 'New Appointment'}
          onAction={
            statusFilter !== 'all' || dateFilter !== 'all'
              ? () => {
                  setStatusFilter('upcoming');
                  setDateFilter('all');
                }
              : () => navigate('/appointments/new')
          }
          actionIcon={statusFilter !== 'all' || dateFilter !== 'all' ? undefined : AddIcon}
        />
      ) : (
        <Grid container spacing={2}>
          {sortedAppointments.map((appointment) => (
            <Grid item xs={12} key={appointment.id}>
              <Card
                sx={{
                  cursor: 'pointer',
                  '&:hover': {
                    boxShadow: 3,
                    transform: 'translateY(-2px)',
                    transition: 'all 0.2s ease-in-out',
                  },
                }}
                onClick={() => navigate(`/appointments/${appointment.id}`)}
              >
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                    <Box flex={1}>
                      <Typography variant="h6" component="h2">
                        {appointment.title || 'Appointment'}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" mt={0.5}>
                        {getDateLabel(appointment.start_time)}
                      </Typography>
                    </Box>
                    <Chip
                      label={appointment.status || 'Scheduled'}
                      color={getStatusColor(appointment.status)}
                      size="small"
                    />
                  </Box>

                  <Box display="flex" flexDirection="column" gap={1}>
                    <Box display="flex" alignItems="center" gap={1}>
                      <ScheduleIcon fontSize="small" color="action" />
                      <Typography variant="body2" color="text.secondary">
                        {getTimeLabel(appointment.start_time, appointment.end_time)}
                      </Typography>
                    </Box>

                    {appointment.client_name && (
                      <Box display="flex" alignItems="center" gap={1}>
                        <PersonIcon fontSize="small" color="action" />
                        <Typography variant="body2" color="text.secondary">
                          {appointment.client_name}
                        </Typography>
                      </Box>
                    )}

                    {appointment.patient_name && (
                      <Box display="flex" alignItems="center" gap={1}>
                        <PetsIcon fontSize="small" color="action" />
                        <Typography variant="body2" color="text.secondary">
                          {appointment.patient_name}
                        </Typography>
                      </Box>
                    )}

                    {appointment.appointment_type_name && (
                      <Box mt={1}>
                        <Chip
                          label={appointment.appointment_type_name}
                          size="small"
                          variant="outlined"
                        />
                      </Box>
                    )}
                  </Box>
                </CardContent>

                <Divider />

                <Box sx={{ p: 2, display: 'flex', justifyContent: 'flex-end' }}>
                  <Button
                    size="small"
                    endIcon={<ChevronRightIcon />}
                    onClick={() => navigate(`/appointments/${appointment.id}`)}
                  >
                    View Details
                  </Button>
                </Box>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );
}

export default Appointments;
