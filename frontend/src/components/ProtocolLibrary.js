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
  Card,
  CardContent,
  CardActions,
  useMediaQuery,
  useTheme,
  Divider,
  List,
  ListItem,
  ListItemText,
  Collapse,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
  LibraryBooks as LibraryIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  AddCircleOutline as AddStepIcon,
  RemoveCircleOutline as RemoveStepIcon,
  Category as CategoryIcon,
  MonetizationOn as CostIcon,
  Schedule as DurationIcon,
} from '@mui/icons-material';
import logger from '../utils/logger';
import ConfirmDialog from './common/ConfirmDialog';
import TableSkeleton from './common/TableSkeleton';
import EmptyState from './common/EmptyState';
import { useNotification } from '../contexts/NotificationContext';

/**
 * Protocol Library Component
 *
 * Manages reusable treatment plan templates (protocols).
 * Features:
 * - List all protocols with search/filter
 * - Create new protocols with multiple steps
 * - Edit existing protocols
 * - Delete protocols
 * - View protocol details with steps
 * - Filter by category and active status
 * - Track estimated cost and default duration
 */
function ProtocolLibrary() {
  const queryClient = useQueryClient();
  const { showNotification } = useNotification();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  // State
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [activeFilter, setActiveFilter] = useState('true');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingProtocol, setEditingProtocol] = useState(null);
  const [deleteDialog, setDeleteDialog] = useState({ open: false, protocolId: null, protocolName: '' });
  const [expandedProtocol, setExpandedProtocol] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    category: '',
    description: '',
    indications: '',
    contraindications: '',
    is_active: true,
    default_duration_days: '',
    estimated_cost: '',
    steps: [],
  });

  useEffect(() => {
    logger.logLifecycle('ProtocolLibrary', 'mounted');
    return () => {
      logger.logLifecycle('ProtocolLibrary', 'unmounted');
    };
  }, []);

  // Fetch protocols
  const {
    data: protocolsData,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ['protocols', categoryFilter, activeFilter, searchTerm],
    queryFn: async () => {
      const startTime = performance.now();

      const params = new URLSearchParams();
      if (categoryFilter) params.append('category', categoryFilter);
      if (activeFilter) params.append('is_active', activeFilter);
      if (searchTerm) params.append('search', searchTerm);

      logger.logAction('Fetching protocols', { categoryFilter, activeFilter, searchTerm });

      const response = await fetch(`/api/protocols?${params}`, {
        credentials: 'include',
      });

      const duration = performance.now() - startTime;

      if (!response.ok) {
        logger.logAPICall('GET', '/api/protocols', response.status, duration, 'Fetch failed');
        throw new Error(`Failed to fetch protocols: ${response.status}`);
      }

      const data = await response.json();
      logger.logAPICall('GET', '/api/protocols', response.status, duration);
      logger.info('Protocols fetched', { count: data.protocols?.length || 0 });

      return data;
    },
    staleTime: 30000,
    retry: 2,
  });

  // Fetch single protocol with steps (for expansion)
  const fetchProtocolDetails = async (protocolId) => {
    const response = await fetch(`/api/protocols/${protocolId}`, {
      credentials: 'include',
    });

    if (!response.ok) {
      throw new Error('Failed to fetch protocol details');
    }

    return response.json();
  };

  // Create/Update mutation
  const saveMutation = useMutation({
    mutationFn: async (data) => {
      const url = editingProtocol
        ? `/api/protocols/${editingProtocol.id}`
        : '/api/protocols';
      const method = editingProtocol ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to save protocol');
      }

      return response.json();
    },
    onSuccess: () => {
      logger.info(editingProtocol ? 'Protocol updated' : 'Protocol created');
      queryClient.invalidateQueries(['protocols']);
      handleCloseDialog();
      showNotification(
        editingProtocol ? 'Protocol updated successfully' : 'Protocol created successfully',
        'success'
      );
    },
    onError: (error) => {
      showNotification(error.message || 'Failed to save protocol', 'error');
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: async (protocolId) => {
      const response = await fetch(`/api/protocols/${protocolId}`, {
        method: 'DELETE',
        credentials: 'include',
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to delete protocol');
      }

      return response.json();
    },
    onSuccess: () => {
      logger.info('Protocol deleted');
      queryClient.invalidateQueries(['protocols']);
      showNotification('Protocol deleted successfully', 'success');
      setDeleteDialog({ open: false, protocolId: null, protocolName: '' });
    },
    onError: (error) => {
      showNotification(error.message || 'Failed to delete protocol', 'error');
    },
  });

  const handleOpenDialog = (protocol = null) => {
    if (protocol) {
      setEditingProtocol(protocol);
      setFormData({
        name: protocol.name || '',
        category: protocol.category || '',
        description: protocol.description || '',
        indications: protocol.indications || '',
        contraindications: protocol.contraindications || '',
        is_active: protocol.is_active ?? true,
        default_duration_days: protocol.default_duration_days || '',
        estimated_cost: protocol.estimated_cost || '',
        steps: protocol.steps || [],
      });
    } else {
      setEditingProtocol(null);
      setFormData({
        name: '',
        category: '',
        description: '',
        indications: '',
        contraindications: '',
        is_active: true,
        default_duration_days: '',
        estimated_cost: '',
        steps: [],
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingProtocol(null);
    setFormData({
      name: '',
      category: '',
      description: '',
      indications: '',
      contraindications: '',
      is_active: true,
      default_duration_days: '',
      estimated_cost: '',
      steps: [],
    });
  };

  const handleFormChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleAddStep = () => {
    const newStep = {
      step_number: formData.steps.length + 1,
      title: '',
      description: '',
      day_offset: 0,
      estimated_duration_minutes: '',
      estimated_cost: '',
    };
    setFormData((prev) => ({ ...prev, steps: [...prev.steps, newStep] }));
  };

  const handleRemoveStep = (index) => {
    setFormData((prev) => ({
      ...prev,
      steps: prev.steps.filter((_, i) => i !== index).map((step, idx) => ({
        ...step,
        step_number: idx + 1,
      })),
    }));
  };

  const handleStepChange = (index, field, value) => {
    setFormData((prev) => ({
      ...prev,
      steps: prev.steps.map((step, i) =>
        i === index ? { ...step, [field]: value } : step
      ),
    }));
  };

  const handleSubmit = () => {
    if (!formData.name.trim()) {
      showNotification('Protocol name is required', 'error');
      return;
    }

    if (formData.steps.length === 0) {
      showNotification('At least one step is required', 'error');
      return;
    }

    // Validate all steps have a title
    const invalidStep = formData.steps.find((step) => !step.title.trim());
    if (invalidStep) {
      showNotification('All steps must have a title', 'error');
      return;
    }

    const payload = {
      ...formData,
      default_duration_days: formData.default_duration_days ? parseInt(formData.default_duration_days) : null,
      estimated_cost: formData.estimated_cost ? parseFloat(formData.estimated_cost) : null,
      steps: formData.steps.map((step) => ({
        ...step,
        day_offset: parseInt(step.day_offset) || 0,
        estimated_duration_minutes: step.estimated_duration_minutes ? parseInt(step.estimated_duration_minutes) : null,
        estimated_cost: step.estimated_cost ? parseFloat(step.estimated_cost) : null,
      })),
    };

    saveMutation.mutate(payload);
  };

  const handleDeleteClick = (protocol) => {
    setDeleteDialog({ open: true, protocolId: protocol.id, protocolName: protocol.name });
  };

  const handleDeleteConfirm = () => {
    deleteMutation.mutate(deleteDialog.protocolId);
  };

  const handleExpandClick = async (protocol) => {
    if (expandedProtocol === protocol.id) {
      setExpandedProtocol(null);
    } else {
      try {
        const details = await fetchProtocolDetails(protocol.id);
        setExpandedProtocol(protocol.id);
        // Update the protocol in the cache with full details
        queryClient.setQueryData(['protocols', categoryFilter, activeFilter, searchTerm], (old) => ({
          ...old,
          protocols: old.protocols.map((p) =>
            p.id === protocol.id ? { ...p, steps: details.protocol.steps } : p
          ),
        }));
      } catch (error) {
        showNotification('Failed to load protocol details', 'error');
      }
    }
  };

  const protocols = protocolsData?.protocols || [];
  const categories = ['general', 'dental', 'surgical', 'emergency', 'chronic_care', 'preventive', 'diagnostic'];

  if (isLoading) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography variant="h4" sx={{ mb: 3 }}>
          Protocol Library
        </Typography>
        <TableSkeleton />
      </Box>
    );
  }

  if (isError) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography variant="h4" sx={{ mb: 3 }}>
          Protocol Library
        </Typography>
        <Alert severity="error">
          Error loading protocols: {error?.message || 'Unknown error'}
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          <LibraryIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Protocol Library
        </Typography>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={() => handleOpenDialog()}
        >
          New Protocol
        </Button>
      </Box>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              label="Search Protocols"
              variant="outlined"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
              }}
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <FormControl fullWidth>
              <InputLabel>Category</InputLabel>
              <Select
                value={categoryFilter}
                label="Category"
                onChange={(e) => setCategoryFilter(e.target.value)}
              >
                <MenuItem value="">All Categories</MenuItem>
                {categories.map((cat) => (
                  <MenuItem key={cat} value={cat}>
                    {cat.replace('_', ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={4}>
            <FormControl fullWidth>
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
        </Grid>
      </Paper>

      {/* Protocol List */}
      {protocols.length === 0 ? (
        <EmptyState
          icon={LibraryIcon}
          message="No protocols found"
          submessage="Create a new protocol template to get started"
          actionLabel="Create Protocol"
          onAction={() => handleOpenDialog()}
        />
      ) : isMobile ? (
        // Card view for mobile
        <Grid container spacing={2}>
          {protocols.map((protocol) => (
            <Grid item xs={12} key={protocol.id}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                    <Typography variant="h6">{protocol.name}</Typography>
                    <Chip
                      size="small"
                      label={protocol.is_active ? 'Active' : 'Inactive'}
                      color={protocol.is_active ? 'success' : 'default'}
                    />
                  </Box>
                  {protocol.category && (
                    <Chip
                      size="small"
                      icon={<CategoryIcon />}
                      label={protocol.category.replace('_', ' ')}
                      sx={{ mt: 1, mr: 1 }}
                    />
                  )}
                  {protocol.estimated_cost && (
                    <Chip
                      size="small"
                      icon={<CostIcon />}
                      label={`$${parseFloat(protocol.estimated_cost).toFixed(2)}`}
                      sx={{ mt: 1, mr: 1 }}
                    />
                  )}
                  {protocol.default_duration_days && (
                    <Chip
                      size="small"
                      icon={<DurationIcon />}
                      label={`${protocol.default_duration_days} days`}
                      sx={{ mt: 1 }}
                    />
                  )}
                  {protocol.description && (
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                      {protocol.description}
                    </Typography>
                  )}
                </CardContent>
                <CardActions>
                  <Button size="small" onClick={() => handleExpandClick(protocol)}>
                    {expandedProtocol === protocol.id ? 'Hide Steps' : 'View Steps'}
                  </Button>
                  <Button size="small" startIcon={<EditIcon />} onClick={() => handleOpenDialog(protocol)}>
                    Edit
                  </Button>
                  <Button
                    size="small"
                    color="error"
                    startIcon={<DeleteIcon />}
                    onClick={() => handleDeleteClick(protocol)}
                  >
                    Delete
                  </Button>
                </CardActions>
                <Collapse in={expandedProtocol === protocol.id}>
                  <Divider />
                  <CardContent>
                    {protocol.steps && protocol.steps.length > 0 ? (
                      <List dense>
                        {protocol.steps.map((step) => (
                          <ListItem key={step.id}>
                            <ListItemText
                              primary={`${step.step_number}. ${step.title}`}
                              secondary={
                                <>
                                  {step.description && <div>{step.description}</div>}
                                  <div>Day {step.day_offset}</div>
                                </>
                              }
                            />
                          </ListItem>
                        ))}
                      </List>
                    ) : (
                      <Typography color="text.secondary">No steps defined</Typography>
                    )}
                  </CardContent>
                </Collapse>
              </Card>
            </Grid>
          ))}
        </Grid>
      ) : (
        // Table view for desktop
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Category</TableCell>
                <TableCell align="center">Steps</TableCell>
                <TableCell align="right">Duration</TableCell>
                <TableCell align="right">Est. Cost</TableCell>
                <TableCell align="center">Status</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {protocols.map((protocol) => (
                <React.Fragment key={protocol.id}>
                  <TableRow hover>
                    <TableCell>
                      <Box>
                        <Typography variant="body1" fontWeight="medium">
                          {protocol.name}
                        </Typography>
                        {protocol.description && (
                          <Typography variant="body2" color="text.secondary">
                            {protocol.description}
                          </Typography>
                        )}
                      </Box>
                    </TableCell>
                    <TableCell>
                      {protocol.category ? (
                        <Chip
                          size="small"
                          icon={<CategoryIcon />}
                          label={protocol.category.replace('_', ' ')}
                        />
                      ) : (
                        '—'
                      )}
                    </TableCell>
                    <TableCell align="center">
                      <Tooltip title="View steps">
                        <IconButton size="small" onClick={() => handleExpandClick(protocol)}>
                          {expandedProtocol === protocol.id ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                        </IconButton>
                      </Tooltip>
                      {protocol.step_count || 0}
                    </TableCell>
                    <TableCell align="right">
                      {protocol.default_duration_days ? `${protocol.default_duration_days} days` : '—'}
                    </TableCell>
                    <TableCell align="right">
                      {protocol.estimated_cost ? `$${parseFloat(protocol.estimated_cost).toFixed(2)}` : '—'}
                    </TableCell>
                    <TableCell align="center">
                      <Chip
                        size="small"
                        label={protocol.is_active ? 'Active' : 'Inactive'}
                        color={protocol.is_active ? 'success' : 'default'}
                      />
                    </TableCell>
                    <TableCell align="right">
                      <Tooltip title="Edit">
                        <IconButton size="small" onClick={() => handleOpenDialog(protocol)}>
                          <EditIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete">
                        <IconButton size="small" color="error" onClick={() => handleDeleteClick(protocol)}>
                          <DeleteIcon />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell colSpan={7} sx={{ py: 0, px: 2, border: 0 }}>
                      <Collapse in={expandedProtocol === protocol.id} timeout="auto">
                        <Box sx={{ py: 2 }}>
                          <Typography variant="subtitle2" gutterBottom>
                            Protocol Steps:
                          </Typography>
                          {protocol.steps && protocol.steps.length > 0 ? (
                            <List dense>
                              {protocol.steps.map((step) => (
                                <ListItem key={step.id}>
                                  <ListItemText
                                    primary={`${step.step_number}. ${step.title}`}
                                    secondary={
                                      <>
                                        {step.description && <div>{step.description}</div>}
                                        <div>
                                          Day {step.day_offset}
                                          {step.estimated_duration_minutes && ` • ${step.estimated_duration_minutes} min`}
                                          {step.estimated_cost && ` • $${parseFloat(step.estimated_cost).toFixed(2)}`}
                                        </div>
                                      </>
                                    }
                                  />
                                </ListItem>
                              ))}
                            </List>
                          ) : (
                            <Typography color="text.secondary">No steps defined</Typography>
                          )}
                        </Box>
                      </Collapse>
                    </TableCell>
                  </TableRow>
                </React.Fragment>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Create/Edit Dialog */}
      <Dialog
        open={dialogOpen}
        onClose={handleCloseDialog}
        maxWidth="md"
        fullWidth
        fullScreen={isMobile}
      >
        <DialogTitle>
          {editingProtocol ? 'Edit Protocol' : 'Create New Protocol'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Protocol Name"
                  value={formData.name}
                  onChange={(e) => handleFormChange('name', e.target.value)}
                  required
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Category</InputLabel>
                  <Select
                    value={formData.category}
                    label="Category"
                    onChange={(e) => handleFormChange('category', e.target.value)}
                  >
                    {categories.map((cat) => (
                      <MenuItem key={cat} value={cat}>
                        {cat.replace('_', ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Status</InputLabel>
                  <Select
                    value={formData.is_active}
                    label="Status"
                    onChange={(e) => handleFormChange('is_active', e.target.value)}
                  >
                    <MenuItem value={true}>Active</MenuItem>
                    <MenuItem value={false}>Inactive</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Description"
                  value={formData.description}
                  onChange={(e) => handleFormChange('description', e.target.value)}
                  multiline
                  rows={2}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  type="number"
                  label="Default Duration (days)"
                  value={formData.default_duration_days}
                  onChange={(e) => handleFormChange('default_duration_days', e.target.value)}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  type="number"
                  label="Estimated Cost ($)"
                  value={formData.estimated_cost}
                  onChange={(e) => handleFormChange('estimated_cost', e.target.value)}
                  inputProps={{ step: '0.01' }}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Indications"
                  value={formData.indications}
                  onChange={(e) => handleFormChange('indications', e.target.value)}
                  multiline
                  rows={2}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Contraindications"
                  value={formData.contraindications}
                  onChange={(e) => handleFormChange('contraindications', e.target.value)}
                  multiline
                  rows={2}
                />
              </Grid>

              {/* Protocol Steps */}
              <Grid item xs={12}>
                <Divider sx={{ my: 2 }} />
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6">Protocol Steps</Typography>
                  <Button
                    startIcon={<AddStepIcon />}
                    onClick={handleAddStep}
                    variant="outlined"
                    size="small"
                  >
                    Add Step
                  </Button>
                </Box>

                {formData.steps.length === 0 ? (
                  <Alert severity="info">
                    Add at least one step to this protocol. Steps will be executed in order when applied to a patient.
                  </Alert>
                ) : (
                  formData.steps.map((step, index) => (
                    <Paper key={index} sx={{ p: 2, mb: 2, position: 'relative' }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 2 }}>
                        <Typography variant="subtitle2">Step {index + 1}</Typography>
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleRemoveStep(index)}
                        >
                          <RemoveStepIcon />
                        </IconButton>
                      </Box>
                      <Grid container spacing={2}>
                        <Grid item xs={12}>
                          <TextField
                            fullWidth
                            label="Step Title"
                            value={step.title}
                            onChange={(e) => handleStepChange(index, 'title', e.target.value)}
                            required
                          />
                        </Grid>
                        <Grid item xs={12}>
                          <TextField
                            fullWidth
                            label="Description"
                            value={step.description}
                            onChange={(e) => handleStepChange(index, 'description', e.target.value)}
                            multiline
                            rows={2}
                          />
                        </Grid>
                        <Grid item xs={12} md={4}>
                          <TextField
                            fullWidth
                            type="number"
                            label="Day Offset"
                            value={step.day_offset}
                            onChange={(e) => handleStepChange(index, 'day_offset', e.target.value)}
                            helperText="Days from plan start"
                          />
                        </Grid>
                        <Grid item xs={12} md={4}>
                          <TextField
                            fullWidth
                            type="number"
                            label="Duration (minutes)"
                            value={step.estimated_duration_minutes}
                            onChange={(e) => handleStepChange(index, 'estimated_duration_minutes', e.target.value)}
                          />
                        </Grid>
                        <Grid item xs={12} md={4}>
                          <TextField
                            fullWidth
                            type="number"
                            label="Cost ($)"
                            value={step.estimated_cost}
                            onChange={(e) => handleStepChange(index, 'estimated_cost', e.target.value)}
                            inputProps={{ step: '0.01' }}
                          />
                        </Grid>
                      </Grid>
                    </Paper>
                  ))
                )}
              </Grid>
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={saveMutation.isLoading}
          >
            {saveMutation.isLoading ? <CircularProgress size={24} /> : editingProtocol ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        open={deleteDialog.open}
        title="Delete Protocol"
        message={`Are you sure you want to delete "${deleteDialog.protocolName}"? This action cannot be undone.`}
        onConfirm={handleDeleteConfirm}
        onCancel={() => setDeleteDialog({ open: false, protocolId: null, protocolName: '' })}
        confirmText="Delete"
        cancelText="Cancel"
        isLoading={deleteMutation.isLoading}
      />
    </Box>
  );
}

export default ProtocolLibrary;
