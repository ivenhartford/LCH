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
  Search as SearchIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import logger from '../utils/logger';

/**
 * Products Component
 *
 * Manages product inventory for medications, supplies, and retail items.
 */
function Products() {
  const queryClient = useQueryClient();

  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [activeFilter, setActiveFilter] = useState('true');
  const [lowStockOnly, setLowStockOnly] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    sku: '',
    category: 'supply',
    unit: 'each',
    unit_cost: '',
    unit_price: '',
    quantity_in_stock: 0,
    reorder_point: 10,
    reorder_quantity: 50,
    vendor_id: '',
    is_active: true,
  });

  useEffect(() => {
    logger.logLifecycle('Products', 'mounted');
    return () => logger.logLifecycle('Products', 'unmounted');
  }, []);

  // Fetch vendors for the dropdown
  const { data: vendorsData } = useQuery({
    queryKey: ['vendors'],
    queryFn: async () => {
      const response = await fetch('/api/vendors?is_active=true', { credentials: 'include' });
      if (!response.ok) throw new Error('Failed to fetch vendors');
      return response.json();
    },
  });

  // Fetch products
  const {
    data: productsData,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['products', categoryFilter, activeFilter],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (categoryFilter) params.append('category', categoryFilter);
      if (activeFilter) params.append('is_active', activeFilter);

      const response = await fetch(`/api/products?${params}`, { credentials: 'include' });
      if (!response.ok) throw new Error('Failed to fetch products');
      return response.json();
    },
  });

  // Fetch low stock products
  const { data: lowStockData } = useQuery({
    queryKey: ['products-low-stock'],
    queryFn: async () => {
      const response = await fetch('/api/products/low-stock', { credentials: 'include' });
      if (!response.ok) throw new Error('Failed to fetch low stock products');
      return response.json();
    },
  });

  const saveMutation = useMutation({
    mutationFn: async (data) => {
      const url = editingProduct ? `/api/products/${editingProduct.id}` : '/api/products';
      const response = await fetch(url, {
        method: editingProduct ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(data),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to save product');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['products']);
      queryClient.invalidateQueries(['products-low-stock']);
      handleCloseDialog();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (productId) => {
      const response = await fetch(`/api/products/${productId}`, {
        method: 'DELETE',
        credentials: 'include',
      });
      if (!response.ok) throw new Error('Failed to delete product');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['products']);
      queryClient.invalidateQueries(['products-low-stock']);
    },
  });

  const handleOpenDialog = (product = null) => {
    if (product) {
      setEditingProduct(product);
      setFormData({
        name: product.name || '',
        description: product.description || '',
        sku: product.sku || '',
        category: product.category || 'supply',
        unit: product.unit || 'each',
        unit_cost: product.unit_cost || '',
        unit_price: product.unit_price || '',
        quantity_in_stock: product.quantity_in_stock || 0,
        reorder_point: product.reorder_point || 10,
        reorder_quantity: product.reorder_quantity || 50,
        vendor_id: product.vendor_id || '',
        is_active: product.is_active ?? true,
      });
    } else {
      setEditingProduct(null);
      setFormData({
        name: '',
        description: '',
        sku: '',
        category: 'supply',
        unit: 'each',
        unit_cost: '',
        unit_price: '',
        quantity_in_stock: 0,
        reorder_point: 10,
        reorder_quantity: 50,
        vendor_id: '',
        is_active: true,
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingProduct(null);
  };

  const handleSubmit = () => {
    saveMutation.mutate(formData);
  };

  const handleDelete = (productId, name) => {
    if (window.confirm(`Delete ${name}? This will soft-delete the product.`)) {
      deleteMutation.mutate(productId);
    }
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
        <Alert severity="error">Failed to load products: {error.message}</Alert>
      </Box>
    );
  }

  const products = productsData?.products || [];
  const lowStockProducts = lowStockData?.products || [];
  const lowStockIds = new Set(lowStockProducts.map((p) => p.id));

  let displayProducts = products;

  // Apply low stock filter
  if (lowStockOnly) {
    displayProducts = products.filter((p) => lowStockIds.has(p.id));
  }

  // Apply search filter
  displayProducts = displayProducts.filter((p) =>
    p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (p.sku && p.sku.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const vendors = vendorsData?.vendors || [];

  const getCategoryColor = (category) => {
    switch (category) {
      case 'medication':
        return 'error';
      case 'supply':
        return 'primary';
      case 'retail':
        return 'success';
      default:
        return 'default';
    }
  };

  const isLowStock = (product) => {
    return product.quantity_in_stock <= product.reorder_point;
  };

  return (
    <Box>
      <Box mb={3} display="flex" justifyContent="space-between" alignItems="center">
        <Box>
          <Typography variant="h4">Product Inventory</Typography>
          {lowStockProducts.length > 0 && (
            <Alert severity="warning" sx={{ mt: 1 }}>
              <WarningIcon sx={{ mr: 1 }} />
              {lowStockProducts.length} product{lowStockProducts.length !== 1 ? 's' : ''} low on stock
            </Alert>
          )}
        </Box>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => handleOpenDialog()}>
          Add Product
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
              placeholder="Name or SKU"
              InputProps={{ startAdornment: <SearchIcon color="action" sx={{ mr: 1 }} /> }}
            />
          </Grid>
          <Grid item xs={12} sm={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Category</InputLabel>
              <Select
                value={categoryFilter}
                label="Category"
                onChange={(e) => setCategoryFilter(e.target.value)}
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="medication">Medication</MenuItem>
                <MenuItem value="supply">Supply</MenuItem>
                <MenuItem value="retail">Retail</MenuItem>
              </Select>
            </FormControl>
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
          <Grid item xs={12} sm={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Stock Level</InputLabel>
              <Select
                value={lowStockOnly ? 'low' : 'all'}
                label="Stock Level"
                onChange={(e) => setLowStockOnly(e.target.value === 'low')}
              >
                <MenuItem value="all">All</MenuItem>
                <MenuItem value="low">Low Stock Only</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>

      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Product</TableCell>
                <TableCell>SKU</TableCell>
                <TableCell>Category</TableCell>
                <TableCell>Vendor</TableCell>
                <TableCell align="right">In Stock</TableCell>
                <TableCell align="right">Unit Cost</TableCell>
                <TableCell align="right">Unit Price</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {displayProducts.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} align="center">
                    <Typography variant="body2" color="text.secondary" py={4}>
                      No products found.
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                displayProducts.map((product) => (
                  <TableRow
                    key={product.id}
                    hover
                    sx={{
                      backgroundColor: isLowStock(product) ? 'rgba(255, 152, 0, 0.08)' : 'inherit',
                    }}
                  >
                    <TableCell>
                      <Box display="flex" alignItems="center" gap={1}>
                        {isLowStock(product) && (
                          <Tooltip title="Low Stock">
                            <WarningIcon color="warning" fontSize="small" />
                          </Tooltip>
                        )}
                        <Box>
                          <Typography variant="body2" fontWeight="medium">
                            {product.name}
                          </Typography>
                          {product.description && (
                            <Typography variant="caption" color="text.secondary">
                              {product.description}
                            </Typography>
                          )}
                        </Box>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" fontFamily="monospace">
                        {product.sku || '-'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={product.category}
                        size="small"
                        color={getCategoryColor(product.category)}
                      />
                    </TableCell>
                    <TableCell>
                      {product.vendor_name || '-'}
                    </TableCell>
                    <TableCell align="right">
                      <Typography
                        variant="body2"
                        color={isLowStock(product) ? 'warning.main' : 'inherit'}
                        fontWeight={isLowStock(product) ? 'bold' : 'normal'}
                      >
                        {product.quantity_in_stock} {product.unit}
                      </Typography>
                      {isLowStock(product) && (
                        <Typography variant="caption" color="text.secondary">
                          Reorder at {product.reorder_point}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell align="right">
                      ${parseFloat(product.unit_cost || 0).toFixed(2)}
                    </TableCell>
                    <TableCell align="right">
                      ${parseFloat(product.unit_price || 0).toFixed(2)}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={product.is_active ? 'Active' : 'Inactive'}
                        color={product.is_active ? 'success' : 'default'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell align="right">
                      <Tooltip title="Edit">
                        <IconButton size="small" onClick={() => handleOpenDialog(product)}>
                          <EditIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete">
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleDelete(product.id, product.name)}
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
            Total: {displayProducts.length} products
            {lowStockProducts.length > 0 &&
              ` (${lowStockProducts.length} low stock)`}
          </Typography>
        </Box>
      </Paper>

      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>{editingProduct ? 'Edit Product' : 'Add Product'}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 0.5 }}>
            <Grid item xs={12} sm={8}>
              <TextField
                fullWidth
                required
                label="Product Name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="SKU"
                value={formData.sku}
                onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
                placeholder="e.g., MED-001"
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
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth required>
                <InputLabel>Category</InputLabel>
                <Select
                  value={formData.category}
                  label="Category"
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                >
                  <MenuItem value="medication">Medication</MenuItem>
                  <MenuItem value="supply">Supply</MenuItem>
                  <MenuItem value="retail">Retail</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                required
                label="Unit"
                value={formData.unit}
                onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
                placeholder="e.g., each, box, ml"
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <InputLabel>Vendor</InputLabel>
                <Select
                  value={formData.vendor_id}
                  label="Vendor"
                  onChange={(e) => setFormData({ ...formData, vendor_id: e.target.value })}
                >
                  <MenuItem value="">None</MenuItem>
                  {vendors.map((vendor) => (
                    <MenuItem key={vendor.id} value={vendor.id}>
                      {vendor.company_name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                required
                type="number"
                label="Unit Cost"
                value={formData.unit_cost}
                onChange={(e) => setFormData({ ...formData, unit_cost: e.target.value })}
                InputProps={{ startAdornment: '$' }}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                required
                type="number"
                label="Unit Price"
                value={formData.unit_price}
                onChange={(e) => setFormData({ ...formData, unit_price: e.target.value })}
                InputProps={{ startAdornment: '$' }}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                required
                type="number"
                label="Quantity in Stock"
                value={formData.quantity_in_stock}
                onChange={(e) => setFormData({ ...formData, quantity_in_stock: parseInt(e.target.value) || 0 })}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                required
                type="number"
                label="Reorder Point"
                value={formData.reorder_point}
                onChange={(e) => setFormData({ ...formData, reorder_point: parseInt(e.target.value) || 0 })}
                helperText="Alert when stock reaches this level"
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                required
                type="number"
                label="Reorder Quantity"
                value={formData.reorder_quantity}
                onChange={(e) => setFormData({ ...formData, reorder_quantity: parseInt(e.target.value) || 0 })}
                helperText="Suggested reorder amount"
              />
            </Grid>
            <Grid item xs={12} sm={4}>
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
            disabled={
              saveMutation.isLoading ||
              !formData.name ||
              !formData.unit ||
              !formData.unit_cost ||
              !formData.unit_price
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
    </Box>
  );
}

export default Products;
