import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  CircularProgress,
  Alert,
  Grid,
  Divider,
} from '@mui/material';
import { Save as SaveIcon, Edit as EditIcon } from '@mui/icons-material';
import logger from '../../utils/logger';

/**
 * SOAP Note Tab Component
 *
 * Displays and edits SOAP notes for a visit
 * SOAP: Subjective, Objective, Assessment, Plan
 */
function SOAPNoteTab({ visitId }) {
  const queryClient = useQueryClient();
  const [editMode, setEditMode] = useState(false);
  const [formData, setFormData] = useState({
    subjective: '',
    objective: '',
    assessment: '',
    plan: '',
  });

  // Fetch SOAP notes for this visit
  const {
    data: soapNotes,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['soapNotes', visitId],
    queryFn: async () => {
      const response = await fetch(`/api/soap-notes?visit_id=${visitId}`, {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to fetch SOAP notes');
      }

      const data = await response.json();
      return data.soap_notes || [];
    },
  });

  const currentNote = soapNotes?.[0]; // Get the most recent note

  // Populate form when note is loaded
  useEffect(() => {
    if (currentNote) {
      setFormData({
        subjective: currentNote.subjective || '',
        objective: currentNote.objective || '',
        assessment: currentNote.assessment || '',
        plan: currentNote.plan || '',
      });
    }
  }, [currentNote]);

  // Create SOAP note mutation
  const createMutation = useMutation({
    mutationFn: async (data) => {
      const response = await fetch('/api/soap-notes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ ...data, visit_id: parseInt(visitId, 10) }),
      });

      if (!response.ok) {
        throw new Error('Failed to create SOAP note');
      }

      return response.json();
    },
    onSuccess: () => {
      logger.info('SOAP note created', { visitId });
      queryClient.invalidateQueries(['soapNotes', visitId]);
      setEditMode(false);
    },
  });

  // Update SOAP note mutation
  const updateMutation = useMutation({
    mutationFn: async (data) => {
      const response = await fetch(`/api/soap-notes/${currentNote.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error('Failed to update SOAP note');
      }

      return response.json();
    },
    onSuccess: () => {
      logger.info('SOAP note updated', { visitId });
      queryClient.invalidateQueries(['soapNotes', visitId]);
      setEditMode(false);
    },
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    if (currentNote) {
      updateMutation.mutate(formData);
    } else {
      createMutation.mutate(formData);
    }
  };

  const handleCancel = () => {
    setEditMode(false);
    if (currentNote) {
      setFormData({
        subjective: currentNote.subjective || '',
        objective: currentNote.objective || '',
        assessment: currentNote.assessment || '',
        plan: currentNote.plan || '',
      });
    }
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" p={4}>
        <CircularProgress />
      </Box>
    );
  }

  if (isError) {
    return (
      <Box p={2}>
        <Alert severity="error">Failed to load SOAP notes: {error.message}</Alert>
      </Box>
    );
  }

  // Display mode
  if (!editMode && currentNote) {
    return (
      <Paper sx={{ p: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h6">SOAP Notes</Typography>
          <Button startIcon={<EditIcon />} onClick={() => setEditMode(true)} variant="outlined">
            Edit
          </Button>
        </Box>

        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2" color="primary" gutterBottom>
              Subjective (Patient History)
            </Typography>
            <Typography variant="body2" style={{ whiteSpace: 'pre-wrap' }}>
              {currentNote.subjective || 'No subjective notes'}
            </Typography>
          </Grid>

          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2" color="primary" gutterBottom>
              Objective (Physical Exam Findings)
            </Typography>
            <Typography variant="body2" style={{ whiteSpace: 'pre-wrap' }}>
              {currentNote.objective || 'No objective notes'}
            </Typography>
          </Grid>

          <Grid item xs={12}>
            <Divider />
          </Grid>

          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2" color="primary" gutterBottom>
              Assessment (Diagnosis)
            </Typography>
            <Typography variant="body2" style={{ whiteSpace: 'pre-wrap' }}>
              {currentNote.assessment || 'No assessment'}
            </Typography>
          </Grid>

          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2" color="primary" gutterBottom>
              Plan (Treatment Plan)
            </Typography>
            <Typography variant="body2" style={{ whiteSpace: 'pre-wrap' }}>
              {currentNote.plan || 'No treatment plan'}
            </Typography>
          </Grid>

          <Grid item xs={12}>
            <Typography variant="caption" color="text.secondary">
              Created by: {currentNote.created_by_name} • Last updated:{' '}
              {new Date(currentNote.updated_at || currentNote.created_at).toLocaleString()}
            </Typography>
          </Grid>
        </Grid>
      </Paper>
    );
  }

  // Edit/Create mode
  return (
    <Paper sx={{ p: 3 }}>
      <Box mb={3}>
        <Typography variant="h6">
          {currentNote ? 'Edit SOAP Notes' : 'Create SOAP Notes'}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Document the clinical findings using the SOAP format
        </Typography>
      </Box>

      <form onSubmit={handleSubmit}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              multiline
              rows={6}
              label="Subjective"
              name="subjective"
              value={formData.subjective}
              onChange={handleChange}
              placeholder="Patient history, owner observations, presenting symptoms..."
              helperText="What the owner reports"
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              multiline
              rows={6}
              label="Objective"
              name="objective"
              value={formData.objective}
              onChange={handleChange}
              placeholder="Physical exam findings, test results, vital signs..."
              helperText="What you observe/measure"
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              multiline
              rows={6}
              label="Assessment"
              name="assessment"
              value={formData.assessment}
              onChange={handleChange}
              placeholder="Diagnosis, differential diagnoses, clinical interpretation..."
              helperText="Your clinical assessment"
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              multiline
              rows={6}
              label="Plan"
              name="plan"
              value={formData.plan}
              onChange={handleChange}
              placeholder="Treatment plan, medications, follow-up recommendations..."
              helperText="Treatment and next steps"
            />
          </Grid>

          {(createMutation.isError || updateMutation.isError) && (
            <Grid item xs={12}>
              <Alert severity="error">
                {createMutation.error?.message || updateMutation.error?.message}
              </Alert>
            </Grid>
          )}

          <Grid item xs={12}>
            <Box display="flex" gap={2}>
              <Button
                type="submit"
                variant="contained"
                startIcon={<SaveIcon />}
                disabled={createMutation.isLoading || updateMutation.isLoading}
              >
                {currentNote ? 'Update' : 'Create'} SOAP Note
              </Button>
              <Button
                variant="outlined"
                onClick={handleCancel}
                disabled={createMutation.isLoading || updateMutation.isLoading}
              >
                Cancel
              </Button>
            </Box>
          </Grid>
        </Grid>
      </form>
    </Paper>
  );
}

export default SOAPNoteTab;
