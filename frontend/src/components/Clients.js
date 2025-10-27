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
  FormControlLabel,
  Switch,
} from '@mui/material';
import {
  Search as SearchIcon,
  Add as AddIcon,
  Clear as ClearIcon,
  Person as PersonIcon,
} from '@mui/icons-material';
import logger from '../utils/logger';

/**
 * Client List Component
 *
 * Displays list of clients (cat owners) with search, filter, and pagination.
 * Features:
 * - Search by name, email, or phone
 * - Filter by active/inactive status
 * - Pagination
 * - Comprehensive logging
 */
function Clients() {
  const navigate = useNavigate();

  // State for pagination and search
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(50);
  const [searchTerm, setSearchTerm] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [activeOnly, setActiveOnly] = useState(true);

  useEffect(() => {
    logger.logLifecycle('Clients', 'mounted', {
      initialPage: page,
      rowsPerPage,
      activeOnly,
    });

    return () => {
      logger.logLifecycle('Clients', 'unmounted');
    };
  }, []);

  // Fetch clients with React Query
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['clients', page + 1, rowsPerPage, searchTerm, activeOnly],
    queryFn: async () => {
      const startTime = performance.now();
      logger.logAction('Fetching clients', {
        page: page + 1,
        perPage: rowsPerPage,
        search: searchTerm,
        activeOnly,
      });

      const params = new URLSearchParams({
        page: page + 1,
        per_page: rowsPerPage,
        active_only: activeOnly,
      });

      if (searchTerm) {
        params.append('search', searchTerm);
      }

      const response = await fetch(`/api/clients?${params.toString()}`, {
        credentials: 'include',
      });

      const duration = performance.now() - startTime;

      if (!response.ok) {
        logger.logAPICall('GET', '/api/clients', response.status, duration, 'Fetch failed');
        throw new Error('Failed to fetch clients');
      }

      const data = await response.json();
      logger.logAPICall('GET', '/api/clients', response.status, duration);
      logger.info('Clients fetched successfully', {
        count: data.clients.length,
        total: data.pagination.total,
      });

      return data;
    },
    staleTime: 30000, // 30 seconds
    retry: 2,
  });

  // Handle search
  const handleSearch = () => {
    logger.logAction('Search clients', { searchTerm: searchInput });
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

  // Handle active filter
  const handleActiveFilterChange = (event) => {
    const newActiveOnly = event.target.checked;
    logger.logAction('Toggle active filter', { activeOnly: newActiveOnly });
    setActiveOnly(newActiveOnly);
    setPage(0);
  };

  // Handle row click
  const handleRowClick = (clientId) => {
    logger.logAction('View client details', { clientId });
    navigate(`/clients/${clientId}`);
  };

  // Handle create new client
  const handleCreateClient = () => {
    logger.logAction('Navigate to create client');
    navigate('/clients/new');
  };

  // Loading state
  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
        <Typography variant="body1" sx={{ ml: 2 }}>
          Loading clients...
        </Typography>
      </Box>
    );
  }

  // Error state
  if (isError) {
    logger.error('Error loading clients', error);
    return (
      <Box p={3}>
        <Alert severity="error" onClose={() => refetch()}>
          Error loading clients: {error.message}. Click to retry.
        </Alert>
      </Box>
    );
  }

  const clients = data?.clients || [];
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
          <PersonIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Clients (Cat Owners)
        </Typography>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={handleCreateClient}
        >
          New Client
        </Button>
      </Box>

      {/* Search and Filters */}
      <Paper sx={{ mb: 2 }}>
        <Toolbar>
          <TextField
            fullWidth
            variant="outlined"
            size="small"
            placeholder="Search by name, email, or phone..."
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
          <Button variant="contained" onClick={handleSearch} disabled={!searchInput && !searchTerm}>
            Search
          </Button>
          <FormControlLabel
            control={<Switch checked={activeOnly} onChange={handleActiveFilterChange} />}
            label="Active Only"
            sx={{ ml: 2 }}
          />
        </Toolbar>
      </Paper>

      {/* Results count */}
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
        {searchTerm && `Search results for "${searchTerm}" - `}
        Showing {clients.length} of {pagination.total} clients
      </Typography>

      {/* Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Phone</TableCell>
              <TableCell>City</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Balance</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {clients.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  <Typography variant="body1" color="text.secondary" py={4}>
                    {searchTerm
                      ? 'No clients found matching your search.'
                      : 'No clients yet. Click "New Client" to add one.'}
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              clients.map((client) => (
                <TableRow
                  key={client.id}
                  hover
                  onClick={() => handleRowClick(client.id)}
                  sx={{ cursor: 'pointer' }}
                >
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium">
                      {client.first_name} {client.last_name}
                    </Typography>
                  </TableCell>
                  <TableCell>{client.email || '-'}</TableCell>
                  <TableCell>{client.phone_primary}</TableCell>
                  <TableCell>{client.city || '-'}</TableCell>
                  <TableCell>
                    {client.is_active ? (
                      <Chip label="Active" color="success" size="small" />
                    ) : (
                      <Chip label="Inactive" color="default" size="small" />
                    )}
                  </TableCell>
                  <TableCell align="right">
                    {client.account_balance
                      ? `$${parseFloat(client.account_balance).toFixed(2)}`
                      : '$0.00'}
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

export default Clients;
