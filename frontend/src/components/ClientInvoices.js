import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
  Alert,
  Chip,
} from '@mui/material';
import { Receipt as ReceiptIcon } from '@mui/icons-material';
import { format } from 'date-fns';

/**
 * Client Invoices Component
 *
 * View all invoices and payment status (read-only)
 */
function ClientInvoices({ portalUser }) {
  const { data: invoices, isLoading, error } = useQuery({
    queryKey: ['portalInvoices', portalUser?.client_id],
    queryFn: async () => {
      const response = await fetch(`/api/portal/invoices/${portalUser.client_id}`);
      if (!response.ok) throw new Error('Failed to fetch invoices');
      return response.json();
    },
    enabled: !!portalUser?.client_id,
  });

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mt: 2 }}>
        Error loading invoices: {error.message}
      </Alert>
    );
  }

  const getStatusColor = (status) => {
    const colors = {
      paid: 'success',
      unpaid: 'error',
      'partially-paid': 'warning',
      overdue: 'error',
    };
    return colors[status] || 'default';
  };

  const totalBalance = invoices?.reduce((sum, inv) => sum + parseFloat(inv.balance_due || 0), 0) || 0;

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <ReceiptIcon sx={{ fontSize: 40, mr: 2, color: 'primary.main' }} />
        <Box>
          <Typography variant="h4">Invoices</Typography>
          <Typography variant="h6" color={totalBalance > 0 ? 'error' : 'success'}>
            Total Balance Due: ${totalBalance.toFixed(2)}
          </Typography>
        </Box>
      </Box>

      {invoices && invoices.length > 0 ? (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell><strong>Invoice #</strong></TableCell>
                <TableCell><strong>Date</strong></TableCell>
                <TableCell><strong>Due Date</strong></TableCell>
                <TableCell align="right"><strong>Total</strong></TableCell>
                <TableCell align="right"><strong>Paid</strong></TableCell>
                <TableCell align="right"><strong>Balance</strong></TableCell>
                <TableCell><strong>Status</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {invoices.map((invoice) => (
                <TableRow
                  key={invoice.id}
                  sx={{
                    backgroundColor: parseFloat(invoice.balance_due) > 0 ? 'rgba(255, 0, 0, 0.05)' : 'inherit',
                  }}
                >
                  <TableCell>{invoice.invoice_number}</TableCell>
                  <TableCell>
                    {invoice.invoice_date ? format(new Date(invoice.invoice_date), 'PP') : 'N/A'}
                  </TableCell>
                  <TableCell>
                    {invoice.due_date ? format(new Date(invoice.due_date), 'PP') : 'N/A'}
                  </TableCell>
                  <TableCell align="right">${invoice.total_amount}</TableCell>
                  <TableCell align="right">${invoice.amount_paid}</TableCell>
                  <TableCell align="right">
                    <strong>${invoice.balance_due}</strong>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={invoice.status}
                      size="small"
                      color={getStatusColor(invoice.status)}
                    />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      ) : (
        <Alert severity="info">No invoices found</Alert>
      )}

      {totalBalance > 0 && (
        <Alert severity="warning" sx={{ mt: 2 }}>
          You have an outstanding balance of ${totalBalance.toFixed(2)}.
          Please contact the clinic at (555) 123-4567 to arrange payment.
        </Alert>
      )}
    </Box>
  );
}

export default ClientInvoices;
