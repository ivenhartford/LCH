import React, { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Paper,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Grid,
  Card,
  CardContent,
  CardHeader,
  Chip,
  Divider,
  IconButton,
  Avatar,
} from '@mui/material';
import {
  Edit as EditIcon,
  ArrowBack as ArrowBackIcon,
  Person as PersonIcon,
  LocalHospital as MedicalIcon,
  Pets as PetsIcon,
  CreditCard as InsuranceIcon,
  Verified as ChipIcon,
} from '@mui/icons-material';
import logger from '../utils/logger';

/**
 * Patient (Cat) Detail Component
 *
 * Displays full details of a single cat patient.
 * Features:
 * - Complete patient information
 * - Owner details with navigation
 * - Medical history and notes
 * - Insurance information
 * - Edit functionality
 * - Comprehensive logging
 */
function PatientDetail() {
  const { patientId } = useParams();
  const navigate = useNavigate();

  useEffect(() => {
    logger.logLifecycle('PatientDetail', 'mounted', { patientId });

    return () => {
      logger.logLifecycle('PatientDetail', 'unmounted');
    };
  }, [patientId]);

  // Fetch patient data
  const {
    data: patient,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ['patient', patientId],
    queryFn: async () => {
      const startTime = performance.now();
      logger.logAction('Fetching patient details', { patientId });

      const response = await fetch(`/api/patients/${patientId}`, {
        credentials: 'include',
      });

      const duration = performance.now() - startTime;

      if (!response.ok) {
        logger.logAPICall('GET', `/api/patients/${patientId}`, response.status, duration, 'Fetch failed');
        throw new Error(`Failed to fetch patient: ${response.status}`);
      }

      const data = await response.json();
      logger.logAPICall('GET', `/api/patients/${patientId}`, response.status, duration);
      logger.info('Patient details fetched', {
        patientId,
        name: data.name,
      });

      return data;
    },
    staleTime: 30000,
    retry: 2,
  });

  // Handle navigation
  const handleBack = () => {
    logger.logAction('Navigate back to patient list');
    navigate('/patients');
  };

  const handleEdit = () => {
    logger.logAction('Navigate to edit patient', { patientId });
    navigate(`/patients/${patientId}/edit`);
  };

  const handleViewOwner = () => {
    logger.logAction('Navigate to owner details', { ownerId: patient.owner_id });
    navigate(`/clients/${patient.owner_id}`);
  };

  // Get status chip color
  const getStatusColor = (status) => {
    switch (status) {
      case 'Active':
        return 'success';
      case 'Inactive':
        return 'default';
      case 'Deceased':
        return 'error';
      default:
        return 'default';
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
        <Typography variant="body1" sx={{ ml: 2 }}>
          Loading patient details...
        </Typography>
      </Box>
    );
  }

  // Error state
  if (isError) {
    logger.error('Error loading patient details', error);
    return (
      <Box p={3}>
        <Alert severity="error" onClose={() => refetch()}>
          Error loading patient: {error.message}. Click to retry.
        </Alert>
        <Button startIcon={<ArrowBackIcon />} onClick={handleBack} sx={{ mt: 2 }}>
          Back to Patients
        </Button>
      </Box>
    );
  }

  if (!patient) {
    return (
      <Box p={3}>
        <Alert severity="warning">
          Patient not found.
        </Alert>
        <Button startIcon={<ArrowBackIcon />} onClick={handleBack} sx={{ mt: 2 }}>
          Back to Patients
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box mb={3} display="flex" justifyContent="space-between" alignItems="center">
        <Box display="flex" alignItems="center">
          <IconButton onClick={handleBack} sx={{ mr: 1 }}>
            <ArrowBackIcon />
          </IconButton>
          {patient.photo_url && (
            <Avatar
              src={patient.photo_url}
              alt={patient.name}
              sx={{ width: 56, height: 56, mr: 2 }}
            />
          )}
          <Box>
            <Typography variant="h4" component="h1">
              {patient.name}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {patient.breed || 'Unknown Breed'} • {patient.age_display}
            </Typography>
          </Box>
          <Chip
            label={patient.status}
            color={getStatusColor(patient.status)}
            size="small"
            sx={{ ml: 2 }}
          />
        </Box>
        <Button
          variant="contained"
          startIcon={<EditIcon />}
          onClick={handleEdit}
          disabled={patient.status === 'Deceased'}
        >
          Edit
        </Button>
      </Box>

      <Grid container spacing={3}>
        {/* Basic Information */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader
              title="Basic Information"
              avatar={<PetsIcon />}
            />
            <CardContent>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="caption" color="text.secondary">
                    Species
                  </Typography>
                  <Typography variant="body1">{patient.species}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="caption" color="text.secondary">
                    Breed
                  </Typography>
                  <Typography variant="body1">{patient.breed || 'Unknown'}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="caption" color="text.secondary">
                    Color
                  </Typography>
                  <Typography variant="body1">{patient.color || 'Not specified'}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="caption" color="text.secondary">
                    Sex
                  </Typography>
                  <Typography variant="body1">{patient.sex || 'Unknown'}</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="caption" color="text.secondary">
                    Reproductive Status
                  </Typography>
                  <Typography variant="body1">
                    {patient.reproductive_status || 'Unknown'}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="caption" color="text.secondary">
                    Weight
                  </Typography>
                  <Typography variant="body1">
                    {patient.weight_kg ? `${patient.weight_kg} kg` : 'Not recorded'}
                  </Typography>
                </Grid>
                {patient.date_of_birth && (
                  <Grid item xs={12}>
                    <Typography variant="caption" color="text.secondary">
                      Date of Birth
                    </Typography>
                    <Typography variant="body1">
                      {new Date(patient.date_of_birth).toLocaleDateString()}
                    </Typography>
                  </Grid>
                )}
              </Grid>

              {patient.markings && (
                <>
                  <Divider sx={{ my: 2 }} />
                  <Typography variant="caption" color="text.secondary">
                    Markings / Distinguishing Features
                  </Typography>
                  <Typography variant="body1" style={{ whiteSpace: 'pre-wrap' }}>
                    {patient.markings}
                  </Typography>
                </>
              )}

              {patient.microchip_number && (
                <>
                  <Divider sx={{ my: 2 }} />
                  <Box display="flex" alignItems="center">
                    <ChipIcon sx={{ mr: 1, color: 'primary.main' }} />
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Microchip Number
                      </Typography>
                      <Typography variant="body1" fontWeight="medium">
                        {patient.microchip_number}
                      </Typography>
                    </Box>
                  </Box>
                </>
              )}

              {patient.status === 'Deceased' && patient.deceased_date && (
                <>
                  <Divider sx={{ my: 2 }} />
                  <Alert severity="error">
                    Deceased on {new Date(patient.deceased_date).toLocaleDateString()}
                  </Alert>
                </>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Owner Information */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader
              title="Owner Information"
              avatar={<PersonIcon />}
              action={
                <Button size="small" onClick={handleViewOwner}>
                  View Profile
                </Button>
              }
            />
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {patient.owner_name || 'Unknown Owner'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Click "View Profile" to see full owner details and other pets
              </Typography>
            </CardContent>
          </Card>

          {/* Insurance Information */}
          {(patient.insurance_company || patient.insurance_policy_number) && (
            <Card sx={{ mt: 2 }}>
              <CardHeader
                title="Insurance Information"
                avatar={<InsuranceIcon />}
              />
              <CardContent>
                {patient.insurance_company && (
                  <Box mb={2}>
                    <Typography variant="caption" color="text.secondary">
                      Insurance Company
                    </Typography>
                    <Typography variant="body1">{patient.insurance_company}</Typography>
                  </Box>
                )}
                {patient.insurance_policy_number && (
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Policy Number
                    </Typography>
                    <Typography variant="body1">{patient.insurance_policy_number}</Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
          )}
        </Grid>

        {/* Medical Information */}
        <Grid item xs={12}>
          <Card>
            <CardHeader
              title="Medical Information"
              avatar={<MedicalIcon />}
            />
            <CardContent>
              <Grid container spacing={3}>
                {patient.allergies && (
                  <Grid item xs={12} md={4}>
                    <Typography variant="subtitle2" color="error.main" gutterBottom>
                      Allergies
                    </Typography>
                    <Alert severity="error" sx={{ mt: 1 }}>
                      {patient.allergies}
                    </Alert>
                  </Grid>
                )}
                {patient.medical_notes && (
                  <Grid item xs={12} md={patient.allergies ? 4 : 6}>
                    <Typography variant="subtitle2" gutterBottom>
                      Medical Notes
                    </Typography>
                    <Typography variant="body2" style={{ whiteSpace: 'pre-wrap' }}>
                      {patient.medical_notes}
                    </Typography>
                  </Grid>
                )}
                {patient.behavioral_notes && (
                  <Grid item xs={12} md={patient.allergies ? 4 : 6}>
                    <Typography variant="subtitle2" gutterBottom>
                      Behavioral Notes
                    </Typography>
                    <Typography variant="body2" style={{ whiteSpace: 'pre-wrap' }}>
                      {patient.behavioral_notes}
                    </Typography>
                  </Grid>
                )}
                {!patient.allergies && !patient.medical_notes && !patient.behavioral_notes && (
                  <Grid item xs={12}>
                    <Typography variant="body2" color="text.secondary">
                      No medical notes recorded yet.
                    </Typography>
                  </Grid>
                )}
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Metadata */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
            <Typography variant="caption" color="text.secondary">
              Created: {new Date(patient.created_at).toLocaleString()} |
              Last Updated: {new Date(patient.updated_at).toLocaleString()}
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}

export default PatientDetail;
