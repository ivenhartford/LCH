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
  FormControlLabel,
  Switch,
  InputAdornment,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Science as ScienceIcon,
  Search as SearchIcon,
} from '@mui/icons-material';
import logger from '../utils/logger';

/**
 * Laboratory Tests Component
 *
 * Manages the laboratory test catalog including test codes, reference ranges,
 * pricing, and external lab integration.
 */
function LabTests() {
  const queryClient = useQueryClient();

  // State
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [openDialog, setOpenDialog] = useState(false);
  const [editingTest, setEditingTest] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [externalLabFilter, setExternalLabFilter] = useState('');
  const [activeFilter, setActiveFilter] = useState('true');

  // Form data
  const [formData, setFormData] = useState({
    test_code: '',
    test_name: '',
    category: '',
    description: '',
    specimen_type: '',
    specimen_volume: '',
    collection_instructions: '',
    reference_range: '',
    unit_of_measure: '',
    turnaround_time: '',
    price: '',
    cost: '',
    external_lab: false,
    external_lab_name: '',
    external_lab_code: '',
    is_active: true,
  });

  useEffect(() => {
    logger.logLifecycle('LabTests', 'mounted');
    return () => logger.logLifecycle('LabTests', 'unmounted');
  }, []);

  // Fetch lab tests
  const { data: testsData, isLoading } = useQuery({
    queryKey: ['lab-tests', categoryFilter, externalLabFilter, activeFilter, searchTerm],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (categoryFilter) params.append('category', categoryFilter);
      if (externalLabFilter) params.append('external_lab', externalLabFilter);
      if (activeFilter) params.append('is_active', activeFilter);
      if (searchTerm) params.append('search', searchTerm);

      const response = await fetch(`/api/lab-tests?${params}`, { credentials: 'include' });
      if (!response.ok) throw new Error('Failed to fetch lab tests');
      return response.json();
    },
  });

  // Create mutation
  const createMutation = useMutation({
    mutationFn: async (data) => {
      const response = await fetch('/api/lab-tests', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(data),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to create lab test');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['lab-tests']);
      handleCloseDialog();
      logger.logAction('Lab test created');
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: async ({ id, data }) => {
      const response = await fetch(`/api/lab-tests/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(data),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to update lab test');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['lab-tests']);
      handleCloseDialog();
      logger.logAction('Lab test updated');
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: async (id) => {
      const response = await fetch(`/api/lab-tests/${id}`, {
        method: 'DELETE',
        credentials: 'include',
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to delete lab test');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['lab-tests']);
      logger.logAction('Lab test deleted');
    },
  });

  const labTests = testsData?.lab_tests || [];
  const categories = [...new Set(labTests.map((t) => t.category))].filter(Boolean);

  const handleOpenDialog = (test = null) => {
    if (test) {
      setEditingTest(test);
      setFormData({
        test_code: test.test_code || '',
        test_name: test.test_name || '',
        category: test.category || '',
        description: test.description || '',
        specimen_type: test.specimen_type || '',
        specimen_volume: test.specimen_volume || '',
        collection_instructions: test.collection_instructions || '',
        reference_range: test.reference_range || '',
        unit_of_measure: test.unit_of_measure || '',
        turnaround_time: test.turnaround_time || '',
        price: test.price || '',
        cost: test.cost || '',
        external_lab: test.external_lab || false,
        external_lab_name: test.external_lab_name || '',
        external_lab_code: test.external_lab_code || '',
        is_active: test.is_active !== undefined ? test.is_active : true,
      });
      logger.logAction('Edit lab test dialog opened', { test_id: test.id });
    } else {
      setEditingTest(null);
      setFormData({
        test_code: '',
        test_name: '',
        category: '',
        description: '',
        specimen_type: '',
        specimen_volume: '',
        collection_instructions: '',
        reference_range: '',
        unit_of_measure: '',
        turnaround_time: '',
        price: '',
        cost: '',
        external_lab: false,
        external_lab_name: '',
        external_lab_code: '',
        is_active: true,
      });
      logger.logAction('New lab test dialog opened');
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingTest(null);
  };

  const handleSubmit = () => {
    const data = { ...formData };

    // Convert numeric fields
    if (data.price) data.price = parseFloat(data.price);
    if (data.cost) data.cost = parseFloat(data.cost);

    if (editingTest) {
      updateMutation.mutate({ id: editingTest.id, data });
    } else {
      createMutation.mutate(data);
    }
  };

  const handleDelete = (test) => {
    if (window.confirm(`Are you sure you want to delete test "${test.test_name}"?`)) {
      deleteMutation.mutate(test.id);
    }
  };

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  const paginatedTests = labTests.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" display="flex" alignItems="center" gap={1}>
          <ScienceIcon fontSize="large" />
          Laboratory Tests
        </Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => handleOpenDialog()}>
          Add Lab Test
        </Button>
      </Box>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              size="small"
              label="Search"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              select
              size="small"
              label="Category"
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
            >
              <MenuItem value="">All Categories</MenuItem>
              {categories.map((cat) => (
                <MenuItem key={cat} value={cat}>
                  {cat}
                </MenuItem>
              ))}
            </TextField>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              select
              size="small"
              label="Lab Type"
              value={externalLabFilter}
              onChange={(e) => setExternalLabFilter(e.target.value)}
            >
              <MenuItem value="">All Types</MenuItem>
              <MenuItem value="false">In-House</MenuItem>
              <MenuItem value="true">External Lab</MenuItem>
            </TextField>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              select
              size="small"
              label="Status"
              value={activeFilter}
              onChange={(e) => setActiveFilter(e.target.value)}
            >
              <MenuItem value="true">Active</MenuItem>
              <MenuItem value="false">Inactive</MenuItem>
              <MenuItem value="">All</MenuItem>
            </TextField>
          </Grid>
        </Grid>
      </Paper>

      {/* Error Messages */}
      {(createMutation.isError || updateMutation.isError || deleteMutation.isError) && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {createMutation.error?.message ||
            updateMutation.error?.message ||
            deleteMutation.error?.message}
        </Alert>
      )}

      {/* Tests Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Test Code</TableCell>
              <TableCell>Test Name</TableCell>
              <TableCell>Category</TableCell>
              <TableCell>Specimen</TableCell>
              <TableCell align="right">Price</TableCell>
              <TableCell>Lab Type</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {paginatedTests.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  <Typography color="text.secondary" py={3}>
                    No lab tests found
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              paginatedTests.map((test) => (
                <TableRow key={test.id} hover>
                  <TableCell>
                    <Typography variant="body2" fontFamily="monospace" fontWeight="bold">
                      {test.test_code}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium">
                      {test.test_name}
                    </Typography>
                    {test.description && (
                      <Typography variant="caption" color="text.secondary" display="block">
                        {test.description.length > 50
                          ? test.description.substring(0, 50) + '...'
                          : test.description}
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    <Chip label={test.category} size="small" />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{test.specimen_type || 'N/A'}</Typography>
                    {test.specimen_volume && (
                      <Typography variant="caption" color="text.secondary">
                        {test.specimen_volume}
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell align="right">
                    <Typography variant="body2">
                      ${parseFloat(test.price || 0).toFixed(2)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {test.external_lab ? (
                      <Chip label={test.external_lab_name || 'External'} size="small" color="info" />
                    ) : (
                      <Chip label="In-House" size="small" color="success" />
                    )}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={test.is_active ? 'Active' : 'Inactive'}
                      size="small"
                      color={test.is_active ? 'success' : 'default'}
                    />
                  </TableCell>
                  <TableCell align="right">
                    <IconButton size="small" onClick={() => handleOpenDialog(test)} color="primary">
                      <EditIcon fontSize="small" />
                    </IconButton>
                    <IconButton size="small" onClick={() => handleDelete(test)} color="error">
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
        <TablePagination
          component="div"
          count={labTests.length}
          page={page}
          onPageChange={handleChangePage}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          rowsPerPageOptions={[5, 10, 25, 50]}
        />
      </TableContainer>

      {/* Add/Edit Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>{editingTest ? 'Edit Lab Test' : 'Add Lab Test'}</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <Grid container spacing={2}>
              {/* Basic Information */}
              <Grid item xs={12}>
                <Typography variant="subtitle2" color="primary" gutterBottom>
                  Basic Information
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  required
                  label="Test Code"
                  value={formData.test_code}
                  onChange={(e) => setFormData({ ...formData, test_code: e.target.value })}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  required
                  label="Test Name"
                  value={formData.test_name}
                  onChange={(e) => setFormData({ ...formData, test_name: e.target.value })}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  required
                  label="Category"
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  helperText="e.g., Hematology, Chemistry, Microbiology"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Unit of Measure"
                  value={formData.unit_of_measure}
                  onChange={(e) => setFormData({ ...formData, unit_of_measure: e.target.value })}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={2}
                  label="Description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                />
              </Grid>

              {/* Specimen Information */}
              <Grid item xs={12}>
                <Typography variant="subtitle2" color="primary" gutterBottom sx={{ mt: 2 }}>
                  Specimen Information
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Specimen Type"
                  value={formData.specimen_type}
                  onChange={(e) => setFormData({ ...formData, specimen_type: e.target.value })}
                  helperText="e.g., Blood, Urine, Feces"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Specimen Volume"
                  value={formData.specimen_volume}
                  onChange={(e) => setFormData({ ...formData, specimen_volume: e.target.value })}
                  helperText="e.g., 2-5 ml"
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={2}
                  label="Collection Instructions"
                  value={formData.collection_instructions}
                  onChange={(e) =>
                    setFormData({ ...formData, collection_instructions: e.target.value })
                  }
                />
              </Grid>

              {/* Reference Range & Pricing */}
              <Grid item xs={12}>
                <Typography variant="subtitle2" color="primary" gutterBottom sx={{ mt: 2 }}>
                  Reference Range & Pricing
                </Typography>
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Reference Range"
                  value={formData.reference_range}
                  onChange={(e) => setFormData({ ...formData, reference_range: e.target.value })}
                  helperText="e.g., 10-20 mg/dL or Normal: <100"
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <TextField
                  fullWidth
                  label="Turnaround Time"
                  value={formData.turnaround_time}
                  onChange={(e) => setFormData({ ...formData, turnaround_time: e.target.value })}
                  helperText="e.g., 24-48 hours"
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <TextField
                  fullWidth
                  type="number"
                  label="Price"
                  value={formData.price}
                  onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                  InputProps={{ startAdornment: <InputAdornment position="start">$</InputAdornment> }}
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <TextField
                  fullWidth
                  type="number"
                  label="Cost"
                  value={formData.cost}
                  onChange={(e) => setFormData({ ...formData, cost: e.target.value })}
                  InputProps={{ startAdornment: <InputAdornment position="start">$</InputAdornment> }}
                />
              </Grid>

              {/* External Lab Information */}
              <Grid item xs={12}>
                <Typography variant="subtitle2" color="primary" gutterBottom sx={{ mt: 2 }}>
                  External Lab Information
                </Typography>
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.external_lab}
                      onChange={(e) => setFormData({ ...formData, external_lab: e.target.checked })}
                    />
                  }
                  label="External Lab Test"
                />
              </Grid>
              {formData.external_lab && (
                <>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="External Lab Name"
                      value={formData.external_lab_name}
                      onChange={(e) =>
                        setFormData({ ...formData, external_lab_name: e.target.value })
                      }
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="External Lab Test Code"
                      value={formData.external_lab_code}
                      onChange={(e) =>
                        setFormData({ ...formData, external_lab_code: e.target.value })
                      }
                    />
                  </Grid>
                </>
              )}

              {/* Status */}
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.is_active}
                      onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    />
                  }
                  label="Active"
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
              !formData.test_code ||
              !formData.test_name ||
              !formData.category ||
              createMutation.isPending ||
              updateMutation.isPending
            }
          >
            {editingTest ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default LabTests;
