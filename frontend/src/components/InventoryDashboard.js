import React, { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Button,
  Divider,
} from '@mui/material';
import {
  Inventory as InventoryIcon,
  Warning as WarningIcon,
  ShoppingCart as ShoppingCartIcon,
  TrendingUp as TrendingUpIcon,
  LocalShipping as LocalShippingIcon,
} from '@mui/icons-material';
import logger from '../utils/logger';

/**
 * Inventory Dashboard Component
 *
 * Provides an overview of inventory status, low stock alerts, and recent activity.
 */
function InventoryDashboard() {
  const navigate = useNavigate();

  useEffect(() => {
    logger.logLifecycle('InventoryDashboard', 'mounted');
    return () => logger.logLifecycle('InventoryDashboard', 'unmounted');
  }, []);

  // Fetch all products for statistics
  const { data: productsData, isLoading: productsLoading } = useQuery({
    queryKey: ['products-all'],
    queryFn: async () => {
      const response = await fetch('/api/products?is_active=true', { credentials: 'include' });
      if (!response.ok) throw new Error('Failed to fetch products');
      return response.json();
    },
  });

  // Fetch low stock products
  const { data: lowStockData, isLoading: lowStockLoading } = useQuery({
    queryKey: ['products-low-stock'],
    queryFn: async () => {
      const response = await fetch('/api/products/low-stock', { credentials: 'include' });
      if (!response.ok) throw new Error('Failed to fetch low stock products');
      return response.json();
    },
  });

  // Fetch recent purchase orders
  const { data: posData, isLoading: posLoading } = useQuery({
    queryKey: ['purchase-orders-recent'],
    queryFn: async () => {
      const response = await fetch('/api/purchase-orders', { credentials: 'include' });
      if (!response.ok) throw new Error('Failed to fetch purchase orders');
      return response.json();
    },
  });

  // Fetch recent inventory transactions
  const { data: transactionsData, isLoading: transactionsLoading } = useQuery({
    queryKey: ['inventory-transactions-recent'],
    queryFn: async () => {
      const response = await fetch('/api/inventory-transactions', { credentials: 'include' });
      if (!response.ok) throw new Error('Failed to fetch transactions');
      return response.json();
    },
  });

  const isLoading = productsLoading || lowStockLoading || posLoading || transactionsLoading;

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  const products = productsData?.products || [];
  const lowStockProducts = lowStockData?.products || [];
  const purchaseOrders = posData?.purchase_orders || [];
  const transactions = transactionsData?.transactions || [];

  // Calculate statistics
  const totalProducts = products.length;
  const totalInventoryValue = products.reduce(
    (sum, p) => sum + parseFloat(p.unit_cost || 0) * parseInt(p.quantity_in_stock || 0),
    0
  );
  const pendingPOs = purchaseOrders.filter((po) => po.status === 'ordered').length;

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

  const getTransactionTypeColor = (type) => {
    switch (type) {
      case 'purchase':
        return 'success';
      case 'adjustment':
        return 'warning';
      case 'usage':
        return 'error';
      case 'return':
        return 'info';
      default:
        return 'default';
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Inventory Dashboard
      </Typography>

      {/* Key Metrics */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card aria-label={`Total products: ${totalProducts}`}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" variant="body2">
                    Total Products
                  </Typography>
                  <Typography variant="h4">{totalProducts}</Typography>
                </Box>
                <InventoryIcon sx={{ fontSize: 48, color: 'primary.main', opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card aria-label={`Low stock items: ${lowStockProducts.length}`}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" variant="body2">
                    Low Stock Items
                  </Typography>
                  <Typography variant="h4" color={lowStockProducts.length > 0 ? 'warning.main' : 'inherit'}>
                    {lowStockProducts.length}
                  </Typography>
                </Box>
                <WarningIcon sx={{ fontSize: 48, color: 'warning.main', opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card aria-label={`Pending orders: ${pendingPOs}`}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" variant="body2">
                    Pending Orders
                  </Typography>
                  <Typography variant="h4">{pendingPOs}</Typography>
                </Box>
                <ShoppingCartIcon sx={{ fontSize: 48, color: 'info.main', opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card aria-label={`Inventory value: $${totalInventoryValue.toFixed(0)}`}>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="text.secondary" variant="body2">
                    Inventory Value
                  </Typography>
                  <Typography variant="h4">${totalInventoryValue.toFixed(0)}</Typography>
                </Box>
                <TrendingUpIcon sx={{ fontSize: 48, color: 'success.main', opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Low Stock Alerts */}
      {lowStockProducts.length > 0 && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6" display="flex" alignItems="center" gap={1}>
              <WarningIcon color="warning" />
              Low Stock Alerts
            </Typography>
            <Button
              variant="outlined"
              size="small"
              onClick={() => navigate('/products')}
              aria-label="View all products"
            >
              View All Products
            </Button>
          </Box>
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Product</TableCell>
                  <TableCell>Category</TableCell>
                  <TableCell align="right">In Stock</TableCell>
                  <TableCell align="right">Reorder Point</TableCell>
                  <TableCell align="right">Suggested Order</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {lowStockProducts.slice(0, 5).map((product) => (
                  <TableRow key={product.id} hover>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        {product.name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {product.sku || 'No SKU'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip label={product.category} size="small" />
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" color="warning.main" fontWeight="bold">
                        {product.quantity_in_stock} {product.unit}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">{product.reorder_point}</TableCell>
                    <TableCell align="right">{product.reorder_quantity}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          {lowStockProducts.length > 5 && (
            <Box mt={2} textAlign="center">
              <Typography variant="body2" color="text.secondary">
                Showing 5 of {lowStockProducts.length} low stock items
              </Typography>
            </Box>
          )}
        </Paper>
      )}

      <Grid container spacing={3}>
        {/* Recent Purchase Orders */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6" display="flex" alignItems="center" gap={1}>
                <LocalShippingIcon />
                Recent Purchase Orders
              </Typography>
              <Button
                variant="outlined"
                size="small"
                onClick={() => navigate('/purchase-orders')}
                aria-label="View all purchase orders"
              >
                View All
              </Button>
            </Box>
            {purchaseOrders.length === 0 ? (
              <Alert severity="info">No purchase orders yet.</Alert>
            ) : (
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>PO Number</TableCell>
                      <TableCell>Vendor</TableCell>
                      <TableCell align="right">Amount</TableCell>
                      <TableCell>Status</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {purchaseOrders.slice(0, 5).map((po) => (
                      <TableRow key={po.id} hover>
                        <TableCell>
                          <Typography variant="body2" fontFamily="monospace">
                            {po.order_number}
                          </Typography>
                        </TableCell>
                        <TableCell>{po.vendor_name}</TableCell>
                        <TableCell align="right">
                          ${parseFloat(po.total_amount || 0).toFixed(2)}
                        </TableCell>
                        <TableCell>
                          <Chip label={po.status} size="small" color={getStatusColor(po.status)} />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Paper>
        </Grid>

        {/* Recent Transactions */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6" display="flex" alignItems="center" gap={1}>
                <TrendingUpIcon />
                Recent Transactions
              </Typography>
            </Box>
            {transactions.length === 0 ? (
              <Alert severity="info">No transactions yet.</Alert>
            ) : (
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Date</TableCell>
                      <TableCell>Product</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell align="right">Quantity</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {transactions.slice(0, 5).map((txn) => (
                      <TableRow key={txn.id} hover>
                        <TableCell>
                          <Typography variant="body2">
                            {new Date(txn.transaction_date).toLocaleDateString()}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">{txn.product_name}</Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={txn.transaction_type}
                            size="small"
                            color={getTransactionTypeColor(txn.transaction_type)}
                          />
                        </TableCell>
                        <TableCell align="right">
                          <Typography
                            variant="body2"
                            color={
                              txn.quantity_change > 0
                                ? 'success.main'
                                : txn.quantity_change < 0
                                ? 'error.main'
                                : 'inherit'
                            }
                          >
                            {txn.quantity_change > 0 ? '+' : ''}
                            {txn.quantity_change}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Paper>
        </Grid>
      </Grid>

      {/* Quick Actions */}
      <Paper sx={{ p: 3, mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          Quick Actions
        </Typography>
        <Divider sx={{ mb: 2 }} />
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <Button
              variant="outlined"
              fullWidth
              onClick={() => navigate('/products')}
              startIcon={<InventoryIcon />}
              aria-label="Manage products"
            >
              Manage Products
            </Button>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Button
              variant="outlined"
              fullWidth
              onClick={() => navigate('/vendors')}
              startIcon={<LocalShippingIcon />}
              aria-label="Manage vendors"
            >
              Manage Vendors
            </Button>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Button
              variant="outlined"
              fullWidth
              onClick={() => navigate('/purchase-orders')}
              startIcon={<ShoppingCartIcon />}
              aria-label="View purchase orders"
            >
              Purchase Orders
            </Button>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Button
              variant="outlined"
              fullWidth
              onClick={() => navigate('/products')}
              startIcon={<WarningIcon />}
              aria-label="View low stock products"
            >
              View Low Stock
            </Button>
          </Grid>
        </Grid>
      </Paper>
    </Box>
  );
}

export default InventoryDashboard;
