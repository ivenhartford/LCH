import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Chip,
} from '@mui/material';
import { Pets as PetsIcon } from '@mui/icons-material';
import { format } from 'date-fns';

/**
 * Client Patients Component
 *
 * View all pets belonging to the client (read-only)
 */
function ClientPatients({ portalUser }) {
  const { data: patients, isLoading, error } = useQuery({
    queryKey: ['portalPatients', portalUser?.client_id],
    queryFn: async () => {
      const response = await fetch(`/api/portal/patients/${portalUser.client_id}`);
      if (!response.ok) throw new Error('Failed to fetch patients');
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
        Error loading pets: {error.message}
      </Alert>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <PetsIcon sx={{ fontSize: 40, mr: 2, color: 'primary.main' }} />
        <Typography variant="h4">My Pets</Typography>
      </Box>

      {patients && patients.length > 0 ? (
        <Grid container spacing={3}>
          {patients.map((patient) => (
            <Grid item xs={12} sm={6} md={4} key={patient.id}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    {patient.name}
                  </Typography>
                  <Box sx={{ mb: 2 }}>
                    <Chip label={patient.species} size="small" sx={{ mr: 1 }} />
                    {patient.sex && <Chip label={patient.sex} size="small" sx={{ mr: 1 }} />}
                  </Box>
                  {patient.breed && (
                    <Typography variant="body2" color="text.secondary">
                      <strong>Breed:</strong> {patient.breed}
                    </Typography>
                  )}
                  {patient.color && (
                    <Typography variant="body2" color="text.secondary">
                      <strong>Color:</strong> {patient.color}
                    </Typography>
                  )}
                  {patient.date_of_birth && (
                    <Typography variant="body2" color="text.secondary">
                      <strong>Born:</strong> {format(new Date(patient.date_of_birth), 'PP')}
                    </Typography>
                  )}
                  {patient.weight_kg && (
                    <Typography variant="body2" color="text.secondary">
                      <strong>Weight:</strong> {patient.weight_kg} kg
                    </Typography>
                  )}
                  {patient.microchip_number && (
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                      <strong>Microchip:</strong> {patient.microchip_number}
                    </Typography>
                  )}
                  {patient.insurance_provider && (
                    <Typography variant="body2" color="text.secondary">
                      <strong>Insurance:</strong> {patient.insurance_provider}
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      ) : (
        <Alert severity="info">No pets found</Alert>
      )}
    </Box>
  );
}

export default ClientPatients;
