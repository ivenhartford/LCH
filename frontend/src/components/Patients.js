import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  TextField,
  Button,
  Typography,
  CircularProgress,
  Alert,
  Chip,
  InputAdornment,
  IconButton,
  Toolbar,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material';
import {
  Search as SearchIcon,
  Add as AddIcon,
  Clear as ClearIcon,
  Pets as PetsIcon,
} from '@mui/icons-material';
import logger from '../utils/logger';

/**
 * Patient (Cat) List Component
 *
 * Displays list of cat patients with search, filter, and pagination.
 * Features:
 * - Search by name, breed, color, microchip, or owner name
 * - Filter by status (Active/Inactive/Deceased)
 * - Filter by owner
 * - Pagination
 * - Comprehensive logging
 */
function Patients() {
  const navigate = useNavigate();

  // State for pagination and search
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(50);
  const [searchTerm, setSearchTerm] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [statusFilter, setStatusFilter] = useState('Active');
  const [ownerFilter] = useState(''); // Not used in UI yet, reserved for future filter

  useEffect(() => {
    logger.logLifecycle('Patients', 'mounted', {
      initialPage: page,
      rowsPerPage,
      statusFilter,
    });

    return () => {
      logger.logLifecycle('Patients', 'unmounted');
    };
  }, []);

  // Fetch patients with React Query
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['patients', page + 1, rowsPerPage, searchTerm, statusFilter, ownerFilter],
    queryFn: async () => {
      const startTime = performance.now();
      logger.logAction('Fetching patients', {
        page: page + 1,
        perPage: rowsPerPage,
        search: searchTerm,
        status: statusFilter,
        ownerId: ownerFilter,
      });

      const params = new URLSearchParams({
        page: page + 1,
        per_page: rowsPerPage,
      });

      if (statusFilter) {
        params.append('status', statusFilter);
      }

      if (searchTerm) {
        params.append('search', searchTerm);
      }

      if (ownerFilter) {
        params.append('owner_id', ownerFilter);
      }

      const response = await fetch(`/api/patients?${params.toString()}`, {
        credentials: 'include',
      });

      const duration = performance.now() - startTime;

      if (!response.ok) {
        logger.logAPICall('GET', '/api/patients', response.status, duration, 'Fetch failed');
        throw new Error('Failed to fetch patients');
      }

      const data = await response.json();
      logger.logAPICall('GET', '/api/patients', response.status, duration);
      logger.info('Patients fetched successfully', {
        count: data.patients.length,
        total: data.pagination.total,
      });

      return data;
    },
    staleTime: 30000, // 30 seconds
    retry: 2,
  });

  // Handle search
  const handleSearch = () => {
    logger.logAction('Search patients', { searchTerm: searchInput });
    setSearchTerm(searchInput);
    setPage(0); // Reset to first page
  };

  const handleClearSearch = () => {
    logger.logAction('Clear search');
    setSearchInput('');
    setSearchTerm('');
    setPage(0);
  };

  const handleSearchKeyPress = (event) => {
    if (event.key === 'Enter') {
      handleSearch();
    }
  };

  // Handle pagination
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

  // Handle status filter
  const handleStatusFilterChange = (event) => {
    const newStatus = event.target.value;
    logger.logAction('Change status filter', { from: statusFilter, to: newStatus });
    setStatusFilter(newStatus);
    setPage(0);
  };

  // Handle row click
  const handleRowClick = (patientId) => {
    logger.logAction('View patient details', { patientId });
    navigate(`/patients/${patientId}`);
  };

  // Handle create new patient
  const handleCreatePatient = () => {
    logger.logAction('Navigate to create patient');
    navigate('/patients/new');
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
          Loading patients...
        </Typography>
      </Box>
    );
  }

  // Error state
  if (isError) {
    logger.error('Error loading patients', error);
    return (
      <Box p={3}>
        <Alert severity="error" onClose={() => refetch()}>
          Error loading patients: {error.message}. Click to retry.
        </Alert>
      </Box>
    );
  }

  const patients = data?.patients || [];
  const pagination = data?.pagination || {
    page: 1,
    total: 0,
    pages: 0,
  };

  return (
    <Box>
      {/* Header */}
      <Box mb={3} display="flex" justifyContent="space-between" alignItems="center">
        <Typography variant="h4" component="h1">
          <PetsIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Patients (Cats)
        </Typography>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={handleCreatePatient}
        >
          New Patient
        </Button>
      </Box>

      {/* Search and Filters */}
      <Paper sx={{ mb: 2 }}>
        <Toolbar>
          <TextField
            fullWidth
            variant="outlined"
            size="small"
            placeholder="Search by name, breed, color, microchip, or owner..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyPress={handleSearchKeyPress}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
              endAdornment: searchInput && (
                <InputAdornment position="end">
                  <IconButton size="small" onClick={handleClearSearch}>
                    <ClearIcon />
                  </IconButton>
                </InputAdornment>
              ),
            }}
            sx={{ mr: 2 }}
          />
          <Button
            variant="contained"
            onClick={handleSearch}
            disabled={!searchInput && !searchTerm}
            sx={{ mr: 2, minWidth: '100px' }}
          >
            Search
          </Button>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Status</InputLabel>
            <Select value={statusFilter} onChange={handleStatusFilterChange} label="Status">
              <MenuItem value="">All</MenuItem>
              <MenuItem value="Active">Active</MenuItem>
              <MenuItem value="Inactive">Inactive</MenuItem>
              <MenuItem value="Deceased">Deceased</MenuItem>
            </Select>
          </FormControl>
        </Toolbar>
      </Paper>

      {/* Results count */}
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
        {searchTerm && `Search results for "${searchTerm}" - `}
        Showing {patients.length} of {pagination.total} patients
      </Typography>

      {/* Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Breed</TableCell>
              <TableCell>Color</TableCell>
              <TableCell>Age</TableCell>
              <TableCell>Sex</TableCell>
              <TableCell>Owner</TableCell>
              <TableCell>Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {patients.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  <Typography variant="body1" color="text.secondary" py={4}>
                    {searchTerm
                      ? 'No patients found matching your search.'
                      : 'No patients yet. Click "New Patient" to add one.'}
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              patients.map((patient) => (
                <TableRow
                  key={patient.id}
                  hover
                  onClick={() => handleRowClick(patient.id)}
                  sx={{ cursor: 'pointer' }}
                >
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium">
                      {patient.name}
                    </Typography>
                    {patient.microchip_number && (
                      <Typography variant="caption" color="text.secondary" display="block">
                        Chip: {patient.microchip_number}
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>{patient.breed || 'Unknown'}</TableCell>
                  <TableCell>{patient.color || '-'}</TableCell>
                  <TableCell>{patient.age_display || 'Unknown'}</TableCell>
                  <TableCell>{patient.sex || '-'}</TableCell>
                  <TableCell>{patient.owner_name || 'Unknown'}</TableCell>
                  <TableCell>
                    <Chip
                      label={patient.status}
                      color={getStatusColor(patient.status)}
                      size="small"
                    />
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
        <TablePagination
          rowsPerPageOptions={[10, 25, 50, 100]}
          component="div"
          count={pagination.total}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </TableContainer>
    </Box>
  );
}

export default Patients;
