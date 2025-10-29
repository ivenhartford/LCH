import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Alert,
  Chip,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  CheckCircle as CheckCircleIcon,
  CalendarToday as CalendarIcon,
} from '@mui/icons-material';
import logger from '../utils/logger';

/**
 * StaffSchedule Component
 *
 * Manages staff work schedules, shifts, and time-off requests.
 */
function StaffSchedule() {
  const queryClient = useQueryClient();

  const today = new Date();
  const weekStart = new Date(today.setDate(today.getDate() - today.getDay()));
  const weekEnd = new Date(today.setDate(today.getDate() + 6));

  const [startDate, setStartDate] = useState(weekStart.toISOString().split('T')[0]);
  const [endDate, setEndDate] = useState(weekEnd.toISOString().split('T')[0]);
  const [staffFilter, setStaffFilter] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingSchedule, setEditingSchedule] = useState(null);
  const [formData, setFormData] = useState({
    staff_id: '',
    shift_date: '',
    start_time: '09:00',
    end_time: '17:00',
    shift_type: 'regular',
    status: 'scheduled',
    break_minutes: 30,
    is_time_off: false,
    time_off_type: '',
    notes: '',
  });

  useEffect(() => {
    logger.logLifecycle('StaffSchedule', 'mounted');
    return () => logger.logLifecycle('StaffSchedule', 'unmounted');
  }, []);

  const { data: staffData } = useQuery({
    queryKey: ['staff-active'],
    queryFn: async () => {
      const response = await fetch('/api/staff?is_active=true', { credentials: 'include' });
      if (!response.ok) throw new Error('Failed to fetch staff');
      return response.json();
    },
  });

  const {
    data: schedulesData,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['schedules', staffFilter, startDate, endDate],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (staffFilter) params.append('staff_id', staffFilter);
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);

      const response = await fetch(`/api/schedules?${params}`, { credentials: 'include' });
      if (!response.ok) throw new Error('Failed to fetch schedules');
      return response.json();
    },
  });

  const saveMutation = useMutation({
    mutationFn: async (data) => {
      const url = editingSchedule ? `/api/schedules/${editingSchedule.id}` : '/api/schedules';
      const response = await fetch(url, {
        method: editingSchedule ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(data),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to save schedule');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['schedules']);
      handleCloseDialog();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (scheduleId) => {
      const response = await fetch(`/api/schedules/${scheduleId}`, {
        method: 'DELETE',
        credentials: 'include',
      });
      if (!response.ok) throw new Error('Failed to delete schedule');
      return response.json();
    },
    onSuccess: () => queryClient.invalidateQueries(['schedules']),
  });

  const approveMutation = useMutation({
    mutationFn: async (scheduleId) => {
      const response = await fetch(`/api/schedules/${scheduleId}/approve`, {
        method: 'POST',
        credentials: 'include',
      });
      if (!response.ok) throw new Error('Failed to approve time-off');
      return response.json();
    },
    onSuccess: () => queryClient.invalidateQueries(['schedules']),
  });

  const handleOpenDialog = (schedule = null) => {
    if (schedule) {
      setEditingSchedule(schedule);
      setFormData({
        staff_id: schedule.staff_id || '',
        shift_date: schedule.shift_date || '',
        start_time: schedule.start_time?.substring(0, 5) || '09:00',
        end_time: schedule.end_time?.substring(0, 5) || '17:00',
        shift_type: schedule.shift_type || 'regular',
        status: schedule.status || 'scheduled',
        break_minutes: schedule.break_minutes || 30,
        is_time_off: schedule.is_time_off || false,
        time_off_type: schedule.time_off_type || '',
        notes: schedule.notes || '',
      });
    } else {
      setEditingSchedule(null);
      setFormData({
        staff_id: '',
        shift_date: new Date().toISOString().split('T')[0],
        start_time: '09:00',
        end_time: '17:00',
        shift_type: 'regular',
        status: 'scheduled',
        break_minutes: 30,
        is_time_off: false,
        time_off_type: '',
        notes: '',
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingSchedule(null);
  };

  const handleSubmit = () => {
    saveMutation.mutate(formData);
  };

  const handleDelete = (scheduleId, staffName, date) => {
    if (window.confirm(`Delete schedule for ${staffName} on ${date}?`)) {
      deleteMutation.mutate(scheduleId);
    }
  };

  const handleApprove = (scheduleId) => {
    approveMutation.mutate(scheduleId);
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (isError) {
    return (
      <Box p={3}>
        <Alert severity="error">Failed to load schedules: {error.message}</Alert>
      </Box>
    );
  }

  const schedules = schedulesData?.schedules || [];
  const staff = staffData?.staff || [];

  const getShiftTypeColor = (type) => {
    switch (type) {
      case 'regular':
        return 'primary';
      case 'on-call':
        return 'warning';
      case 'overtime':
        return 'error';
      case 'training':
        return 'info';
      default:
        return 'default';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'scheduled':
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

  return (
    <Box>
      <Box mb={3} display="flex" justifyContent="space-between" alignItems="center">
        <Typography variant="h4">Staff Schedule</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => handleOpenDialog()}>
          Add Schedule
        </Button>
      </Box>

      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Staff Member</InputLabel>
              <Select
                value={staffFilter}
                label="Staff Member"
                onChange={(e) => setStaffFilter(e.target.value)}
              >
                <MenuItem value="">All Staff</MenuItem>
                {staff.map((member) => (
                  <MenuItem key={member.id} value={member.id}>
                    {member.full_name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={3}>
            <TextField
              fullWidth
              size="small"
              type="date"
              label="Start Date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
          <Grid item xs={12} sm={3}>
            <TextField
              fullWidth
              size="small"
              type="date"
              label="End Date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
        </Grid>
      </Paper>

      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Date</TableCell>
                <TableCell>Staff Member</TableCell>
                <TableCell>Time</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Notes</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {schedules.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    <Typography variant="body2" color="text.secondary" py={4}>
                      No schedules found for this period.
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                schedules.map((schedule) => (
                  <TableRow key={schedule.id} hover>
                    <TableCell>
                      <Box display="flex" alignItems="center" gap={0.5}>
                        <CalendarIcon fontSize="small" color="action" />
                        <Typography variant="body2">
                          {new Date(schedule.shift_date).toLocaleDateString()}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        {schedule.staff_name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {schedule.staff_position}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {schedule.is_time_off ? (
                        <Chip label={`Time Off: ${schedule.time_off_type}`} size="small" color="warning" />
                      ) : (
                        <Typography variant="body2">
                          {schedule.start_time?.substring(0, 5)} - {schedule.end_time?.substring(0, 5)}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={schedule.shift_type}
                        size="small"
                        color={getShiftTypeColor(schedule.shift_type)}
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={schedule.status}
                        size="small"
                        color={getStatusColor(schedule.status)}
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="caption">{schedule.notes || '-'}</Typography>
                    </TableCell>
                    <TableCell align="right">
                      {schedule.is_time_off && !schedule.time_off_approved && (
                        <Tooltip title="Approve Time-Off">
                          <IconButton size="small" color="success" onClick={() => handleApprove(schedule.id)}>
                            <CheckCircleIcon />
                          </IconButton>
                        </Tooltip>
                      )}
                      <Tooltip title="Edit">
                        <IconButton size="small" onClick={() => handleOpenDialog(schedule)}>
                          <EditIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete">
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleDelete(schedule.id, schedule.staff_name, schedule.shift_date)}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
        <Box p={2}>
          <Typography variant="body2" color="text.secondary">
            Total: {schedules.length} schedule entries
          </Typography>
        </Box>
      </Paper>

      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>{editingSchedule ? 'Edit Schedule' : 'Add Schedule'}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 0.5 }}>
            <Grid item xs={12}>
              <FormControl fullWidth required>
                <InputLabel>Staff Member</InputLabel>
                <Select
                  value={formData.staff_id}
                  label="Staff Member"
                  onChange={(e) => setFormData({ ...formData, staff_id: e.target.value })}
                >
                  {staff.map((member) => (
                    <MenuItem key={member.id} value={member.id}>
                      {member.full_name} - {member.position}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                required
                type="date"
                label="Date"
                value={formData.shift_date}
                onChange={(e) => setFormData({ ...formData, shift_date: e.target.value })}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Time Off?</InputLabel>
                <Select
                  value={formData.is_time_off}
                  label="Time Off?"
                  onChange={(e) => setFormData({ ...formData, is_time_off: e.target.value })}
                >
                  <MenuItem value={false}>No - Regular Shift</MenuItem>
                  <MenuItem value={true}>Yes - Time Off Request</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            {!formData.is_time_off ? (
              <>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    required
                    type="time"
                    label="Start Time"
                    value={formData.start_time}
                    onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                    InputLabelProps={{ shrink: true }}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    required
                    type="time"
                    label="End Time"
                    value={formData.end_time}
                    onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                    InputLabelProps={{ shrink: true }}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Shift Type</InputLabel>
                    <Select
                      value={formData.shift_type}
                      label="Shift Type"
                      onChange={(e) => setFormData({ ...formData, shift_type: e.target.value })}
                    >
                      <MenuItem value="regular">Regular</MenuItem>
                      <MenuItem value="on-call">On-Call</MenuItem>
                      <MenuItem value="overtime">Overtime</MenuItem>
                      <MenuItem value="training">Training</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Break (minutes)"
                    value={formData.break_minutes}
                    onChange={(e) => setFormData({ ...formData, break_minutes: parseInt(e.target.value) })}
                  />
                </Grid>
              </>
            ) : (
              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>Time Off Type</InputLabel>
                  <Select
                    value={formData.time_off_type}
                    label="Time Off Type"
                    onChange={(e) => setFormData({ ...formData, time_off_type: e.target.value })}
                  >
                    <MenuItem value="vacation">Vacation</MenuItem>
                    <MenuItem value="sick">Sick Leave</MenuItem>
                    <MenuItem value="personal">Personal</MenuItem>
                    <MenuItem value="unpaid">Unpaid Leave</MenuItem>
                    <MenuItem value="bereavement">Bereavement</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            )}
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Notes"
                multiline
                rows={2}
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={saveMutation.isLoading || !formData.staff_id || !formData.shift_date}
          >
            {saveMutation.isLoading ? <CircularProgress size={24} /> : 'Save'}
          </Button>
        </DialogActions>
        {saveMutation.isError && (
          <Alert severity="error" sx={{ m: 2 }}>
            {saveMutation.error.message}
          </Alert>
        )}
      </Dialog>
    </Box>
  );
}

export default StaffSchedule;
