import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useParams, useNavigate } from 'react-router-dom';
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
  Card,
  CardContent,
  useMediaQuery,
  useTheme,
  Divider,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  Checkbox,
  FormControlLabel,
  Stepper,
  Step,
  StepLabel,
  StepContent,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  ArrowBack as BackIcon,
  CheckCircle as CompleteIcon,
  Cancel as CancelIcon,
  PlayArrow as StartIcon,
  LibraryBooks as LibraryIcon,
  Assessment as ProgressIcon,
  AttachMoney as CostIcon,
  Event as DateIcon,
} from '@mui/icons-material';
import logger from '../utils/logger';
import ConfirmDialog from './common/ConfirmDialog';
import EmptyState from './common/EmptyState';
import { useNotification } from '../contexts/NotificationContext';

/**
 * Treatment Plan Builder Component
 *
 * Manages patient-specific treatment plans.
 * Features:
 * - View all treatment plans for a patient
 * - Apply protocol templates to create new plans
 * - Create custom treatment plans from scratch
 * - Update plan status (draft → active → completed/cancelled)
 * - Update individual step status and actual costs
 * - Track progress and cost comparison (estimated vs actual)
 * - View detailed step information
 */
function TreatmentPlanBuilder() {
  const { patientId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { showNotification } = useNotification();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  // State
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [applyProtocolDialog, setApplyProtocolDialog] = useState(false);
  const [selectedProtocol, setSelectedProtocol] = useState('');
  const [planStartDate, setPlanStartDate] = useState(new Date().toISOString().split('T')[0]);
  const [updateStepDialog, setUpdateStepDialog] = useState({ open: false, step: null });
  const [deleteDialog, setDeleteDialog] = useState({ open: false, planId: null, planTitle: '' });

  useEffect(() => {
    logger.logLifecycle('TreatmentPlanBuilder', 'mounted', { patientId });
    return () => {
      logger.logLifecycle('TreatmentPlanBuilder', 'unmounted');
    };
  }, [patientId]);

  // Fetch patient info
  const { data: patientData } = useQuery({
    queryKey: ['patient', patientId],
    queryFn: async () => {
      const response = await fetch(`/api/patients/${patientId}`, {
        credentials: 'include',
      });
      if (!response.ok) throw new Error('Failed to fetch patient');
      return response.json();
    },
    enabled: !!patientId,
  });

  // Fetch treatment plans for patient
  const {
    data: plansData,
    isLoading: plansLoading,
    isError: plansError,
    error: plansErrorMsg,
  } = useQuery({
    queryKey: ['treatment-plans', patientId, statusFilter, searchTerm],
    queryFn: async () => {
      const startTime = performance.now();

      const params = new URLSearchParams();
      if (patientId) params.append('patient_id', patientId);
      if (statusFilter) params.append('status', statusFilter);
      if (searchTerm) params.append('search', searchTerm);

      logger.logAction('Fetching treatment plans', { patientId, statusFilter, searchTerm });

      const response = await fetch(`/api/treatment-plans?${params}`, {
        credentials: 'include',
      });

      const duration = performance.now() - startTime;

      if (!response.ok) {
        logger.logAPICall('GET', '/api/treatment-plans', response.status, duration, 'Fetch failed');
        throw new Error(`Failed to fetch treatment plans: ${response.status}`);
      }

      const data = await response.json();
      logger.logAPICall('GET', '/api/treatment-plans', response.status, duration);
      logger.info('Treatment plans fetched', { count: data.treatment_plans?.length || 0 });

      return data;
    },
    staleTime: 10000,
    retry: 2,
  });

  // Fetch protocols for dropdown
  const { data: protocolsData } = useQuery({
    queryKey: ['protocols', 'true'], // Only active protocols
    queryFn: async () => {
      const response = await fetch('/api/protocols?is_active=true', {
        credentials: 'include',
      });
      if (!response.ok) throw new Error('Failed to fetch protocols');
      return response.json();
    },
  });

  // Apply protocol to patient
  const applyProtocolMutation = useMutation({
    mutationFn: async (data) => {
      const response = await fetch(`/api/protocols/${data.protocol_id}/apply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          patient_id: patientId,
          start_date: data.start_date,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to apply protocol');
      }

      return response.json();
    },
    onSuccess: () => {
      logger.info('Protocol applied successfully');
      queryClient.invalidateQueries(['treatment-plans']);
      setApplyProtocolDialog(false);
      setSelectedProtocol('');
      showNotification('Protocol applied successfully', 'success');
    },
    onError: (error) => {
      showNotification(error.message || 'Failed to apply protocol', 'error');
    },
  });

  // Update plan status
  const updatePlanStatusMutation = useMutation({
    mutationFn: async ({ planId, status }) => {
      const response = await fetch(`/api/treatment-plans/${planId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ status }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to update plan status');
      }

      return response.json();
    },
    onSuccess: () => {
      logger.info('Plan status updated');
      queryClient.invalidateQueries(['treatment-plans']);
      showNotification('Plan status updated successfully', 'success');
    },
    onError: (error) => {
      showNotification(error.message || 'Failed to update plan status', 'error');
    },
  });

  // Update step
  const updateStepMutation = useMutation({
    mutationFn: async ({ planId, stepId, data }) => {
      const response = await fetch(`/api/treatment-plans/${planId}/steps/${stepId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to update step');
      }

      return response.json();
    },
    onSuccess: () => {
      logger.info('Step updated');
      queryClient.invalidateQueries(['treatment-plans']);
      setUpdateStepDialog({ open: false, step: null });
      showNotification('Step updated successfully', 'success');
    },
    onError: (error) => {
      showNotification(error.message || 'Failed to update step', 'error');
    },
  });

  // Delete plan
  const deletePlanMutation = useMutation({
    mutationFn: async (planId) => {
      const response = await fetch(`/api/treatment-plans/${planId}`, {
        method: 'DELETE',
        credentials: 'include',
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to delete plan');
      }

      return response.json();
    },
    onSuccess: () => {
      logger.info('Plan deleted');
      queryClient.invalidateQueries(['treatment-plans']);
      setDeleteDialog({ open: false, planId: null, planTitle: '' });
      setSelectedPlan(null);
      showNotification('Treatment plan deleted successfully', 'success');
    },
    onError: (error) => {
      showNotification(error.message || 'Failed to delete plan', 'error');
    },
  });

  const handleApplyProtocol = () => {
    if (!selectedProtocol) {
      showNotification('Please select a protocol', 'error');
      return;
    }

    applyProtocolMutation.mutate({
      protocol_id: selectedProtocol,
      start_date: planStartDate,
    });
  };

  const handleUpdatePlanStatus = (planId, newStatus) => {
    updatePlanStatusMutation.mutate({ planId, status: newStatus });
  };

  const handleOpenStepUpdateDialog = (step) => {
    setUpdateStepDialog({ open: true, step: { ...step } });
  };

  const handleUpdateStep = () => {
    const { step } = updateStepDialog;
    if (!step) return;

    updateStepMutation.mutate({
      planId: selectedPlan.id,
      stepId: step.id,
      data: {
        status: step.status,
        notes: step.notes,
        actual_cost: step.actual_cost ? parseFloat(step.actual_cost) : null,
      },
    });
  };

  const handleDeletePlan = (plan) => {
    setDeleteDialog({ open: true, planId: plan.id, planTitle: plan.title });
  };

  const handleDeleteConfirm = () => {
    deletePlanMutation.mutate(deleteDialog.planId);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'draft':
        return 'default';
      case 'active':
        return 'primary';
      case 'completed':
        return 'success';
      case 'cancelled':
        return 'error';
      default:
        return 'default';
    }
  };

  const patient = patientData?.patient;
  const plans = plansData?.treatment_plans || [];
  const protocols = protocolsData?.protocols || [];

  if (plansLoading) {
    return (
      <Box sx={{ p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (plansError) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          Error loading treatment plans: {plansErrorMsg?.message || 'Unknown error'}
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Button
          startIcon={<BackIcon />}
          onClick={() => navigate(patientId ? `/patients/${patientId}` : '/patients')}
          sx={{ mb: 2 }}
        >
          Back to Patient
        </Button>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h4">
            Treatment Plans{patient && ` - ${patient.name}`}
          </Typography>
          <Button
            variant="contained"
            color="primary"
            startIcon={<LibraryIcon />}
            onClick={() => setApplyProtocolDialog(true)}
          >
            Apply Protocol
          </Button>
        </Box>
      </Box>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Search Plans"
              variant="outlined"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                value={statusFilter}
                label="Status"
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="draft">Draft</MenuItem>
                <MenuItem value="active">Active</MenuItem>
                <MenuItem value="completed">Completed</MenuItem>
                <MenuItem value="cancelled">Cancelled</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>

      {/* Treatment Plans List */}
      {plans.length === 0 ? (
        <EmptyState
          icon={ProgressIcon}
          message="No treatment plans found"
          submessage="Apply a protocol or create a custom plan to get started"
          actionLabel="Apply Protocol"
          onAction={() => setApplyProtocolDialog(true)}
        />
      ) : (
        <Grid container spacing={3}>
          {/* Plans List */}
          <Grid item xs={12} md={selectedPlan ? 6 : 12}>
            <Grid container spacing={2}>
              {plans.map((plan) => (
                <Grid item xs={12} key={plan.id}>
                  <Card
                    sx={{
                      cursor: 'pointer',
                      border: selectedPlan?.id === plan.id ? 2 : 0,
                      borderColor: 'primary.main',
                    }}
                    onClick={() => setSelectedPlan(plan)}
                  >
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 2 }}>
                        <Typography variant="h6">{plan.title}</Typography>
                        <Chip
                          size="small"
                          label={plan.status}
                          color={getStatusColor(plan.status)}
                        />
                      </Box>

                      {plan.description && (
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                          {plan.description}
                        </Typography>
                      )}

                      {/* Progress Bar */}
                      <Box sx={{ mb: 2 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body2">Progress</Typography>
                          <Typography variant="body2">{plan.progress_percentage || 0}%</Typography>
                        </Box>
                        <LinearProgress
                          variant="determinate"
                          value={plan.progress_percentage || 0}
                          color={plan.progress_percentage === 100 ? 'success' : 'primary'}
                        />
                      </Box>

                      {/* Cost Summary */}
                      <Grid container spacing={1}>
                        <Grid item xs={6}>
                          <Typography variant="caption" color="text.secondary">
                            Est. Cost
                          </Typography>
                          <Typography variant="body2">
                            ${parseFloat(plan.total_estimated_cost || 0).toFixed(2)}
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="caption" color="text.secondary">
                            Actual Cost
                          </Typography>
                          <Typography variant="body2">
                            ${parseFloat(plan.total_actual_cost || 0).toFixed(2)}
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="caption" color="text.secondary">
                            Start Date
                          </Typography>
                          <Typography variant="body2">
                            {plan.start_date ? new Date(plan.start_date).toLocaleDateString() : '—'}
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="caption" color="text.secondary">
                            End Date
                          </Typography>
                          <Typography variant="body2">
                            {plan.end_date ? new Date(plan.end_date).toLocaleDateString() : '—'}
                          </Typography>
                        </Grid>
                      </Grid>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Grid>

          {/* Plan Details */}
          {selectedPlan && (
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 3 }}>
                  <Typography variant="h5">{selectedPlan.title}</Typography>
                  <Chip label={selectedPlan.status} color={getStatusColor(selectedPlan.status)} />
                </Box>

                {selectedPlan.description && (
                  <Typography variant="body1" sx={{ mb: 3 }}>
                    {selectedPlan.description}
                  </Typography>
                )}

                {/* Status Actions */}
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Plan Actions
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {selectedPlan.status === 'draft' && (
                      <Button
                        size="small"
                        variant="outlined"
                        startIcon={<StartIcon />}
                        onClick={() => handleUpdatePlanStatus(selectedPlan.id, 'active')}
                      >
                        Start Plan
                      </Button>
                    )}
                    {selectedPlan.status === 'active' && (
                      <>
                        <Button
                          size="small"
                          variant="outlined"
                          color="success"
                          startIcon={<CompleteIcon />}
                          onClick={() => handleUpdatePlanStatus(selectedPlan.id, 'completed')}
                        >
                          Mark Complete
                        </Button>
                        <Button
                          size="small"
                          variant="outlined"
                          color="error"
                          startIcon={<CancelIcon />}
                          onClick={() => handleUpdatePlanStatus(selectedPlan.id, 'cancelled')}
                        >
                          Cancel Plan
                        </Button>
                      </>
                    )}
                    <Button
                      size="small"
                      variant="outlined"
                      color="error"
                      startIcon={<DeleteIcon />}
                      onClick={() => handleDeletePlan(selectedPlan)}
                    >
                      Delete
                    </Button>
                  </Box>
                </Box>

                <Divider sx={{ my: 3 }} />

                {/* Plan Steps */}
                <Typography variant="h6" gutterBottom>
                  Treatment Steps
                </Typography>
                {selectedPlan.steps && selectedPlan.steps.length > 0 ? (
                  <Stepper orientation="vertical">
                    {selectedPlan.steps.map((step) => (
                      <Step key={step.id} active expanded>
                        <StepLabel
                          icon={step.status === 'completed' ? <CompleteIcon color="success" /> : step.step_number}
                        >
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <Typography>{step.title}</Typography>
                            <Chip
                              size="small"
                              label={step.status}
                              color={step.status === 'completed' ? 'success' : 'default'}
                            />
                          </Box>
                        </StepLabel>
                        <StepContent>
                          {step.description && (
                            <Typography variant="body2" sx={{ mb: 1 }}>
                              {step.description}
                            </Typography>
                          )}
                          <Grid container spacing={1} sx={{ mb: 1 }}>
                            <Grid item xs={6}>
                              <Typography variant="caption" color="text.secondary">
                                Scheduled
                              </Typography>
                              <Typography variant="body2">
                                {step.scheduled_date ? new Date(step.scheduled_date).toLocaleDateString() : '—'}
                              </Typography>
                            </Grid>
                            <Grid item xs={6}>
                              <Typography variant="caption" color="text.secondary">
                                Completed
                              </Typography>
                              <Typography variant="body2">
                                {step.completed_date ? new Date(step.completed_date).toLocaleDateString() : '—'}
                              </Typography>
                            </Grid>
                            <Grid item xs={6}>
                              <Typography variant="caption" color="text.secondary">
                                Est. Cost
                              </Typography>
                              <Typography variant="body2">
                                ${parseFloat(step.estimated_cost || 0).toFixed(2)}
                              </Typography>
                            </Grid>
                            <Grid item xs={6}>
                              <Typography variant="caption" color="text.secondary">
                                Actual Cost
                              </Typography>
                              <Typography variant="body2">
                                ${step.actual_cost ? parseFloat(step.actual_cost).toFixed(2) : '—'}
                              </Typography>
                            </Grid>
                          </Grid>
                          {step.notes && (
                            <Alert severity="info" sx={{ mb: 1 }}>
                              {step.notes}
                            </Alert>
                          )}
                          <Button
                            size="small"
                            startIcon={<EditIcon />}
                            onClick={() => handleOpenStepUpdateDialog(step)}
                          >
                            Update Step
                          </Button>
                        </StepContent>
                      </Step>
                    ))}
                  </Stepper>
                ) : (
                  <Alert severity="info">No steps defined for this plan</Alert>
                )}
              </Paper>
            </Grid>
          )}
        </Grid>
      )}

      {/* Apply Protocol Dialog */}
      <Dialog
        open={applyProtocolDialog}
        onClose={() => setApplyProtocolDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Apply Protocol to Patient</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Select Protocol</InputLabel>
              <Select
                value={selectedProtocol}
                label="Select Protocol"
                onChange={(e) => setSelectedProtocol(e.target.value)}
              >
                {protocols.map((protocol) => (
                  <MenuItem key={protocol.id} value={protocol.id}>
                    {protocol.name}
                    {protocol.estimated_cost && ` - $${parseFloat(protocol.estimated_cost).toFixed(2)}`}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              fullWidth
              type="date"
              label="Plan Start Date"
              value={planStartDate}
              onChange={(e) => setPlanStartDate(e.target.value)}
              InputLabelProps={{ shrink: true }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setApplyProtocolDialog(false)}>Cancel</Button>
          <Button
            onClick={handleApplyProtocol}
            variant="contained"
            disabled={applyProtocolMutation.isLoading || !selectedProtocol}
          >
            {applyProtocolMutation.isLoading ? <CircularProgress size={24} /> : 'Apply'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Update Step Dialog */}
      <Dialog
        open={updateStepDialog.open}
        onClose={() => setUpdateStepDialog({ open: false, step: null })}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Update Treatment Step</DialogTitle>
        <DialogContent>
          {updateStepDialog.step && (
            <Box sx={{ pt: 2 }}>
              <Typography variant="h6" gutterBottom>
                {updateStepDialog.step.title}
              </Typography>
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Status</InputLabel>
                <Select
                  value={updateStepDialog.step.status}
                  label="Status"
                  onChange={(e) =>
                    setUpdateStepDialog((prev) => ({
                      ...prev,
                      step: { ...prev.step, status: e.target.value },
                    }))
                  }
                >
                  <MenuItem value="pending">Pending</MenuItem>
                  <MenuItem value="in_progress">In Progress</MenuItem>
                  <MenuItem value="completed">Completed</MenuItem>
                  <MenuItem value="skipped">Skipped</MenuItem>
                </Select>
              </FormControl>
              <TextField
                fullWidth
                type="number"
                label="Actual Cost ($)"
                value={updateStepDialog.step.actual_cost || ''}
                onChange={(e) =>
                  setUpdateStepDialog((prev) => ({
                    ...prev,
                    step: { ...prev.step, actual_cost: e.target.value },
                  }))
                }
                inputProps={{ step: '0.01' }}
                sx={{ mb: 2 }}
              />
              <TextField
                fullWidth
                label="Notes"
                value={updateStepDialog.step.notes || ''}
                onChange={(e) =>
                  setUpdateStepDialog((prev) => ({
                    ...prev,
                    step: { ...prev.step, notes: e.target.value },
                  }))
                }
                multiline
                rows={3}
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUpdateStepDialog({ open: false, step: null })}>
            Cancel
          </Button>
          <Button
            onClick={handleUpdateStep}
            variant="contained"
            disabled={updateStepMutation.isLoading}
          >
            {updateStepMutation.isLoading ? <CircularProgress size={24} /> : 'Update'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        open={deleteDialog.open}
        title="Delete Treatment Plan"
        message={`Are you sure you want to delete "${deleteDialog.planTitle}"? This action cannot be undone.`}
        onConfirm={handleDeleteConfirm}
        onCancel={() => setDeleteDialog({ open: false, planId: null, planTitle: '' })}
        confirmText="Delete"
        cancelText="Cancel"
        isLoading={deletePlanMutation.isLoading}
      />
    </Box>
  );
}

export default TreatmentPlanBuilder;
