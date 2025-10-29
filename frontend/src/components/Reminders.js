import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Box,
  Paper,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Grid,
  Chip,
  IconButton,
  Alert,
  CircularProgress,
  MenuItem,
  Tabs,
  Tab,
  Tooltip,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Cancel as CancelIcon,
  Notifications as NotificationsIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';
import logger from '../utils/logger';

/**
 * Reminders Component
 *
 * Manages reminders for appointments, vaccinations, medications, etc.
 * Supports email and SMS delivery with scheduling and retry logic.
 */
function Reminders() {
  const queryClient = useQueryClient();

  // State
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [openDialog, setOpenDialog] = useState(false);
  const [editingReminder, setEditingReminder] = useState(null);
  const [tabValue, setTabValue] = useState(0);
  const [clientFilter, setClientFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [reminderTypeFilter, setReminderTypeFilter] = useState('');

  // Form data
  const [formData, setFormData] = useState({
    client_id: '',
    patient_id: '',
    appointment_id: '',
    reminder_type: 'appointment',
    scheduled_date: new Date().toISOString().split('T')[0],
    scheduled_time: '09:00',
    send_at: '',
    delivery_method: 'email',
    status: 'pending',
    template_id: '',
    subject: '',
    message: '',
    notes: '',
  });

  useEffect(() => {
    logger.logLifecycle('Reminders', 'mounted');
    return () => logger.logLifecycle('Reminders', 'unmounted');
  }, []);

  // Fetch reminders based on active tab
  const getQueryKey = () => {
    if (tabValue === 0) return ['reminders', statusFilter, reminderTypeFilter, clientFilter];
    if (tabValue === 1) return ['reminders-pending'];
    if (tabValue === 2) return ['reminders-upcoming'];
    return ['reminders'];
  };

  const getQueryFn = async () => {
    let url = '/api/reminders';

    if (tabValue === 1) {
      url = '/api/reminders/pending';
    } else if (tabValue === 2) {
      url = '/api/reminders/upcoming';
    } else {
      const params = new URLSearchParams();
      if (statusFilter) params.append('status', statusFilter);
      if (reminderTypeFilter) params.append('reminder_type', reminderTypeFilter);
      if (clientFilter) params.append('client_id', clientFilter);
      if (params.toString()) url += `?${params}`;
    }

    const response = await fetch(url, { credentials: 'include' });
    if (!response.ok) throw new Error('Failed to fetch reminders');
    return response.json();
  };

  const { data: remindersData, isLoading } = useQuery({
    queryKey: getQueryKey(),
    queryFn: getQueryFn,
  });

  // Fetch clients for dropdown
  const { data: clientsData } = useQuery({
    queryKey: ['clients-all'],
    queryFn: async () => {
      const response = await fetch('/api/clients', { credentials: 'include' });
      if (!response.ok) throw new Error('Failed to fetch clients');
      return response.json();
    },
  });

  // Fetch patients for dropdown
  const { data: patientsData } = useQuery({
    queryKey: ['patients-all'],
    queryFn: async () => {
      const response = await fetch('/api/patients', { credentials: 'include' });
      if (!response.ok) throw new Error('Failed to fetch patients');
      return response.json();
    },
  });

  // Fetch templates for dropdown
  const { data: templatesData } = useQuery({
    queryKey: ['notification-templates'],
    queryFn: async () => {
      const response = await fetch('/api/notification-templates?is_active=true', {
        credentials: 'include',
      });
      if (!response.ok) throw new Error('Failed to fetch templates');
      return response.json();
    },
  });

  // Create mutation
  const createMutation = useMutation({
    mutationFn: async (data) => {
      const response = await fetch('/api/reminders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(data),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to create reminder');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['reminders']);
      queryClient.invalidateQueries(['reminders-pending']);
      queryClient.invalidateQueries(['reminders-upcoming']);
      handleCloseDialog();
      logger.logAction('Reminder created');
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: async ({ id, data }) => {
      const response = await fetch(`/api/reminders/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(data),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to update reminder');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['reminders']);
      queryClient.invalidateQueries(['reminders-pending']);
      queryClient.invalidateQueries(['reminders-upcoming']);
      handleCloseDialog();
      logger.logAction('Reminder updated');
    },
  });

  // Cancel mutation
  const cancelMutation = useMutation({
    mutationFn: async (id) => {
      const response = await fetch(`/api/reminders/${id}/cancel`, {
        method: 'POST',
        credentials: 'include',
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to cancel reminder');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['reminders']);
      queryClient.invalidateQueries(['reminders-pending']);
      queryClient.invalidateQueries(['reminders-upcoming']);
      logger.logAction('Reminder cancelled');
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: async (id) => {
      const response = await fetch(`/api/reminders/${id}`, {
        method: 'DELETE',
        credentials: 'include',
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to delete reminder');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['reminders']);
      queryClient.invalidateQueries(['reminders-pending']);
      queryClient.invalidateQueries(['reminders-upcoming']);
      logger.logAction('Reminder deleted');
    },
  });

  const reminders = remindersData?.reminders || [];
  const clients = clientsData?.clients || [];
  const patients = patientsData?.patients || [];
  const templates = templatesData?.templates || [];

  const handleOpenDialog = (reminder = null) => {
    if (reminder) {
      setEditingReminder(reminder);
      setFormData({
        client_id: reminder.client_id || '',
        patient_id: reminder.patient_id || '',
        appointment_id: reminder.appointment_id || '',
        reminder_type: reminder.reminder_type || 'appointment',
        scheduled_date: reminder.scheduled_date
          ? new Date(reminder.scheduled_date).toISOString().split('T')[0]
          : '',
        scheduled_time: reminder.scheduled_time || '09:00',
        send_at: reminder.send_at ? new Date(reminder.send_at).toISOString().slice(0, 16) : '',
        delivery_method: reminder.delivery_method || 'email',
        status: reminder.status || 'pending',
        template_id: reminder.template_id || '',
        subject: reminder.subject || '',
        message: reminder.message || '',
        notes: reminder.notes || '',
      });
      logger.logAction('Edit reminder dialog opened', { reminder_id: reminder.id });
    } else {
      setEditingReminder(null);
      setFormData({
        client_id: '',
        patient_id: '',
        appointment_id: '',
        reminder_type: 'appointment',
        scheduled_date: new Date().toISOString().split('T')[0],
        scheduled_time: '09:00',
        send_at: '',
        delivery_method: 'email',
        status: 'pending',
        template_id: '',
        subject: '',
        message: '',
        notes: '',
      });
      logger.logAction('New reminder dialog opened');
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingReminder(null);
  };

  const handleSubmit = () => {
    const data = { ...formData };

    // Convert empty strings to null for optional fields
    if (!data.patient_id) data.patient_id = null;
    if (!data.appointment_id) data.appointment_id = null;
    if (!data.template_id) data.template_id = null;
    if (!data.subject) data.subject = null;

    // Combine scheduled_date and scheduled_time to create send_at if not manually set
    if (!data.send_at && data.scheduled_date && data.scheduled_time) {
      data.send_at = `${data.scheduled_date}T${data.scheduled_time}:00`;
    }

    if (editingReminder) {
      updateMutation.mutate({ id: editingReminder.id, data });
    } else {
      createMutation.mutate(data);
    }
  };

  const handleCancel = (reminder) => {
    if (window.confirm(`Cancel this reminder for ${reminder.client_name}?`)) {
      cancelMutation.mutate(reminder.id);
    }
  };

  const handleDelete = (reminder) => {
    if (window.confirm(`Are you sure you want to delete this reminder for ${reminder.client_name}?`)) {
      deleteMutation.mutate(reminder.id);
    }
  };

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending':
        return 'warning';
      case 'sent':
        return 'success';
      case 'failed':
        return 'error';
      case 'cancelled':
        return 'default';
      default:
        return 'default';
    }
  };

  const getReminderTypeLabel = (type) => {
    const labels = {
      appointment: 'Appointment',
      vaccination: 'Vaccination',
      medication: 'Medication',
      checkup: 'Checkup',
      followup: 'Follow-up',
    };
    return labels[type] || type;
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  const paginatedReminders = reminders.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" display="flex" alignItems="center" gap={1}>
          <NotificationsIcon fontSize="large" />
          Reminders
        </Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => handleOpenDialog()}>
          Create Reminder
        </Button>
      </Box>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
          <Tab label="All Reminders" />
          <Tab label="Pending" />
          <Tab label="Upcoming (7 Days)" />
        </Tabs>
      </Paper>

      {/* Filters (only show on "All Reminders" tab) */}
      {tabValue === 0 && (
        <Paper sx={{ p: 2, mb: 3 }}>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                select
                size="small"
                label="Client"
                value={clientFilter}
                onChange={(e) => setClientFilter(e.target.value)}
              >
                <MenuItem value="">All Clients</MenuItem>
                {clients.map((c) => (
                  <MenuItem key={c.id} value={c.id}>
                    {c.name}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                select
                size="small"
                label="Type"
                value={reminderTypeFilter}
                onChange={(e) => setReminderTypeFilter(e.target.value)}
              >
                <MenuItem value="">All Types</MenuItem>
                <MenuItem value="appointment">Appointment</MenuItem>
                <MenuItem value="vaccination">Vaccination</MenuItem>
                <MenuItem value="medication">Medication</MenuItem>
                <MenuItem value="checkup">Checkup</MenuItem>
                <MenuItem value="followup">Follow-up</MenuItem>
              </TextField>
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                select
                size="small"
                label="Status"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <MenuItem value="">All Statuses</MenuItem>
                <MenuItem value="pending">Pending</MenuItem>
                <MenuItem value="sent">Sent</MenuItem>
                <MenuItem value="failed">Failed</MenuItem>
                <MenuItem value="cancelled">Cancelled</MenuItem>
              </TextField>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* Error Messages */}
      {(createMutation.isError ||
        updateMutation.isError ||
        deleteMutation.isError ||
        cancelMutation.isError) && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {createMutation.error?.message ||
            updateMutation.error?.message ||
            deleteMutation.error?.message ||
            cancelMutation.error?.message}
        </Alert>
      )}

      {/* Reminders Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Client</TableCell>
              <TableCell>Patient</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Scheduled</TableCell>
              <TableCell>Delivery</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {paginatedReminders.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  <Typography color="text.secondary" py={3}>
                    No reminders found
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              paginatedReminders.map((reminder) => (
                <TableRow key={reminder.id} hover>
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium">
                      {reminder.client_name}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{reminder.patient_name || 'N/A'}</Typography>
                  </TableCell>
                  <TableCell>
                    <Chip label={getReminderTypeLabel(reminder.reminder_type)} size="small" />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {new Date(reminder.send_at).toLocaleString()}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={reminder.delivery_method.toUpperCase()}
                      size="small"
                      color={reminder.delivery_method === 'email' ? 'primary' : 'info'}
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={reminder.status}
                      size="small"
                      color={getStatusColor(reminder.status)}
                    />
                  </TableCell>
                  <TableCell align="right">
                    <Tooltip title="Edit">
                      <IconButton
                        size="small"
                        onClick={() => handleOpenDialog(reminder)}
                        color="primary"
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    {reminder.status === 'pending' && (
                      <Tooltip title="Cancel">
                        <IconButton
                          size="small"
                          onClick={() => handleCancel(reminder)}
                          color="warning"
                        >
                          <CancelIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    )}
                    <Tooltip title="Delete">
                      <IconButton
                        size="small"
                        onClick={() => handleDelete(reminder)}
                        color="error"
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
        <TablePagination
          component="div"
          count={reminders.length}
          page={page}
          onPageChange={handleChangePage}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          rowsPerPageOptions={[5, 10, 25, 50]}
        />
      </TableContainer>

      {/* Add/Edit Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>{editingReminder ? 'Edit Reminder' : 'Create Reminder'}</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <Typography variant="subtitle2" color="primary" gutterBottom>
                  Recipient Information
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  required
                  select
                  label="Client"
                  value={formData.client_id}
                  onChange={(e) => setFormData({ ...formData, client_id: e.target.value })}
                >
                  {clients.map((c) => (
                    <MenuItem key={c.id} value={c.id}>
                      {c.name}
                    </MenuItem>
                  ))}
                </TextField>
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  select
                  label="Patient (Optional)"
                  value={formData.patient_id}
                  onChange={(e) => setFormData({ ...formData, patient_id: e.target.value })}
                >
                  <MenuItem value="">None</MenuItem>
                  {patients.map((p) => (
                    <MenuItem key={p.id} value={p.id}>
                      {p.name}
                    </MenuItem>
                  ))}
                </TextField>
              </Grid>

              <Grid item xs={12}>
                <Typography variant="subtitle2" color="primary" gutterBottom sx={{ mt: 2 }}>
                  Reminder Details
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  required
                  select
                  label="Reminder Type"
                  value={formData.reminder_type}
                  onChange={(e) => setFormData({ ...formData, reminder_type: e.target.value })}
                >
                  <MenuItem value="appointment">Appointment</MenuItem>
                  <MenuItem value="vaccination">Vaccination</MenuItem>
                  <MenuItem value="medication">Medication</MenuItem>
                  <MenuItem value="checkup">Checkup</MenuItem>
                  <MenuItem value="followup">Follow-up</MenuItem>
                </TextField>
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  required
                  select
                  label="Delivery Method"
                  value={formData.delivery_method}
                  onChange={(e) => setFormData({ ...formData, delivery_method: e.target.value })}
                >
                  <MenuItem value="email">Email</MenuItem>
                  <MenuItem value="sms">SMS</MenuItem>
                  <MenuItem value="both">Email & SMS</MenuItem>
                </TextField>
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  required
                  type="date"
                  label="Scheduled Date"
                  value={formData.scheduled_date}
                  onChange={(e) => setFormData({ ...formData, scheduled_date: e.target.value })}
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  required
                  type="time"
                  label="Scheduled Time"
                  value={formData.scheduled_time}
                  onChange={(e) => setFormData({ ...formData, scheduled_time: e.target.value })}
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>

              <Grid item xs={12}>
                <Typography variant="subtitle2" color="primary" gutterBottom sx={{ mt: 2 }}>
                  Message Content
                </Typography>
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  select
                  label="Template (Optional)"
                  value={formData.template_id}
                  onChange={(e) => setFormData({ ...formData, template_id: e.target.value })}
                  helperText="Select a template or enter custom message below"
                >
                  <MenuItem value="">No Template</MenuItem>
                  {templates.map((t) => (
                    <MenuItem key={t.id} value={t.id}>
                      {t.name}
                    </MenuItem>
                  ))}
                </TextField>
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Subject (Email Only)"
                  value={formData.subject}
                  onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  required
                  multiline
                  rows={4}
                  label="Message"
                  value={formData.message}
                  onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                  helperText="Enter the reminder message text"
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={2}
                  label="Notes (Internal)"
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                />
              </Grid>
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={
              !formData.client_id ||
              !formData.reminder_type ||
              !formData.scheduled_date ||
              !formData.message ||
              createMutation.isPending ||
              updateMutation.isPending
            }
          >
            {editingReminder ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default Reminders;
