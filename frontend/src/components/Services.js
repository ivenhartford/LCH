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
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
  AttachMoney as MoneyIcon,
  Category as CategoryIcon,
  ChevronRight as ChevronRightIcon,
} from '@mui/icons-material';
import logger from '../utils/logger';
import ConfirmDialog from './common/ConfirmDialog';
import TableSkeleton from './common/TableSkeleton';
import EmptyState from './common/EmptyState';
import { useNotification } from '../contexts/NotificationContext';

/**
 * Services Catalog Component
 *
 * Manages billable services and products for invoicing.
 */
function Services() {
  const queryClient = useQueryClient();
  const { showNotification } = useNotification();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const [searchTerm, setSearchTerm] = useState('');
  const [activeFilter, setActiveFilter] = useState('true');
  const [typeFilter, setTypeFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingService, setEditingService] = useState(null);
  const [deleteDialog, setDeleteDialog] = useState({ open: false, serviceId: null, serviceName: '' });
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    category: '',
    service_type: 'service',
    unit_price: '',
    cost: '',
    taxable: true,
    is_active: true,
  });

  useEffect(() => {
    logger.logLifecycle('Services', 'mounted');
    return () => logger.logLifecycle('Services', 'unmounted');
  }, []);

  const {
    data: servicesData,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['services', activeFilter, typeFilter, categoryFilter],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (activeFilter) params.append('is_active', activeFilter);
      if (typeFilter) params.append('service_type', typeFilter);
      if (categoryFilter) params.append('category', categoryFilter);

      const response = await fetch(`/api/services?${params}`, { credentials: 'include' });
      if (!response.ok) throw new Error('Failed to fetch services');
      return response.json();
    },
  });

  const saveMutation = useMutation({
    mutationFn: async (data) => {
      const url = editingService ? `/api/services/${editingService.id}` : '/api/services';
      const response = await fetch(url, {
        method: editingService ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(data),
      });
      if (!response.ok) throw new Error('Failed to save service');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['services']);
      handleCloseDialog();
      showNotification(
        editingService ? 'Service updated successfully' : 'Service created successfully',
        'success'
      );
    },
    onError: (error) => {
      showNotification(error.message || 'Failed to save service', 'error');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (serviceId) => {
      const response = await fetch(`/api/services/${serviceId}`, {
        method: 'DELETE',
        credentials: 'include',
      });
      if (!response.ok) throw new Error('Failed to delete service');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['services']);
      showNotification('Service deleted successfully', 'success');
    },
    onError: (error) => {
      showNotification(error.message || 'Failed to delete service', 'error');
    },
  });

  const handleOpenDialog = (service = null) => {
    if (service) {
      setEditingService(service);
      setFormData({
        name: service.name || '',
        description: service.description || '',
        category: service.category || '',
        service_type: service.service_type || 'service',
        unit_price: service.unit_price || '',
        cost: service.cost || '',
        taxable: service.taxable ?? true,
        is_active: service.is_active ?? true,
      });
    } else {
      setEditingService(null);
      setFormData({
        name: '',
        description: '',
        category: '',
        service_type: 'service',
        unit_price: '',
        cost: '',
        taxable: true,
        is_active: true,
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingService(null);
  };

  const handleSubmit = () => {
    saveMutation.mutate(formData);
  };

  const handleDelete = (serviceId, name) => {
    setDeleteDialog({ open: true, serviceId, serviceName: name });
  };

  const handleDeleteConfirm = () => {
    deleteMutation.mutate(deleteDialog.serviceId);
    setDeleteDialog({ open: false, serviceId: null, serviceName: '' });
  };

  const handleDeleteCancel = () => {
    setDeleteDialog({ open: false, serviceId: null, serviceName: '' });
  };

  if (isLoading) {
    return (
      <Box>
        <Typography variant="h4" gutterBottom>
          Services Catalog
        </Typography>
        <TableSkeleton
          rows={10}
          columns={7}
          headers={['Name', 'Category', 'Type', 'Price', 'Cost', 'Taxable', 'Status']}
        />
      </Box>
    );
  }

  if (isError) {
    return (
      <Box p={3}>
        <Alert severity="error">Failed to load services: {error.message}</Alert>
      </Box>
    );
  }

  const services = servicesData?.services || [];
  const filteredServices = services.filter((s) =>
    s.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <Box>
      <Box mb={3} display="flex" justifyContent="space-between" alignItems="center">
        <Typography variant="h4">Service Catalog</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => handleOpenDialog()}>
          Add Service
        </Button>
      </Box>

      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={4}>
            <TextField
              fullWidth
              size="small"
              label="Search"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{ startAdornment: <SearchIcon color="action" sx={{ mr: 1 }} /> }}
            />
          </Grid>
          <Grid item xs={12} sm={2}>
            <FormControl fullWidth size="small">
              <InputLabel>Type</InputLabel>
              <Select
                value={typeFilter}
                label="Type"
                onChange={(e) => setTypeFilter(e.target.value)}
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="service">Service</MenuItem>
                <MenuItem value="product">Product</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={3}>
            <TextField
              fullWidth
              size="small"
              label="Category"
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
            />
          </Grid>
          <Grid item xs={12} sm={2}>
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
        </Grid>
      </Paper>

      {/* Empty State or Service List */}
      {filteredServices.length === 0 ? (
        <EmptyState
          icon={searchTerm || activeFilter || typeFilter || categoryFilter ? SearchIcon : AddIcon}
          title={
            searchTerm || activeFilter || typeFilter || categoryFilter
              ? 'No Services Found'
              : 'No Services Yet'
          }
          message={
            searchTerm || activeFilter || typeFilter || categoryFilter
              ? 'No services match your current search or filter criteria. Try adjusting your filters.'
              : 'Get started by adding your first service or product to the catalog. Services can be used for creating invoices and tracking revenue.'
          }
          actionLabel={
            searchTerm || activeFilter || typeFilter || categoryFilter ? 'Clear Filters' : 'Add Service'
          }
          onAction={
            searchTerm || activeFilter || typeFilter || categoryFilter
              ? () => {
                  setSearchTerm('');
                  setActiveFilter('true');
                  setTypeFilter('');
                  setCategoryFilter('');
                }
              : () => handleOpenDialog()
          }
          actionIcon={searchTerm || activeFilter || typeFilter || categoryFilter ? undefined : AddIcon}
        />
      ) : isMobile ? (
        /* Mobile Card Layout */
        <>
          <Grid container spacing={2}>
            {filteredServices.map((service) => (
              <Grid item xs={12} key={service.id}>
                <Card>
                  <CardContent>
                    <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
                      <Box flex={1}>
                        <Typography variant="h6" component="h2">
                          {service.name}
                        </Typography>
                        {service.description && (
                          <Typography variant="body2" color="text.secondary" mt={0.5}>
                            {service.description}
                          </Typography>
                        )}
                      </Box>
                      <Box ml={2} display="flex" flexDirection="column" alignItems="flex-end" gap={0.5}>
                        <Chip
                          label={service.service_type}
                          size="small"
                          color={service.service_type === 'service' ? 'primary' : 'secondary'}
                        />
                        <Chip
                          label={service.is_active ? 'Active' : 'Inactive'}
                          color={service.is_active ? 'success' : 'default'}
                          size="small"
                        />
                      </Box>
                    </Box>

                    <Box display="flex" flexDirection="column" gap={1} mt={2}>
                      {service.category && (
                        <Box display="flex" alignItems="center" gap={1}>
                          <CategoryIcon fontSize="small" color="action" />
                          <Typography variant="body2" color="text.secondary">
                            {service.category}
                          </Typography>
                        </Box>
                      )}

                      <Box display="flex" alignItems="center" gap={1}>
                        <MoneyIcon fontSize="small" color="action" />
                        <Typography variant="body2" color="text.secondary">
                          Price: ${parseFloat(service.unit_price).toFixed(2)}
                          {service.cost && ` • Cost: $${parseFloat(service.cost).toFixed(2)}`}
                          {service.taxable && ' • Taxable'}
                        </Typography>
                      </Box>
                    </Box>
                  </CardContent>

                  <Divider />

                  <CardActions sx={{ justifyContent: 'space-between', px: 2 }}>
                    <Box display="flex" gap={1}>
                      <Button
                        size="small"
                        startIcon={<EditIcon />}
                        onClick={() => handleOpenDialog(service)}
                      >
                        Edit
                      </Button>
                      <Button
                        size="small"
                        color="error"
                        startIcon={<DeleteIcon />}
                        onClick={() => handleDelete(service.id, service.name)}
                      >
                        Delete
                      </Button>
                    </Box>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>

          <Box mt={2}>
            <Typography variant="body2" color="text.secondary">
              Total: {filteredServices.length} services
            </Typography>
          </Box>
        </>
      ) : (
        /* Desktop Table Layout */
        <Paper>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Category</TableCell>
                  <TableCell align="right">Price</TableCell>
                  <TableCell align="right">Cost</TableCell>
                  <TableCell>Taxable</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredServices.map((service) => (
                  <TableRow key={service.id} hover>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        {service.name}
                      </Typography>
                      {service.description && (
                        <Typography variant="caption" color="text.secondary">
                          {service.description}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={service.service_type}
                        size="small"
                        color={service.service_type === 'service' ? 'primary' : 'secondary'}
                      />
                    </TableCell>
                    <TableCell>{service.category || '-'}</TableCell>
                    <TableCell align="right">
                      ${parseFloat(service.unit_price).toFixed(2)}
                    </TableCell>
                    <TableCell align="right">
                      {service.cost ? `$${parseFloat(service.cost).toFixed(2)}` : '-'}
                    </TableCell>
                    <TableCell>{service.taxable ? 'Yes' : 'No'}</TableCell>
                    <TableCell>
                      <Chip
                        label={service.is_active ? 'Active' : 'Inactive'}
                        color={service.is_active ? 'success' : 'default'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell align="right">
                      <Tooltip title="Edit">
                        <IconButton size="small" onClick={() => handleOpenDialog(service)}>
                          <EditIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete">
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleDelete(service.id, service.name)}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          <Box p={2}>
            <Typography variant="body2" color="text.secondary">
              Total: {filteredServices.length} services
            </Typography>
          </Box>
        </Paper>
      )}

      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>{editingService ? 'Edit Service' : 'Add Service'}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 0.5 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                required
                label="Name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                multiline
                rows={2}
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Type</InputLabel>
                <Select
                  value={formData.service_type}
                  label="Type"
                  onChange={(e) => setFormData({ ...formData, service_type: e.target.value })}
                >
                  <MenuItem value="service">Service</MenuItem>
                  <MenuItem value="product">Product</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Category"
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                placeholder="e.g., Exam, Surgery, Lab"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                required
                type="number"
                label="Price"
                value={formData.unit_price}
                onChange={(e) => setFormData({ ...formData, unit_price: e.target.value })}
                InputProps={{ startAdornment: '$' }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                type="number"
                label="Cost"
                value={formData.cost}
                onChange={(e) => setFormData({ ...formData, cost: e.target.value })}
                InputProps={{ startAdornment: '$' }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth>
                <InputLabel>Taxable</InputLabel>
                <Select
                  value={formData.taxable}
                  label="Taxable"
                  onChange={(e) => setFormData({ ...formData, taxable: e.target.value })}
                >
                  <MenuItem value={true}>Yes</MenuItem>
                  <MenuItem value={false}>No</MenuItem>
                </Select>
              </FormControl>
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
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={saveMutation.isLoading || !formData.name || !formData.unit_price}
          >
            {saveMutation.isLoading ? <CircularProgress size={24} /> : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        open={deleteDialog.open}
        title="Delete Service"
        message={`Are you sure you want to delete "${deleteDialog.serviceName}"? This action cannot be undone.`}
        onConfirm={handleDeleteConfirm}
        onCancel={handleDeleteCancel}
        confirmText="Delete"
        confirmColor="error"
        loading={deleteMutation.isLoading}
      />
    </Box>
  );
}

export default Services;
