import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Box,
  Paper,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Grid,
  Chip,
  IconButton,
  Alert,
  CircularProgress,
  MenuItem,
  FormControlLabel,
  Switch,
  List,
  ListItem,
  ListItemText,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Email as EmailIcon,
  Sms as SmsIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import logger from '../utils/logger';

/**
 * Notification Templates Component
 *
 * Manages email and SMS templates for automated reminders.
 * Supports variable substitution and template management.
 */
function NotificationTemplates() {
  const queryClient = useQueryClient();

  // State
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [openDialog, setOpenDialog] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [typeFilter, setTypeFilter] = useState('');
  const [channelFilter, setChannelFilter] = useState('');

  // Form data
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    template_type: 'appointment_reminder',
    channel: 'email',
    subject: '',
    body: '',
    variables: [],
    is_active: true,
    is_default: false,
  });

  // Variable input
  const [newVariable, setNewVariable] = useState('');

  useEffect(() => {
    logger.logLifecycle('NotificationTemplates', 'mounted');
    return () => logger.logLifecycle('NotificationTemplates', 'unmounted');
  }, []);

  // Fetch templates
  const { data: templatesData, isLoading } = useQuery({
    queryKey: ['notification-templates', typeFilter, channelFilter],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (typeFilter) params.append('template_type', typeFilter);
      if (channelFilter) params.append('channel', channelFilter);

      const response = await fetch(`/api/notification-templates?${params}`, {
        credentials: 'include',
      });
      if (!response.ok) throw new Error('Failed to fetch notification templates');
      return response.json();
    },
  });

  // Create mutation
  const createMutation = useMutation({
    mutationFn: async (data) => {
      const response = await fetch('/api/notification-templates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(data),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to create notification template');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['notification-templates']);
      handleCloseDialog();
      logger.logAction('Notification template created');
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: async ({ id, data }) => {
      const response = await fetch(`/api/notification-templates/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(data),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to update notification template');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['notification-templates']);
      handleCloseDialog();
      logger.logAction('Notification template updated');
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: async (id) => {
      const response = await fetch(`/api/notification-templates/${id}`, {
        method: 'DELETE',
        credentials: 'include',
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to delete notification template');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['notification-templates']);
      logger.logAction('Notification template deleted');
    },
  });

  const templates = templatesData?.templates || [];

  const handleOpenDialog = (template = null) => {
    if (template) {
      setEditingTemplate(template);
      setFormData({
        name: template.name || '',
        description: template.description || '',
        template_type: template.template_type || 'appointment_reminder',
        channel: template.channel || 'email',
        subject: template.subject || '',
        body: template.body || '',
        variables: template.variables || [],
        is_active: template.is_active !== undefined ? template.is_active : true,
        is_default: template.is_default || false,
      });
      logger.logAction('Edit template dialog opened', { template_id: template.id });
    } else {
      setEditingTemplate(null);
      setFormData({
        name: '',
        description: '',
        template_type: 'appointment_reminder',
        channel: 'email',
        subject: '',
        body: '',
        variables: [],
        is_active: true,
        is_default: false,
      });
      logger.logAction('New template dialog opened');
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingTemplate(null);
    setNewVariable('');
  };

  const handleAddVariable = () => {
    if (newVariable && !formData.variables.includes(newVariable)) {
      setFormData({
        ...formData,
        variables: [...formData.variables, newVariable],
      });
      setNewVariable('');
    }
  };

  const handleRemoveVariable = (variable) => {
    setFormData({
      ...formData,
      variables: formData.variables.filter((v) => v !== variable),
    });
  };

  const handleSubmit = () => {
    const data = { ...formData };

    if (editingTemplate) {
      updateMutation.mutate({ id: editingTemplate.id, data });
    } else {
      createMutation.mutate(data);
    }
  };

  const handleDelete = (template) => {
    if (window.confirm(`Are you sure you want to delete template "${template.name}"?`)) {
      deleteMutation.mutate(template.id);
    }
  };

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const getTemplateTypeLabel = (type) => {
    const labels = {
      appointment_reminder: 'Appointment Reminder',
      vaccination_reminder: 'Vaccination Reminder',
      medication_reminder: 'Medication Reminder',
      followup_reminder: 'Follow-up Reminder',
      general: 'General',
    };
    return labels[type] || type;
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  const paginatedTemplates = templates.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" display="flex" alignItems="center" gap={1}>
          <EmailIcon fontSize="large" />
          Notification Templates
        </Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => handleOpenDialog()}>
          Create Template
        </Button>
      </Box>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              select
              size="small"
              label="Template Type"
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
            >
              <MenuItem value="">All Types</MenuItem>
              <MenuItem value="appointment_reminder">Appointment Reminder</MenuItem>
              <MenuItem value="vaccination_reminder">Vaccination Reminder</MenuItem>
              <MenuItem value="medication_reminder">Medication Reminder</MenuItem>
              <MenuItem value="followup_reminder">Follow-up Reminder</MenuItem>
              <MenuItem value="general">General</MenuItem>
            </TextField>
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              select
              size="small"
              label="Channel"
              value={channelFilter}
              onChange={(e) => setChannelFilter(e.target.value)}
            >
              <MenuItem value="">All Channels</MenuItem>
              <MenuItem value="email">Email</MenuItem>
              <MenuItem value="sms">SMS</MenuItem>
              <MenuItem value="both">Both</MenuItem>
            </TextField>
          </Grid>
        </Grid>
      </Paper>

      {/* Error Messages */}
      {(createMutation.isError || updateMutation.isError || deleteMutation.isError) && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {createMutation.error?.message ||
            updateMutation.error?.message ||
            deleteMutation.error?.message}
        </Alert>
      )}

      {/* Templates Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Channel</TableCell>
              <TableCell>Variables</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {paginatedTemplates.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  <Typography color="text.secondary" py={3}>
                    No notification templates found
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              paginatedTemplates.map((template) => (
                <TableRow key={template.id} hover>
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium">
                      {template.name}
                    </Typography>
                    {template.description && (
                      <Typography variant="caption" color="text.secondary" display="block">
                        {template.description.length > 50
                          ? template.description.substring(0, 50) + '...'
                          : template.description}
                      </Typography>
                    )}
                    {template.is_default && (
                      <Chip label="Default" size="small" color="primary" sx={{ mt: 0.5 }} />
                    )}
                  </TableCell>
                  <TableCell>
                    <Chip label={getTemplateTypeLabel(template.template_type)} size="small" />
                  </TableCell>
                  <TableCell>
                    {template.channel === 'email' && <Chip icon={<EmailIcon />} label="Email" size="small" color="primary" />}
                    {template.channel === 'sms' && <Chip icon={<SmsIcon />} label="SMS" size="small" color="info" />}
                    {template.channel === 'both' && (
                      <Box display="flex" gap={0.5}>
                        <Chip icon={<EmailIcon />} label="Email" size="small" color="primary" />
                        <Chip icon={<SmsIcon />} label="SMS" size="small" color="info" />
                      </Box>
                    )}
                  </TableCell>
                  <TableCell>
                    {template.variables && template.variables.length > 0 ? (
                      <Typography variant="caption" color="text.secondary">
                        {template.variables.length} variable{template.variables.length > 1 ? 's' : ''}
                      </Typography>
                    ) : (
                      <Typography variant="caption" color="text.secondary">
                        None
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={template.is_active ? 'Active' : 'Inactive'}
                      size="small"
                      color={template.is_active ? 'success' : 'default'}
                    />
                  </TableCell>
                  <TableCell align="right">
                    <IconButton
                      size="small"
                      onClick={() => handleOpenDialog(template)}
                      color="primary"
                    >
                      <EditIcon fontSize="small" />
                    </IconButton>
                    <IconButton size="small" onClick={() => handleDelete(template)} color="error">
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
        <TablePagination
          component="div"
          count={templates.length}
          page={page}
          onPageChange={handleChangePage}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          rowsPerPageOptions={[5, 10, 25, 50]}
        />
      </TableContainer>

      {/* Add/Edit Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingTemplate ? 'Edit Notification Template' : 'Create Notification Template'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <Grid container spacing={2}>
              {/* Basic Information */}
              <Grid item xs={12}>
                <Typography variant="subtitle2" color="primary" gutterBottom>
                  Basic Information
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  required
                  label="Template Name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  helperText="Unique name for this template"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  required
                  select
                  label="Template Type"
                  value={formData.template_type}
                  onChange={(e) => setFormData({ ...formData, template_type: e.target.value })}
                >
                  <MenuItem value="appointment_reminder">Appointment Reminder</MenuItem>
                  <MenuItem value="vaccination_reminder">Vaccination Reminder</MenuItem>
                  <MenuItem value="medication_reminder">Medication Reminder</MenuItem>
                  <MenuItem value="followup_reminder">Follow-up Reminder</MenuItem>
                  <MenuItem value="general">General</MenuItem>
                </TextField>
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={2}
                  label="Description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                />
              </Grid>

              {/* Channel Settings */}
              <Grid item xs={12}>
                <Typography variant="subtitle2" color="primary" gutterBottom sx={{ mt: 2 }}>
                  Channel Settings
                </Typography>
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  required
                  select
                  label="Delivery Channel"
                  value={formData.channel}
                  onChange={(e) => setFormData({ ...formData, channel: e.target.value })}
                >
                  <MenuItem value="email">Email Only</MenuItem>
                  <MenuItem value="sms">SMS Only</MenuItem>
                  <MenuItem value="both">Both Email & SMS</MenuItem>
                </TextField>
              </Grid>

              {/* Message Content */}
              <Grid item xs={12}>
                <Typography variant="subtitle2" color="primary" gutterBottom sx={{ mt: 2 }}>
                  Message Content
                </Typography>
              </Grid>
              {(formData.channel === 'email' || formData.channel === 'both') && (
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Email Subject"
                    value={formData.subject}
                    onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                    helperText="Subject line for email notifications"
                  />
                </Grid>
              )}
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  required
                  multiline
                  rows={6}
                  label="Message Body"
                  value={formData.body}
                  onChange={(e) => setFormData({ ...formData, body: e.target.value })}
                  helperText="Use {variable_name} for variable substitution"
                />
              </Grid>

              {/* Variables */}
              <Grid item xs={12}>
                <Typography variant="subtitle2" color="primary" gutterBottom sx={{ mt: 2 }}>
                  Variables
                </Typography>
                <Alert severity="info" icon={<InfoIcon />} sx={{ mb: 2 }}>
                  Add variables that can be used in the message body. Format: {'{variable_name}'}
                </Alert>
              </Grid>
              <Grid item xs={12}>
                <Box display="flex" gap={1} alignItems="center">
                  <TextField
                    fullWidth
                    size="small"
                    label="Variable Name"
                    value={newVariable}
                    onChange={(e) => setNewVariable(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        handleAddVariable();
                      }
                    }}
                    placeholder="e.g., client_name, appointment_date"
                  />
                  <Button
                    variant="outlined"
                    onClick={handleAddVariable}
                    disabled={!newVariable}
                  >
                    Add
                  </Button>
                </Box>
              </Grid>
              {formData.variables.length > 0 && (
                <Grid item xs={12}>
                  <Paper variant="outlined" sx={{ p: 1 }}>
                    <List dense>
                      {formData.variables.map((variable) => (
                        <ListItem
                          key={variable}
                          secondaryAction={
                            <IconButton
                              edge="end"
                              size="small"
                              onClick={() => handleRemoveVariable(variable)}
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          }
                        >
                          <ListItemText
                            primary={`{${variable}}`}
                            primaryTypographyProps={{ fontFamily: 'monospace', fontSize: '0.9rem' }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Paper>
                </Grid>
              )}

              {/* Settings */}
              <Grid item xs={12}>
                <Typography variant="subtitle2" color="primary" gutterBottom sx={{ mt: 2 }}>
                  Settings
                </Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.is_active}
                      onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                    />
                  }
                  label="Active"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.is_default}
                      onChange={(e) => setFormData({ ...formData, is_default: e.target.checked })}
                    />
                  }
                  label="Default Template for Type"
                />
              </Grid>
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={
              !formData.name ||
              !formData.template_type ||
              !formData.channel ||
              !formData.body ||
              createMutation.isPending ||
              updateMutation.isPending
            }
          >
            {editingTemplate ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default NotificationTemplates;
