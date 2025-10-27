import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  CircularProgress,
  Alert,
  Grid,
  MenuItem,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import { Add as AddIcon, Delete as DeleteIcon, Edit as EditIcon } from '@mui/icons-material';
import logger from '../../utils/logger';

const diagnosisTypes = ['primary', 'differential', 'rule-out'];
const severities = ['mild', 'moderate', 'severe'];
const statuses = ['active', 'resolved', 'chronic', 'ruled-out'];

/**
 * Diagnoses Tab Component
 *
 * Manages diagnoses for a visit
 */
function DiagnosesTab({ visitId }) {
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingDiagnosis, setEditingDiagnosis] = useState(null);
  const [formData, setFormData] = useState({
    diagnosis_name: '',
    icd_code: '',
    diagnosis_type: 'primary',
    severity: '',
    status: 'active',
    onset_date: '',
    resolution_date: '',
    notes: '',
  });

  // Fetch diagnoses
  const {
    data: diagnosesList,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['diagnoses', visitId],
    queryFn: async () => {
      const response = await fetch(`/api/diagnoses?visit_id=${visitId}`, {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to fetch diagnoses');
      }

      const data = await response.json();
      return data.diagnoses || [];
    },
  });

  // Create diagnosis mutation
  const createMutation = useMutation({
    mutationFn: async (data) => {
      const response = await fetch('/api/diagnoses', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ ...data, visit_id: parseInt(visitId, 10) }),
      });

      if (!response.ok) {
        throw new Error('Failed to create diagnosis');
      }

      return response.json();
    },
    onSuccess: () => {
      logger.info('Diagnosis created', { visitId });
      queryClient.invalidateQueries(['diagnoses', visitId]);
      handleCloseDialog();
    },
  });

  // Update diagnosis mutation
  const updateMutation = useMutation({
    mutationFn: async ({ id, data }) => {
      const response = await fetch(`/api/diagnoses/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error('Failed to update diagnosis');
      }

      return response.json();
    },
    onSuccess: () => {
      logger.info('Diagnosis updated');
      queryClient.invalidateQueries(['diagnoses', visitId]);
      handleCloseDialog();
    },
  });

  // Delete diagnosis mutation
  const deleteMutation = useMutation({
    mutationFn: async (id) => {
      const response = await fetch(`/api/diagnoses/${id}`, {
        method: 'DELETE',
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to delete diagnosis');
      }

      return response.json();
    },
    onSuccess: () => {
      logger.info('Diagnosis deleted');
      queryClient.invalidateQueries(['diagnoses', visitId]);
    },
  });

  const handleOpenDialog = (diagnosis = null) => {
    if (diagnosis) {
      setEditingDiagnosis(diagnosis);
      setFormData({
        diagnosis_name: diagnosis.diagnosis_name || '',
        icd_code: diagnosis.icd_code || '',
        diagnosis_type: diagnosis.diagnosis_type || 'primary',
        severity: diagnosis.severity || '',
        status: diagnosis.status || 'active',
        onset_date: diagnosis.onset_date || '',
        resolution_date: diagnosis.resolution_date || '',
        notes: diagnosis.notes || '',
      });
    } else {
      setEditingDiagnosis(null);
      setFormData({
        diagnosis_name: '',
        icd_code: '',
        diagnosis_type: 'primary',
        severity: '',
        status: 'active',
        onset_date: '',
        resolution_date: '',
        notes: '',
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingDiagnosis(null);
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    const submitData = { ...formData };
    // Remove empty strings
    Object.keys(submitData).forEach((key) => {
      if (submitData[key] === '') {
        submitData[key] = null;
      }
    });

    if (editingDiagnosis) {
      updateMutation.mutate({ id: editingDiagnosis.id, data: submitData });
    } else {
      createMutation.mutate(submitData);
    }
  };

  const handleDelete = (id) => {
    if (window.confirm('Are you sure you want to delete this diagnosis?')) {
      deleteMutation.mutate(id);
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'severe':
        return 'error';
      case 'moderate':
        return 'warning';
      case 'mild':
        return 'success';
      default:
        return 'default';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
        return 'error';
      case 'chronic':
        return 'warning';
      case 'resolved':
        return 'success';
      case 'ruled-out':
        return 'default';
      default:
        return 'default';
    }
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" p={4}>
        <CircularProgress />
      </Box>
    );
  }

  if (isError) {
    return (
      <Box p={2}>
        <Alert severity="error">Failed to load diagnoses: {error.message}</Alert>
      </Box>
    );
  }

  return (
    <Paper sx={{ p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h6">Diagnoses</Typography>
        <Button startIcon={<AddIcon />} onClick={() => handleOpenDialog()} variant="contained">
          Add Diagnosis
        </Button>
      </Box>

      {diagnosesList.length === 0 ? (
        <Alert severity="info">No diagnoses recorded for this visit yet.</Alert>
      ) : (
        <List>
          {diagnosesList.map((diagnosis) => (
            <ListItem key={diagnosis.id} divider>
              <ListItemText
                primary={
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography variant="body1">{diagnosis.diagnosis_name}</Typography>
                    {diagnosis.icd_code && (
                      <Chip label={diagnosis.icd_code} size="small" variant="outlined" />
                    )}
                    <Chip
                      label={diagnosis.diagnosis_type}
                      size="small"
                      color={diagnosis.diagnosis_type === 'primary' ? 'primary' : 'default'}
                    />
                    {diagnosis.severity && (
                      <Chip
                        label={diagnosis.severity}
                        size="small"
                        color={getSeverityColor(diagnosis.severity)}
                      />
                    )}
                    <Chip
                      label={diagnosis.status}
                      size="small"
                      color={getStatusColor(diagnosis.status)}
                    />
                  </Box>
                }
                secondary={
                  <Box>
                    {diagnosis.notes && (
                      <Typography variant="body2" color="text.secondary">
                        {diagnosis.notes}
                      </Typography>
                    )}
                    {diagnosis.onset_date && (
                      <Typography variant="caption" color="text.secondary">
                        Onset: {new Date(diagnosis.onset_date).toLocaleDateString()}
                      </Typography>
                    )}
                  </Box>
                }
              />
              <ListItemSecondaryAction>
                <IconButton edge="end" onClick={() => handleOpenDialog(diagnosis)} sx={{ mr: 1 }}>
                  <EditIcon />
                </IconButton>
                <IconButton edge="end" onClick={() => handleDelete(diagnosis.id)} color="error">
                  <DeleteIcon />
                </IconButton>
              </ListItemSecondaryAction>
            </ListItem>
          ))}
        </List>
      )}

      {/* Add/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>{editingDiagnosis ? 'Edit Diagnosis' : 'Add Diagnosis'}</DialogTitle>
        <form onSubmit={handleSubmit}>
          <DialogContent>
            <Grid container spacing={2}>
              <Grid item xs={12} md={8}>
                <TextField
                  fullWidth
                  required
                  label="Diagnosis Name"
                  name="diagnosis_name"
                  value={formData.diagnosis_name}
                  onChange={handleChange}
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="ICD-10 Code"
                  name="icd_code"
                  value={formData.icd_code}
                  onChange={handleChange}
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  select
                  fullWidth
                  label="Type"
                  name="diagnosis_type"
                  value={formData.diagnosis_type}
                  onChange={handleChange}
                >
                  {diagnosisTypes.map((type) => (
                    <MenuItem key={type} value={type}>
                      {type}
                    </MenuItem>
                  ))}
                </TextField>
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  select
                  fullWidth
                  label="Severity"
                  name="severity"
                  value={formData.severity}
                  onChange={handleChange}
                >
                  <MenuItem value="">Not specified</MenuItem>
                  {severities.map((severity) => (
                    <MenuItem key={severity} value={severity}>
                      {severity}
                    </MenuItem>
                  ))}
                </TextField>
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  select
                  fullWidth
                  label="Status"
                  name="status"
                  value={formData.status}
                  onChange={handleChange}
                >
                  {statuses.map((status) => (
                    <MenuItem key={status} value={status}>
                      {status}
                    </MenuItem>
                  ))}
                </TextField>
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  type="date"
                  label="Onset Date"
                  name="onset_date"
                  value={formData.onset_date}
                  onChange={handleChange}
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  type="date"
                  label="Resolution Date"
                  name="resolution_date"
                  value={formData.resolution_date}
                  onChange={handleChange}
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  label="Notes"
                  name="notes"
                  value={formData.notes}
                  onChange={handleChange}
                />
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseDialog}>Cancel</Button>
            <Button
              type="submit"
              variant="contained"
              disabled={createMutation.isLoading || updateMutation.isLoading}
            >
              {editingDiagnosis ? 'Update' : 'Add'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </Paper>
  );
}

export default DiagnosesTab;
