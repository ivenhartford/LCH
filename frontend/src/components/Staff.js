import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
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
  CircularProgress,
  Alert,
  Chip,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
  Email as EmailIcon,
  Phone as PhoneIcon,
  Badge as BadgeIcon,
} from '@mui/icons-material';
import logger from '../utils/logger';

/**
 * Staff Component
 *
 * Manages staff directory with employment details, credentials, and permissions.
 */
function Staff() {
  const queryClient = useQueryClient();

  const [searchTerm, setSearchTerm] = useState('');
  const [positionFilter, setPositionFilter] = useState('');
  const [departmentFilter, setDepartmentFilter] = useState('');
  const [activeFilter, setActiveFilter] = useState('true');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingStaff, setEditingStaff] = useState(null);
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    emergency_contact_name: '',
    emergency_contact_phone: '',
    position: '',
    department: '',
    employment_type: 'full-time',
    hire_date: '',
    license_number: '',
    license_state: '',
    license_expiry: '',
    certifications: '',
    education: '',
    default_schedule: '',
    hourly_rate: '',
    can_prescribe: false,
    can_perform_surgery: false,
    can_access_billing: false,
    notes: '',
    is_active: true,
  });

  useEffect(() => {
    logger.logLifecycle('Staff', 'mounted');
    return () => logger.logLifecycle('Staff', 'unmounted');
  }, []);

  const {
    data: staffData,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['staff', positionFilter, departmentFilter, activeFilter],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (positionFilter) params.append('position', positionFilter);
      if (departmentFilter) params.append('department', departmentFilter);
      if (activeFilter) params.append('is_active', activeFilter);

      const response = await fetch(`/api/staff?${params}`, { credentials: 'include' });
      if (!response.ok) throw new Error('Failed to fetch staff');
      return response.json();
    },
  });

  const saveMutation = useMutation({
    mutationFn: async (data) => {
      const url = editingStaff ? `/api/staff/${editingStaff.id}` : '/api/staff';
      const response = await fetch(url, {
        method: editingStaff ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(data),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to save staff member');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['staff']);
      handleCloseDialog();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (staffId) => {
      const response = await fetch(`/api/staff/${staffId}`, {
        method: 'DELETE',
        credentials: 'include',
      });
      if (!response.ok) throw new Error('Failed to delete staff member');
      return response.json();
    },
    onSuccess: () => queryClient.invalidateQueries(['staff']),
  });

  const handleOpenDialog = (staff = null) => {
    if (staff) {
      setEditingStaff(staff);
      setFormData({
        first_name: staff.first_name || '',
        last_name: staff.last_name || '',
        email: staff.email || '',
        phone: staff.phone || '',
        emergency_contact_name: staff.emergency_contact_name || '',
        emergency_contact_phone: staff.emergency_contact_phone || '',
        position: staff.position || '',
        department: staff.department || '',
        employment_type: staff.employment_type || 'full-time',
        hire_date: staff.hire_date || '',
        license_number: staff.license_number || '',
        license_state: staff.license_state || '',
        license_expiry: staff.license_expiry || '',
        certifications: staff.certifications || '',
        education: staff.education || '',
        default_schedule: staff.default_schedule || '',
        hourly_rate: staff.hourly_rate || '',
        can_prescribe: staff.can_prescribe ?? false,
        can_perform_surgery: staff.can_perform_surgery ?? false,
        can_access_billing: staff.can_access_billing ?? false,
        notes: staff.notes || '',
        is_active: staff.is_active ?? true,
      });
    } else {
      setEditingStaff(null);
      setFormData({
        first_name: '',
        last_name: '',
        email: '',
        phone: '',
        emergency_contact_name: '',
        emergency_contact_phone: '',
        position: '',
        department: '',
        employment_type: 'full-time',
        hire_date: new Date().toISOString().split('T')[0],
        license_number: '',
        license_state: '',
        license_expiry: '',
        certifications: '',
        education: '',
        default_schedule: '',
        hourly_rate: '',
        can_prescribe: false,
        can_perform_surgery: false,
        can_access_billing: false,
        notes: '',
        is_active: true,
      });
    }
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingStaff(null);
  };

  const handleSubmit = () => {
    saveMutation.mutate(formData);
  };

  const handleDelete = (staffId, name) => {
    if (window.confirm(`Deactivate ${name}? This will soft-delete the staff member.`)) {
      deleteMutation.mutate(staffId);
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
        <Alert severity="error">Failed to load staff: {error.message}</Alert>
      </Box>
    );
  }

  const staff = staffData?.staff || [];

  // Apply search filter
  const displayStaff = staff.filter(
    (s) =>
      s.first_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.last_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.position.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getEmploymentTypeColor = (type) => {
    switch (type) {
      case 'full-time':
        return 'success';
      case 'part-time':
        return 'primary';
      case 'contract':
        return 'warning';
      case 'intern':
        return 'info';
      default:
        return 'default';
    }
  };

  return (
    <Box>
      <Box mb={3} display="flex" justifyContent="space-between" alignItems="center">
        <Typography variant="h4">Staff Directory</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => handleOpenDialog()}>
          Add Staff Member
        </Button>
      </Box>

      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={4}>
            <TextField
              fullWidth
              size="small"
              label="Search"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Name, email, or position"
              InputProps={{ startAdornment: <SearchIcon color="action" sx={{ mr: 1 }} /> }}
            />
          </Grid>
          <Grid item xs={12} sm={3}>
            <TextField
              fullWidth
              size="small"
              label="Position"
              value={positionFilter}
              onChange={(e) => setPositionFilter(e.target.value)}
              placeholder="e.g., Veterinarian"
            />
          </Grid>
          <Grid item xs={12} sm={3}>
            <TextField
              fullWidth
              size="small"
              label="Department"
              value={departmentFilter}
              onChange={(e) => setDepartmentFilter(e.target.value)}
              placeholder="e.g., Surgery"
            />
          </Grid>
          <Grid item xs={12} sm={2}>
            <FormControl fullWidth size="small">
              <InputLabel>Status</InputLabel>
              <Select
                value={activeFilter}
                label="Status"
                onChange={(e) => setActiveFilter(e.target.value)}
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="true">Active</MenuItem>
                <MenuItem value="false">Inactive</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>

      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Position</TableCell>
                <TableCell>Department</TableCell>
                <TableCell>Contact</TableCell>
                <TableCell>Employment</TableCell>
                <TableCell>Credentials</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {displayStaff.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} align="center">
                    <Typography variant="body2" color="text.secondary" py={4}>
                      No staff members found.
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                displayStaff.map((member) => (
                  <TableRow key={member.id} hover>
                    <TableCell>
                      <Box>
                        <Typography variant="body2" fontWeight="medium">
                          {member.full_name}
                        </Typography>
                        {member.email && (
                          <Box display="flex" alignItems="center" gap={0.5}>
                            <EmailIcon fontSize="small" color="action" />
                            <Typography variant="caption" color="text.secondary">
                              {member.email}
                            </Typography>
                          </Box>
                        )}
                      </Box>
                    </TableCell>
                    <TableCell>{member.position}</TableCell>
                    <TableCell>{member.department || '-'}</TableCell>
                    <TableCell>
                      {member.phone && (
                        <Box display="flex" alignItems="center" gap={0.5}>
                          <PhoneIcon fontSize="small" color="action" />
                          <Typography variant="body2">{member.phone}</Typography>
                        </Box>
                      )}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={member.employment_type}
                        size="small"
                        color={getEmploymentTypeColor(member.employment_type)}
                      />
                    </TableCell>
                    <TableCell>
                      {member.license_number && (
                        <Box display="flex" alignItems="center" gap={0.5}>
                          <BadgeIcon fontSize="small" color="action" />
                          <Typography variant="caption">{member.license_number}</Typography>
                        </Box>
                      )}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={member.is_active ? 'Active' : 'Inactive'}
                        color={member.is_active ? 'success' : 'default'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell align="right">
                      <Tooltip title="Edit">
                        <IconButton size="small" onClick={() => handleOpenDialog(member)}>
                          <EditIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Deactivate">
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleDelete(member.id, member.full_name)}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
        <Box p={2}>
          <Typography variant="body2" color="text.secondary">
            Total: {displayStaff.length} staff members
          </Typography>
        </Box>
      </Paper>

      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>{editingStaff ? 'Edit Staff Member' : 'Add Staff Member'}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 0.5 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                required
                label="First Name"
                value={formData.first_name}
                onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                required
                label="Last Name"
                value={formData.last_name}
                onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                required
                type="email"
                label="Email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Phone"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                required
                label="Position"
                value={formData.position}
                onChange={(e) => setFormData({ ...formData, position: e.target.value })}
                placeholder="e.g., Veterinarian, Vet Tech"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Department"
                value={formData.department}
                onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                placeholder="e.g., Surgery, Front Desk"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth required>
                <InputLabel>Employment Type</InputLabel>
                <Select
                  value={formData.employment_type}
                  label="Employment Type"
                  onChange={(e) => setFormData({ ...formData, employment_type: e.target.value })}
                >
                  <MenuItem value="full-time">Full-time</MenuItem>
                  <MenuItem value="part-time">Part-time</MenuItem>
                  <MenuItem value="contract">Contract</MenuItem>
                  <MenuItem value="intern">Intern</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                required
                type="date"
                label="Hire Date"
                value={formData.hire_date}
                onChange={(e) => setFormData({ ...formData, hire_date: e.target.value })}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="License Number"
                value={formData.license_number}
                onChange={(e) => setFormData({ ...formData, license_number: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="License State"
                value={formData.license_state}
                onChange={(e) => setFormData({ ...formData, license_state: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                type="date"
                label="License Expiry"
                value={formData.license_expiry}
                onChange={(e) => setFormData({ ...formData, license_expiry: e.target.value })}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Certifications"
                value={formData.certifications}
                onChange={(e) => setFormData({ ...formData, certifications: e.target.value })}
                placeholder="e.g., Fear Free Certified, CVPM"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Notes"
                multiline
                rows={2}
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <InputLabel>Can Prescribe</InputLabel>
                <Select
                  value={formData.can_prescribe}
                  label="Can Prescribe"
                  onChange={(e) => setFormData({ ...formData, can_prescribe: e.target.value })}
                >
                  <MenuItem value={true}>Yes</MenuItem>
                  <MenuItem value={false}>No</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <InputLabel>Can Perform Surgery</InputLabel>
                <Select
                  value={formData.can_perform_surgery}
                  label="Can Perform Surgery"
                  onChange={(e) =>
                    setFormData({ ...formData, can_perform_surgery: e.target.value })
                  }
                >
                  <MenuItem value={true}>Yes</MenuItem>
                  <MenuItem value={false}>No</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={formData.is_active}
                  label="Status"
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.value })}
                >
                  <MenuItem value={true}>Active</MenuItem>
                  <MenuItem value={false}>Inactive</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={
              saveMutation.isLoading ||
              !formData.first_name ||
              !formData.last_name ||
              !formData.email ||
              !formData.position ||
              !formData.hire_date
            }
          >
            {saveMutation.isLoading ? <CircularProgress size={24} /> : 'Save'}
          </Button>
        </DialogActions>
        {saveMutation.isError && (
          <Alert severity="error" sx={{ m: 2 }}>
            {saveMutation.error.message}
          </Alert>
        )}
      </Dialog>
    </Box>
  );
}

export default Staff;
