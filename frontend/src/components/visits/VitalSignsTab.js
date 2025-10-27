import React, { useState, useEffect } from 'react';
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
  InputAdornment,
} from '@mui/material';
import { Save as SaveIcon, Edit as EditIcon } from '@mui/icons-material';
import logger from '../../utils/logger';

/**
 * Vital Signs Tab Component
 *
 * Records and displays vital signs for a visit
 */
function VitalSignsTab({ visitId }) {
  const queryClient = useQueryClient();
  const [editMode, setEditMode] = useState(false);
  const [formData, setFormData] = useState({
    temperature_c: '',
    weight_kg: '',
    heart_rate: '',
    respiratory_rate: '',
    blood_pressure_systolic: '',
    blood_pressure_diastolic: '',
    capillary_refill_time: '',
    mucous_membrane_color: '',
    body_condition_score: '',
    pain_score: '',
    notes: '',
  });

  // Fetch vital signs
  const {
    data: vitalSignsList,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['vitalSigns', visitId],
    queryFn: async () => {
      const response = await fetch(`/api/vital-signs?visit_id=${visitId}`, {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to fetch vital signs');
      }

      const data = await response.json();
      return data.vital_signs || [];
    },
  });

  const currentVitalSigns = vitalSignsList?.[0];

  useEffect(() => {
    if (currentVitalSigns) {
      setFormData({
        temperature_c: currentVitalSigns.temperature_c || '',
        weight_kg: currentVitalSigns.weight_kg || '',
        heart_rate: currentVitalSigns.heart_rate || '',
        respiratory_rate: currentVitalSigns.respiratory_rate || '',
        blood_pressure_systolic: currentVitalSigns.blood_pressure_systolic || '',
        blood_pressure_diastolic: currentVitalSigns.blood_pressure_diastolic || '',
        capillary_refill_time: currentVitalSigns.capillary_refill_time || '',
        mucous_membrane_color: currentVitalSigns.mucous_membrane_color || '',
        body_condition_score: currentVitalSigns.body_condition_score || '',
        pain_score: currentVitalSigns.pain_score || '',
        notes: currentVitalSigns.notes || '',
      });
    }
  }, [currentVitalSigns]);

  const createMutation = useMutation({
    mutationFn: async (data) => {
      const response = await fetch('/api/vital-signs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ ...data, visit_id: parseInt(visitId, 10) }),
      });

      if (!response.ok) {
        throw new Error('Failed to create vital signs');
      }

      return response.json();
    },
    onSuccess: () => {
      logger.info('Vital signs created', { visitId });
      queryClient.invalidateQueries(['vitalSigns', visitId]);
      setEditMode(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: async (data) => {
      const response = await fetch(`/api/vital-signs/${currentVitalSigns.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error('Failed to update vital signs');
      }

      return response.json();
    },
    onSuccess: () => {
      logger.info('Vital signs updated', { visitId });
      queryClient.invalidateQueries(['vitalSigns', visitId]);
      setEditMode(false);
    },
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    // Convert empty strings to null for numeric fields
    const submitData = { ...formData };
    const numericFields = [
      'temperature_c',
      'weight_kg',
      'heart_rate',
      'respiratory_rate',
      'blood_pressure_systolic',
      'blood_pressure_diastolic',
      'body_condition_score',
      'pain_score',
    ];

    numericFields.forEach((field) => {
      if (submitData[field] === '') {
        submitData[field] = null;
      }
    });

    if (currentVitalSigns) {
      updateMutation.mutate(submitData);
    } else {
      createMutation.mutate(submitData);
    }
  };

  const handleCancel = () => {
    setEditMode(false);
    if (currentVitalSigns) {
      setFormData({
        temperature_c: currentVitalSigns.temperature_c || '',
        weight_kg: currentVitalSigns.weight_kg || '',
        heart_rate: currentVitalSigns.heart_rate || '',
        respiratory_rate: currentVitalSigns.respiratory_rate || '',
        blood_pressure_systolic: currentVitalSigns.blood_pressure_systolic || '',
        blood_pressure_diastolic: currentVitalSigns.blood_pressure_diastolic || '',
        capillary_refill_time: currentVitalSigns.capillary_refill_time || '',
        mucous_membrane_color: currentVitalSigns.mucous_membrane_color || '',
        body_condition_score: currentVitalSigns.body_condition_score || '',
        pain_score: currentVitalSigns.pain_score || '',
        notes: currentVitalSigns.notes || '',
      });
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
        <Alert severity="error">Failed to load vital signs: {error.message}</Alert>
      </Box>
    );
  }

  // Display mode
  if (!editMode && currentVitalSigns) {
    return (
      <Paper sx={{ p: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h6">Vital Signs</Typography>
          <Button startIcon={<EditIcon />} onClick={() => setEditMode(true)} variant="outlined">
            Edit
          </Button>
        </Box>

        <Grid container spacing={3}>
          <Grid item xs={6} md={3}>
            <Typography variant="caption" color="text.secondary">
              Temperature
            </Typography>
            <Typography variant="body1">{currentVitalSigns.temperature_c || '-'} °C</Typography>
          </Grid>
          <Grid item xs={6} md={3}>
            <Typography variant="caption" color="text.secondary">
              Weight
            </Typography>
            <Typography variant="body1">{currentVitalSigns.weight_kg || '-'} kg</Typography>
          </Grid>
          <Grid item xs={6} md={3}>
            <Typography variant="caption" color="text.secondary">
              Heart Rate
            </Typography>
            <Typography variant="body1">{currentVitalSigns.heart_rate || '-'} bpm</Typography>
          </Grid>
          <Grid item xs={6} md={3}>
            <Typography variant="caption" color="text.secondary">
              Respiratory Rate
            </Typography>
            <Typography variant="body1">
              {currentVitalSigns.respiratory_rate || '-'} /min
            </Typography>
          </Grid>
          <Grid item xs={6} md={3}>
            <Typography variant="caption" color="text.secondary">
              Blood Pressure
            </Typography>
            <Typography variant="body1">
              {currentVitalSigns.blood_pressure_systolic || '-'}/
              {currentVitalSigns.blood_pressure_diastolic || '-'} mmHg
            </Typography>
          </Grid>
          <Grid item xs={6} md={3}>
            <Typography variant="caption" color="text.secondary">
              Body Condition Score
            </Typography>
            <Typography variant="body1">
              {currentVitalSigns.body_condition_score || '-'}/9
            </Typography>
          </Grid>
          <Grid item xs={6} md={3}>
            <Typography variant="caption" color="text.secondary">
              Pain Score
            </Typography>
            <Typography variant="body1">{currentVitalSigns.pain_score || '-'}/10</Typography>
          </Grid>
          <Grid item xs={6} md={3}>
            <Typography variant="caption" color="text.secondary">
              Capillary Refill Time
            </Typography>
            <Typography variant="body1">
              {currentVitalSigns.capillary_refill_time || '-'}
            </Typography>
          </Grid>
          <Grid item xs={12} md={6}>
            <Typography variant="caption" color="text.secondary">
              Mucous Membrane Color
            </Typography>
            <Typography variant="body1">
              {currentVitalSigns.mucous_membrane_color || '-'}
            </Typography>
          </Grid>
          {currentVitalSigns.notes && (
            <Grid item xs={12}>
              <Typography variant="caption" color="text.secondary">
                Notes
              </Typography>
              <Typography variant="body2" style={{ whiteSpace: 'pre-wrap' }}>
                {currentVitalSigns.notes}
              </Typography>
            </Grid>
          )}
          <Grid item xs={12}>
            <Typography variant="caption" color="text.secondary">
              Recorded by: {currentVitalSigns.recorded_by_name} •{' '}
              {new Date(currentVitalSigns.recorded_at).toLocaleString()}
            </Typography>
          </Grid>
        </Grid>
      </Paper>
    );
  }

  // Edit/Create mode
  return (
    <Paper sx={{ p: 3 }}>
      <Box mb={3}>
        <Typography variant="h6">
          {currentVitalSigns ? 'Edit Vital Signs' : 'Record Vital Signs'}
        </Typography>
      </Box>

      <form onSubmit={handleSubmit}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={3}>
            <TextField
              fullWidth
              type="number"
              inputProps={{ step: '0.1' }}
              label="Temperature"
              name="temperature_c"
              value={formData.temperature_c}
              onChange={handleChange}
              InputProps={{ endAdornment: <InputAdornment position="end">°C</InputAdornment> }}
            />
          </Grid>
          <Grid item xs={12} md={3}>
            <TextField
              fullWidth
              type="number"
              inputProps={{ step: '0.01' }}
              label="Weight"
              name="weight_kg"
              value={formData.weight_kg}
              onChange={handleChange}
              InputProps={{ endAdornment: <InputAdornment position="end">kg</InputAdornment> }}
            />
          </Grid>
          <Grid item xs={12} md={3}>
            <TextField
              fullWidth
              type="number"
              label="Heart Rate"
              name="heart_rate"
              value={formData.heart_rate}
              onChange={handleChange}
              InputProps={{ endAdornment: <InputAdornment position="end">bpm</InputAdornment> }}
            />
          </Grid>
          <Grid item xs={12} md={3}>
            <TextField
              fullWidth
              type="number"
              label="Respiratory Rate"
              name="respiratory_rate"
              value={formData.respiratory_rate}
              onChange={handleChange}
              InputProps={{ endAdornment: <InputAdornment position="end">/min</InputAdornment> }}
            />
          </Grid>
          <Grid item xs={12} md={3}>
            <TextField
              fullWidth
              type="number"
              label="BP Systolic"
              name="blood_pressure_systolic"
              value={formData.blood_pressure_systolic}
              onChange={handleChange}
              InputProps={{ endAdornment: <InputAdornment position="end">mmHg</InputAdornment> }}
            />
          </Grid>
          <Grid item xs={12} md={3}>
            <TextField
              fullWidth
              type="number"
              label="BP Diastolic"
              name="blood_pressure_diastolic"
              value={formData.blood_pressure_diastolic}
              onChange={handleChange}
              InputProps={{ endAdornment: <InputAdornment position="end">mmHg</InputAdornment> }}
            />
          </Grid>
          <Grid item xs={12} md={3}>
            <TextField
              fullWidth
              type="number"
              inputProps={{ min: 1, max: 9 }}
              label="Body Condition Score"
              name="body_condition_score"
              value={formData.body_condition_score}
              onChange={handleChange}
              helperText="1-9 scale"
            />
          </Grid>
          <Grid item xs={12} md={3}>
            <TextField
              fullWidth
              type="number"
              inputProps={{ min: 0, max: 10 }}
              label="Pain Score"
              name="pain_score"
              value={formData.pain_score}
              onChange={handleChange}
              helperText="0-10 scale"
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Capillary Refill Time"
              name="capillary_refill_time"
              value={formData.capillary_refill_time}
              onChange={handleChange}
              placeholder="e.g., <2 seconds"
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Mucous Membrane Color"
              name="mucous_membrane_color"
              value={formData.mucous_membrane_color}
              onChange={handleChange}
              placeholder="e.g., Pink, Pale, Cyanotic"
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
              placeholder="Additional observations..."
            />
          </Grid>

          {(createMutation.isError || updateMutation.isError) && (
            <Grid item xs={12}>
              <Alert severity="error">
                {createMutation.error?.message || updateMutation.error?.message}
              </Alert>
            </Grid>
          )}

          <Grid item xs={12}>
            <Box display="flex" gap={2}>
              <Button
                type="submit"
                variant="contained"
                startIcon={<SaveIcon />}
                disabled={createMutation.isLoading || updateMutation.isLoading}
              >
                {currentVitalSigns ? 'Update' : 'Record'} Vital Signs
              </Button>
              <Button
                variant="outlined"
                onClick={handleCancel}
                disabled={createMutation.isLoading || updateMutation.isLoading}
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

export default VitalSignsTab;
