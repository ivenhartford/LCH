import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Grid,
  Card,
  CardContent,
  CardHeader,
  Typography,
  Button,
  List,
  ListItem,
  ListItemText,
  Chip,
  CircularProgress,
  IconButton,
  Avatar,
} from '@mui/material';
import {
  CalendarToday as CalendarIcon,
  Pets as PetsIcon,
  Person as PersonIcon,
  TrendingUp as TrendingUpIcon,
  Add as AddIcon,
  Event as EventIcon,
  ArrowForward as ArrowForwardIcon,
  CheckCircle as CheckCircleIcon,
} from '@mui/icons-material';
import { format, isToday, isTomorrow, parseISO } from 'date-fns';
import MyCalendar from './Calendar';

// Fetch functions
const fetchDashboardStats = async () => {
  const [appointmentsRes, patientsRes, clientsRes] = await Promise.all([
    fetch('/api/appointments?per_page=1000'),
    fetch('/api/patients?per_page=1000'),
    fetch('/api/clients?per_page=1000'),
  ]);

  const appointmentsData = await appointmentsRes.json();
  const patientsData = await patientsRes.json();
  const clientsData = await clientsRes.json();

  const appointments = appointmentsData.appointments || [];
  const patients = patientsData.patients || [];
  const clients = clientsData.clients || [];

  // Calculate stats
  const now = new Date();
  const todayAppointments = appointments.filter(apt =>
    isToday(parseISO(apt.start_time))
  );

  const upcomingAppointments = appointments.filter(apt => {
    const aptDate = parseISO(apt.start_time);
    return aptDate > now && !isToday(aptDate);
  }).slice(0, 10);

  const recentPatients = patients
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    .slice(0, 5);

  return {
    totalAppointments: appointments.length,
    todayAppointments: todayAppointments.length,
    upcomingAppointments,
    totalPatients: patients.length,
    totalClients: clients.length,
    recentPatients,
    todayAppointmentsList: todayAppointments,
  };
};

function Dashboard() {
  const navigate = useNavigate();

  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboardStats'],
    queryFn: fetchDashboardStats,
    refetchInterval: 60000, // Refetch every minute
  });

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <CircularProgress />
      </Box>
    );
  }

  const quickActions = [
    { label: 'New Appointment', icon: <EventIcon />, path: '/appointments/new', color: 'primary' },
    { label: 'New Patient', icon: <PetsIcon />, path: '/patients/new', color: 'success' },
    { label: 'New Client', icon: <PersonIcon />, path: '/clients/new', color: 'secondary' },
  ];

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Welcome to Lenox Cat Hospital Management System
        </Typography>
      </Box>

      {/* Quick Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h4" component="div">
                    {stats.todayAppointments}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Today's Appointments
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'primary.main', width: 56, height: 56 }}>
                  <CalendarIcon />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h4" component="div">
                    {stats.upcomingAppointments.length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Upcoming
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'warning.main', width: 56, height: 56 }}>
                  <TrendingUpIcon />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h4" component="div">
                    {stats.totalPatients}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Patients
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'success.main', width: 56, height: 56 }}>
                  <PetsIcon />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h4" component="div">
                    {stats.totalClients}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Clients
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'secondary.main', width: 56, height: 56 }}>
                  <PersonIcon />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Quick Actions */}
      <Card sx={{ mb: 4 }}>
        <CardHeader title="Quick Actions" />
        <CardContent>
          <Grid container spacing={2}>
            {quickActions.map((action) => (
              <Grid item xs={12} sm={4} key={action.label}>
                <Button
                  fullWidth
                  variant="outlined"
                  color={action.color}
                  startIcon={action.icon}
                  onClick={() => navigate(action.path)}
                  sx={{ py: 2 }}
                >
                  {action.label}
                </Button>
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>

      <Grid container spacing={3}>
        {/* Today's Appointments */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader
              title="Today's Appointments"
              action={
                <IconButton onClick={() => navigate('/calendar')}>
                  <ArrowForwardIcon />
                </IconButton>
              }
            />
            <CardContent>
              {stats.todayAppointmentsList.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  No appointments scheduled for today
                </Typography>
              ) : (
                <List>
                  {stats.todayAppointmentsList
                    .sort((a, b) => new Date(a.start_time) - new Date(b.start_time))
                    .map((apt) => (
                      <ListItem
                        key={apt.id}
                        button
                        onClick={() => navigate(`/appointments/${apt.id}`)}
                        sx={{ borderRadius: 1, mb: 1, '&:hover': { bgcolor: 'action.hover' } }}
                      >
                        <ListItemText
                          primary={
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              {apt.appointment_type_color && (
                                <Box
                                  sx={{
                                    width: 12,
                                    height: 12,
                                    borderRadius: '50%',
                                    backgroundColor: apt.appointment_type_color,
                                  }}
                                />
                              )}
                              <Typography variant="body1">{apt.title}</Typography>
                            </Box>
                          }
                          secondary={
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                              <Typography variant="body2" color="text.secondary">
                                {format(parseISO(apt.start_time), 'h:mm a')}
                              </Typography>
                              {apt.patient_name && (
                                <>
                                  <Typography variant="body2" color="text.secondary">•</Typography>
                                  <Typography variant="body2" color="text.secondary">
                                    {apt.patient_name}
                                  </Typography>
                                </>
                              )}
                              <Chip
                                label={apt.status}
                                size="small"
                                color={
                                  apt.status === 'completed' ? 'success' :
                                  apt.status === 'in_progress' ? 'warning' :
                                  apt.status === 'checked_in' ? 'secondary' :
                                  'default'
                                }
                                sx={{ ml: 'auto', textTransform: 'capitalize' }}
                              />
                            </Box>
                          }
                        />
                      </ListItem>
                    ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Patients */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader
              title="Recently Added Patients"
              action={
                <IconButton onClick={() => navigate('/patients')}>
                  <ArrowForwardIcon />
                </IconButton>
              }
            />
            <CardContent>
              {stats.recentPatients.length === 0 ? (
                <Typography variant="body2" color="text.secondary">
                  No patients added yet
                </Typography>
              ) : (
                <List>
                  {stats.recentPatients.map((patient) => (
                    <ListItem
                      key={patient.id}
                      button
                      onClick={() => navigate(`/patients/${patient.id}`)}
                      sx={{ borderRadius: 1, mb: 1, '&:hover': { bgcolor: 'action.hover' } }}
                    >
                      <Avatar sx={{ mr: 2, bgcolor: 'success.light' }}>
                        <PetsIcon />
                      </Avatar>
                      <ListItemText
                        primary={patient.name}
                        secondary={
                          <Box>
                            <Typography variant="body2" color="text.secondary">
                              {patient.breed || 'Unknown breed'}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Added {format(parseISO(patient.created_at), 'MMM dd, yyyy')}
                            </Typography>
                          </Box>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Calendar Widget */}
        <Grid item xs={12}>
          <Card>
            <CardHeader title="Calendar" />
            <CardContent>
              <MyCalendar />
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export default Dashboard;
