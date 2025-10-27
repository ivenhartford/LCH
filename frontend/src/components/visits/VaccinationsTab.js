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

const vaccineTypes = ['Core', 'Non-core', 'Lifestyle-dependent'];
const routes = ['SC', 'IM', 'IV', 'PO', 'Intranasal', 'Other'];
const statuses = ['current', 'overdue', 'not_due', 'declined'];

/**
 * Vaccinations Tab Component
 *
 * Manages vaccination records for a visit
 */
function VaccinationsTab({ visitId, patientId }) {
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingVaccination, setEditingVaccination] = useState(null);
  const [formData, setFormData] = useState({
    vaccine_name: '',
    vaccine_type: '',
    manufacturer: '',
    lot_number: '',
    serial_number: '',
    administration_date: new Date().toISOString().slice(0, 10),
    expiration_date: '',
    next_due_date: '',
    dosage: '',
    route: 'SC',
    administration_site: '',
    status: 'current',
    notes: '',
    adverse_reactions: '',
  });

  // Fetch vaccinations for this patient
  const {
    data: vaccinationsList,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['vaccinations', patientId],
    queryFn: async () => {
      const response = await fetch(`/api/vaccinations?patient_id=${patientId}`, {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to fetch vaccinations');
      }

      const data = await response.json();
      return data.vaccinations || [];
    },
  });

  // Create vaccination mutation
  const createMutation = useMutation({
    mutationFn: async (data) => {
      const response = await fetch('/api/vaccinations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          ...data,
          patient_id: parseInt(patientId, 10),
          visit_id: parseInt(visitId, 10),
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to create vaccination');
      }

      return response.json();
    },
    onSuccess: () => {
      logger.info('Vaccination created', { visitId, patientId });
      queryClient.invalidateQueries(['vaccinations', patientId]);
      handleCloseDialog();
    },
  });

  // Update vaccination mutation
  const updateMutation = useMutation({
    mutationFn: async ({ id, data }) => {
      const response = await fetch(`/api/vaccinations/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error('Failed to update vaccination');
      }

      return response.json();
    },
    onSuccess: () => {
      logger.info('Vaccination updated');
      queryClient.invalidateQueries(['vaccinations', patientId]);
      handleCloseDialog();
    },
  });

  // Delete vaccination mutation
  const deleteMutation = useMutation({
    mutationFn: async (id) => {
      const response = await fetch(`/api/vaccinations/${id}`, {
        method: 'DELETE',
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to delete vaccination');
      }

      return response.json();
    },
    onSuccess: () => {
      logger.info('Vaccination deleted');
      queryClient.invalidateQueries(['vaccinations', patientId]);
    },
  });

  const handleOpenDialog = (vaccination = null) => {
    if (vaccination) {
      setEditingVaccination(vaccination);
      setFormData({
        vaccine_name: vaccination.vaccine_name || '',
        vaccine_type: vaccination.vaccine_type || '',
        manufacturer: vaccination.manufacturer || '',
        lot_number: vaccination.lot_number || '',
        serial_number: vaccination.serial_number || '',
        administration_date: vaccination.administration_date || '',
        expiration_date: vaccination.expiration_date || '',
        next_due_date: vaccination.next_due_date || '',
        dosage: vaccination.dosage || '',
        route: vaccination.route || 'SC',
        administration_site: vaccination.administration_site || '',
        status: vaccination.status || 'current',
        notes: vaccination.notes || '',
        adverse_reactions: vaccination.adverse_reactions || '',
      });
    } else {
      setEditingVaccination(null);
      setFormData({
        vaccine_name: '',
        vaccine_type: '',
        manufacturer: '',
        lot_number: '',
        serial_number: '',
        administration_date: new Date().toISOString().slice(0, 10),
        expiration_date: '',
        next_due_date: '',
        dosage: '',
        route: 'SC',
        administration_site: '',
        status: 'current',
        notes: '',
        adverse_reactions: '',
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingVaccination(null);
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

    if (editingVaccination) {
      updateMutation.mutate({ id: editingVaccination.id, data: submitData });
    } else {
      createMutation.mutate(submitData);
    }
  };

  const handleDelete = (id) => {
    if (window.confirm('Are you sure you want to delete this vaccination record?')) {
      deleteMutation.mutate(id);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'current':
        return 'success';
      case 'overdue':
        return 'error';
      case 'not_due':
        return 'info';
      case 'declined':
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
        <Alert severity="error">Failed to load vaccinations: {error.message}</Alert>
      </Box>
    );
  }

  return (
    <Paper sx={{ p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h6">Vaccination History</Typography>
        <Button startIcon={<AddIcon />} onClick={() => handleOpenDialog()} variant="contained">
          Add Vaccination
        </Button>
      </Box>

      {vaccinationsList.length === 0 ? (
        <Alert severity="info">No vaccination records found for this patient.</Alert>
      ) : (
        <List>
          {vaccinationsList.map((vaccination) => (
            <ListItem key={vaccination.id} divider>
              <ListItemText
                primary={
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography variant="body1" fontWeight="bold">
                      {vaccination.vaccine_name}
                    </Typography>
                    {vaccination.vaccine_type && (
                      <Chip
                        label={vaccination.vaccine_type}
                        size="small"
                        color="primary"
                        variant="outlined"
                      />
                    )}
                    <Chip
                      label={vaccination.status}
                      size="small"
                      color={getStatusColor(vaccination.status)}
                    />
                  </Box>
                }
                secondary={
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Administered: {new Date(vaccination.administration_date).toLocaleDateString()}
                      {vaccination.route && ` • Route: ${vaccination.route}`}
                      {vaccination.administration_site &&
                        ` • Site: ${vaccination.administration_site}`}
                    </Typography>
                    {vaccination.next_due_date && (
                      <Typography variant="body2" color="text.secondary">
                        Next due: {new Date(vaccination.next_due_date).toLocaleDateString()}
                      </Typography>
                    )}
                    {vaccination.adverse_reactions && (
                      <Alert severity="warning" sx={{ mt: 1 }}>
                        Adverse Reaction: {vaccination.adverse_reactions}
                      </Alert>
                    )}
                  </Box>
                }
              />
              <ListItemSecondaryAction>
                <IconButton edge="end" onClick={() => handleOpenDialog(vaccination)} sx={{ mr: 1 }}>
                  <EditIcon />
                </IconButton>
                <IconButton edge="end" onClick={() => handleDelete(vaccination.id)} color="error">
                  <DeleteIcon />
                </IconButton>
              </ListItemSecondaryAction>
            </ListItem>
          ))}
        </List>
      )}

      {/* Add/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>{editingVaccination ? 'Edit Vaccination' : 'Add Vaccination'}</DialogTitle>
        <form onSubmit={handleSubmit}>
          <DialogContent>
            <Grid container spacing={2}>
              <Grid item xs={12} md={8}>
                <TextField
                  fullWidth
                  required
                  label="Vaccine Name"
                  name="vaccine_name"
                  value={formData.vaccine_name}
                  onChange={handleChange}
                  placeholder="e.g., FVRCP, Rabies, FeLV"
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  select
                  fullWidth
                  label="Type"
                  name="vaccine_type"
                  value={formData.vaccine_type}
                  onChange={handleChange}
                >
                  <MenuItem value="">Not specified</MenuItem>
                  {vaccineTypes.map((type) => (
                    <MenuItem key={type} value={type}>
                      {type}
                    </MenuItem>
                  ))}
                </TextField>
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Manufacturer"
                  name="manufacturer"
                  value={formData.manufacturer}
                  onChange={handleChange}
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <TextField
                  fullWidth
                  label="Lot Number"
                  name="lot_number"
                  value={formData.lot_number}
                  onChange={handleChange}
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <TextField
                  fullWidth
                  label="Serial Number"
                  name="serial_number"
                  value={formData.serial_number}
                  onChange={handleChange}
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  required
                  type="date"
                  label="Administration Date"
                  name="administration_date"
                  value={formData.administration_date}
                  onChange={handleChange}
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  type="date"
                  label="Expiration Date"
                  name="expiration_date"
                  value={formData.expiration_date}
                  onChange={handleChange}
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  type="date"
                  label="Next Due Date"
                  name="next_due_date"
                  value={formData.next_due_date}
                  onChange={handleChange}
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Dosage"
                  name="dosage"
                  value={formData.dosage}
                  onChange={handleChange}
                  placeholder="e.g., 1ml"
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  select
                  fullWidth
                  label="Route"
                  name="route"
                  value={formData.route}
                  onChange={handleChange}
                >
                  {routes.map((route) => (
                    <MenuItem key={route} value={route}>
                      {route}
                    </MenuItem>
                  ))}
                </TextField>
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Administration Site"
                  name="administration_site"
                  value={formData.administration_site}
                  onChange={handleChange}
                  placeholder="e.g., Right shoulder"
                />
              </Grid>
              <Grid item xs={12}>
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
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={2}
                  label="Notes"
                  name="notes"
                  value={formData.notes}
                  onChange={handleChange}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={2}
                  label="Adverse Reactions"
                  name="adverse_reactions"
                  value={formData.adverse_reactions}
                  onChange={handleChange}
                  placeholder="Document any adverse reactions..."
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
              {editingVaccination ? 'Update' : 'Add'}
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </Paper>
  );
}

export default VaccinationsTab;
