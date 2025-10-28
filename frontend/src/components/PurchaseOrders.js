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
  Divider,
  Card,
  CardContent,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Visibility as VisibilityIcon,
  CheckCircle as CheckCircleIcon,
  RemoveCircle as RemoveIcon,
  AddCircle as AddCircleIcon,
} from '@mui/icons-material';
import logger from '../utils/logger';

/**
 * Purchase Orders Component
 *
 * Manages purchase orders for inventory replenishment.
 */
function PurchaseOrders() {
  const queryClient = useQueryClient();

  const [statusFilter, setStatusFilter] = useState('');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [receiveDialogOpen, setReceiveDialogOpen] = useState(false);
  const [selectedPO, setSelectedPO] = useState(null);
  const [formData, setFormData] = useState({
    vendor_id: '',
    notes: '',
    items: [{ product_id: '', quantity: 1, unit_cost: '' }],
  });

  useEffect(() => {
    logger.logLifecycle('PurchaseOrders', 'mounted');
    return () => logger.logLifecycle('PurchaseOrders', 'unmounted');
  }, []);

  // Fetch vendors
  const { data: vendorsData } = useQuery({
    queryKey: ['vendors-active'],
    queryFn: async () => {
      const response = await fetch('/api/vendors?is_active=true', { credentials: 'include' });
      if (!response.ok) throw new Error('Failed to fetch vendors');
      return response.json();
    },
  });

  // Fetch products
  const { data: productsData } = useQuery({
    queryKey: ['products-active'],
    queryFn: async () => {
      const response = await fetch('/api/products?is_active=true', { credentials: 'include' });
      if (!response.ok) throw new Error('Failed to fetch products');
      return response.json();
    },
  });

  // Fetch purchase orders
  const {
    data: posData,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['purchase-orders', statusFilter],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (statusFilter) params.append('status', statusFilter);

      const response = await fetch(`/api/purchase-orders?${params}`, { credentials: 'include' });
      if (!response.ok) throw new Error('Failed to fetch purchase orders');
      return response.json();
    },
  });

  const createMutation = useMutation({
    mutationFn: async (data) => {
      const response = await fetch('/api/purchase-orders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(data),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to create purchase order');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['purchase-orders']);
      setCreateDialogOpen(false);
      setFormData({
        vendor_id: '',
        notes: '',
        items: [{ product_id: '', quantity: 1, unit_cost: '' }],
      });
    },
  });

  const receiveMutation = useMutation({
    mutationFn: async (poId) => {
      const response = await fetch(`/api/purchase-orders/${poId}/receive`, {
        method: 'POST',
        credentials: 'include',
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to receive purchase order');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['purchase-orders']);
      queryClient.invalidateQueries(['products']);
      queryClient.invalidateQueries(['inventory-transactions']);
      setReceiveDialogOpen(false);
    },
  });

  const handleViewDetails = async (poId) => {
    try {
      const response = await fetch(`/api/purchase-orders/${poId}`, { credentials: 'include' });
      if (!response.ok) throw new Error('Failed to fetch PO details');
      const data = await response.json();
      setSelectedPO(data.purchase_order);
      setDetailDialogOpen(true);
    } catch (err) {
      logger.logError('PurchaseOrders', 'Failed to load PO details', { error: err.message });
    }
  };

  const handleReceivePO = (po) => {
    setSelectedPO(po);
    setReceiveDialogOpen(true);
  };

  const confirmReceive = () => {
    if (selectedPO) {
      receiveMutation.mutate(selectedPO.id);
    }
  };

  const handleAddItem = () => {
    setFormData({
      ...formData,
      items: [...formData.items, { product_id: '', quantity: 1, unit_cost: '' }],
    });
  };

  const handleRemoveItem = (index) => {
    const newItems = formData.items.filter((_, i) => i !== index);
    setFormData({ ...formData, items: newItems });
  };

  const handleItemChange = (index, field, value) => {
    const newItems = [...formData.items];
    newItems[index][field] = value;

    // Auto-fill unit cost when product is selected
    if (field === 'product_id' && value) {
      const product = products.find((p) => p.id === parseInt(value));
      if (product) {
        newItems[index].unit_cost = product.unit_cost;
      }
    }

    setFormData({ ...formData, items: newItems });
  };

  const handleSubmit = () => {
    createMutation.mutate(formData);
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
        <Alert severity="error">Failed to load purchase orders: {error.message}</Alert>
      </Box>
    );
  }

  const purchaseOrders = posData?.purchase_orders || [];
  const vendors = vendorsData?.vendors || [];
  const products = productsData?.products || [];

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending':
        return 'warning';
      case 'ordered':
        return 'info';
      case 'received':
        return 'success';
      case 'cancelled':
        return 'error';
      default:
        return 'default';
    }
  };

  const calculateTotal = (items) => {
    return items.reduce((sum, item) => {
      const cost = parseFloat(item.unit_cost || 0);
      const qty = parseInt(item.quantity || 0);
      return sum + cost * qty;
    }, 0);
  };

  return (
    <Box>
      <Box mb={3} display="flex" justifyContent="space-between" alignItems="center">
        <Typography variant="h4">Purchase Orders</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateDialogOpen(true)}
        >
          Create Purchase Order
        </Button>
      </Box>

      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={4}>
            <FormControl fullWidth size="small">
              <InputLabel>Status</InputLabel>
              <Select
                value={statusFilter}
                label="Status"
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="pending">Pending</MenuItem>
                <MenuItem value="ordered">Ordered</MenuItem>
                <MenuItem value="received">Received</MenuItem>
                <MenuItem value="cancelled">Cancelled</MenuItem>
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
                <TableCell>PO Number</TableCell>
                <TableCell>Vendor</TableCell>
                <TableCell>Order Date</TableCell>
                <TableCell align="right">Total</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {purchaseOrders.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    <Typography variant="body2" color="text.secondary" py={4}>
                      No purchase orders found.
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                purchaseOrders.map((po) => (
                  <TableRow key={po.id} hover>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium" fontFamily="monospace">
                        {po.order_number}
                      </Typography>
                    </TableCell>
                    <TableCell>{po.vendor_name}</TableCell>
                    <TableCell>
                      {new Date(po.order_date).toLocaleDateString()}
                    </TableCell>
                    <TableCell align="right">
                      ${parseFloat(po.total_amount || 0).toFixed(2)}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={po.status}
                        size="small"
                        color={getStatusColor(po.status)}
                      />
                    </TableCell>
                    <TableCell align="right">
                      <Tooltip title="View Details">
                        <IconButton size="small" onClick={() => handleViewDetails(po.id)}>
                          <VisibilityIcon />
                        </IconButton>
                      </Tooltip>
                      {po.status === 'ordered' && (
                        <Tooltip title="Receive Order">
                          <IconButton
                            size="small"
                            color="success"
                            onClick={() => handleReceivePO(po)}
                          >
                            <CheckCircleIcon />
                          </IconButton>
                        </Tooltip>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
        <Box p={2}>
          <Typography variant="body2" color="text.secondary">
            Total: {purchaseOrders.length} purchase orders
          </Typography>
        </Box>
      </Paper>

      {/* Create PO Dialog */}
      <Dialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Create Purchase Order</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 0.5 }}>
            <Grid item xs={12}>
              <FormControl fullWidth required>
                <InputLabel>Vendor</InputLabel>
                <Select
                  value={formData.vendor_id}
                  label="Vendor"
                  onChange={(e) => setFormData({ ...formData, vendor_id: e.target.value })}
                >
                  <MenuItem value="">Select Vendor</MenuItem>
                  {vendors.map((vendor) => (
                    <MenuItem key={vendor.id} value={vendor.id}>
                      {vendor.company_name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12}>
              <Divider>
                <Typography variant="body2" color="text.secondary">
                  Order Items
                </Typography>
              </Divider>
            </Grid>

            {formData.items.map((item, index) => (
              <Grid item xs={12} key={index}>
                <Card variant="outlined">
                  <CardContent>
                    <Grid container spacing={2} alignItems="center">
                      <Grid item xs={12} sm={5}>
                        <FormControl fullWidth required size="small">
                          <InputLabel>Product</InputLabel>
                          <Select
                            value={item.product_id}
                            label="Product"
                            onChange={(e) => handleItemChange(index, 'product_id', e.target.value)}
                          >
                            <MenuItem value="">Select Product</MenuItem>
                            {products.map((product) => (
                              <MenuItem key={product.id} value={product.id}>
                                {product.name} - {product.sku || 'No SKU'}
                              </MenuItem>
                            ))}
                          </Select>
                        </FormControl>
                      </Grid>
                      <Grid item xs={12} sm={3}>
                        <TextField
                          fullWidth
                          required
                          size="small"
                          type="number"
                          label="Quantity"
                          value={item.quantity}
                          onChange={(e) => handleItemChange(index, 'quantity', parseInt(e.target.value) || 0)}
                        />
                      </Grid>
                      <Grid item xs={12} sm={3}>
                        <TextField
                          fullWidth
                          required
                          size="small"
                          type="number"
                          label="Unit Cost"
                          value={item.unit_cost}
                          onChange={(e) => handleItemChange(index, 'unit_cost', e.target.value)}
                          InputProps={{ startAdornment: '$' }}
                        />
                      </Grid>
                      <Grid item xs={12} sm={1}>
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleRemoveItem(index)}
                          disabled={formData.items.length === 1}
                        >
                          <RemoveIcon />
                        </IconButton>
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              </Grid>
            ))}

            <Grid item xs={12}>
              <Button
                startIcon={<AddCircleIcon />}
                onClick={handleAddItem}
                variant="outlined"
                fullWidth
              >
                Add Item
              </Button>
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Notes"
                multiline
                rows={2}
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                placeholder="Delivery instructions, payment terms, etc."
              />
            </Grid>

            <Grid item xs={12}>
              <Divider />
              <Box mt={2} display="flex" justifyContent="space-between">
                <Typography variant="h6">Total:</Typography>
                <Typography variant="h6">
                  ${calculateTotal(formData.items).toFixed(2)}
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={
              createMutation.isLoading ||
              !formData.vendor_id ||
              formData.items.some((item) => !item.product_id || !item.quantity || !item.unit_cost)
            }
          >
            {createMutation.isLoading ? <CircularProgress size={24} /> : 'Create Order'}
          </Button>
        </DialogActions>
        {createMutation.isError && (
          <Alert severity="error" sx={{ m: 2 }}>
            {createMutation.error.message}
          </Alert>
        )}
      </Dialog>

      {/* PO Details Dialog */}
      <Dialog
        open={detailDialogOpen}
        onClose={() => setDetailDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        {selectedPO && (
          <>
            <DialogTitle>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Typography variant="h6">PO {selectedPO.order_number}</Typography>
                <Chip label={selectedPO.status} color={getStatusColor(selectedPO.status)} />
              </Box>
            </DialogTitle>
            <DialogContent>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Vendor
                  </Typography>
                  <Typography variant="body1">{selectedPO.vendor_name}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Order Date
                  </Typography>
                  <Typography variant="body1">
                    {new Date(selectedPO.order_date).toLocaleDateString()}
                  </Typography>
                </Grid>
                {selectedPO.received_date && (
                  <Grid item xs={12} sm={6}>
                    <Typography variant="body2" color="text.secondary">
                      Received Date
                    </Typography>
                    <Typography variant="body1">
                      {new Date(selectedPO.received_date).toLocaleDateString()}
                    </Typography>
                  </Grid>
                )}
                {selectedPO.notes && (
                  <Grid item xs={12}>
                    <Typography variant="body2" color="text.secondary">
                      Notes
                    </Typography>
                    <Typography variant="body1">{selectedPO.notes}</Typography>
                  </Grid>
                )}
                <Grid item xs={12}>
                  <Divider sx={{ my: 1 }} />
                  <Typography variant="h6" gutterBottom>
                    Order Items
                  </Typography>
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Product</TableCell>
                          <TableCell align="right">Quantity</TableCell>
                          <TableCell align="right">Unit Cost</TableCell>
                          <TableCell align="right">Subtotal</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {selectedPO.items?.map((item) => (
                          <TableRow key={item.id}>
                            <TableCell>{item.product_name}</TableCell>
                            <TableCell align="right">{item.quantity}</TableCell>
                            <TableCell align="right">
                              ${parseFloat(item.unit_cost).toFixed(2)}
                            </TableCell>
                            <TableCell align="right">
                              ${(parseFloat(item.unit_cost) * parseInt(item.quantity)).toFixed(2)}
                            </TableCell>
                          </TableRow>
                        ))}
                        <TableRow>
                          <TableCell colSpan={3} align="right">
                            <Typography variant="subtitle1" fontWeight="bold">
                              Total:
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="subtitle1" fontWeight="bold">
                              ${parseFloat(selectedPO.total_amount).toFixed(2)}
                            </Typography>
                          </TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Grid>
              </Grid>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setDetailDialogOpen(false)}>Close</Button>
              {selectedPO.status === 'ordered' && (
                <Button
                  variant="contained"
                  color="success"
                  startIcon={<CheckCircleIcon />}
                  onClick={() => {
                    setDetailDialogOpen(false);
                    handleReceivePO(selectedPO);
                  }}
                >
                  Receive Order
                </Button>
              )}
            </DialogActions>
          </>
        )}
      </Dialog>

      {/* Receive PO Dialog */}
      <Dialog
        open={receiveDialogOpen}
        onClose={() => setReceiveDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Receive Purchase Order</DialogTitle>
        <DialogContent>
          {selectedPO && (
            <Box>
              <Alert severity="info" sx={{ mb: 2 }}>
                This will mark the purchase order as received and update inventory quantities for all
                products in this order.
              </Alert>
              <Typography variant="body1" gutterBottom>
                <strong>PO Number:</strong> {selectedPO.order_number}
              </Typography>
              <Typography variant="body1" gutterBottom>
                <strong>Vendor:</strong> {selectedPO.vendor_name}
              </Typography>
              <Typography variant="body1" gutterBottom>
                <strong>Total Amount:</strong> ${parseFloat(selectedPO.total_amount).toFixed(2)}
              </Typography>
              <Typography variant="body1" gutterBottom>
                <strong>Items:</strong> {selectedPO.items?.length || 0}
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setReceiveDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={confirmReceive}
            variant="contained"
            color="success"
            disabled={receiveMutation.isLoading}
          >
            {receiveMutation.isLoading ? <CircularProgress size={24} /> : 'Confirm Receipt'}
          </Button>
        </DialogActions>
        {receiveMutation.isError && (
          <Alert severity="error" sx={{ m: 2 }}>
            {receiveMutation.error.message}
          </Alert>
        )}
      </Dialog>
    </Box>
  );
}

export default PurchaseOrders;
