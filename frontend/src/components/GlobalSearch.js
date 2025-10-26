import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  TextField,
  Dialog,
  DialogContent,
  List,
  ListItem,
  ListItemText,
  ListItemButton,
  Typography,
  Chip,
  CircularProgress,
  InputAdornment,
  Divider,
} from '@mui/material';
import {
  Search as SearchIcon,
  Person as PersonIcon,
  Pets as PetsIcon,
  Event as EventIcon,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { format, parseISO } from 'date-fns';

const searchAll = async (query) => {
  if (!query || query.length < 2) {
    return { clients: [], patients: [], appointments: [] };
  }

  const [clientsRes, patientsRes, appointmentsRes] = await Promise.all([
    fetch(`/api/clients?search=${encodeURIComponent(query)}&per_page=5`),
    fetch(`/api/patients?search=${encodeURIComponent(query)}&per_page=5`),
    fetch(`/api/appointments?per_page=100`), // We'll filter appointments client-side
  ]);

  const clientsData = await clientsRes.json();
  const patientsData = await patientsRes.json();
  const appointmentsData = await appointmentsRes.json();

  // Filter appointments by title or patient/client names
  const appointments = (appointmentsData.appointments || []).filter(apt =>
    apt.title?.toLowerCase().includes(query.toLowerCase()) ||
    apt.patient_name?.toLowerCase().includes(query.toLowerCase()) ||
    apt.client_name?.toLowerCase().includes(query.toLowerCase())
  ).slice(0, 5);

  return {
    clients: clientsData.clients || [],
    patients: patientsData.patients || [],
    appointments,
  };
};

const GlobalSearch = ({ open, onClose }) => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');

  // Debounce search query
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(searchQuery);
    }, 300);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  const { data: results, isLoading } = useQuery({
    queryKey: ['globalSearch', debouncedQuery],
    queryFn: () => searchAll(debouncedQuery),
    enabled: debouncedQuery.length >= 2,
  });

  const handleSelect = (type, id) => {
    onClose();
    setSearchQuery('');

    switch (type) {
      case 'client':
        navigate(`/clients/${id}`);
        break;
      case 'patient':
        navigate(`/patients/${id}`);
        break;
      case 'appointment':
        navigate(`/appointments/${id}`);
        break;
      default:
        break;
    }
  };

  const handleClose = () => {
    setSearchQuery('');
    onClose();
  };

  const hasResults = results && (
    results.clients.length > 0 ||
    results.patients.length > 0 ||
    results.appointments.length > 0
  );

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          position: 'fixed',
          top: 100,
          m: 0,
          maxHeight: 'calc(100% - 200px)',
        },
      }}
    >
      <Box sx={{ p: 2 }}>
        <TextField
          fullWidth
          autoFocus
          placeholder="Search clients, patients, or appointments..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
            endAdornment: isLoading && (
              <InputAdornment position="end">
                <CircularProgress size={20} />
              </InputAdornment>
            ),
          }}
        />
      </Box>

      <DialogContent sx={{ pt: 0 }}>
        {searchQuery.length === 0 && (
          <Typography variant="body2" color="text.secondary" sx={{ p: 2, textAlign: 'center' }}>
            Start typing to search across clients, patients, and appointments...
          </Typography>
        )}

        {searchQuery.length > 0 && searchQuery.length < 2 && (
          <Typography variant="body2" color="text.secondary" sx={{ p: 2, textAlign: 'center' }}>
            Type at least 2 characters to search
          </Typography>
        )}

        {debouncedQuery.length >= 2 && !isLoading && !hasResults && (
          <Typography variant="body2" color="text.secondary" sx={{ p: 2, textAlign: 'center' }}>
            No results found for "{debouncedQuery}"
          </Typography>
        )}

        {results && hasResults && (
          <List sx={{ pt: 0 }}>
            {/* Clients */}
            {results.clients.length > 0 && (
              <>
                <ListItem>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <PersonIcon color="primary" fontSize="small" />
                    <Typography variant="subtitle2" color="text.secondary">
                      Clients ({results.clients.length})
                    </Typography>
                  </Box>
                </ListItem>
                {results.clients.map((client) => (
                  <ListItemButton
                    key={client.id}
                    onClick={() => handleSelect('client', client.id)}
                    sx={{ pl: 4 }}
                  >
                    <ListItemText
                      primary={`${client.first_name} ${client.last_name}`}
                      secondary={
                        <Box component="span" sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                          {client.email && (
                            <Typography variant="body2" color="text.secondary">
                              {client.email}
                            </Typography>
                          )}
                          {client.phone_primary && (
                            <>
                              <span>•</span>
                              <Typography variant="body2" color="text.secondary">
                                {client.phone_primary}
                              </Typography>
                            </>
                          )}
                        </Box>
                      }
                    />
                  </ListItemButton>
                ))}
                <Divider sx={{ my: 1 }} />
              </>
            )}

            {/* Patients */}
            {results.patients.length > 0 && (
              <>
                <ListItem>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <PetsIcon color="success" fontSize="small" />
                    <Typography variant="subtitle2" color="text.secondary">
                      Patients ({results.patients.length})
                    </Typography>
                  </Box>
                </ListItem>
                {results.patients.map((patient) => (
                  <ListItemButton
                    key={patient.id}
                    onClick={() => handleSelect('patient', patient.id)}
                    sx={{ pl: 4 }}
                  >
                    <ListItemText
                      primary={patient.name}
                      secondary={
                        <Box component="span" sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                          {patient.breed && (
                            <Typography variant="body2" color="text.secondary">
                              {patient.breed}
                            </Typography>
                          )}
                          {patient.owner_name && (
                            <>
                              <span>•</span>
                              <Typography variant="body2" color="text.secondary">
                                Owner: {patient.owner_name}
                              </Typography>
                            </>
                          )}
                          <Chip
                            label={patient.status}
                            size="small"
                            color={patient.status === 'Active' ? 'success' : 'default'}
                            sx={{ ml: 'auto' }}
                          />
                        </Box>
                      }
                    />
                  </ListItemButton>
                ))}
                <Divider sx={{ my: 1 }} />
              </>
            )}

            {/* Appointments */}
            {results.appointments.length > 0 && (
              <>
                <ListItem>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <EventIcon color="warning" fontSize="small" />
                    <Typography variant="subtitle2" color="text.secondary">
                      Appointments ({results.appointments.length})
                    </Typography>
                  </Box>
                </ListItem>
                {results.appointments.map((appointment) => (
                  <ListItemButton
                    key={appointment.id}
                    onClick={() => handleSelect('appointment', appointment.id)}
                    sx={{ pl: 4 }}
                  >
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          {appointment.appointment_type_color && (
                            <Box
                              sx={{
                                width: 12,
                                height: 12,
                                borderRadius: '50%',
                                backgroundColor: appointment.appointment_type_color,
                              }}
                            />
                          )}
                          {appointment.title}
                        </Box>
                      }
                      secondary={
                        <Box component="span" sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                          <Typography variant="body2" color="text.secondary">
                            {format(parseISO(appointment.start_time), 'MMM dd, yyyy h:mm a')}
                          </Typography>
                          {appointment.patient_name && (
                            <>
                              <span>•</span>
                              <Typography variant="body2" color="text.secondary">
                                {appointment.patient_name}
                              </Typography>
                            </>
                          )}
                          <Chip
                            label={appointment.status}
                            size="small"
                            color={
                              appointment.status === 'completed' ? 'success' :
                              appointment.status === 'in_progress' ? 'warning' :
                              'default'
                            }
                            sx={{ ml: 'auto', textTransform: 'capitalize' }}
                          />
                        </Box>
                      }
                    />
                  </ListItemButton>
                ))}
              </>
            )}
          </List>
        )}

        {/* Keyboard shortcut hint */}
        <Box sx={{ p: 2, pt: 3 }}>
          <Typography variant="caption" color="text.secondary">
            Tip: Press Ctrl+K (or ⌘+K on Mac) to open search from anywhere
          </Typography>
        </Box>
      </DialogContent>
    </Dialog>
  );
};

export default GlobalSearch;
