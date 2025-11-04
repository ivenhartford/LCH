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
  Card,
  CardContent,
  CardActions,
  Grid,
  useMediaQuery,
  useTheme,
  Divider,
} from '@mui/material';
import {
  Search as SearchIcon,
  Add as AddIcon,
  Clear as ClearIcon,
  Pets as PetsIcon,
  Cake as CakeIcon,
  ColorLens as ColorIcon,
  Person as PersonIcon,
  ChevronRight as ChevronRightIcon,
} from '@mui/icons-material';
import logger from '../utils/logger';
import TableSkeleton from './common/TableSkeleton';
import EmptyState from './common/EmptyState';

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
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

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
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
      <Box>
        <Box mb={3} display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h4" component="h1">
            <PetsIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
            Patients (Cats)
          </Typography>
        </Box>
        <TableSkeleton
          rows={rowsPerPage}
          columns={7}
          headers={['Name', 'Breed', 'Color', 'Age', 'Sex', 'Owner', 'Status']}
        />
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
          aria-label="Create new patient"
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
                  <IconButton
                    onClick={handleClearSearch}
                    aria-label="Clear search"
                    sx={{
                      minWidth: 44,
                      minHeight: 44,
                    }}
                  >
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
            aria-label="Search patients"
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
      {patients.length > 0 && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {searchTerm && `Search results for "${searchTerm}" - `}
          Showing {patients.length} of {pagination.total} patients
        </Typography>
      )}

      {/* Empty State or Patient List */}
      {patients.length === 0 ? (
        <EmptyState
          icon={PetsIcon}
          title={searchTerm ? 'No Patients Found' : 'No Patients Yet'}
          message={
            searchTerm
              ? `No patients match your search for "${searchTerm}". Try adjusting your search terms or filters.`
              : 'Get started by adding your first patient to the system. Patients are the cats that receive veterinary care.'
          }
          actionLabel={searchTerm ? undefined : 'New Patient'}
          onAction={searchTerm ? undefined : handleCreatePatient}
          actionIcon={AddIcon}
          secondaryActionLabel={searchTerm ? 'Clear Search' : undefined}
          onSecondaryAction={searchTerm ? handleClearSearch : undefined}
        />
      ) : isMobile ? (
        /* Mobile Card Layout */
        <>
          <Grid container spacing={2}>
            {patients.map((patient) => (
              <Grid item xs={12} key={patient.id}>
                <Card
                  sx={{
                    cursor: 'pointer',
                    '&:hover': {
                      boxShadow: 3,
                      transform: 'translateY(-2px)',
                      transition: 'all 0.2s ease-in-out',
                    },
                  }}
                  onClick={() => handleRowClick(patient.id)}
                >
                  <CardContent>
                    <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
                      <Typography variant="h6" component="h2">
                        {patient.name}
                      </Typography>
                      <Chip
                        label={patient.status}
                        color={getStatusColor(patient.status)}
                        size="small"
                      />
                    </Box>

                    <Box display="flex" flexDirection="column" gap={1}>
                      {patient.breed && (
                        <Box display="flex" alignItems="center" gap={1}>
                          <PetsIcon fontSize="small" color="action" />
                          <Typography variant="body2" color="text.secondary">
                            {patient.breed}
                          </Typography>
                        </Box>
                      )}

                      {patient.color && (
                        <Box display="flex" alignItems="center" gap={1}>
                          <ColorIcon fontSize="small" color="action" />
                          <Typography variant="body2" color="text.secondary">
                            {patient.color}
                          </Typography>
                        </Box>
                      )}

                      {patient.age_display && (
                        <Box display="flex" alignItems="center" gap={1}>
                          <CakeIcon fontSize="small" color="action" />
                          <Typography variant="body2" color="text.secondary">
                            {patient.age_display} {patient.sex && `• ${patient.sex}`}
                          </Typography>
                        </Box>
                      )}

                      {patient.owner_name && (
                        <Box display="flex" alignItems="center" gap={1}>
                          <PersonIcon fontSize="small" color="action" />
                          <Typography variant="body2" color="text.secondary">
                            {patient.owner_name}
                          </Typography>
                        </Box>
                      )}

                      {patient.microchip_number && (
                        <Box mt={1}>
                          <Chip
                            label={`Chip: ${patient.microchip_number}`}
                            size="small"
                            variant="outlined"
                          />
                        </Box>
                      )}
                    </Box>
                  </CardContent>

                  <CardActions sx={{ justifyContent: 'flex-end', pt: 0 }}>
                    <Button
                      size="small"
                      endIcon={<ChevronRightIcon />}
                      onClick={() => handleRowClick(patient.id)}
                    >
                      View Details
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>

          <Box mt={2}>
            <TablePagination
              rowsPerPageOptions={[10, 25, 50, 100]}
              component="div"
              count={pagination.total}
              rowsPerPage={rowsPerPage}
              page={page}
              onPageChange={handleChangePage}
              onRowsPerPageChange={handleChangeRowsPerPage}
            />
          </Box>
        </>
      ) : (
        /* Desktop Table Layout */
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
              {patients.map((patient) => (
                <TableRow
                  key={patient.id}
                  hover
                  onClick={() => handleRowClick(patient.id)}
                  sx={{ cursor: 'pointer' }}
                  aria-label={`View details for ${patient.name}`}
                  role="button"
                  tabIndex={0}
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
              ))}
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
      )}
    </Box>
  );
}

export default Patients;
