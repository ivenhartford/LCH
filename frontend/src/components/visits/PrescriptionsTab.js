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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  IconButton,
  Tooltip,
  Autocomplete,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Calculate as CalculateIcon,
} from '@mui/icons-material';
import logger from '../../utils/logger';

/**
 * Prescriptions Tab Component
 *
 * Manages prescriptions for a specific visit.
 * Features:
 * - List all prescriptions for the patient
 * - Create new prescriptions
 * - Edit existing prescriptions
 * - Dosage calculator by weight
 * - Track refills
 */
function PrescriptionsTab({ visitId, patientId }) {
  const queryClient = useQueryClient();

  // State
  const [dialogOpen, setDialogOpen] = useState(false);
  const [calculatorOpen, setCalculatorOpen] = useState(false);
  const [editingPrescription, setEditingPrescription] = useState(null);
  const [selectedMedication, setSelectedMedication] = useState(null);
  const [patientWeight, setPatientWeight] = useState('');
  const [formData, setFormData] = useState({
    medication_id: '',
    dosage: '',
    dosage_form: '',
    frequency: '',
    route: '',
    duration_days: '',
    quantity: '',
    refills_allowed: 0,
    instructions: '',
    indication: '',
    start_date: new Date().toISOString().split('T')[0],
  });

  useEffect(() => {
    logger.logLifecycle('PrescriptionsTab', 'mounted', { visitId, patientId });
  }, [visitId, patientId]);

  // Fetch prescriptions for patient
  const {
    data: prescriptionsData,
    isLoading: prescriptionsLoading,
    isError: prescriptionsError,
    error: prescriptionsErrorMsg,
  } = useQuery({
    queryKey: ['prescriptions', patientId],
    queryFn: async () => {
      const response = await fetch(`/api/prescriptions?patient_id=${patientId}`, {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to fetch prescriptions');
      }

      return response.json();
    },
    enabled: !!patientId,
  });

  // Fetch medications for selection
  const { data: medicationsData, isLoading: medicationsLoading } = useQuery({
    queryKey: ['medications', 'active'],
    queryFn: async () => {
      const response = await fetch('/api/medications?is_active=true', {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to fetch medications');
      }

      return response.json();
    },
  });

  // Fetch patient details for weight
  const { data: patientData } = useQuery({
    queryKey: ['patient', patientId],
    queryFn: async () => {
      const response = await fetch(`/api/patients/${patientId}`, {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to fetch patient');
      }

      return response.json();
    },
    enabled: !!patientId,
  });

  // Create/Update mutation
  const saveMutation = useMutation({
    mutationFn: async (data) => {
      const url = editingPrescription
        ? `/api/prescriptions/${editingPrescription.id}`
        : '/api/prescriptions';
      const method = editingPrescription ? 'PUT' : 'POST';

      const payload = {
        ...data,
        patient_id: patientId,
        visit_id: visitId,
      };

      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to save prescription');
      }

      return response.json();
    },
    onSuccess: () => {
      logger.info(editingPrescription ? 'Prescription updated' : 'Prescription created');
      queryClient.invalidateQueries(['prescriptions', patientId]);
      handleCloseDialog();
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: async (prescriptionId) => {
      const response = await fetch(`/api/prescriptions/${prescriptionId}`, {
        method: 'DELETE',
        credentials: 'include',
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to delete prescription');
      }

      return response.json();
    },
    onSuccess: () => {
      logger.info('Prescription deleted');
      queryClient.invalidateQueries(['prescriptions', patientId]);
    },
  });

  const handleOpenDialog = (prescription = null) => {
    if (prescription) {
      setEditingPrescription(prescription);
      setFormData({
        medication_id: prescription.medication_id || '',
        dosage: prescription.dosage || '',
        dosage_form: prescription.dosage_form || '',
        frequency: prescription.frequency || '',
        route: prescription.route || '',
        duration_days: prescription.duration_days || '',
        quantity: prescription.quantity || '',
        refills_allowed: prescription.refills_allowed || 0,
        instructions: prescription.instructions || '',
        indication: prescription.indication || '',
        start_date: prescription.start_date || new Date().toISOString().split('T')[0],
      });
      // Find selected medication
      const med = medicationsData?.medications?.find((m) => m.id === prescription.medication_id);
      setSelectedMedication(med || null);
    } else {
      setEditingPrescription(null);
      setFormData({
        medication_id: '',
        dosage: '',
        dosage_form: '',
        frequency: '',
        route: '',
        duration_days: '',
        quantity: '',
        refills_allowed: 0,
        instructions: '',
        indication: '',
        start_date: new Date().toISOString().split('T')[0],
      });
      setSelectedMedication(null);
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingPrescription(null);
    setSelectedMedication(null);
  };

  const handleMedicationChange = (event, value) => {
    setSelectedMedication(value);
    if (value) {
      setFormData({
        ...formData,
        medication_id: value.id,
        // Pre-fill from medication database
        dosage_form: value.available_forms?.split(',')[0]?.trim() || '',
        frequency: value.dosing_frequency || '',
        route: value.route_of_administration || '',
      });
    }
  };

  const handleOpenCalculator = () => {
    setPatientWeight(patientData?.weight_kg || '');
    setCalculatorOpen(true);
  };

  const handleCalculateDosage = () => {
    if (selectedMedication && patientWeight) {
      // Extract dose from typical_dose_cats (e.g., "5-10 mg/kg BID")
      const doseText = selectedMedication.typical_dose_cats || '';
      const match = doseText.match(/(\d+(?:\.\d+)?)-?(\d+(?:\.\d+)?)?/);

      if (match) {
        const minDose = parseFloat(match[1]);
        const maxDose = match[2] ? parseFloat(match[2]) : minDose;
        const avgDose = (minDose + maxDose) / 2;
        const calculatedDose = avgDose * parseFloat(patientWeight);

        setFormData({
          ...formData,
          dosage: `${calculatedDose.toFixed(1)}mg`,
        });

        logger.info('Dosage calculated', {
          medication: selectedMedication.drug_name,
          weight: patientWeight,
          dose: calculatedDose,
        });
      }
    }
    setCalculatorOpen(false);
  };

  const handleSubmit = () => {
    logger.logAction(editingPrescription ? 'Update prescription' : 'Create prescription', formData);
    saveMutation.mutate(formData);
  };

  const handleDelete = (prescriptionId, medicationName) => {
    if (window.confirm(`Are you sure you want to delete prescription for ${medicationName}?`)) {
      logger.logAction('Delete prescription', { prescriptionId, medicationName });
      deleteMutation.mutate(prescriptionId);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'completed':
        return 'default';
      case 'discontinued':
        return 'warning';
      case 'expired':
        return 'error';
      default:
        return 'default';
    }
  };

  if (prescriptionsLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  if (prescriptionsError) {
    return (
      <Alert severity="error">Failed to load prescriptions: {prescriptionsErrorMsg.message}</Alert>
    );
  }

  const prescriptions = prescriptionsData?.prescriptions || [];
  const medications = medicationsData?.medications || [];

  return (
    <Box>
      {/* Header */}
      <Box mb={2} display="flex" justifyContent="space-between" alignItems="center">
        <Typography variant="h6">Prescriptions</Typography>
        <Button
          variant="contained"
          size="small"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
        >
          New Prescription
        </Button>
      </Box>

      {/* Prescriptions List */}
      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Medication</TableCell>
                <TableCell>Dosage</TableCell>
                <TableCell>Frequency</TableCell>
                <TableCell>Quantity</TableCell>
                <TableCell>Refills</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Prescribed Date</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {prescriptions.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} align="center">
                    <Typography variant="body2" color="text.secondary" py={3}>
                      No prescriptions found.
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                prescriptions.map((prescription) => (
                  <TableRow key={prescription.id} hover>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        {prescription.medication_name}
                      </Typography>
                      {prescription.dosage_form && (
                        <Typography variant="caption" color="text.secondary">
                          {prescription.dosage_form}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>{prescription.dosage}</TableCell>
                    <TableCell>{prescription.frequency}</TableCell>
                    <TableCell>{prescription.quantity}</TableCell>
                    <TableCell>
                      {prescription.refills_remaining} / {prescription.refills_allowed}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={prescription.status}
                        color={getStatusColor(prescription.status)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>{new Date(prescription.start_date).toLocaleDateString()}</TableCell>
                    <TableCell align="right">
                      <Tooltip title="Edit">
                        <IconButton
                          size="small"
                          onClick={() => handleOpenDialog(prescription)}
                          color="primary"
                        >
                          <EditIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete">
                        <IconButton
                          size="small"
                          onClick={() =>
                            handleDelete(prescription.id, prescription.medication_name)
                          }
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
        </TableContainer>
      </Paper>

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>{editingPrescription ? 'Edit Prescription' : 'New Prescription'}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 0.5 }}>
            <Grid item xs={12}>
              <Autocomplete
                value={selectedMedication}
                onChange={handleMedicationChange}
                options={medications}
                getOptionLabel={(option) => option.drug_name}
                loading={medicationsLoading}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    required
                    label="Medication"
                    placeholder="Search medications..."
                  />
                )}
                renderOption={(props, option) => (
                  <Box component="li" {...props}>
                    <Box>
                      <Typography variant="body2">{option.drug_name}</Typography>
                      {option.brand_names && (
                        <Typography variant="caption" color="text.secondary">
                          {option.brand_names}
                        </Typography>
                      )}
                    </Box>
                  </Box>
                )}
              />
            </Grid>

            {selectedMedication && (
              <Grid item xs={12}>
                <Paper sx={{ p: 1, bgcolor: 'background.default' }}>
                  <Typography variant="caption" color="text.secondary">
                    Typical Dose: {selectedMedication.typical_dose_cats || 'Not specified'}
                  </Typography>
                  <br />
                  <Typography variant="caption" color="text.secondary">
                    Forms: {selectedMedication.available_forms || 'Not specified'}
                  </Typography>
                </Paper>
              </Grid>
            )}

            <Grid item xs={12} sm={8}>
              <TextField
                fullWidth
                required
                label="Dosage"
                value={formData.dosage}
                onChange={(e) => setFormData({ ...formData, dosage: e.target.value })}
                placeholder="e.g., 50mg, 2.5ml"
              />
            </Grid>

            <Grid item xs={12} sm={4}>
              <Button
                fullWidth
                variant="outlined"
                startIcon={<CalculateIcon />}
                onClick={handleOpenCalculator}
                disabled={!selectedMedication}
                sx={{ height: '56px' }}
              >
                Calculate
              </Button>
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Dosage Form"
                value={formData.dosage_form}
                onChange={(e) => setFormData({ ...formData, dosage_form: e.target.value })}
                placeholder="e.g., Tablet, Capsule, Liquid"
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                required
                label="Frequency"
                value={formData.frequency}
                onChange={(e) => setFormData({ ...formData, frequency: e.target.value })}
                placeholder="e.g., BID, TID, Once daily"
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Route"
                value={formData.route}
                onChange={(e) => setFormData({ ...formData, route: e.target.value })}
                placeholder="e.g., Oral, SC, IM"
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                type="number"
                label="Duration (days)"
                value={formData.duration_days}
                onChange={(e) => setFormData({ ...formData, duration_days: e.target.value })}
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                required
                type="number"
                label="Quantity"
                value={formData.quantity}
                onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
              />
            </Grid>

            <Grid item xs={12} sm={3}>
              <TextField
                fullWidth
                type="number"
                label="Refills Allowed"
                value={formData.refills_allowed}
                onChange={(e) =>
                  setFormData({ ...formData, refills_allowed: parseInt(e.target.value) || 0 })
                }
              />
            </Grid>

            <Grid item xs={12} sm={3}>
              <TextField
                fullWidth
                type="date"
                label="Start Date"
                value={formData.start_date}
                onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={2}
                label="Instructions"
                value={formData.instructions}
                onChange={(e) => setFormData({ ...formData, instructions: e.target.value })}
                placeholder="Give with food, administer in the morning, etc."
              />
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Indication"
                value={formData.indication}
                onChange={(e) => setFormData({ ...formData, indication: e.target.value })}
                placeholder="Reason for prescription"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={
              saveMutation.isLoading ||
              !formData.medication_id ||
              !formData.dosage ||
              !formData.frequency ||
              !formData.quantity
            }
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

      {/* Dosage Calculator Dialog */}
      <Dialog
        open={calculatorOpen}
        onClose={() => setCalculatorOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Calculate Dosage by Weight</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" gutterBottom>
              Medication: <strong>{selectedMedication?.drug_name}</strong>
            </Typography>
            <Typography variant="body2" gutterBottom>
              Typical Dose: {selectedMedication?.typical_dose_cats || 'Not specified'}
            </Typography>
            <TextField
              fullWidth
              type="number"
              label="Patient Weight (kg)"
              value={patientWeight}
              onChange={(e) => setPatientWeight(e.target.value)}
              sx={{ mt: 2 }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCalculatorOpen(false)}>Cancel</Button>
          <Button
            onClick={handleCalculateDosage}
            variant="contained"
            disabled={!patientWeight || !selectedMedication}
          >
            Calculate
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default PrescriptionsTab;
