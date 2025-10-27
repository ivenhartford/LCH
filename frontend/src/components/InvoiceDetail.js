import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
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
  CircularProgress,
  Alert,
  Chip,
  Grid,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Payment as PaymentIcon,
  Delete as DeleteIcon,
  Print as PrintIcon,
} from '@mui/icons-material';
import logger from '../utils/logger';

/**
 * Invoice Detail Component
 *
 * Displays complete invoice information including line items, payments, and balance.
 */
function InvoiceDetail() {
  const { invoiceId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [paymentDialogOpen, setPaymentDialogOpen] = useState(false);
  const [paymentFormData, setPaymentFormData] = useState({
    amount: '',
    payment_method: 'cash',
    reference_number: '',
    notes: '',
    payment_date: new Date().toISOString().split('T')[0],
  });

  useEffect(() => {
    logger.logLifecycle('InvoiceDetail', 'mounted', { invoiceId });
    return () => logger.logLifecycle('InvoiceDetail', 'unmounted');
  }, [invoiceId]);

  const {
    data: invoice,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['invoice', invoiceId],
    queryFn: async () => {
      const response = await fetch(`/api/invoices/${invoiceId}`, { credentials: 'include' });
      if (!response.ok) throw new Error('Failed to fetch invoice');
      return response.json();
    },
    enabled: !!invoiceId,
  });

  const paymentMutation = useMutation({
    mutationFn: async (data) => {
      const response = await fetch('/api/payments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          ...data,
          invoice_id: parseInt(invoiceId),
          client_id: invoice.client_id,
          payment_date: new Date(data.payment_date).toISOString(),
        }),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to record payment');
      }
      return response.json();
    },
    onSuccess: () => {
      logger.info('Payment recorded');
      queryClient.invalidateQueries(['invoice', invoiceId]);
      queryClient.invalidateQueries(['invoices']);
      handleClosePaymentDialog();
    },
  });

  const deletePaymentMutation = useMutation({
    mutationFn: async (paymentId) => {
      const response = await fetch(`/api/payments/${paymentId}`, {
        method: 'DELETE',
        credentials: 'include',
      });
      if (!response.ok) throw new Error('Failed to delete payment');
      return response.json();
    },
    onSuccess: () => {
      logger.info('Payment deleted');
      queryClient.invalidateQueries(['invoice', invoiceId]);
      queryClient.invalidateQueries(['invoices']);
    },
  });

  const handleOpenPaymentDialog = () => {
    const balance = parseFloat(invoice.balance_due || 0);
    setPaymentFormData({
      amount: balance > 0 ? balance.toFixed(2) : '',
      payment_method: 'cash',
      reference_number: '',
      notes: '',
      payment_date: new Date().toISOString().split('T')[0],
    });
    setPaymentDialogOpen(true);
  };

  const handleClosePaymentDialog = () => {
    setPaymentDialogOpen(false);
  };

  const handleSubmitPayment = () => {
    logger.logAction('Record payment', paymentFormData);
    paymentMutation.mutate(paymentFormData);
  };

  const handleDeletePayment = (paymentId) => {
    if (window.confirm('Delete this payment?')) {
      deletePaymentMutation.mutate(paymentId);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'paid':
        return 'success';
      case 'partial_paid':
        return 'info';
      case 'sent':
        return 'warning';
      case 'overdue':
        return 'error';
      case 'draft':
        return 'default';
      case 'cancelled':
        return 'default';
      default:
        return 'default';
    }
  };

  const getStatusLabel = (status) => {
    return status.replace('_', ' ').replace(/\b\w/g, (l) => l.toUpperCase());
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
        <Alert severity="error">Failed to load invoice: {error.message}</Alert>
      </Box>
    );
  }

  const items = invoice?.items || [];
  const payments = invoice?.payments || [];

  return (
    <Box>
      {/* Header */}
      <Box mb={3} display="flex" justifyContent="space-between" alignItems="center">
        <Box display="flex" alignItems="center" gap={2}>
          <IconButton onClick={() => navigate('/invoices')}>
            <ArrowBackIcon />
          </IconButton>
          <Box>
            <Typography variant="h4">{invoice.invoice_number}</Typography>
            <Typography variant="body2" color="text.secondary">
              {new Date(invoice.invoice_date).toLocaleDateString()}
            </Typography>
          </Box>
          <Chip label={getStatusLabel(invoice.status)} color={getStatusColor(invoice.status)} />
        </Box>
        <Box display="flex" gap={1}>
          <Button startIcon={<PrintIcon />} variant="outlined">
            Print
          </Button>
          {parseFloat(invoice.balance_due) > 0 && (
            <Button
              startIcon={<PaymentIcon />}
              variant="contained"
              onClick={handleOpenPaymentDialog}
            >
              Record Payment
            </Button>
          )}
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Client & Patient Info */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Bill To
            </Typography>
            <Typography variant="body1" fontWeight="medium">
              {invoice.client_name}
            </Typography>
            {invoice.patient_name && (
              <Typography variant="body2" color="text.secondary">
                Patient: {invoice.patient_name}
              </Typography>
            )}
            {invoice.visit_id && (
              <Typography variant="body2" color="text.secondary">
                Visit ID: {invoice.visit_id}
              </Typography>
            )}
          </Paper>
        </Grid>

        {/* Invoice Summary */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Summary
            </Typography>
            <Box display="flex" justifyContent="space-between" mb={1}>
              <Typography>Subtotal:</Typography>
              <Typography>${parseFloat(invoice.subtotal).toFixed(2)}</Typography>
            </Box>
            {parseFloat(invoice.discount_amount) > 0 && (
              <Box display="flex" justifyContent="space-between" mb={1} color="success.main">
                <Typography>Discount:</Typography>
                <Typography>-${parseFloat(invoice.discount_amount).toFixed(2)}</Typography>
              </Box>
            )}
            <Box display="flex" justifyContent="space-between" mb={1}>
              <Typography>Tax ({parseFloat(invoice.tax_rate).toFixed(1)}%):</Typography>
              <Typography>${parseFloat(invoice.tax_amount).toFixed(2)}</Typography>
            </Box>
            <Divider sx={{ my: 1 }} />
            <Box display="flex" justifyContent="space-between" mb={1}>
              <Typography fontWeight="bold">Total:</Typography>
              <Typography fontWeight="bold">
                ${parseFloat(invoice.total_amount).toFixed(2)}
              </Typography>
            </Box>
            <Box display="flex" justifyContent="space-between" mb={1}>
              <Typography>Amount Paid:</Typography>
              <Typography color="success.main">
                ${parseFloat(invoice.amount_paid).toFixed(2)}
              </Typography>
            </Box>
            <Box display="flex" justifyContent="space-between">
              <Typography
                fontWeight="bold"
                color={parseFloat(invoice.balance_due) > 0 ? 'error' : 'success'}
              >
                Balance Due:
              </Typography>
              <Typography
                fontWeight="bold"
                color={parseFloat(invoice.balance_due) > 0 ? 'error' : 'success'}
              >
                ${parseFloat(invoice.balance_due).toFixed(2)}
              </Typography>
            </Box>
          </Paper>
        </Grid>

        {/* Line Items */}
        <Grid item xs={12}>
          <Paper>
            <Box p={2} borderBottom={1} borderColor="divider">
              <Typography variant="h6">Line Items</Typography>
            </Box>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Description</TableCell>
                    <TableCell align="right">Quantity</TableCell>
                    <TableCell align="right">Unit Price</TableCell>
                    <TableCell>Taxable</TableCell>
                    <TableCell align="right">Total</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {items.map((item, index) => (
                    <TableRow key={index}>
                      <TableCell>
                        <Typography variant="body2">{item.description}</Typography>
                        {item.service_name && (
                          <Typography variant="caption" color="text.secondary">
                            ({item.service_name})
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell align="right">{parseFloat(item.quantity).toFixed(2)}</TableCell>
                      <TableCell align="right">${parseFloat(item.unit_price).toFixed(2)}</TableCell>
                      <TableCell>{item.taxable ? 'Yes' : 'No'}</TableCell>
                      <TableCell align="right" fontWeight="medium">
                        ${parseFloat(item.total_price).toFixed(2)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>

        {/* Payment History */}
        <Grid item xs={12}>
          <Paper>
            <Box p={2} borderBottom={1} borderColor="divider">
              <Typography variant="h6">Payment History</Typography>
            </Box>
            {payments.length === 0 ? (
              <Box p={3} textAlign="center">
                <Typography variant="body2" color="text.secondary">
                  No payments recorded yet.
                </Typography>
              </Box>
            ) : (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Date</TableCell>
                      <TableCell>Amount</TableCell>
                      <TableCell>Method</TableCell>
                      <TableCell>Reference</TableCell>
                      <TableCell>Processed By</TableCell>
                      <TableCell align="right">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {payments.map((payment) => (
                      <TableRow key={payment.id}>
                        <TableCell>{new Date(payment.payment_date).toLocaleDateString()}</TableCell>
                        <TableCell fontWeight="medium">
                          ${parseFloat(payment.amount).toFixed(2)}
                        </TableCell>
                        <TableCell>{payment.payment_method.replace('_', ' ')}</TableCell>
                        <TableCell>{payment.reference_number || '-'}</TableCell>
                        <TableCell>{payment.processed_by_name}</TableCell>
                        <TableCell align="right">
                          <Tooltip title="Delete Payment">
                            <IconButton
                              size="small"
                              color="error"
                              onClick={() => handleDeletePayment(payment.id)}
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
            )}
          </Paper>
        </Grid>
      </Grid>

      {/* Payment Dialog */}
      <Dialog open={paymentDialogOpen} onClose={handleClosePaymentDialog} maxWidth="sm" fullWidth>
        <DialogTitle>Record Payment</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 0.5 }}>
            <Grid item xs={12}>
              <Alert severity="info">
                Balance Due: ${parseFloat(invoice.balance_due).toFixed(2)}
              </Alert>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                required
                type="number"
                label="Payment Amount"
                value={paymentFormData.amount}
                onChange={(e) => setPaymentFormData({ ...paymentFormData, amount: e.target.value })}
                InputProps={{ startAdornment: '$' }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                required
                type="date"
                label="Payment Date"
                value={paymentFormData.payment_date}
                onChange={(e) =>
                  setPaymentFormData({ ...paymentFormData, payment_date: e.target.value })
                }
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth required>
                <InputLabel>Payment Method</InputLabel>
                <Select
                  value={paymentFormData.payment_method}
                  label="Payment Method"
                  onChange={(e) =>
                    setPaymentFormData({ ...paymentFormData, payment_method: e.target.value })
                  }
                >
                  <MenuItem value="cash">Cash</MenuItem>
                  <MenuItem value="check">Check</MenuItem>
                  <MenuItem value="credit_card">Credit Card</MenuItem>
                  <MenuItem value="debit_card">Debit Card</MenuItem>
                  <MenuItem value="bank_transfer">Bank Transfer</MenuItem>
                  <MenuItem value="other">Other</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Reference Number"
                value={paymentFormData.reference_number}
                onChange={(e) =>
                  setPaymentFormData({ ...paymentFormData, reference_number: e.target.value })
                }
                placeholder="Check number, transaction ID, etc."
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={2}
                label="Notes"
                value={paymentFormData.notes}
                onChange={(e) => setPaymentFormData({ ...paymentFormData, notes: e.target.value })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClosePaymentDialog}>Cancel</Button>
          <Button
            onClick={handleSubmitPayment}
            variant="contained"
            disabled={paymentMutation.isLoading || !paymentFormData.amount}
          >
            {paymentMutation.isLoading ? <CircularProgress size={24} /> : 'Record Payment'}
          </Button>
        </DialogActions>
        {paymentMutation.isError && (
          <Alert severity="error" sx={{ m: 2 }}>
            {paymentMutation.error.message}
          </Alert>
        )}
      </Dialog>
    </Box>
  );
}

export default InvoiceDetail;
