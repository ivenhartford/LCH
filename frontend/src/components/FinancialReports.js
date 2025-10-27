import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
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
  TextField,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Tabs,
  Tab,
  Divider,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  AccountBalance as AccountBalanceIcon,
  Payment as PaymentIcon,
  Assessment as AssessmentIcon,
  Download as DownloadIcon,
} from '@mui/icons-material';
import logger from '../utils/logger';

/**
 * Financial Reports Component
 *
 * Comprehensive financial reporting dashboard with:
 * - Financial summary metrics
 * - Revenue reports by period
 * - Outstanding balance report
 * - Payment method breakdown
 * - Service revenue analysis
 * - CSV export functionality
 */
function FinancialReports() {
  const [activeTab, setActiveTab] = useState(0);
  const [dateRange, setDateRange] = useState({
    start_date: new Date(new Date().getFullYear(), 0, 1).toISOString().split('T')[0],
    end_date: new Date().toISOString().split('T')[0],
  });
  const [revenuePeriod, setRevenuePeriod] = useState('monthly');

  useEffect(() => {
    logger.logLifecycle('FinancialReports', 'mounted');
    return () => logger.logLifecycle('FinancialReports', 'unmounted');
  }, []);

  // Financial Summary Query
  const {
    data: summary,
    isLoading: summaryLoading,
    isError: summaryError,
  } = useQuery({
    queryKey: ['financial-summary', dateRange.start_date, dateRange.end_date],
    queryFn: async () => {
      const params = new URLSearchParams(dateRange);
      const response = await fetch(`/api/reports/financial-summary?${params}`, {
        credentials: 'include',
      });
      if (!response.ok) throw new Error('Failed to fetch financial summary');
      return response.json();
    },
  });

  // Revenue by Period Query
  const {
    data: revenueByPeriod,
    isLoading: revenueLoading,
    isError: revenueError,
  } = useQuery({
    queryKey: ['revenue-by-period', revenuePeriod, dateRange.start_date, dateRange.end_date],
    queryFn: async () => {
      const params = new URLSearchParams({ period: revenuePeriod, ...dateRange });
      const response = await fetch(`/api/reports/revenue-by-period?${params}`, {
        credentials: 'include',
      });
      if (!response.ok) throw new Error('Failed to fetch revenue by period');
      return response.json();
    },
  });

  // Outstanding Balance Query
  const {
    data: outstandingBalance,
    isLoading: outstandingLoading,
    isError: outstandingError,
  } = useQuery({
    queryKey: ['outstanding-balance'],
    queryFn: async () => {
      const response = await fetch('/api/reports/outstanding-balance', {
        credentials: 'include',
      });
      if (!response.ok) throw new Error('Failed to fetch outstanding balance');
      return response.json();
    },
  });

  // Payment Methods Query
  const {
    data: paymentMethods,
    isLoading: paymentMethodsLoading,
    isError: paymentMethodsError,
  } = useQuery({
    queryKey: ['payment-methods', dateRange.start_date, dateRange.end_date],
    queryFn: async () => {
      const params = new URLSearchParams(dateRange);
      const response = await fetch(`/api/reports/payment-methods?${params}`, {
        credentials: 'include',
      });
      if (!response.ok) throw new Error('Failed to fetch payment methods');
      return response.json();
    },
  });

  // Service Revenue Query
  const {
    data: serviceRevenue,
    isLoading: serviceRevenueLoading,
    isError: serviceRevenueError,
  } = useQuery({
    queryKey: ['service-revenue', dateRange.start_date, dateRange.end_date],
    queryFn: async () => {
      const params = new URLSearchParams(dateRange);
      const response = await fetch(`/api/reports/service-revenue?${params}`, {
        credentials: 'include',
      });
      if (!response.ok) throw new Error('Failed to fetch service revenue');
      return response.json();
    },
  });

  const handleExportCSV = (data, filename) => {
    if (!data || data.length === 0) {
      alert('No data to export');
      return;
    }

    // Convert to CSV
    const headers = Object.keys(data[0]);
    const csvContent = [
      headers.join(','),
      ...data.map((row) => headers.map((header) => JSON.stringify(row[header] || '')).join(',')),
    ].join('\n');

    // Download
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename}_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);

    logger.logAction('Export CSV', { filename, rows: data.length });
  };

  const formatCurrency = (value) => {
    return `$${parseFloat(value || 0).toFixed(2)}`;
  };

  const formatPaymentMethod = (method) => {
    return method.replace('_', ' ').replace(/\b\w/g, (l) => l.toUpperCase());
  };

  if (summaryLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box mb={3}>
        <Typography variant="h4" gutterBottom>
          Financial Reports
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Comprehensive financial analytics and reporting
        </Typography>
      </Box>

      {/* Date Range Filter */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={4}>
            <TextField
              fullWidth
              type="date"
              label="Start Date"
              value={dateRange.start_date}
              onChange={(e) => setDateRange({ ...dateRange, start_date: e.target.value })}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
          <Grid item xs={12} sm={4}>
            <TextField
              fullWidth
              type="date"
              label="End Date"
              value={dateRange.end_date}
              onChange={(e) => setDateRange({ ...dateRange, end_date: e.target.value })}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
          <Grid item xs={12} sm={4}>
            <Button
              fullWidth
              variant="outlined"
              onClick={() =>
                setDateRange({
                  start_date: new Date(new Date().getFullYear(), 0, 1).toISOString().split('T')[0],
                  end_date: new Date().toISOString().split('T')[0],
                })
              }
            >
              Reset to YTD
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Summary Cards */}
      {summaryError ? (
        <Alert severity="error" sx={{ mb: 3 }}>
          Failed to load financial summary
        </Alert>
      ) : (
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={1}>
                  <TrendingUpIcon color="success" sx={{ mr: 1 }} />
                  <Typography variant="body2" color="text.secondary">
                    Total Revenue
                  </Typography>
                </Box>
                <Typography variant="h4">{formatCurrency(summary?.total_revenue)}</Typography>
                <Typography variant="caption" color="text.secondary">
                  {summary?.paid_invoices} paid invoices
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={1}>
                  <AccountBalanceIcon color="error" sx={{ mr: 1 }} />
                  <Typography variant="body2" color="text.secondary">
                    Outstanding Balance
                  </Typography>
                </Box>
                <Typography variant="h4" color="error.main">
                  {formatCurrency(summary?.total_outstanding)}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Unpaid/partially paid
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={1}>
                  <PaymentIcon color="primary" sx={{ mr: 1 }} />
                  <Typography variant="body2" color="text.secondary">
                    Total Payments
                  </Typography>
                </Box>
                <Typography variant="h4">{formatCurrency(summary?.total_payments)}</Typography>
                <Typography variant="caption" color="text.secondary">
                  All payment methods
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={1}>
                  <AssessmentIcon color="info" sx={{ mr: 1 }} />
                  <Typography variant="body2" color="text.secondary">
                    Average Invoice
                  </Typography>
                </Box>
                <Typography variant="h4">{formatCurrency(summary?.avg_invoice)}</Typography>
                <Typography variant="caption" color="text.secondary">
                  {summary?.total_invoices} total invoices
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)}>
          <Tab label="Revenue by Period" />
          <Tab label="Outstanding Balance" />
          <Tab label="Payment Methods" />
          <Tab label="Service Revenue" />
        </Tabs>
        <Divider />

        {/* Tab 0: Revenue by Period */}
        {activeTab === 0 && (
          <Box p={3}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Revenue by Period</Typography>
              <Box display="flex" gap={2}>
                <FormControl size="small" sx={{ minWidth: 120 }}>
                  <InputLabel>Period</InputLabel>
                  <Select
                    value={revenuePeriod}
                    label="Period"
                    onChange={(e) => setRevenuePeriod(e.target.value)}
                  >
                    <MenuItem value="daily">Daily</MenuItem>
                    <MenuItem value="weekly">Weekly</MenuItem>
                    <MenuItem value="monthly">Monthly</MenuItem>
                  </Select>
                </FormControl>
                <Button
                  startIcon={<DownloadIcon />}
                  variant="outlined"
                  size="small"
                  onClick={() => handleExportCSV(revenueByPeriod?.data, 'revenue_by_period')}
                  disabled={!revenueByPeriod?.data || revenueByPeriod.data.length === 0}
                >
                  Export CSV
                </Button>
              </Box>
            </Box>
            {revenueLoading ? (
              <CircularProgress />
            ) : revenueError ? (
              <Alert severity="error">Failed to load revenue data</Alert>
            ) : (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Period</TableCell>
                      <TableCell align="right">Revenue</TableCell>
                      <TableCell align="right">Invoice Count</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {revenueByPeriod?.data?.map((row, index) => (
                      <TableRow key={index}>
                        <TableCell>{row.period}</TableCell>
                        <TableCell align="right" fontWeight="medium">
                          {formatCurrency(row.revenue)}
                        </TableCell>
                        <TableCell align="right">{row.count}</TableCell>
                      </TableRow>
                    ))}
                    {(!revenueByPeriod?.data || revenueByPeriod.data.length === 0) && (
                      <TableRow>
                        <TableCell colSpan={3} align="center">
                          <Typography variant="body2" color="text.secondary">
                            No revenue data for selected period
                          </Typography>
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Box>
        )}

        {/* Tab 1: Outstanding Balance */}
        {activeTab === 1 && (
          <Box p={3}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Outstanding Balance by Client</Typography>
              <Button
                startIcon={<DownloadIcon />}
                variant="outlined"
                size="small"
                onClick={() => handleExportCSV(outstandingBalance?.data, 'outstanding_balance')}
                disabled={!outstandingBalance?.data || outstandingBalance.data.length === 0}
              >
                Export CSV
              </Button>
            </Box>
            {outstandingLoading ? (
              <CircularProgress />
            ) : outstandingError ? (
              <Alert severity="error">Failed to load outstanding balance data</Alert>
            ) : (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Client Name</TableCell>
                      <TableCell align="right">Outstanding Amount</TableCell>
                      <TableCell align="right">Invoice Count</TableCell>
                      <TableCell>Oldest Invoice</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {outstandingBalance?.data?.map((row, index) => (
                      <TableRow key={index}>
                        <TableCell>{row.client_name}</TableCell>
                        <TableCell align="right" fontWeight="medium" color="error.main">
                          {formatCurrency(row.total_outstanding)}
                        </TableCell>
                        <TableCell align="right">{row.invoice_count}</TableCell>
                        <TableCell>
                          {row.oldest_invoice_date
                            ? new Date(row.oldest_invoice_date).toLocaleDateString()
                            : '-'}
                        </TableCell>
                      </TableRow>
                    ))}
                    {(!outstandingBalance?.data || outstandingBalance.data.length === 0) && (
                      <TableRow>
                        <TableCell colSpan={4} align="center">
                          <Typography variant="body2" color="text.secondary">
                            No outstanding balances - all invoices paid!
                          </Typography>
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Box>
        )}

        {/* Tab 2: Payment Methods */}
        {activeTab === 2 && (
          <Box p={3}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Payment Method Breakdown</Typography>
              <Button
                startIcon={<DownloadIcon />}
                variant="outlined"
                size="small"
                onClick={() => handleExportCSV(paymentMethods?.data, 'payment_methods')}
                disabled={!paymentMethods?.data || paymentMethods.data.length === 0}
              >
                Export CSV
              </Button>
            </Box>
            {paymentMethodsLoading ? (
              <CircularProgress />
            ) : paymentMethodsError ? (
              <Alert severity="error">Failed to load payment methods data</Alert>
            ) : (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Payment Method</TableCell>
                      <TableCell align="right">Total Amount</TableCell>
                      <TableCell align="right">Transaction Count</TableCell>
                      <TableCell align="right">Average</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {paymentMethods?.data?.map((row, index) => (
                      <TableRow key={index}>
                        <TableCell>{formatPaymentMethod(row.payment_method)}</TableCell>
                        <TableCell align="right" fontWeight="medium">
                          {formatCurrency(row.total)}
                        </TableCell>
                        <TableCell align="right">{row.count}</TableCell>
                        <TableCell align="right">{formatCurrency(row.total / row.count)}</TableCell>
                      </TableRow>
                    ))}
                    {(!paymentMethods?.data || paymentMethods.data.length === 0) && (
                      <TableRow>
                        <TableCell colSpan={4} align="center">
                          <Typography variant="body2" color="text.secondary">
                            No payment data for selected period
                          </Typography>
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Box>
        )}

        {/* Tab 3: Service Revenue */}
        {activeTab === 3 && (
          <Box p={3}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Service Revenue Analysis</Typography>
              <Button
                startIcon={<DownloadIcon />}
                variant="outlined"
                size="small"
                onClick={() => handleExportCSV(serviceRevenue?.data, 'service_revenue')}
                disabled={!serviceRevenue?.data || serviceRevenue.data.length === 0}
              >
                Export CSV
              </Button>
            </Box>
            {serviceRevenueLoading ? (
              <CircularProgress />
            ) : serviceRevenueError ? (
              <Alert severity="error">Failed to load service revenue data</Alert>
            ) : (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Service Name</TableCell>
                      <TableCell>Type</TableCell>
                      <TableCell align="right">Total Revenue</TableCell>
                      <TableCell align="right">Quantity Sold</TableCell>
                      <TableCell align="right">Times Sold</TableCell>
                      <TableCell align="right">Avg per Sale</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {serviceRevenue?.data?.map((row, index) => (
                      <TableRow key={index}>
                        <TableCell>{row.service_name}</TableCell>
                        <TableCell>{row.service_type.replace('_', ' ').toUpperCase()}</TableCell>
                        <TableCell align="right" fontWeight="medium">
                          {formatCurrency(row.total_revenue)}
                        </TableCell>
                        <TableCell align="right">
                          {parseFloat(row.total_quantity).toFixed(2)}
                        </TableCell>
                        <TableCell align="right">{row.times_sold}</TableCell>
                        <TableCell align="right">
                          {formatCurrency(row.total_revenue / row.times_sold)}
                        </TableCell>
                      </TableRow>
                    ))}
                    {(!serviceRevenue?.data || serviceRevenue.data.length === 0) && (
                      <TableRow>
                        <TableCell colSpan={6} align="center">
                          <Typography variant="body2" color="text.secondary">
                            No service revenue data for selected period
                          </Typography>
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Box>
        )}
      </Paper>
    </Box>
  );
}

export default FinancialReports;
