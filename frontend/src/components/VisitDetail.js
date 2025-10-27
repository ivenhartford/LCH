import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Box,
  Paper,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  IconButton,
  Chip,
} from '@mui/material';
import { ArrowBack as ArrowBackIcon, CheckCircle as CompleteIcon } from '@mui/icons-material';
import VisitOverview from './visits/VisitOverview';
import SOAPNoteTab from './visits/SOAPNoteTab';
import VitalSignsTab from './visits/VitalSignsTab';
import DiagnosesTab from './visits/DiagnosesTab';
import VaccinationsTab from './visits/VaccinationsTab';
import PrescriptionsTab from './visits/PrescriptionsTab';
import logger from '../utils/logger';

/**
 * Visit Detail Component
 *
 * Comprehensive visit management with tabs for:
 * - Overview (visit details, patient info)
 * - SOAP Notes
 * - Vital Signs
 * - Diagnoses
 * - Vaccinations
 */
function VisitDetail() {
  const { visitId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [currentTab, setCurrentTab] = useState(0);
  const [editMode, setEditMode] = useState(!visitId); // New visits start in edit mode

  useEffect(() => {
    logger.logLifecycle('VisitDetail', 'mounted', { visitId });

    return () => {
      logger.logLifecycle('VisitDetail', 'unmounted');
    };
  }, [visitId]);

  // Fetch visit data
  const {
    data: visit,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['visit', visitId],
    queryFn: async () => {
      if (!visitId || visitId === 'new') return null;

      const startTime = performance.now();
      logger.logAction('Fetching visit details', { visitId });

      const response = await fetch(`/api/visits/${visitId}`, {
        credentials: 'include',
      });

      const duration = performance.now() - startTime;

      if (!response.ok) {
        logger.logAPICall(
          'GET',
          `/api/visits/${visitId}`,
          response.status,
          duration,
          'Fetch failed'
        );
        throw new Error(`Failed to fetch visit: ${response.status}`);
      }

      const data = await response.json();
      logger.logAPICall('GET', `/api/visits/${visitId}`, response.status, duration);

      return data;
    },
    enabled: !!visitId && visitId !== 'new',
    staleTime: 30000,
  });

  // Mark visit as completed
  const completeVisitMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch(`/api/visits/${visitId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ status: 'completed' }),
      });

      if (!response.ok) {
        throw new Error('Failed to complete visit');
      }

      return response.json();
    },
    onSuccess: () => {
      logger.info('Visit marked as completed', { visitId });
      queryClient.invalidateQueries(['visit', visitId]);
      queryClient.invalidateQueries(['visits']);
    },
  });

  const handleBack = () => {
    logger.logAction('Navigate back from visit detail');
    navigate(-1);
  };

  const handleTabChange = (event, newValue) => {
    logger.logAction('Switch visit tab', { from: currentTab, to: newValue });
    setCurrentTab(newValue);
  };

  const handleCompleteVisit = () => {
    if (window.confirm('Mark this visit as completed?')) {
      logger.logAction('Complete visit', { visitId });
      completeVisitMutation.mutate();
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'in_progress':
        return 'warning';
      case 'scheduled':
        return 'info';
      case 'cancelled':
        return 'error';
      default:
        return 'default';
    }
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
        <Alert severity="error">Failed to load visit: {error.message}</Alert>
        <Button startIcon={<ArrowBackIcon />} onClick={handleBack} sx={{ mt: 2 }}>
          Back
        </Button>
      </Box>
    );
  }

  const isNewVisit = !visitId || visitId === 'new';

  return (
    <Box>
      {/* Header */}
      <Box mb={3} display="flex" justifyContent="space-between" alignItems="center">
        <Box display="flex" alignItems="center">
          <IconButton onClick={handleBack} sx={{ mr: 1 }}>
            <ArrowBackIcon />
          </IconButton>
          <Box>
            <Typography variant="h4" component="h1">
              {isNewVisit ? 'New Visit' : `Visit #${visitId}`}
            </Typography>
            {visit && (
              <Typography variant="body2" color="text.secondary">
                {visit.patient_name} • {new Date(visit.visit_date).toLocaleDateString()}
              </Typography>
            )}
          </Box>
          {visit && (
            <Chip
              label={visit.status}
              color={getStatusColor(visit.status)}
              size="small"
              sx={{ ml: 2 }}
            />
          )}
        </Box>
        <Box display="flex" gap={1}>
          {visit && visit.status !== 'completed' && visit.status !== 'cancelled' && (
            <Button
              variant="outlined"
              startIcon={<CompleteIcon />}
              onClick={handleCompleteVisit}
              disabled={completeVisitMutation.isLoading}
            >
              Complete Visit
            </Button>
          )}
        </Box>
      </Box>

      {/* Tabs */}
      <Paper sx={{ mb: 2 }}>
        <Tabs
          value={currentTab}
          onChange={handleTabChange}
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab label="Overview" />
          <Tab label="SOAP Notes" disabled={isNewVisit} />
          <Tab label="Vital Signs" disabled={isNewVisit} />
          <Tab label="Diagnoses" disabled={isNewVisit} />
          <Tab label="Vaccinations" disabled={isNewVisit} />
          <Tab label="Prescriptions" disabled={isNewVisit} />
        </Tabs>
      </Paper>

      {/* Tab Content */}
      <Box>
        {currentTab === 0 && (
          <VisitOverview
            visit={visit}
            isNewVisit={isNewVisit}
            editMode={editMode}
            setEditMode={setEditMode}
          />
        )}
        {currentTab === 1 && visit && <SOAPNoteTab visitId={visitId} />}
        {currentTab === 2 && visit && <VitalSignsTab visitId={visitId} />}
        {currentTab === 3 && visit && <DiagnosesTab visitId={visitId} />}
        {currentTab === 4 && visit && (
          <VaccinationsTab visitId={visitId} patientId={visit.patient_id} />
        )}
        {currentTab === 5 && visit && (
          <PrescriptionsTab visitId={visitId} patientId={visit.patient_id} />
        )}
      </Box>
    </Box>
  );
}

export default VisitDetail;
