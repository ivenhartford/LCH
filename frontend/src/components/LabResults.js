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
  FormControlLabel,
  Checkbox,
  Tooltip,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Biotech as BiotechIcon,
  Visibility as VisibilityIcon,
} from '@mui/icons-material';
import logger from '../utils/logger';

/**
 * Laboratory Results Component
 *
 * Manages laboratory test results including ordering tests, entering results,
 * flagging abnormal values, and review workflow.
 */
function LabResults() {
  const queryClient = useQueryClient();

  // State
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [openDialog, setOpenDialog] = useState(false);
  const [openViewDialog, setOpenViewDialog] = useState(false);
  const [editingResult, setEditingResult] = useState(null);
  const [viewingResult, setViewingResult] = useState(null);
  const [tabValue, setTabValue] = useState(0);
  const [patientFilter, setPatientFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [testFilter, setTestFilter] = useState('');

  // Form data
  const [formData, setFormData] = useState({
    patient_id: '',
    visit_id: '',
    test_id: '',
    collection_date: new Date().toISOString().split('T')[0],
    collection_time: '',
    result_value: '',
    result_date: '',
    status: 'pending',
    is_abnormal: false,
    abnormal_flag: '',
    result_notes: '',
    technician_notes: '',
  });

  useEffect(() => {
    logger.logLifecycle('LabResults', 'mounted');
    return () => logger.logLifecycle('LabResults', 'unmounted');
  }, []);

  // Fetch lab results based on active tab
  const getQueryKey = () => {
    if (tabValue === 0) return ['lab-results', statusFilter, testFilter, patientFilter];
    if (tabValue === 1) return ['lab-results-pending'];
    if (tabValue === 2) return ['lab-results-abnormal'];
    return ['lab-results'];
  };

  const getQueryFn = async () => {
    let url = '/api/lab-results';

    if (tabValue === 1) {
      url = '/api/lab-results/pending';
    } else if (tabValue === 2) {
      url = '/api/lab-results/abnormal?reviewed=false';
    } else {
      const params = new URLSearchParams();
      if (statusFilter) params.append('status', statusFilter);
      if (testFilter) params.append('test_id', testFilter);
      if (patientFilter) params.append('patient_id', patientFilter);
      if (params.toString()) url += `?${params}`;
    }

    const response = await fetch(url, { credentials: 'include' });
    if (!response.ok) throw new Error('Failed to fetch lab results');
    return response.json();
  };

  const { data: resultsData, isLoading } = useQuery({
    queryKey: getQueryKey(),
    queryFn: getQueryFn,
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

  // Fetch lab tests for dropdown
  const { data: testsData } = useQuery({
    queryKey: ['lab-tests-active'],
    queryFn: async () => {
      const response = await fetch('/api/lab-tests?is_active=true', { credentials: 'include' });
      if (!response.ok) throw new Error('Failed to fetch lab tests');
      return response.json();
    },
  });

  // Create mutation
  const createMutation = useMutation({
    mutationFn: async (data) => {
      const response = await fetch('/api/lab-results', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(data),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to create lab result');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['lab-results']);
      queryClient.invalidateQueries(['lab-results-pending']);
      handleCloseDialog();
      logger.logAction('Lab result created');
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: async ({ id, data }) => {
      const response = await fetch(`/api/lab-results/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(data),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to update lab result');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['lab-results']);
      queryClient.invalidateQueries(['lab-results-pending']);
      queryClient.invalidateQueries(['lab-results-abnormal']);
      handleCloseDialog();
      logger.logAction('Lab result updated');
    },
  });

  // Review mutation
  const reviewMutation = useMutation({
    mutationFn: async (id) => {
      const response = await fetch(`/api/lab-results/${id}/review`, {
        method: 'POST',
        credentials: 'include',
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to review lab result');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['lab-results']);
      queryClient.invalidateQueries(['lab-results-abnormal']);
      logger.logAction('Lab result reviewed');
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: async (id) => {
      const response = await fetch(`/api/lab-results/${id}`, {
        method: 'DELETE',
        credentials: 'include',
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to delete lab result');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['lab-results']);
      queryClient.invalidateQueries(['lab-results-pending']);
      queryClient.invalidateQueries(['lab-results-abnormal']);
      logger.logAction('Lab result deleted');
    },
  });

  const labResults = resultsData?.lab_results || [];
  const patients = patientsData?.patients || [];
  const labTests = testsData?.lab_tests || [];

  const handleOpenDialog = (result = null) => {
    if (result) {
      setEditingResult(result);
      setFormData({
        patient_id: result.patient_id || '',
        visit_id: result.visit_id || '',
        test_id: result.test_id || '',
        collection_date: result.collection_date
          ? new Date(result.collection_date).toISOString().split('T')[0]
          : '',
        collection_time: result.collection_time || '',
        result_value: result.result_value || '',
        result_date: result.result_date
          ? new Date(result.result_date).toISOString().split('T')[0]
          : '',
        status: result.status || 'pending',
        is_abnormal: result.is_abnormal || false,
        abnormal_flag: result.abnormal_flag || '',
        result_notes: result.result_notes || '',
        technician_notes: result.technician_notes || '',
      });
      logger.logAction('Edit lab result dialog opened', { result_id: result.id });
    } else {
      setEditingResult(null);
      setFormData({
        patient_id: '',
        visit_id: '',
        test_id: '',
        collection_date: new Date().toISOString().split('T')[0],
        collection_time: '',
        result_value: '',
        result_date: '',
        status: 'pending',
        is_abnormal: false,
        abnormal_flag: '',
        result_notes: '',
        technician_notes: '',
      });
      logger.logAction('New lab result dialog opened');
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingResult(null);
  };

  const handleOpenViewDialog = (result) => {
    setViewingResult(result);
    setOpenViewDialog(true);
    logger.logAction('View lab result dialog opened', { result_id: result.id });
  };

  const handleCloseViewDialog = () => {
    setOpenViewDialog(false);
    setViewingResult(null);
  };

  const handleSubmit = () => {
    const data = { ...formData };

    // Convert empty strings to null for optional fields
    if (!data.visit_id) data.visit_id = null;
    if (!data.collection_time) data.collection_time = null;
    if (!data.result_date) data.result_date = null;
    if (!data.abnormal_flag) data.abnormal_flag = null;

    if (editingResult) {
      updateMutation.mutate({ id: editingResult.id, data });
    } else {
      createMutation.mutate(data);
    }
  };

  const handleReview = (result) => {
    if (
      window.confirm(
        `Mark this ${result.is_abnormal ? 'abnormal ' : ''}result as reviewed?\n\nTest: ${result.test_name}\nPatient: ${result.patient_name}`
      )
    ) {
      reviewMutation.mutate(result.id);
    }
  };

  const handleDelete = (result) => {
    if (
      window.confirm(
        `Are you sure you want to delete this lab result?\n\nTest: ${result.test_name}\nPatient: ${result.patient_name}`
      )
    ) {
      deleteMutation.mutate(result.id);
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
      case 'in_progress':
        return 'info';
      case 'completed':
        return 'success';
      case 'cancelled':
        return 'error';
      default:
        return 'default';
    }
  };

  const getAbnormalFlagColor = (flag) => {
    switch (flag) {
      case 'H':
        return 'error';
      case 'L':
        return 'warning';
      case 'A':
        return 'error';
      default:
        return 'default';
    }
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  const paginatedResults = labResults.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" display="flex" alignItems="center" gap={1}>
          <BiotechIcon fontSize="large" />
          Laboratory Results
        </Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => handleOpenDialog()}>
          Order Lab Test
        </Button>
      </Box>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
          <Tab label="All Results" />
          <Tab label="Pending" />
          <Tab label="Abnormal (Unreviewed)" />
        </Tabs>
      </Paper>

      {/* Filters (only show on "All Results" tab) */}
      {tabValue === 0 && (
        <Paper sx={{ p: 2, mb: 3 }}>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                select
                size="small"
                label="Patient"
                value={patientFilter}
                onChange={(e) => setPatientFilter(e.target.value)}
              >
                <MenuItem value="">All Patients</MenuItem>
                {patients.map((p) => (
                  <MenuItem key={p.id} value={p.id}>
                    {p.name}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                select
                size="small"
                label="Test"
                value={testFilter}
                onChange={(e) => setTestFilter(e.target.value)}
              >
                <MenuItem value="">All Tests</MenuItem>
                {labTests.map((t) => (
                  <MenuItem key={t.id} value={t.id}>
                    {t.test_name}
                  </MenuItem>
                ))}
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
                <MenuItem value="in_progress">In Progress</MenuItem>
                <MenuItem value="completed">Completed</MenuItem>
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
        reviewMutation.isError) && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {createMutation.error?.message ||
            updateMutation.error?.message ||
            deleteMutation.error?.message ||
            reviewMutation.error?.message}
        </Alert>
      )}

      {/* Results Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Date</TableCell>
              <TableCell>Patient</TableCell>
              <TableCell>Test</TableCell>
              <TableCell>Result</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Flags</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {paginatedResults.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  <Typography color="text.secondary" py={3}>
                    No lab results found
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              paginatedResults.map((result) => (
                <TableRow
                  key={result.id}
                  hover
                  sx={{
                    backgroundColor: result.is_abnormal && !result.reviewed ? '#fff3e0' : 'inherit',
                  }}
                >
                  <TableCell>
                    <Typography variant="body2">
                      {new Date(result.collection_date).toLocaleDateString()}
                    </Typography>
                    {result.collection_time && (
                      <Typography variant="caption" color="text.secondary">
                        {result.collection_time}
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium">
                      {result.patient_name}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium">
                      {result.test_name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" fontFamily="monospace">
                      {result.test_code}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {result.result_value ? (
                      <>
                        <Typography
                          variant="body2"
                          fontWeight="bold"
                          color={result.is_abnormal ? 'error.main' : 'inherit'}
                        >
                          {result.result_value}
                        </Typography>
                        {result.result_date && (
                          <Typography variant="caption" color="text.secondary">
                            {new Date(result.result_date).toLocaleDateString()}
                          </Typography>
                        )}
                      </>
                    ) : (
                      <Typography variant="body2" color="text.secondary" fontStyle="italic">
                        Pending
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    <Chip label={result.status} size="small" color={getStatusColor(result.status)} />
                  </TableCell>
                  <TableCell>
                    <Box display="flex" gap={0.5} flexWrap="wrap">
                      {result.is_abnormal && (
                        <Chip
                          icon={<WarningIcon />}
                          label={result.abnormal_flag || 'Abnormal'}
                          size="small"
                          color={getAbnormalFlagColor(result.abnormal_flag)}
                        />
                      )}
                      {result.reviewed ? (
                        <Chip
                          icon={<CheckCircleIcon />}
                          label="Reviewed"
                          size="small"
                          color="success"
                        />
                      ) : result.is_abnormal ? (
                        <Chip label="Needs Review" size="small" color="warning" />
                      ) : null}
                    </Box>
                  </TableCell>
                  <TableCell align="right">
                    <Tooltip title="View Details">
                      <IconButton
                        size="small"
                        onClick={() => handleOpenViewDialog(result)}
                        color="info"
                      >
                        <VisibilityIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Edit">
                      <IconButton
                        size="small"
                        onClick={() => handleOpenDialog(result)}
                        color="primary"
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    {result.is_abnormal && !result.reviewed && (
                      <Tooltip title="Mark as Reviewed">
                        <IconButton
                          size="small"
                          onClick={() => handleReview(result)}
                          color="success"
                        >
                          <CheckCircleIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    )}
                    <Tooltip title="Delete">
                      <IconButton size="small" onClick={() => handleDelete(result)} color="error">
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
          count={labResults.length}
          page={page}
          onPageChange={handleChangePage}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          rowsPerPageOptions={[5, 10, 25, 50]}
        />
      </TableContainer>

      {/* Add/Edit Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>{editingResult ? 'Edit Lab Result' : 'Order Lab Test'}</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <Typography variant="subtitle2" color="primary" gutterBottom>
                  Test Order Information
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  required
                  select
                  label="Patient"
                  value={formData.patient_id}
                  onChange={(e) => setFormData({ ...formData, patient_id: e.target.value })}
                >
                  {patients.map((p) => (
                    <MenuItem key={p.id} value={p.id}>
                      {p.name}
                    </MenuItem>
                  ))}
                </TextField>
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  required
                  select
                  label="Lab Test"
                  value={formData.test_id}
                  onChange={(e) => setFormData({ ...formData, test_id: e.target.value })}
                >
                  {labTests.map((t) => (
                    <MenuItem key={t.id} value={t.id}>
                      {t.test_name} ({t.test_code})
                    </MenuItem>
                  ))}
                </TextField>
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  required
                  type="date"
                  label="Collection Date"
                  value={formData.collection_date}
                  onChange={(e) => setFormData({ ...formData, collection_date: e.target.value })}
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  type="time"
                  label="Collection Time"
                  value={formData.collection_time}
                  onChange={(e) => setFormData({ ...formData, collection_time: e.target.value })}
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>

              <Grid item xs={12}>
                <Typography variant="subtitle2" color="primary" gutterBottom sx={{ mt: 2 }}>
                  Result Information
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  select
                  label="Status"
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                >
                  <MenuItem value="pending">Pending</MenuItem>
                  <MenuItem value="in_progress">In Progress</MenuItem>
                  <MenuItem value="completed">Completed</MenuItem>
                  <MenuItem value="cancelled">Cancelled</MenuItem>
                </TextField>
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  type="date"
                  label="Result Date"
                  value={formData.result_date}
                  onChange={(e) => setFormData({ ...formData, result_date: e.target.value })}
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={2}
                  label="Result Value"
                  value={formData.result_value}
                  onChange={(e) => setFormData({ ...formData, result_value: e.target.value })}
                  helperText="Enter the test result value"
                />
              </Grid>

              <Grid item xs={12}>
                <Typography variant="subtitle2" color="primary" gutterBottom sx={{ mt: 2 }}>
                  Abnormal Flags
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={formData.is_abnormal}
                      onChange={(e) => setFormData({ ...formData, is_abnormal: e.target.checked })}
                    />
                  }
                  label="Mark as Abnormal"
                />
              </Grid>
              {formData.is_abnormal && (
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    select
                    label="Abnormal Flag"
                    value={formData.abnormal_flag}
                    onChange={(e) => setFormData({ ...formData, abnormal_flag: e.target.value })}
                  >
                    <MenuItem value="H">H - High</MenuItem>
                    <MenuItem value="L">L - Low</MenuItem>
                    <MenuItem value="A">A - Alert/Critical</MenuItem>
                  </TextField>
                </Grid>
              )}

              <Grid item xs={12}>
                <Typography variant="subtitle2" color="primary" gutterBottom sx={{ mt: 2 }}>
                  Notes
                </Typography>
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={2}
                  label="Result Notes"
                  value={formData.result_notes}
                  onChange={(e) => setFormData({ ...formData, result_notes: e.target.value })}
                  helperText="Clinical interpretation or notes about the result"
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={2}
                  label="Technician Notes"
                  value={formData.technician_notes}
                  onChange={(e) => setFormData({ ...formData, technician_notes: e.target.value })}
                  helperText="Technical notes about specimen or testing process"
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
              !formData.patient_id ||
              !formData.test_id ||
              !formData.collection_date ||
              createMutation.isPending ||
              updateMutation.isPending
            }
          >
            {editingResult ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* View Details Dialog */}
      <Dialog open={openViewDialog} onClose={handleCloseViewDialog} maxWidth="sm" fullWidth>
        <DialogTitle>Lab Result Details</DialogTitle>
        <DialogContent>
          {viewingResult && (
            <Box sx={{ mt: 2 }}>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="caption" color="text.secondary">
                    Patient
                  </Typography>
                  <Typography variant="body1" fontWeight="medium">
                    {viewingResult.patient_name}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="caption" color="text.secondary">
                    Test
                  </Typography>
                  <Typography variant="body1" fontWeight="medium">
                    {viewingResult.test_name}
                  </Typography>
                  <Typography variant="caption" fontFamily="monospace">
                    {viewingResult.test_code}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="caption" color="text.secondary">
                    Collection Date
                  </Typography>
                  <Typography variant="body2">
                    {new Date(viewingResult.collection_date).toLocaleDateString()}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="caption" color="text.secondary">
                    Status
                  </Typography>
                  <Box mt={0.5}>
                    <Chip
                      label={viewingResult.status}
                      size="small"
                      color={getStatusColor(viewingResult.status)}
                    />
                  </Box>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="caption" color="text.secondary">
                    Result
                  </Typography>
                  <Typography
                    variant="h6"
                    color={viewingResult.is_abnormal ? 'error.main' : 'inherit'}
                  >
                    {viewingResult.result_value || 'Pending'}
                  </Typography>
                  {viewingResult.result_date && (
                    <Typography variant="caption" color="text.secondary">
                      Result Date: {new Date(viewingResult.result_date).toLocaleDateString()}
                    </Typography>
                  )}
                </Grid>
                {viewingResult.is_abnormal && (
                  <Grid item xs={12}>
                    <Alert severity="warning">
                      Abnormal Result - Flag: {viewingResult.abnormal_flag || 'Abnormal'}
                      {!viewingResult.reviewed && ' (Needs Review)'}
                    </Alert>
                  </Grid>
                )}
                {viewingResult.result_notes && (
                  <Grid item xs={12}>
                    <Typography variant="caption" color="text.secondary">
                      Result Notes
                    </Typography>
                    <Typography variant="body2">{viewingResult.result_notes}</Typography>
                  </Grid>
                )}
                {viewingResult.technician_notes && (
                  <Grid item xs={12}>
                    <Typography variant="caption" color="text.secondary">
                      Technician Notes
                    </Typography>
                    <Typography variant="body2">{viewingResult.technician_notes}</Typography>
                  </Grid>
                )}
                {viewingResult.reviewed && (
                  <Grid item xs={12}>
                    <Chip icon={<CheckCircleIcon />} label="Reviewed" color="success" />
                    {viewingResult.reviewed_date && (
                      <Typography variant="caption" color="text.secondary" ml={1}>
                        on {new Date(viewingResult.reviewed_date).toLocaleDateString()}
                      </Typography>
                    )}
                  </Grid>
                )}
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseViewDialog}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default LabResults;
