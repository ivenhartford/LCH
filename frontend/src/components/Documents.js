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
  FormControlLabel,
  Checkbox,
  Card,
  CardContent,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Download as DownloadIcon,
  Search as SearchIcon,
  CloudUpload as UploadIcon,
  Description as FileIcon,
  Image as ImageIcon,
  PictureAsPdf as PdfIcon,
  InsertDriveFile as DefaultFileIcon,
} from '@mui/icons-material';
import logger from '../utils/logger';

/**
 * Documents Component
 *
 * Manages document uploads and viewing for patients, visits, and clients.
 * Supports multiple document types including medical records, consent forms, lab results, and images.
 */
function Documents() {
  const queryClient = useQueryClient();

  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [patientIdFilter, setPatientIdFilter] = useState('');
  const [visitIdFilter, setVisitIdFilter] = useState('');
  const [clientIdFilter, setClientIdFilter] = useState('');
  const [isConsentFormFilter, setIsConsentFormFilter] = useState('');
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editingDocument, setEditingDocument] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadFormData, setUploadFormData] = useState({
    category: 'general',
    patient_id: '',
    visit_id: '',
    client_id: '',
    description: '',
    tags: '',
    is_consent_form: false,
    consent_type: '',
    signed_date: '',
  });

  useEffect(() => {
    logger.logLifecycle('Documents', 'mounted');
    return () => logger.logLifecycle('Documents', 'unmounted');
  }, []);

  // Fetch patients for dropdown
  const { data: patientsData } = useQuery({
    queryKey: ['patients'],
    queryFn: async () => {
      const response = await fetch('/api/patients', { credentials: 'include' });
      if (!response.ok) throw new Error('Failed to fetch patients');
      return response.json();
    },
  });

  // Fetch clients for dropdown
  const { data: clientsData } = useQuery({
    queryKey: ['clients'],
    queryFn: async () => {
      const response = await fetch('/api/clients', { credentials: 'include' });
      if (!response.ok) throw new Error('Failed to fetch clients');
      return response.json();
    },
  });

  // Fetch documents
  const {
    data: documentsData,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['documents', categoryFilter, patientIdFilter, visitIdFilter, clientIdFilter, isConsentFormFilter],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (categoryFilter) params.append('category', categoryFilter);
      if (patientIdFilter) params.append('patient_id', patientIdFilter);
      if (visitIdFilter) params.append('visit_id', visitIdFilter);
      if (clientIdFilter) params.append('client_id', clientIdFilter);
      if (isConsentFormFilter) params.append('is_consent_form', isConsentFormFilter);

      const response = await fetch(`/api/documents?${params}`, { credentials: 'include' });
      if (!response.ok) throw new Error('Failed to fetch documents');
      return response.json();
    },
  });

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: async (formData) => {
      const response = await fetch('/api/documents', {
        method: 'POST',
        credentials: 'include',
        body: formData,
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to upload document');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['documents']);
      handleCloseUploadDialog();
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: async ({ id, data }) => {
      const response = await fetch(`/api/documents/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(data),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to update document');
      }
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['documents']);
      handleCloseEditDialog();
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: async (documentId) => {
      const response = await fetch(`/api/documents/${documentId}`, {
        method: 'DELETE',
        credentials: 'include',
      });
      if (!response.ok) throw new Error('Failed to delete document');
      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['documents']);
    },
  });

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    setSelectedFile(file);
  };

  const handleOpenUploadDialog = () => {
    setUploadDialogOpen(true);
  };

  const handleCloseUploadDialog = () => {
    setUploadDialogOpen(false);
    setSelectedFile(null);
    setUploadFormData({
      category: 'general',
      patient_id: '',
      visit_id: '',
      client_id: '',
      description: '',
      tags: '',
      is_consent_form: false,
      consent_type: '',
      signed_date: '',
    });
  };

  const handleOpenEditDialog = (document) => {
    setEditingDocument(document);
    setEditDialogOpen(true);
  };

  const handleCloseEditDialog = () => {
    setEditDialogOpen(false);
    setEditingDocument(null);
  };

  const handleUploadSubmit = (e) => {
    e.preventDefault();

    if (!selectedFile) {
      alert('Please select a file to upload');
      return;
    }

    if (!uploadFormData.patient_id && !uploadFormData.visit_id && !uploadFormData.client_id) {
      alert('Document must be linked to a patient, visit, or client');
      return;
    }

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('category', uploadFormData.category);
    if (uploadFormData.patient_id) formData.append('patient_id', uploadFormData.patient_id);
    if (uploadFormData.visit_id) formData.append('visit_id', uploadFormData.visit_id);
    if (uploadFormData.client_id) formData.append('client_id', uploadFormData.client_id);
    if (uploadFormData.description) formData.append('description', uploadFormData.description);
    if (uploadFormData.tags) formData.append('tags', uploadFormData.tags);
    formData.append('is_consent_form', uploadFormData.is_consent_form);
    if (uploadFormData.is_consent_form && uploadFormData.consent_type) {
      formData.append('consent_type', uploadFormData.consent_type);
    }
    if (uploadFormData.signed_date) formData.append('signed_date', uploadFormData.signed_date);

    uploadMutation.mutate(formData);
  };

  const handleUpdateSubmit = (e) => {
    e.preventDefault();

    const updateData = {
      category: editingDocument.category,
      tags: editingDocument.tags,
      description: editingDocument.description,
      notes: editingDocument.notes,
      is_consent_form: editingDocument.is_consent_form,
      consent_type: editingDocument.consent_type,
      patient_id: editingDocument.patient_id || null,
      visit_id: editingDocument.visit_id || null,
      client_id: editingDocument.client_id || null,
    };

    updateMutation.mutate({ id: editingDocument.id, data: updateData });
  };

  const handleDownload = async (documentId, filename) => {
    try {
      const response = await fetch(`/api/documents/${documentId}/download`, {
        credentials: 'include',
      });
      if (!response.ok) throw new Error('Failed to download document');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      logger.logError(error, 'handleDownload');
      alert('Failed to download document');
    }
  };

  const handleDelete = (documentId) => {
    if (window.confirm('Are you sure you want to archive this document?')) {
      deleteMutation.mutate(documentId);
    }
  };

  const getFileIcon = (fileType) => {
    if (fileType.startsWith('image/')) return <ImageIcon color="primary" />;
    if (fileType === 'application/pdf') return <PdfIcon color="error" />;
    if (fileType.includes('word')) return <FileIcon color="info" />;
    return <DefaultFileIcon />;
  };

  const getCategoryColor = (category) => {
    const colors = {
      general: 'default',
      medical_record: 'primary',
      lab_result: 'secondary',
      imaging: 'info',
      consent_form: 'warning',
      vaccination_record: 'success',
      other: 'default',
    };
    return colors[category] || 'default';
  };

  const filteredDocuments = documentsData?.documents?.filter((doc) => {
    if (!searchTerm) return true;
    const search = searchTerm.toLowerCase();
    return (
      doc.original_filename.toLowerCase().includes(search) ||
      (doc.description && doc.description.toLowerCase().includes(search)) ||
      (doc.patient_name && doc.patient_name.toLowerCase().includes(search)) ||
      (doc.client_name && doc.client_name.toLowerCase().includes(search))
    );
  });

  if (isLoading) return <CircularProgress />;
  if (isError) return <Alert severity="error">Error: {error.message}</Alert>;

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Document Management</Typography>
        <Button
          variant="contained"
          startIcon={<UploadIcon />}
          onClick={handleOpenUploadDialog}
        >
          Upload Document
        </Button>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={2} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Documents
              </Typography>
              <Typography variant="h4">{documentsData?.total || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Medical Records
              </Typography>
              <Typography variant="h4">
                {filteredDocuments?.filter((d) => d.category === 'medical_record').length || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Consent Forms
              </Typography>
              <Typography variant="h4">
                {filteredDocuments?.filter((d) => d.is_consent_form).length || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Lab Results
              </Typography>
              <Typography variant="h4">
                {filteredDocuments?.filter((d) => d.category === 'lab_result').length || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={3}>
            <TextField
              fullWidth
              label="Search"
              variant="outlined"
              size="small"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: <SearchIcon />,
              }}
            />
          </Grid>
          <Grid item xs={12} md={2}>
            <FormControl fullWidth size="small">
              <InputLabel>Category</InputLabel>
              <Select
                value={categoryFilter}
                label="Category"
                onChange={(e) => setCategoryFilter(e.target.value)}
              >
                <MenuItem value="">All Categories</MenuItem>
                <MenuItem value="general">General</MenuItem>
                <MenuItem value="medical_record">Medical Record</MenuItem>
                <MenuItem value="lab_result">Lab Result</MenuItem>
                <MenuItem value="imaging">Imaging</MenuItem>
                <MenuItem value="consent_form">Consent Form</MenuItem>
                <MenuItem value="vaccination_record">Vaccination Record</MenuItem>
                <MenuItem value="other">Other</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={2}>
            <FormControl fullWidth size="small">
              <InputLabel>Patient</InputLabel>
              <Select
                value={patientIdFilter}
                label="Patient"
                onChange={(e) => setPatientIdFilter(e.target.value)}
              >
                <MenuItem value="">All Patients</MenuItem>
                {patientsData?.patients?.map((patient) => (
                  <MenuItem key={patient.id} value={patient.id}>
                    {patient.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={2}>
            <FormControl fullWidth size="small">
              <InputLabel>Consent Forms</InputLabel>
              <Select
                value={isConsentFormFilter}
                label="Consent Forms"
                onChange={(e) => setIsConsentFormFilter(e.target.value)}
              >
                <MenuItem value="">All Documents</MenuItem>
                <MenuItem value="true">Consent Forms Only</MenuItem>
                <MenuItem value="false">Exclude Consent Forms</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={3}>
            <Button
              variant="outlined"
              onClick={() => {
                setSearchTerm('');
                setCategoryFilter('');
                setPatientIdFilter('');
                setVisitIdFilter('');
                setClientIdFilter('');
                setIsConsentFormFilter('');
              }}
            >
              Clear Filters
            </Button>
          </Grid>
        </Grid>
      </Paper>

      {/* Documents Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Type</TableCell>
              <TableCell>Filename</TableCell>
              <TableCell>Category</TableCell>
              <TableCell>Patient</TableCell>
              <TableCell>Client</TableCell>
              <TableCell>Size</TableCell>
              <TableCell>Uploaded</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredDocuments?.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  <Typography color="textSecondary">No documents found</Typography>
                </TableCell>
              </TableRow>
            ) : (
              filteredDocuments?.map((doc) => (
                <TableRow key={doc.id} hover>
                  <TableCell>{getFileIcon(doc.file_type)}</TableCell>
                  <TableCell>
                    <Box>
                      <Typography variant="body2">{doc.original_filename}</Typography>
                      {doc.description && (
                        <Typography variant="caption" color="textSecondary">
                          {doc.description}
                        </Typography>
                      )}
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={doc.category.replace('_', ' ')}
                      color={getCategoryColor(doc.category)}
                      size="small"
                    />
                    {doc.is_consent_form && (
                      <Chip
                        label="Consent"
                        color="warning"
                        size="small"
                        sx={{ ml: 1 }}
                      />
                    )}
                  </TableCell>
                  <TableCell>{doc.patient_name || '-'}</TableCell>
                  <TableCell>{doc.client_name || '-'}</TableCell>
                  <TableCell>{doc.file_size_mb} MB</TableCell>
                  <TableCell>
                    {new Date(doc.created_at).toLocaleDateString()}
                    <Typography variant="caption" display="block" color="textSecondary">
                      by {doc.uploaded_by_name}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Tooltip title="Download">
                      <IconButton
                        size="small"
                        onClick={() => handleDownload(doc.id, doc.original_filename)}
                      >
                        <DownloadIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Edit">
                      <IconButton size="small" onClick={() => handleOpenEditDialog(doc)}>
                        <EditIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Archive">
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => handleDelete(doc.id)}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Upload Dialog */}
      <Dialog open={uploadDialogOpen} onClose={handleCloseUploadDialog} maxWidth="sm" fullWidth>
        <form onSubmit={handleUploadSubmit}>
          <DialogTitle>Upload Document</DialogTitle>
          <DialogContent>
            <Box sx={{ pt: 2 }}>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <Button variant="outlined" component="label" fullWidth startIcon={<UploadIcon />}>
                    {selectedFile ? selectedFile.name : 'Choose File'}
                    <input type="file" hidden onChange={handleFileSelect} />
                  </Button>
                </Grid>

                <Grid item xs={12}>
                  <FormControl fullWidth required>
                    <InputLabel>Category</InputLabel>
                    <Select
                      value={uploadFormData.category}
                      label="Category"
                      onChange={(e) =>
                        setUploadFormData({ ...uploadFormData, category: e.target.value })
                      }
                    >
                      <MenuItem value="general">General</MenuItem>
                      <MenuItem value="medical_record">Medical Record</MenuItem>
                      <MenuItem value="lab_result">Lab Result</MenuItem>
                      <MenuItem value="imaging">Imaging</MenuItem>
                      <MenuItem value="consent_form">Consent Form</MenuItem>
                      <MenuItem value="vaccination_record">Vaccination Record</MenuItem>
                      <MenuItem value="other">Other</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>Patient</InputLabel>
                    <Select
                      value={uploadFormData.patient_id}
                      label="Patient"
                      onChange={(e) =>
                        setUploadFormData({ ...uploadFormData, patient_id: e.target.value })
                      }
                    >
                      <MenuItem value="">None</MenuItem>
                      {patientsData?.patients?.map((patient) => (
                        <MenuItem key={patient.id} value={patient.id}>
                          {patient.name}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>Client</InputLabel>
                    <Select
                      value={uploadFormData.client_id}
                      label="Client"
                      onChange={(e) =>
                        setUploadFormData({ ...uploadFormData, client_id: e.target.value })
                      }
                    >
                      <MenuItem value="">None</MenuItem>
                      {clientsData?.clients?.map((client) => (
                        <MenuItem key={client.id} value={client.id}>
                          {client.first_name} {client.last_name}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Description"
                    multiline
                    rows={2}
                    value={uploadFormData.description}
                    onChange={(e) =>
                      setUploadFormData({ ...uploadFormData, description: e.target.value })
                    }
                  />
                </Grid>

                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Tags (comma-separated)"
                    value={uploadFormData.tags}
                    onChange={(e) =>
                      setUploadFormData({ ...uploadFormData, tags: e.target.value })
                    }
                  />
                </Grid>

                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={uploadFormData.is_consent_form}
                        onChange={(e) =>
                          setUploadFormData({
                            ...uploadFormData,
                            is_consent_form: e.target.checked,
                          })
                        }
                      />
                    }
                    label="This is a consent form"
                  />
                </Grid>

                {uploadFormData.is_consent_form && (
                  <>
                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        label="Consent Type"
                        value={uploadFormData.consent_type}
                        onChange={(e) =>
                          setUploadFormData({
                            ...uploadFormData,
                            consent_type: e.target.value,
                          })
                        }
                        placeholder="e.g., Surgery, Anesthesia"
                      />
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        label="Signed Date"
                        type="date"
                        value={uploadFormData.signed_date}
                        onChange={(e) =>
                          setUploadFormData({
                            ...uploadFormData,
                            signed_date: e.target.value,
                          })
                        }
                        InputLabelProps={{ shrink: true }}
                      />
                    </Grid>
                  </>
                )}
              </Grid>
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseUploadDialog}>Cancel</Button>
            <Button
              type="submit"
              variant="contained"
              disabled={uploadMutation.isPending || !selectedFile}
            >
              {uploadMutation.isPending ? 'Uploading...' : 'Upload'}
            </Button>
          </DialogActions>
          {uploadMutation.isError && (
            <Alert severity="error" sx={{ m: 2 }}>
              {uploadMutation.error.message}
            </Alert>
          )}
        </form>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onClose={handleCloseEditDialog} maxWidth="sm" fullWidth>
        <form onSubmit={handleUpdateSubmit}>
          <DialogTitle>Edit Document</DialogTitle>
          <DialogContent>
            {editingDocument && (
              <Box sx={{ pt: 2 }}>
                <Grid container spacing={2}>
                  <Grid item xs={12}>
                    <Typography variant="body2" color="textSecondary">
                      File: {editingDocument.original_filename}
                    </Typography>
                  </Grid>

                  <Grid item xs={12}>
                    <FormControl fullWidth>
                      <InputLabel>Category</InputLabel>
                      <Select
                        value={editingDocument.category}
                        label="Category"
                        onChange={(e) =>
                          setEditingDocument({ ...editingDocument, category: e.target.value })
                        }
                      >
                        <MenuItem value="general">General</MenuItem>
                        <MenuItem value="medical_record">Medical Record</MenuItem>
                        <MenuItem value="lab_result">Lab Result</MenuItem>
                        <MenuItem value="imaging">Imaging</MenuItem>
                        <MenuItem value="consent_form">Consent Form</MenuItem>
                        <MenuItem value="vaccination_record">Vaccination Record</MenuItem>
                        <MenuItem value="other">Other</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>

                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Description"
                      multiline
                      rows={2}
                      value={editingDocument.description || ''}
                      onChange={(e) =>
                        setEditingDocument({ ...editingDocument, description: e.target.value })
                      }
                    />
                  </Grid>

                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Tags (comma-separated)"
                      value={editingDocument.tags?.join(', ') || ''}
                      onChange={(e) =>
                        setEditingDocument({
                          ...editingDocument,
                          tags: e.target.value.split(',').map((t) => t.trim()),
                        })
                      }
                    />
                  </Grid>

                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      label="Notes"
                      multiline
                      rows={3}
                      value={editingDocument.notes || ''}
                      onChange={(e) =>
                        setEditingDocument({ ...editingDocument, notes: e.target.value })
                      }
                    />
                  </Grid>
                </Grid>
              </Box>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseEditDialog}>Cancel</Button>
            <Button type="submit" variant="contained" disabled={updateMutation.isPending}>
              {updateMutation.isPending ? 'Saving...' : 'Save'}
            </Button>
          </DialogActions>
          {updateMutation.isError && (
            <Alert severity="error" sx={{ m: 2 }}>
              {updateMutation.error.message}
            </Alert>
          )}
        </form>
      </Dialog>
    </Box>
  );
}

export default Documents;
