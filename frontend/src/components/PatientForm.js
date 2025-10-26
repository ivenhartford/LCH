import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  Box,
  Paper,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Grid,
  TextField,
  MenuItem,
  IconButton,
  Divider,
  Autocomplete,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Save as SaveIcon,
} from '@mui/icons-material';
import logger from '../utils/logger';

// Validation schema using Zod
const patientSchema = z.object({
  name: z.string().min(1, 'Name is required').max(100),
  species: z.string().default('Cat'),
  breed: z.string().max(100).optional(),
  color: z.string().max(100).optional(),
  markings: z.string().optional(),
  sex: z.enum(['Male', 'Female', '']).optional(),
  reproductive_status: z.enum(['Intact', 'Spayed', 'Neutered', '']).optional(),
  date_of_birth: z.string().optional(), // Will be converted to date by API
  approximate_age: z.string().max(50).optional(),
  weight_kg: z.string().optional(), // Will be converted to decimal by API
  microchip_number: z.string().max(50).optional(),
  owner_id: z.number({ required_error: 'Owner is required' }),
  insurance_company: z.string().max(100).optional(),
  insurance_policy_number: z.string().max(100).optional(),
  allergies: z.string().optional(),
  medical_notes: z.string().optional(),
  behavioral_notes: z.string().optional(),
  status: z.enum(['Active', 'Inactive', 'Deceased']).default('Active'),
  deceased_date: z.string().optional(), // Only if status is Deceased
});

/**
 * Patient (Cat) Form Component
 *
 * Handles both creating new patients and editing existing ones.
 * Features:
 * - Comprehensive validation with Zod
 * - React Hook Form integration
 * - Owner selection from list of clients
 * - Material-UI fields
 * - Comprehensive logging
 * - Loading and error states
 */
