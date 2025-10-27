import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import {
  Box,
  Paper,
  Grid,
  TextField,
  Button,
  MenuItem,
  Alert,
  Typography,
  Card,
  CardContent,
  CardHeader,
} from '@mui/material';
import { Save as SaveIcon, Edit as EditIcon, Cancel as CancelIcon } from '@mui/icons-material';
import logger from '../../utils/logger';

const visitTypes = ['Wellness', 'Sick', 'Emergency', 'Follow-up', 'Surgery', 'Dental', 'Other'];
const visitStatuses = ['scheduled', 'in_progress', 'completed', 'cancelled'];

function VisitOverview({ visit, isNewVisit, editMode, setEditMode }) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [formData, setFormData] = useState({
    patient_id: '',
    visit_type: 'Wellness',
    status: 'scheduled',
    visit_date: new Date().toISOString().slice(0, 16),
    chief_complaint: '',
    visit_notes: '',
    veterinarian_id: '',
  });

  const [errors, setErrors] = useState({});

  // Populate form with existing visit data
  useEffect(() => {
    if (visit && !isNewVisit) {
      setFormData({
        patient_id: visit.patient_id || '',
        visit_type: visit.visit_type || 'Wellness',
        status: visit.status || 'scheduled',
        visit_date: visit.visit_date ? new Date(visit.visit_date).toISOString().slice(0, 16) : '',
        chief_complaint: visit.chief_complaint || '',
        visit_notes: visit.visit_notes || '',
        veterinarian_id: visit.veterinarian_id || '',
      });
    }
  }, [visit, isNewVisit]);

  // Fetch patients for dropdown
  const { data: patientsData } = useQuery({
    queryKey: ['patients', 'all'],
    queryFn: async () => {
      const response = await fetch('/api/patients?per_page=1000', {
        credentials: 'include',
      });
      if (!response.ok) throw new Error('Failed to fetch patients');
      return response.json();
    },
  });

  // Create visit mutation
  const createVisitMutation = useMutation({
    mutationFn: async (data) => {
      const response = await fetch('/api/visits', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to create visit');
      }

      return response.json();
    },
    onSuccess: (data) => {
      logger.info('Visit created successfully', { visitId: data.id });
      queryClient.invalidateQueries(['visits']);
      navigate(`/visits/${data.id}`);
    },
  });

  // Update visit mutation
  const updateVisitMutation = useMutation({
    mutationFn: async (data) => {
      const response = await fetch(`/api/visits/${visit.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to update visit');
      }

      return response.json();
    },
    onSuccess: () => {
      logger.info('Visit updated successfully', { visitId: visit.id });
      queryClient.invalidateQueries(['visit', visit.id.toString()]);
      queryClient.invalidateQueries(['visits']);
      setEditMode(false);
    },
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    // Clear error for this field
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: '' }));
    }
  };

  const validate = () => {
    const newErrors = {};

    if (!formData.patient_id) {
      newErrors.patient_id = 'Patient is required';
    }
    if (!formData.visit_type) {
      newErrors.visit_type = 'Visit type is required';
    }
    if (!formData.visit_date) {
      newErrors.visit_date = 'Visit date is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    if (!validate()) {
      return;
    }

    const submitData = {
      ...formData,
      patient_id: parseInt(formData.patient_id, 10),
      veterinarian_id: formData.veterinarian_id ? parseInt(formData.veterinarian_id, 10) : null,
    };

    if (isNewVisit) {
      logger.logAction('Create new visit', submitData);
      createVisitMutation.mutate(submitData);
    } else {
      logger.logAction('Update visit', { visitId: visit.id, ...submitData });
      updateVisitMutation.mutate(submitData);
    }
  };

  const handleCancel = () => {
    if (isNewVisit) {
      navigate(-1);
    } else {
      setEditMode(false);
      // Reset form to original visit data
      setFormData({
        patient_id: visit.patient_id || '',
        visit_type: visit.visit_type || 'Wellness',
        status: visit.status || 'scheduled',
        visit_date: visit.visit_date ? new Date(visit.visit_date).toISOString().slice(0, 16) : '',
        chief_complaint: visit.chief_complaint || '',
        visit_notes: visit.visit_notes || '',
        veterinarian_id: visit.veterinarian_id || '',
      });
      setErrors({});
    }
  };

  const patients = patientsData?.patients || [];

  // Display mode
  if (!editMode && !isNewVisit && visit) {
    return (
      <Paper sx={{ p: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h6">Visit Details</Typography>
          {visit.status !== 'completed' && visit.status !== 'cancelled' && (
            <Button startIcon={<EditIcon />} onClick={() => setEditMode(true)} variant="outlined">
              Edit
            </Button>
          )}
        </Box>

        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card variant="outlined">
              <CardHeader
                title="Visit Information"
                titleTypographyProps={{ variant: 'subtitle1' }}
              />
              <CardContent>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">
                      Patient
                    </Typography>
                    <Typography variant="body1">
                      {visit.patient_name || `Patient #${visit.patient_id}`}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">
                      Visit Date
                    </Typography>
                    <Typography variant="body1">
                      {new Date(visit.visit_date).toLocaleString()}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">
                      Visit Type
                    </Typography>
                    <Typography variant="body1">{visit.visit_type}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="text.secondary">
                      Status
                    </Typography>
                    <Typography variant="body1">{visit.status}</Typography>
                  </Grid>
                  <Grid item xs={12}>
                    <Typography variant="caption" color="text.secondary">
                      Veterinarian
                    </Typography>
                    <Typography variant="body1">
                      {visit.veterinarian_name || 'Not assigned'}
                    </Typography>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card variant="outlined">
              <CardHeader title="Clinical Notes" titleTypographyProps={{ variant: 'subtitle1' }} />
              <CardContent>
                <Box mb={2}>
                  <Typography variant="caption" color="text.secondary">
                    Chief Complaint
                  </Typography>
                  <Typography variant="body1" style={{ whiteSpace: 'pre-wrap' }}>
                    {visit.chief_complaint || 'None'}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    Visit Notes
                  </Typography>
                  <Typography variant="body1" style={{ whiteSpace: 'pre-wrap' }}>
                    {visit.visit_notes || 'None'}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {visit.completed_at && (
            <Grid item xs={12}>
              <Alert severity="success">
                Visit completed on {new Date(visit.completed_at).toLocaleString()}
              </Alert>
            </Grid>
          )}
        </Grid>
      </Paper>
    );
  }

  // Edit mode / New visit form
  return (
    <Paper sx={{ p: 3 }}>
      <Box mb={3}>
        <Typography variant="h6">{isNewVisit ? 'Create New Visit' : 'Edit Visit'}</Typography>
      </Box>

      <form onSubmit={handleSubmit}>
        <Grid container spacing={3}>
          {/* Patient Selection */}
          <Grid item xs={12} md={6}>
            <TextField
              select
              fullWidth
              required
              label="Patient"
              name="patient_id"
              value={formData.patient_id}
              onChange={handleChange}
              error={!!errors.patient_id}
              helperText={errors.patient_id}
              disabled={!isNewVisit}
            >
              <MenuItem value="">Select a patient...</MenuItem>
              {patients.map((patient) => (
                <MenuItem key={patient.id} value={patient.id}>
                  {patient.name} - {patient.owner_name}
                </MenuItem>
              ))}
            </TextField>
          </Grid>

          {/* Visit Date */}
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              required
              type="datetime-local"
              label="Visit Date"
              name="visit_date"
              value={formData.visit_date}
              onChange={handleChange}
              error={!!errors.visit_date}
              helperText={errors.visit_date}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>

          {/* Visit Type */}
          <Grid item xs={12} md={6}>
            <TextField
              select
              fullWidth
              required
              label="Visit Type"
              name="visit_type"
              value={formData.visit_type}
              onChange={handleChange}
              error={!!errors.visit_type}
              helperText={errors.visit_type}
            >
              {visitTypes.map((type) => (
                <MenuItem key={type} value={type}>
                  {type}
                </MenuItem>
              ))}
            </TextField>
          </Grid>

          {/* Status */}
          <Grid item xs={12} md={6}>
            <TextField
              select
              fullWidth
              label="Status"
              name="status"
              value={formData.status}
              onChange={handleChange}
            >
              {visitStatuses.map((status) => (
                <MenuItem key={status} value={status}>
                  {status}
                </MenuItem>
              ))}
            </TextField>
          </Grid>

          {/* Chief Complaint */}
          <Grid item xs={12}>
            <TextField
              fullWidth
              multiline
              rows={3}
              label="Chief Complaint"
              name="chief_complaint"
              value={formData.chief_complaint}
              onChange={handleChange}
              placeholder="Reason for visit..."
            />
          </Grid>

          {/* Visit Notes */}
          <Grid item xs={12}>
            <TextField
              fullWidth
              multiline
              rows={4}
              label="Visit Notes"
              name="visit_notes"
              value={formData.visit_notes}
              onChange={handleChange}
              placeholder="Additional notes about the visit..."
            />
          </Grid>

          {/* Error Display */}
          {(createVisitMutation.isError || updateVisitMutation.isError) && (
            <Grid item xs={12}>
              <Alert severity="error">
                {createVisitMutation.error?.message || updateVisitMutation.error?.message}
              </Alert>
            </Grid>
          )}

          {/* Action Buttons */}
          <Grid item xs={12}>
            <Box display="flex" gap={2}>
              <Button
                type="submit"
                variant="contained"
                startIcon={<SaveIcon />}
                disabled={createVisitMutation.isLoading || updateVisitMutation.isLoading}
              >
                {isNewVisit ? 'Create Visit' : 'Save Changes'}
              </Button>
              <Button
                variant="outlined"
                startIcon={<CancelIcon />}
                onClick={handleCancel}
                disabled={createVisitMutation.isLoading || updateVisitMutation.isLoading}
              >
                Cancel
              </Button>
            </Box>
          </Grid>
        </Grid>
      </form>
    </Paper>
  );
}

export default VisitOverview;
