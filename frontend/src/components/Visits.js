import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  CircularProgress,
  Alert,
  Chip,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Add as AddIcon,
  Visibility as ViewIcon,
  FilterList as FilterIcon,
} from '@mui/icons-material';
import logger from '../utils/logger';

/**
 * Visits List Component
 *
 * Displays a filterable, paginated list of all visits.
 * Features:
 * - Filter by patient, status, visit type
 * - Pagination
 * - Quick view/edit
 * - Create new visit
 */
function Visits() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  // State
  const [page, setPage] = useState(parseInt(searchParams.get('page') || '0', 10));
  const [rowsPerPage, setRowsPerPage] = useState(
    parseInt(searchParams.get('per_page') || '25', 10)
  );
  const [statusFilter, setStatusFilter] = useState(searchParams.get('status') || '');
  const [typeFilter, setTypeFilter] = useState(searchParams.get('visit_type') || '');
  const [patientSearch, setPatientSearch] = useState(searchParams.get('patient_id') || '');

  useEffect(() => {
    logger.logLifecycle('Visits', 'mounted');

    return () => {
      logger.logLifecycle('Visits', 'unmounted');
    };
  }, []);

  // Fetch visits
  const {
    data: visitsData,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ['visits', page, rowsPerPage, statusFilter, typeFilter, patientSearch],
    queryFn: async () => {
      const startTime = performance.now();

      const params = new URLSearchParams({
        page: (page + 1).toString(),
        per_page: rowsPerPage.toString(),
      });

      if (statusFilter) params.append('status', statusFilter);
      if (typeFilter) params.append('visit_type', typeFilter);
      if (patientSearch) params.append('patient_id', patientSearch);

      logger.logAction('Fetching visits', { page, rowsPerPage, statusFilter, typeFilter });

      const response = await fetch(`/api/visits?${params}`, {
        credentials: 'include',
      });

      const duration = performance.now() - startTime;

      if (!response.ok) {
        logger.logAPICall('GET', '/api/visits', response.status, duration, 'Fetch failed');
        throw new Error(`Failed to fetch visits: ${response.status}`);
      }

      const data = await response.json();
      logger.logAPICall('GET', '/api/visits', response.status, duration);
      logger.info('Visits fetched', { count: data.visits?.length || 0, total: data.total });

      return data;
    },
    staleTime: 30000,
    retry: 2,
  });

  // Update URL params
  useEffect(() => {
    const params = {};
    if (page > 0) params.page = page.toString();
    if (rowsPerPage !== 25) params.per_page = rowsPerPage.toString();
    if (statusFilter) params.status = statusFilter;
    if (typeFilter) params.visit_type = typeFilter;
    if (patientSearch) params.patient_id = patientSearch;

    setSearchParams(params);
  }, [page, rowsPerPage, statusFilter, typeFilter, patientSearch, setSearchParams]);

  const handleChangePage = (event, newPage) => {
    logger.logAction('Change page', { from: page, to: newPage });
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    const newRowsPerPage = parseInt(event.target.value, 10);
    logger.logAction('Change rows per page', {
      from: rowsPerPage,
      to: newRowsPerPage,
    });
    setRowsPerPage(newRowsPerPage);
    setPage(0);
  };

  const handleViewVisit = (visitId) => {
    logger.logAction('Navigate to visit detail', { visitId });
    navigate(`/visits/${visitId}`);
  };

  const handleNewVisit = () => {
    logger.logAction('Navigate to new visit form');
    navigate('/visits/new');
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

  const getVisitTypeColor = (type) => {
    switch (type) {
      case 'Emergency':
        return 'error';
      case 'Surgery':
        return 'warning';
      case 'Wellness':
        return 'success';
      default:
        return 'default';
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return (
      date.toLocaleDateString() +
      ' ' +
      date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    );
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
        <Alert severity="error">
          Failed to load visits: {error.message}
          <Button onClick={() => refetch()} sx={{ ml: 2 }}>
            Retry
          </Button>
        </Alert>
      </Box>
    );
  }

  const visits = visitsData?.visits || [];
  const total = visitsData?.total || 0;

  return (
    <Box>
      {/* Header */}
      <Box mb={3} display="flex" justifyContent="space-between" alignItems="center">
        <Typography variant="h4" component="h1">
          Visits
        </Typography>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={handleNewVisit}
        >
          New Visit
        </Button>
      </Box>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box display="flex" gap={2} alignItems="center" flexWrap="wrap">
          <FilterIcon color="action" />
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Status</InputLabel>
            <Select
              value={statusFilter}
              label="Status"
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(0);
              }}
            >
              <MenuItem value="">All</MenuItem>
              <MenuItem value="scheduled">Scheduled</MenuItem>
              <MenuItem value="in_progress">In Progress</MenuItem>
              <MenuItem value="completed">Completed</MenuItem>
              <MenuItem value="cancelled">Cancelled</MenuItem>
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Visit Type</InputLabel>
            <Select
              value={typeFilter}
              label="Visit Type"
              onChange={(e) => {
                setTypeFilter(e.target.value);
                setPage(0);
              }}
            >
              <MenuItem value="">All</MenuItem>
              <MenuItem value="Wellness">Wellness</MenuItem>
              <MenuItem value="Sick">Sick</MenuItem>
              <MenuItem value="Emergency">Emergency</MenuItem>
              <MenuItem value="Follow-up">Follow-up</MenuItem>
              <MenuItem value="Surgery">Surgery</MenuItem>
              <MenuItem value="Dental">Dental</MenuItem>
              <MenuItem value="Other">Other</MenuItem>
            </Select>
          </FormControl>

          <TextField
            size="small"
            label="Patient ID"
            value={patientSearch}
            onChange={(e) => {
              setPatientSearch(e.target.value);
              setPage(0);
            }}
            sx={{ width: 120 }}
          />

          {(statusFilter || typeFilter || patientSearch) && (
            <Button
              size="small"
              onClick={() => {
                setStatusFilter('');
                setTypeFilter('');
                setPatientSearch('');
                setPage(0);
              }}
            >
              Clear Filters
            </Button>
          )}
        </Box>
      </Paper>

      {/* Table */}
      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Date</TableCell>
                <TableCell>Patient</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Veterinarian</TableCell>
                <TableCell>Chief Complaint</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {visits.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    <Typography variant="body2" color="text.secondary" py={4}>
                      No visits found.
                      {(statusFilter || typeFilter || patientSearch) && ' Try adjusting filters.'}
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                visits.map((visit) => (
                  <TableRow key={visit.id} hover>
                    <TableCell>{formatDate(visit.visit_date)}</TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {visit.patient_name || `Patient #${visit.patient_id}`}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={visit.visit_type}
                        color={getVisitTypeColor(visit.visit_type)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={visit.status}
                        color={getStatusColor(visit.status)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {visit.veterinarian_name || '-'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" noWrap sx={{ maxWidth: 300 }}>
                        {visit.chief_complaint || '-'}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Tooltip title="View Details">
                        <IconButton
                          size="small"
                          onClick={() => handleViewVisit(visit.id)}
                          color="primary"
                        >
                          <ViewIcon />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          component="div"
          count={total}
          page={page}
          onPageChange={handleChangePage}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          rowsPerPageOptions={[10, 25, 50, 100]}
        />
      </Paper>
    </Box>
  );
}

export default Visits;
