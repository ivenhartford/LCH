import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
  CircularProgress,
} from '@mui/material';
import { Warning as WarningIcon } from '@mui/icons-material';

/**
 * Reusable Confirmation Dialog Component
 *
 * A modal dialog for confirming destructive actions (like delete operations).
 *
 * Props:
 * - open: Boolean - Controls dialog visibility
 * - title: String - Dialog title
 * - message: String - Confirmation message
 * - onConfirm: Function - Called when user confirms action
 * - onCancel: Function - Called when user cancels
 * - confirmText: String - Text for confirm button (default: "Delete")
 * - confirmColor: String - Color for confirm button (default: "error")
 * - cancelText: String - Text for cancel button (default: "Cancel")
 * - showWarningIcon: Boolean - Show warning icon in title (default: true)
 * - loading: Boolean - Show loading spinner and disable buttons (default: false)
 *
 * Example usage:
 * ```jsx
 * <ConfirmDialog
 *   open={deleteDialog.open}
 *   title="Delete Client"
 *   message="Are you sure you want to delete this client? This action cannot be undone."
 *   onConfirm={handleDeleteConfirm}
 *   onCancel={handleDeleteCancel}
 * />
 * ```
 */
const ConfirmDialog = ({
  open,
  title,
  message,
  onConfirm,
  onCancel,
  confirmText = 'Delete',
  confirmColor = 'error',
  cancelText = 'Cancel',
  showWarningIcon = true,
  loading = false,
}) => {
  return (
    <Dialog
      open={open}
      onClose={onCancel}
      aria-labelledby="confirm-dialog-title"
      aria-describedby="confirm-dialog-description"
      maxWidth="sm"
      fullWidth
    >
      <DialogTitle
        id="confirm-dialog-title"
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1,
        }}
      >
        {showWarningIcon && <WarningIcon color="warning" />}
        {title}
      </DialogTitle>
      <DialogContent>
        <DialogContentText id="confirm-dialog-description">
          {message}
        </DialogContentText>
      </DialogContent>
      <DialogActions sx={{ px: 3, pb: 2 }}>
        <Button
          onClick={onCancel}
          variant="outlined"
          disabled={loading}
          sx={{
            minWidth: 100,
          }}
        >
          {cancelText}
        </Button>
        <Button
          onClick={onConfirm}
          variant="contained"
          color={confirmColor}
          autoFocus
          disabled={loading}
          startIcon={loading ? <CircularProgress size={20} color="inherit" /> : null}
          sx={{
            minWidth: 100,
          }}
        >
          {loading ? 'Deleting...' : confirmText}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ConfirmDialog;
