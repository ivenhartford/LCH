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
  Warning as WarningIcon,
  Search as SearchIcon,
} from '@mui/icons-material';
import logger from '../utils/logger';
import ConfirmDialog from './common/ConfirmDialog';

/**
 * Medications Management Component
 *
 * Manages the veterinary drug database (formulary).
 * Features:
 * - List all medications with search/filter
 * - Create new medications
 * - Edit existing medications
 * - Mark medications as active/inactive
 * - Track inventory levels
 */
function Medications() {
  const queryClient = useQueryClient();

  // State
  const [searchTerm, setSearchTerm] = useState('');
  const [activeFilter, setActiveFilter] = useState('true');
  const [drugClassFilter, setDrugClassFilter] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingMedication, setEditingMedication] = useState(null);
  const [deleteDialog, setDeleteDialog] = useState({ open: false, medicationId: null, drugName: '' });
  const [formData, setFormData] = useState({
    drug_name: '',
    brand_names: '',
    drug_class: '',
    controlled_substance: false,
    dea_schedule: '',
    available_forms: '',
    strengths: '',
    typical_dose_cats: '',
    dosing_frequency: '',
    route_of_administration: '',
    indications: '',
    contraindications: '',
    side_effects: '',
    warnings: '',
    stock_quantity: 0,
    reorder_level: 0,
    unit_cost: '',
    is_active: true,
  });

  useEffect(() => {
    logger.logLifecycle('Medications', 'mounted');
    return () => {
      logger.logLifecycle('Medications', 'unmounted');
    };
  }, []);

  // Fetch medications
  const {
    data: medicationsData,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ['medications', activeFilter, drugClassFilter, searchTerm],
    queryFn: async () => {
      const startTime = performance.now();

      const params = new URLSearchParams();
      if (activeFilter) params.append('is_active', activeFilter);
      if (drugClassFilter) params.append('drug_class', drugClassFilter);
      if (searchTerm) params.append('search', searchTerm);

      logger.logAction('Fetching medications', { activeFilter, drugClassFilter, searchTerm });

      const response = await fetch(`/api/medications?${params}`, {
        credentials: 'include',
      });

      const duration = performance.now() - startTime;

      if (!response.ok) {
        logger.logAPICall('GET', '/api/medications', response.status, duration, 'Fetch failed');
        throw new Error(`Failed to fetch medications: ${response.status}`);
      }

      const data = await response.json();
      logger.logAPICall('GET', '/api/medications', response.status, duration);
      logger.info('Medications fetched', { count: data.medications?.length || 0 });

      return data;
    },
    staleTime: 30000,
    retry: 2,
  });

  // Create/Update mutation
  const saveMutation = useMutation({
    mutationFn: async (data) => {
      const url = editingMedication
        ? `/api/medications/${editingMedication.id}`
        : '/api/medications';
      const method = editingMedication ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to save medication');
      }

      return response.json();
    },
    onSuccess: () => {
      logger.info(editingMedication ? 'Medication updated' : 'Medication created');
      queryClient.invalidateQueries(['medications']);
      handleCloseDialog();
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: async (medicationId) => {
      const response = await fetch(`/api/medications/${medicationId}`, {
        method: 'DELETE',
        credentials: 'include',
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to delete medication');
      }

      return response.json();
    },
    onSuccess: () => {
      logger.info('Medication deleted');
      queryClient.invalidateQueries(['medications']);
    },
  });

  const handleOpenDialog = (medication = null) => {
    if (medication) {
      setEditingMedication(medication);
      setFormData({
        drug_name: medication.drug_name || '',
        brand_names: medication.brand_names || '',
        drug_class: medication.drug_class || '',
        controlled_substance: medication.controlled_substance || false,
        dea_schedule: medication.dea_schedule || '',
        available_forms: medication.available_forms || '',
        strengths: medication.strengths || '',
        typical_dose_cats: medication.typical_dose_cats || '',
        dosing_frequency: medication.dosing_frequency || '',
        route_of_administration: medication.route_of_administration || '',
        indications: medication.indications || '',
        contraindications: medication.contraindications || '',
        side_effects: medication.side_effects || '',
        warnings: medication.warnings || '',
        stock_quantity: medication.stock_quantity || 0,
        reorder_level: medication.reorder_level || 0,
        unit_cost: medication.unit_cost || '',
        is_active: medication.is_active ?? true,
      });
    } else {
      setEditingMedication(null);
      setFormData({
        drug_name: '',
        brand_names: '',
        drug_class: '',
        controlled_substance: false,
        dea_schedule: '',
        available_forms: '',
        strengths: '',
        typical_dose_cats: '',
        dosing_frequency: '',
        route_of_administration: '',
        indications: '',
        contraindications: '',
        side_effects: '',
        warnings: '',
        stock_quantity: 0,
        reorder_level: 0,
        unit_cost: '',
        is_active: true,
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingMedication(null);
  };

  const handleSubmit = () => {
    logger.logAction(editingMedication ? 'Update medication' : 'Create medication', formData);
    saveMutation.mutate(formData);
  };

  const handleDelete = (medicationId, drugName) => {
    setDeleteDialog({ open: true, medicationId, drugName });
  };

  const handleDeleteConfirm = () => {
    logger.logAction('Delete medication', { medicationId: deleteDialog.medicationId, drugName: deleteDialog.drugName });
    deleteMutation.mutate(deleteDialog.medicationId);
    setDeleteDialog({ open: false, medicationId: null, drugName: '' });
  };

  const handleDeleteCancel = () => {
    setDeleteDialog({ open: false, medicationId: null, drugName: '' });
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
        <Alert severity="error">
          Failed to load medications: {error.message}
          <Button onClick={() => refetch()} sx={{ ml: 2 }}>
            Retry
          </Button>
        </Alert>
      </Box>
    );
  }

  const medications = medicationsData?.medications || [];

  return (
    <Box>
      {/* Header */}
      <Box mb={3} display="flex" justifyContent="space-between" alignItems="center">
        <Typography variant="h4" component="h1">
          Medication Database
        </Typography>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
        >
          Add Medication
        </Button>
      </Box>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={4}>
            <TextField
              fullWidth
              size="small"
              label="Search Medications"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: <SearchIcon color="action" sx={{ mr: 1 }} />,
              }}
            />
          </Grid>

          <Grid item xs={12} sm={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Status</InputLabel>
              <Select
                value={activeFilter}
                label="Status"
                onChange={(e) => setActiveFilter(e.target.value)}
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="true">Active</MenuItem>
                <MenuItem value="false">Inactive</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} sm={3}>
            <TextField
              fullWidth
              size="small"
              label="Drug Class"
              value={drugClassFilter}
              onChange={(e) => setDrugClassFilter(e.target.value)}
            />
          </Grid>

          <Grid item xs={12} sm={2}>
            {(searchTerm || drugClassFilter || activeFilter !== 'true') && (
              <Button
                size="small"
                onClick={() => {
                  setSearchTerm('');
                  setDrugClassFilter('');
                  setActiveFilter('true');
                }}
              >
                Clear Filters
              </Button>
            )}
          </Grid>
        </Grid>
      </Paper>

      {/* Table */}
      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Drug Name</TableCell>
                <TableCell>Brand Names</TableCell>
                <TableCell>Drug Class</TableCell>
                <TableCell>Forms</TableCell>
                <TableCell>Strengths</TableCell>
                <TableCell>Stock</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {medications.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} align="center">
                    <Typography variant="body2" color="text.secondary" py={4}>
                      No medications found.
                      {(searchTerm || drugClassFilter) && ' Try adjusting filters.'}
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                medications.map((medication) => (
                  <TableRow key={medication.id} hover>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        {medication.drug_name}
                      </Typography>
                      {medication.controlled_substance && (
                        <Chip
                          label={`DEA ${medication.dea_schedule}`}
                          size="small"
                          color="error"
                          sx={{ mt: 0.5 }}
                        />
                      )}
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {medication.brand_names || '-'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">{medication.drug_class || '-'}</Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" fontSize="0.8rem">
                        {medication.available_forms || '-'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" fontSize="0.8rem">
                        {medication.strengths || '-'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Box display="flex" alignItems="center" gap={0.5}>
                        <Typography variant="body2">{medication.stock_quantity}</Typography>
                        {medication.stock_quantity <= medication.reorder_level && (
                          <Tooltip title="Stock below reorder level">
                            <WarningIcon color="warning" fontSize="small" />
                          </Tooltip>
                        )}
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={medication.is_active ? 'Active' : 'Inactive'}
                        color={medication.is_active ? 'success' : 'default'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell align="right">
                      <Tooltip title="Edit">
                        <IconButton
                          size="small"
                          onClick={() => handleOpenDialog(medication)}
                          color="primary"
                        >
                          <EditIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete">
                        <IconButton
                          size="small"
                          onClick={() => handleDelete(medication.id, medication.drug_name)}
                          color="error"
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
            Total: {medications.length} medications
          </Typography>
        </Box>
      </Paper>

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>{editingMedication ? 'Edit Medication' : 'Add New Medication'}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 0.5 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                required
                label="Drug Name"
                value={formData.drug_name}
                onChange={(e) => setFormData({ ...formData, drug_name: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Brand Names"
                value={formData.brand_names}
                onChange={(e) => setFormData({ ...formData, brand_names: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Drug Class"
                value={formData.drug_class}
                onChange={(e) => setFormData({ ...formData, drug_class: e.target.value })}
                placeholder="e.g., Antibiotic, NSAID, Antiparasitic"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Controlled Substance</InputLabel>
                <Select
                  value={formData.controlled_substance}
                  label="Controlled Substance"
                  onChange={(e) =>
                    setFormData({ ...formData, controlled_substance: e.target.value })
                  }
                >
                  <MenuItem value={false}>No</MenuItem>
                  <MenuItem value={true}>Yes</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            {formData.controlled_substance && (
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="DEA Schedule"
                  value={formData.dea_schedule}
                  onChange={(e) => setFormData({ ...formData, dea_schedule: e.target.value })}
                  placeholder="e.g., II, III, IV"
                />
              </Grid>
            )}
            <Grid item xs={12} sm={formData.controlled_substance ? 6 : 12}>
              <TextField
                fullWidth
                label="Available Forms"
                value={formData.available_forms}
                onChange={(e) => setFormData({ ...formData, available_forms: e.target.value })}
                placeholder="e.g., Tablet, Capsule, Liquid"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Strengths"
                value={formData.strengths}
                onChange={(e) => setFormData({ ...formData, strengths: e.target.value })}
                placeholder="e.g., 50mg, 100mg, 200mg"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Typical Dose (Cats)"
                value={formData.typical_dose_cats}
                onChange={(e) => setFormData({ ...formData, typical_dose_cats: e.target.value })}
                placeholder="e.g., 5-10 mg/kg BID"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Dosing Frequency"
                value={formData.dosing_frequency}
                onChange={(e) => setFormData({ ...formData, dosing_frequency: e.target.value })}
                placeholder="e.g., BID, TID, QD"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Route of Administration"
                value={formData.route_of_administration}
                onChange={(e) =>
                  setFormData({ ...formData, route_of_administration: e.target.value })
                }
                placeholder="e.g., Oral, SC, IM, IV"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={formData.is_active}
                  label="Status"
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.value })}
                >
                  <MenuItem value={true}>Active</MenuItem>
                  <MenuItem value={false}>Inactive</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={2}
                label="Indications"
                value={formData.indications}
                onChange={(e) => setFormData({ ...formData, indications: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={2}
                label="Contraindications"
                value={formData.contraindications}
                onChange={(e) => setFormData({ ...formData, contraindications: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                type="number"
                label="Stock Quantity"
                value={formData.stock_quantity}
                onChange={(e) =>
                  setFormData({ ...formData, stock_quantity: parseInt(e.target.value) || 0 })
                }
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                type="number"
                label="Reorder Level"
                value={formData.reorder_level}
                onChange={(e) =>
                  setFormData({ ...formData, reorder_level: parseInt(e.target.value) || 0 })
                }
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                type="number"
                label="Unit Cost"
                value={formData.unit_cost}
                onChange={(e) => setFormData({ ...formData, unit_cost: e.target.value })}
                InputProps={{ startAdornment: '$' }}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={saveMutation.isLoading || !formData.drug_name}
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

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        open={deleteDialog.open}
        title="Delete Medication"
        message={`Are you sure you want to delete "${deleteDialog.drugName}"? This action cannot be undone and will remove all medication information.`}
        onConfirm={handleDeleteConfirm}
        onCancel={handleDeleteCancel}
        confirmText="Delete"
        confirmColor="error"
      />
    </Box>
  );
}

export default Medications;
