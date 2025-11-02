import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Alert,
  Chip,
} from '@mui/material';
import { Event as EventIcon } from '@mui/icons-material';
import { format } from 'date-fns';

/**
 * Client Appointment History Component
 *
 * View all past and upcoming appointments (read-only)
 */
function ClientAppointmentHistory({ portalUser }) {
  const { data: appointments, isLoading, error } = useQuery({
    queryKey: ['portalAppointments', portalUser?.client_id],
    queryFn: async () => {
      const response = await fetch(`/api/portal/appointments/${portalUser.client_id}`);
      if (!response.ok) throw new Error('Failed to fetch appointments');
      return response.json();
    },
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
        Error loading appointments: {error.message}
      </Alert>
    );
  }

  const getStatusColor = (status) => {
    const colors = {
      scheduled: 'primary',
      confirmed: 'success',
      'in-progress': 'warning',
      completed: 'default',
      cancelled: 'error',
    };
    return colors[status] || 'default';
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <EventIcon sx={{ fontSize: 40, mr: 2, color: 'primary.main' }} />
        <Typography variant="h4">Appointment History</Typography>
      </Box>

      {appointments && appointments.length > 0 ? (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell><strong>Date & Time</strong></TableCell>
                <TableCell><strong>Appointment</strong></TableCell>
                <TableCell><strong>Status</strong></TableCell>
                <TableCell><strong>Description</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {appointments.map((apt) => (
                <TableRow key={apt.id}>
                  <TableCell>
                    {apt.start_time ? format(new Date(apt.start_time), 'PPp') : 'N/A'}
                  </TableCell>
                  <TableCell>{apt.title}</TableCell>
                  <TableCell>
                    <Chip
                      label={apt.status}
                      size="small"
                      color={getStatusColor(apt.status)}
                    />
                  </TableCell>
                  <TableCell>
                    {apt.description || '-'}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      ) : (
        <Alert severity="info">No appointments found</Alert>
      )}
    </Box>
  );
}

export default ClientAppointmentHistory;