function PatientForm() {
  const { patientId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [searchParams] = useSearchParams();
  const isEditMode = Boolean(patientId);
  const [selectedOwner, setSelectedOwner] = useState(null);
  const preselectedOwnerId = searchParams.get('owner_id');

  useEffect(() => {
    logger.logLifecycle('PatientForm', 'mounted', {
      mode: isEditMode ? 'edit' : 'create',
      patientId,
      preselectedOwnerId,
    });

    return () => {
      logger.logLifecycle('PatientForm', 'unmounted');
    };
  }, [isEditMode, patientId, preselectedOwnerId]);

  // Form setup
  const {
    control,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors, isDirty },
  } = useForm({
    resolver: zodResolver(patientSchema),
    defaultValues: {
      name: '',
      species: 'Cat',
      breed: '',
      color: '',
      markings: '',
      sex: '',
      reproductive_status: '',
      date_of_birth: '',
      approximate_age: '',
      weight_kg: '',
      microchip_number: '',
      owner_id: 0,
      insurance_company: '',
      insurance_policy_number: '',
      allergies: '',
      medical_notes: '',
      behavioral_notes: '',
      status: 'Active',
      deceased_date: '',
    },
  });

  // Watch status field to show/hide deceased_date
  const statusValue = watch('status');

  // Fetch owners/clients for selection
  const {
    data: ownersData,
    isLoading: isLoadingOwners,
  } = useQuery({
    queryKey: ['clients', 'all'],
    queryFn: async () => {
      logger.logAction('Fetching owners for patient form');
      const response = await fetch('/api/clients?per_page=1000&active_only=true', {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to fetch owners');
      }

      const data = await response.json();
      return data.clients || [];
    },
    staleTime: 60000, // 1 minute
  });

  // Fetch existing patient data (edit mode only)
  const {
    isLoading: isLoadingPatient,
    isError: isPatientError,
    error: patientError,
  } = useQuery({
    queryKey: ['patient', patientId],
    queryFn: async () => {
      const startTime = performance.now();
      logger.logAction('Fetching patient for edit', { patientId });

      const response = await fetch(`/api/patients/${patientId}`, {
        credentials: 'include',
      });

      const duration = performance.now() - startTime;

      if (!response.ok) {
        logger.logAPICall('GET', `/api/patients/${patientId}`, response.status, duration, 'Fetch failed');
        throw new Error('Failed to fetch patient');
      }

      const data = await response.json();
      logger.logAPICall('GET', `/api/patients/${patientId}`, response.status, duration);

      // Convert data for form
      const formData = {
        ...data,
        weight_kg: data.weight_kg ? String(data.weight_kg) : '',
        date_of_birth: data.date_of_birth || '',
        deceased_date: data.deceased_date || '',
        sex: data.sex || '',
        reproductive_status: data.reproductive_status || '',
      };

      // Find and set owner
      if (ownersData) {
        const owner = ownersData.find(o => o.id === data.owner_id);
        if (owner) {
          setSelectedOwner(owner);
        }
      }

      // Reset form with fetched data
      reset(formData);

      return data;
    },
    enabled: isEditMode && Boolean(ownersData),
    staleTime: 0, // Always fetch fresh data for editing
  });

  // Pre-populate owner if specified in URL
  useEffect(() => {
    if (preselectedOwnerId && ownersData && !isEditMode) {
      const ownerId = parseInt(preselectedOwnerId, 10);
      const owner = ownersData.find(o => o.id === ownerId);
      if (owner) {
        setSelectedOwner(owner);
        setValue('owner_id', owner.id);
        logger.info('Pre-populated owner from URL', { ownerId, ownerName: `${owner.first_name} ${owner.last_name}` });
      }
    }
  }, [preselectedOwnerId, ownersData, isEditMode, setValue]);

  // Create/Update mutation
  const mutation = useMutation({
    mutationFn: async (data) => {
      const url = isEditMode ? `/api/patients/${patientId}` : '/api/patients';
      const method = isEditMode ? 'PUT' : 'POST';

      const startTime = performance.now();
      logger.logAction(isEditMode ? 'Updating patient' : 'Creating patient', {
        patientId,
        data: { name: data.name, owner_id: data.owner_id },
      });

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(data),
      });

      const duration = performance.now() - startTime;

      if (!response.ok) {
        const errorData = await response.json();
        logger.logAPICall(method, url, response.status, duration, errorData.error || 'Request failed');
        throw new Error(errorData.error || 'Failed to save patient');
      }

      const result = await response.json();
      logger.logAPICall(method, url, response.status, duration);
      logger.info(isEditMode ? 'Patient updated' : 'Patient created', {
        patientId: result.id,
        name: result.name,
      });

      return result;
    },
    onSuccess: (data) => {
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: ['patients'] });
      queryClient.invalidateQueries({ queryKey: ['patient', data.id] });

      logger.logAction('Navigate to patient detail after save', { patientId: data.id });
      navigate(`/patients/${data.id}`);
    },
    onError: (error) => {
      logger.error('Error saving patient', error);
    },
  });

  // Handle form submission
  const onSubmit = (data) => {
    // Clean up empty optional fields and convert types
    const cleanedData = {};
    Object.entries(data).forEach(([key, value]) => {
      if (value !== '' && value !== 0) {
        cleanedData[key] = value;
      }
    });

    // Ensure owner_id is set
    if (!cleanedData.owner_id) {
      cleanedData.owner_id = data.owner_id;
    }

    // Remove deceased_date if status is not Deceased
    if (cleanedData.status !== 'Deceased') {
      delete cleanedData.deceased_date;
    }

    logger.logAction('Submitting patient form', {
      mode: isEditMode ? 'edit' : 'create',
      isDirty,
    });

    mutation.mutate(cleanedData);
  };

  // Handle navigation
  const handleBack = () => {
    if (isDirty) {
      const confirmLeave = window.confirm(
        'You have unsaved changes. Are you sure you want to leave?'
      );
      if (!confirmLeave) {
        logger.logAction('Cancelled navigation with unsaved changes');
        return;
      }
    }

    logger.logAction('Navigate back from patient form');
    navigate(isEditMode ? `/patients/${patientId}` : '/patients');
  };

  // Loading state
  if (isLoadingOwners || (isEditMode && isLoadingPatient)) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
        <Typography variant="body1" sx={{ ml: 2 }}>
          Loading...
        </Typography>
      </Box>
    );
  }

  // Error state (edit mode)
  if (isEditMode && isPatientError) {
    logger.error('Error loading patient for edit', patientError);
    return (
      <Box p={3}>
        <Alert severity="error">
          Error loading patient: {patientError.message}
        </Alert>
        <Button startIcon={<ArrowBackIcon />} onClick={handleBack} sx={{ mt: 2 }}>
          Back
        </Button>
      </Box>
    );
  }

  const owners = ownersData || [];

  return (
    <Box>
      {/* Header */}
      <Box mb={3} display="flex" justifyContent="space-between" alignItems="center">
        <Box display="flex" alignItems="center">
          <IconButton onClick={handleBack} sx={{ mr: 1 }}>
            <ArrowBackIcon />
          </IconButton>
          <Typography variant="h4" component="h1">
            {isEditMode ? 'Edit Patient' : 'New Patient'}
          </Typography>
        </Box>
      </Box>

      {/* Form */}
      <Paper sx={{ p: 3 }}>
        <form onSubmit={handleSubmit(onSubmit)}>
          {/* Mutation error */}
          {mutation.isError && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {mutation.error.message}
            </Alert>
          )}

          <Grid container spacing={3}>
            {/* Basic Information */}
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Basic Information
              </Typography>
            </Grid>

            <Grid item xs={12} sm={6}>
              <Controller
                name="name"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="Cat's Name"
                    required
                    error={!!errors.name}
                    helperText={errors.name?.message}
                  />
                )}
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <Controller
                name="species"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="Species"
                    disabled
                    helperText="Lenox Cat Hospital is a feline-only clinic"
                  />
                )}
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <Controller
                name="breed"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="Breed"
                    placeholder="e.g., Persian, Siamese, Domestic Shorthair"
                  />
                )}
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <Controller
                name="color"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="Color"
                    placeholder="e.g., Orange Tabby, Black, Calico"
                  />
                )}
              />
            </Grid>

            <Grid item xs={12}>
              <Controller
                name="markings"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    multiline
                    rows={2}
                    label="Markings / Distinguishing Features"
                    placeholder="Special markings, patterns, or distinguishing features"
                  />
                )}
              />
            </Grid>

            {/* Physical Details */}
            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Typography variant="h6" gutterBottom>
                Physical Details
              </Typography>
            </Grid>

            <Grid item xs={12} sm={6}>
              <Controller
                name="sex"
                control={control}
                render={({ field }) => (
                  <TextField {...field} fullWidth select label="Sex">
                    <MenuItem value="">Unknown</MenuItem>
                    <MenuItem value="Male">Male</MenuItem>
                    <MenuItem value="Female">Female</MenuItem>
                  </TextField>
                )}
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <Controller
                name="reproductive_status"
                control={control}
                render={({ field }) => (
                  <TextField {...field} fullWidth select label="Reproductive Status">
                    <MenuItem value="">Unknown</MenuItem>
                    <MenuItem value="Intact">Intact</MenuItem>
                    <MenuItem value="Spayed">Spayed</MenuItem>
                    <MenuItem value="Neutered">Neutered</MenuItem>
                  </TextField>
                )}
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <Controller
                name="date_of_birth"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    type="date"
                    label="Date of Birth"
                    InputLabelProps={{ shrink: true }}
                    helperText="Leave empty if unknown"
                  />
                )}
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <Controller
                name="approximate_age"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="Approximate Age (if DOB unknown)"
                    placeholder="e.g., 2 years, 6 months"
                  />
                )}
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <Controller
                name="weight_kg"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    type="number"
                    label="Weight (kg)"
                    inputProps={{ step: '0.01', min: '0' }}
                  />
                )}
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <Controller
                name="microchip_number"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="Microchip Number"
                    error={!!errors.microchip_number}
                    helperText={errors.microchip_number?.message}
                  />
                )}
              />
            </Grid>

            {/* Owner */}
            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Typography variant="h6" gutterBottom>
                Owner Information
              </Typography>
            </Grid>

            <Grid item xs={12}>
              <Controller
                name="owner_id"
                control={control}
                render={({ field }) => (
                  <Autocomplete
                    options={owners}
                    getOptionLabel={(option) => `${option.first_name} ${option.last_name}`}
                    value={selectedOwner}
                    onChange={(event, newValue) => {
                      setSelectedOwner(newValue);
                      field.onChange(newValue ? newValue.id : 0);
                    }}
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        label="Owner"
                        required
                        error={!!errors.owner_id}
                        helperText={errors.owner_id?.message || 'Select the cat owner from the list'}
                      />
                    )}
                  />
                )}
              />
            </Grid>

            {/* Medical Information */}
            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Typography variant="h6" gutterBottom>
                Medical Information
              </Typography>
            </Grid>

            <Grid item xs={12}>
              <Controller
                name="allergies"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    multiline
                    rows={2}
                    label="Allergies"
                    placeholder="Known allergies or sensitivities"
                    error={!!errors.allergies}
                    helperText={errors.allergies?.message}
                  />
                )}
              />
            </Grid>

            <Grid item xs={12}>
              <Controller
                name="medical_notes"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    multiline
                    rows={3}
                    label="Medical Notes"
                    placeholder="Important medical notes, conditions, or history"
                  />
                )}
              />
            </Grid>

            <Grid item xs={12}>
              <Controller
                name="behavioral_notes"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    multiline
                    rows={3}
                    label="Behavioral Notes"
                    placeholder="Temperament, behavior, handling notes"
                  />
                )}
              />
            </Grid>

            {/* Insurance */}
            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Typography variant="h6" gutterBottom>
                Insurance Information
              </Typography>
            </Grid>

            <Grid item xs={12} sm={6}>
              <Controller
                name="insurance_company"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="Insurance Company"
                  />
                )}
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <Controller
                name="insurance_policy_number"
                control={control}
                render={({ field }) => (
                  <TextField
                    {...field}
                    fullWidth
                    label="Policy Number"
                  />
                )}
              />
            </Grid>

            {/* Status */}
            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Typography variant="h6" gutterBottom>
                Status
              </Typography>
            </Grid>

            <Grid item xs={12} sm={6}>
              <Controller
                name="status"
                control={control}
                render={({ field }) => (
                  <TextField {...field} fullWidth select label="Status">
                    <MenuItem value="Active">Active</MenuItem>
                    <MenuItem value="Inactive">Inactive</MenuItem>
                    <MenuItem value="Deceased">Deceased</MenuItem>
                  </TextField>
                )}
              />
            </Grid>

            {statusValue === 'Deceased' && (
              <Grid item xs={12} sm={6}>
                <Controller
                  name="deceased_date"
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      fullWidth
                      type="date"
                      label="Deceased Date"
                      InputLabelProps={{ shrink: true }}
                    />
                  )}
                />
              </Grid>
            )}

            {/* Actions */}
            <Grid item xs={12}>
              <Box display="flex" justifyContent="flex-end" gap={2} mt={2}>
                <Button onClick={handleBack} disabled={mutation.isPending}>
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="contained"
                  startIcon={mutation.isPending ? <CircularProgress size={20} /> : <SaveIcon />}
                  disabled={mutation.isPending || !isDirty}
                >
                  {mutation.isPending ? 'Saving...' : 'Save Patient'}
                </Button>
              </Box>
            </Grid>
          </Grid>
        </form>
      </Paper>
    </Box>
  );
}

export default PatientForm;
