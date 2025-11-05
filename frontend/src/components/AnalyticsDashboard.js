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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tabs,
  Tab,
  useTheme,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Assessment as AssessmentIcon,
  People as PeopleIcon,
  Pets as PetsIcon,
  CalendarMonth as CalendarIcon,
  AttachMoney as MoneyIcon,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import logger from '../utils/logger';
import { useNotification } from '../contexts/NotificationContext';

/**
 * Analytics Dashboard Component
 *
 * Comprehensive analytics dashboard with charts and KPIs.
 * Features:
 * - Revenue trends over time
 * - Client retention metrics
 * - Appointment volume analysis
 * - Procedure/service volume
 * - Patient demographics
 * - Interactive charts with Recharts
 * - Date range filtering
 */
function AnalyticsDashboard() {
  const theme = useTheme();
  const { showNotification } = useNotification();
  const [selectedTab, setSelectedTab] = useState(0);
  const [revenuePeriod, setRevenuePeriod] = useState('month');

  useEffect(() => {
    logger.logLifecycle('AnalyticsDashboard', 'mounted');
    return () => {
      logger.logLifecycle('AnalyticsDashboard', 'unmounted');
    };
  }, []);

  // Fetch dashboard summary (KPIs)
  const { data: summaryData, isLoading: summaryLoading } = useQuery({
    queryKey: ['analytics-summary'],
    queryFn: async () => {
      const response = await fetch('/api/analytics/dashboard-summary', {
        credentials: 'include',
      });
      if (!response.ok) throw new Error('Failed to fetch dashboard summary');
      return response.json();
    },
    staleTime: 60000,
  });

  // Fetch revenue trends
  const { data: revenueData, isLoading: revenueLoading } = useQuery({
    queryKey: ['analytics-revenue-trends', revenuePeriod],
    queryFn: async () => {
      const response = await fetch(`/api/analytics/revenue-trends?period=${revenuePeriod}`, {
        credentials: 'include',
      });
      if (!response.ok) throw new Error('Failed to fetch revenue trends');
      return response.json();
    },
    staleTime: 60000,
  });

  // Fetch client retention
  const { data: retentionData, isLoading: retentionLoading } = useQuery({
    queryKey: ['analytics-client-retention'],
    queryFn: async () => {
      const response = await fetch('/api/analytics/client-retention', {
        credentials: 'include',
      });
      if (!response.ok) throw new Error('Failed to fetch client retention');
      return response.json();
    },
    staleTime: 60000,
  });

  // Fetch appointment trends
  const { data: appointmentData, isLoading: appointmentLoading } = useQuery({
    queryKey: ['analytics-appointment-trends'],
    queryFn: async () => {
      const response = await fetch('/api/analytics/appointment-trends', {
        credentials: 'include',
      });
      if (!response.ok) throw new Error('Failed to fetch appointment trends');
      return response.json();
    },
    staleTime: 60000,
  });

  // Fetch procedure volume
  const { data: procedureData, isLoading: procedureLoading } = useQuery({
    queryKey: ['analytics-procedure-volume'],
    queryFn: async () => {
      const response = await fetch('/api/analytics/procedure-volume', {
        credentials: 'include',
      });
      if (!response.ok) throw new Error('Failed to fetch procedure volume');
      return response.json();
    },
    staleTime: 60000,
  });

  // Fetch patient demographics
  const { data: demographicsData, isLoading: demographicsLoading } = useQuery({
    queryKey: ['analytics-patient-demographics'],
    queryFn: async () => {
      const response = await fetch('/api/analytics/patient-demographics', {
        credentials: 'include',
      });
      if (!response.ok) throw new Error('Failed to fetch patient demographics');
      return response.json();
    },
    staleTime: 60000,
  });

  const summary = summaryData || {};
  const revenueGrowthPositive = summary.revenue_growth >= 0;

  // Chart colors
  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d', '#ffc658'];

  // KPI Card Component
  const KPICard = ({ title, value, subtitle, icon, trend }) => (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
          <Box>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {title}
            </Typography>
            <Typography variant="h4" component="div">
              {value}
            </Typography>
            {subtitle && (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                {subtitle}
              </Typography>
            )}
          </Box>
          <Box
            sx={{
              backgroundColor: theme.palette.primary.light,
              borderRadius: 2,
              p: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {icon}
          </Box>
        </Box>
        {trend !== undefined && (
          <Box sx={{ display: 'flex', alignItems: 'center', mt: 2 }}>
            {trend >= 0 ? (
              <TrendingUpIcon color="success" fontSize="small" />
            ) : (
              <TrendingDownIcon color="error" fontSize="small" />
            )}
            <Typography
              variant="body2"
              color={trend >= 0 ? 'success.main' : 'error.main'}
              sx={{ ml: 0.5 }}
            >
              {Math.abs(trend).toFixed(1)}% vs last month
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );

  if (summaryLoading) {
    return (
      <Box sx={{ p: 3, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          <AssessmentIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Analytics Dashboard
        </Typography>
      </Box>

      {/* KPI Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <KPICard
            title="Revenue This Month"
            value={`$${summary.revenue_this_month?.toLocaleString() || 0}`}
            trend={summary.revenue_growth}
            icon={<MoneyIcon color="primary" />}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <KPICard
            title="Active Patients"
            value={summary.active_patients?.toLocaleString() || 0}
            subtitle={`${summary.new_patients_this_month || 0} new this month`}
            icon={<PetsIcon color="primary" />}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <KPICard
            title="Appointments"
            value={summary.appointments_this_month?.toLocaleString() || 0}
            subtitle={`${summary.completed_appointments || 0} completed`}
            icon={<CalendarIcon color="primary" />}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <KPICard
            title="Avg Revenue/Appt"
            value={`$${summary.avg_revenue_per_appointment?.toLocaleString() || 0}`}
            subtitle={`$${summary.outstanding_balance?.toLocaleString() || 0} outstanding`}
            icon={<TrendingUpIcon color="primary" />}
          />
        </Grid>
      </Grid>

      {/* Tabs for different views */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={selectedTab} onChange={(e, newValue) => setSelectedTab(newValue)}>
          <Tab label="Revenue & Finance" />
          <Tab label="Clients & Retention" />
          <Tab label="Appointments" />
          <Tab label="Procedures" />
          <Tab label="Patient Demographics" />
        </Tabs>
      </Paper>

      {/* Tab 0: Revenue & Finance */}
      {selectedTab === 0 && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h6">Revenue Trends</Typography>
                <FormControl size="small" sx={{ minWidth: 120 }}>
                  <InputLabel>Period</InputLabel>
                  <Select
                    value={revenuePeriod}
                    label="Period"
                    onChange={(e) => setRevenuePeriod(e.target.value)}
                  >
                    <MenuItem value="day">Daily</MenuItem>
                    <MenuItem value="week">Weekly</MenuItem>
                    <MenuItem value="month">Monthly</MenuItem>
                  </Select>
                </FormControl>
              </Box>
              {revenueLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                  <CircularProgress />
                </Box>
              ) : revenueData?.data?.length > 0 ? (
                <ResponsiveContainer width="100%" height={400}>
                  <LineChart data={revenueData.data}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="period" />
                    <YAxis />
                    <Tooltip
                      formatter={(value, name) => {
                        if (name === 'revenue') return [`$${value.toLocaleString()}`, 'Revenue'];
                        if (name === 'invoice_count') return [value, 'Invoices'];
                        return [value, name];
                      }}
                    />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="revenue"
                      stroke={theme.palette.primary.main}
                      strokeWidth={2}
                      name="Revenue"
                    />
                    <Line
                      type="monotone"
                      dataKey="invoice_count"
                      stroke={theme.palette.secondary.main}
                      strokeWidth={2}
                      name="Invoice Count"
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <Alert severity="info">No revenue data available for the selected period</Alert>
              )}
            </Paper>
          </Grid>
        </Grid>
      )}

      {/* Tab 1: Clients & Retention */}
      {selectedTab === 1 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Client Retention Metrics
              </Typography>
              {retentionLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                  <CircularProgress />
                </Box>
              ) : (
                <Grid container spacing={2} sx={{ mt: 1 }}>
                  <Grid item xs={6}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="body2" color="text.secondary">
                          New Clients
                        </Typography>
                        <Typography variant="h4">{retentionData?.new_clients || 0}</Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={6}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="body2" color="text.secondary">
                          Returning Clients
                        </Typography>
                        <Typography variant="h4">{retentionData?.returning_clients || 0}</Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={6}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="body2" color="text.secondary">
                          Retention Rate
                        </Typography>
                        <Typography variant="h4" color="success.main">
                          {retentionData?.retention_rate || 0}%
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={6}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="body2" color="text.secondary">
                          Churn Rate
                        </Typography>
                        <Typography variant="h4" color="error.main">
                          {retentionData?.churn_rate || 0}%
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
              )}
            </Paper>
          </Grid>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                New Clients by Month
              </Typography>
              {retentionLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                  <CircularProgress />
                </Box>
              ) : retentionData?.monthly_breakdown?.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={retentionData.monthly_breakdown}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="new_clients" fill={theme.palette.primary.main} name="New Clients" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <Alert severity="info">No client data available</Alert>
              )}
            </Paper>
          </Grid>
        </Grid>
      )}

      {/* Tab 2: Appointments */}
      {selectedTab === 2 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Appointments by Status
              </Typography>
              {appointmentLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                  <CircularProgress />
                </Box>
              ) : appointmentData?.by_status?.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={appointmentData.by_status}
                      dataKey="count"
                      nameKey="status"
                      cx="50%"
                      cy="50%"
                      outerRadius={100}
                      label
                    >
                      {appointmentData.by_status.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <Alert severity="info">No appointment data available</Alert>
              )}
            </Paper>
          </Grid>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Appointments by Type
              </Typography>
              {appointmentLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                  <CircularProgress />
                </Box>
              ) : appointmentData?.by_type?.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={appointmentData.by_type} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" />
                    <YAxis dataKey="type" type="category" width={150} />
                    <Tooltip />
                    <Bar dataKey="count" fill={theme.palette.secondary.main} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <Alert severity="info">No appointment type data available</Alert>
              )}
            </Paper>
          </Grid>
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Appointment Completion Rate: {appointmentData?.completion_rate || 0}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {appointmentData?.completed_appointments || 0} of {appointmentData?.total_appointments || 0}{' '}
                appointments completed
              </Typography>
            </Paper>
          </Grid>
        </Grid>
      )}

      {/* Tab 3: Procedures */}
      {selectedTab === 3 && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Top Procedures by Volume
              </Typography>
              {procedureLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                  <CircularProgress />
                </Box>
              ) : procedureData?.top_procedures?.length > 0 ? (
                <ResponsiveContainer width="100%" height={400}>
                  <BarChart data={procedureData.top_procedures} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" />
                    <YAxis dataKey="name" type="category" width={200} />
                    <Tooltip
                      formatter={(value, name) => {
                        if (name === 'revenue') return [`$${value.toLocaleString()}`, 'Revenue'];
                        if (name === 'times_performed') return [value, 'Times Performed'];
                        return [value, name];
                      }}
                    />
                    <Legend />
                    <Bar dataKey="times_performed" fill={theme.palette.primary.main} name="Times Performed" />
                    <Bar dataKey="revenue" fill={theme.palette.secondary.main} name="Revenue" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <Alert severity="info">No procedure data available</Alert>
              )}
            </Paper>
          </Grid>
        </Grid>
      )}

      {/* Tab 4: Patient Demographics */}
      {selectedTab === 4 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Age Distribution
              </Typography>
              {demographicsLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                  <CircularProgress />
                </Box>
              ) : demographicsData?.age_distribution?.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={demographicsData.age_distribution}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="age_group" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" fill={theme.palette.primary.main} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <Alert severity="info">No age distribution data available</Alert>
              )}
            </Paper>
          </Grid>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Top Breeds
              </Typography>
              {demographicsLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                  <CircularProgress />
                </Box>
              ) : demographicsData?.breed_distribution?.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={demographicsData.breed_distribution}
                      dataKey="count"
                      nameKey="breed"
                      cx="50%"
                      cy="50%"
                      outerRadius={100}
                      label
                    >
                      {demographicsData.breed_distribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <Alert severity="info">No breed data available</Alert>
              )}
            </Paper>
          </Grid>
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Patient Overview
              </Typography>
              <Grid container spacing={2} sx={{ mt: 1 }}>
                <Grid item xs={12} sm={4}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="body2" color="text.secondary">
                        Total Active Patients
                      </Typography>
                      <Typography variant="h4">{demographicsData?.total_patients || 0}</Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="body2" color="text.secondary">
                        Spay/Neuter Rate
                      </Typography>
                      <Typography variant="h4" color="success.main">
                        {demographicsData?.spay_neuter_rate || 0}%
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </Paper>
          </Grid>
        </Grid>
      )}
    </Box>
  );
}

export default AnalyticsDashboard;
