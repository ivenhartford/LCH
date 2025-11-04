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
  Person as PersonIcon,
  Email as EmailIcon,
  Phone as PhoneIcon,
  LocationOn as LocationIcon,
  ChevronRight as ChevronRightIcon,
} from '@mui/icons-material';
import logger from '../utils/logger';
import TableSkeleton from './common/TableSkeleton';
import EmptyState from './common/EmptyState';

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
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

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
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
      <Box>
        <Box mb={3} display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h4" component="h1">
            <PersonIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
            Clients (Cat Owners)
          </Typography>
        </Box>
        <TableSkeleton
          rows={rowsPerPage}
          columns={6}
          headers={['Name', 'Email', 'Phone', 'City', 'Status', 'Balance']}
        />
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
          aria-label="Create new client"
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
            aria-label="Search clients"
          >
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
      {clients.length > 0 && (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {searchTerm && `Search results for "${searchTerm}" - `}
          Showing {clients.length} of {pagination.total} clients
        </Typography>
      )}

      {/* Empty State or Client List */}
      {clients.length === 0 ? (
        <EmptyState
          icon={PersonIcon}
          title={searchTerm ? 'No Clients Found' : 'No Clients Yet'}
          message={
            searchTerm
              ? `No clients match your search for "${searchTerm}". Try adjusting your search terms or filters.`
              : 'Get started by adding your first client to the system. Clients are the cat owners who bring their pets for care.'
          }
          actionLabel={searchTerm ? undefined : 'New Client'}
          onAction={searchTerm ? undefined : handleCreateClient}
          actionIcon={AddIcon}
          secondaryActionLabel={searchTerm ? 'Clear Search' : undefined}
          onSecondaryAction={searchTerm ? handleClearSearch : undefined}
        />
      ) : isMobile ? (
        /* Mobile Card Layout */
        <>
          <Grid container spacing={2}>
            {clients.map((client) => (
              <Grid item xs={12} key={client.id}>
                <Card
                  sx={{
                    cursor: 'pointer',
                    '&:hover': {
                      boxShadow: 3,
                      transform: 'translateY(-2px)',
                      transition: 'all 0.2s ease-in-out',
                    },
                  }}
                  onClick={() => handleRowClick(client.id)}
                >
                  <CardContent>
                    <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
                      <Typography variant="h6" component="h2">
                        {client.first_name} {client.last_name}
                      </Typography>
                      {client.is_active ? (
                        <Chip label="Active" color="success" size="small" />
                      ) : (
                        <Chip label="Inactive" color="default" size="small" />
                      )}
                    </Box>

                    <Box display="flex" flexDirection="column" gap={1}>
                      {client.email && (
                        <Box display="flex" alignItems="center" gap={1}>
                          <EmailIcon fontSize="small" color="action" />
                          <Typography variant="body2" color="text.secondary">
                            {client.email}
                          </Typography>
                        </Box>
                      )}

                      <Box display="flex" alignItems="center" gap={1}>
                        <PhoneIcon fontSize="small" color="action" />
                        <Typography variant="body2" color="text.secondary">
                          {client.phone_primary}
                        </Typography>
                      </Box>

                      {client.city && (
                        <Box display="flex" alignItems="center" gap={1}>
                          <LocationIcon fontSize="small" color="action" />
                          <Typography variant="body2" color="text.secondary">
                            {client.city}
                          </Typography>
                        </Box>
                      )}
                    </Box>

                    <Divider sx={{ my: 1.5 }} />

                    <Box display="flex" justifyContent="space-between" alignItems="center">
                      <Typography variant="body2" color="text.secondary">
                        Account Balance
                      </Typography>
                      <Typography variant="h6" color="primary">
                        {client.account_balance
                          ? `$${parseFloat(client.account_balance).toFixed(2)}`
                          : '$0.00'}
                      </Typography>
                    </Box>
                  </CardContent>

                  <CardActions sx={{ justifyContent: 'flex-end', pt: 0 }}>
                    <Button
                      size="small"
                      endIcon={<ChevronRightIcon />}
                      onClick={() => handleRowClick(client.id)}
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
                <TableCell>Email</TableCell>
                <TableCell>Phone</TableCell>
                <TableCell>City</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Balance</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {clients.map((client) => (
                <TableRow
                  key={client.id}
                  hover
                  onClick={() => handleRowClick(client.id)}
                  sx={{ cursor: 'pointer' }}
                  aria-label={`View details for ${client.first_name} ${client.last_name}`}
                  role="button"
                  tabIndex={0}
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

export default Clients;
