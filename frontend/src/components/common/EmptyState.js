import React from 'react';
import { Box, Typography, Button } from '@mui/material';
import { Inbox } from '@mui/icons-material';

/**
 * EmptyState Component
 *
 * Displays a friendly empty state when lists or tables have no data.
 * Provides better UX than blank screens or "No items found" text.
 *
 * Props:
 * - icon: React Component - Icon to display (default: Inbox)
 * - title: String - Main heading text (required)
 * - message: String - Descriptive message (required)
 * - actionLabel: String - Call-to-action button text (optional)
 * - onAction: Function - Called when action button is clicked (optional)
 * - actionIcon: React Component - Icon for action button (optional)
 * - secondaryActionLabel: String - Secondary action button text (optional)
 * - onSecondaryAction: Function - Called when secondary button clicked (optional)
 *
 * Usage:
 * ```jsx
 * {clients.length === 0 ? (
 *   <EmptyState
 *     icon={PersonIcon}
 *     title="No Clients Yet"
 *     message="Get started by adding your first client to the system"
 *     actionLabel="New Client"
 *     onAction={() => navigate('/clients/new')}
 *   />
 * ) : (
 *   <Table>{clients.map(...)}</Table>
 * )}
 * ```
 */
const EmptyState = ({
  icon: Icon = Inbox,
  title,
  message,
  actionLabel,
  onAction,
  actionIcon: ActionIcon,
  secondaryActionLabel,
  onSecondaryAction,
}) => {
  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      minHeight="400px"
      textAlign="center"
      p={4}
      sx={{
        backgroundColor: 'background.paper',
        borderRadius: 2,
        border: '1px dashed',
        borderColor: 'divider',
      }}
    >
      {/* Icon */}
      <Icon
        sx={{
          fontSize: 80,
          color: 'text.secondary',
          opacity: 0.5,
          mb: 2,
        }}
      />

      {/* Title */}
      <Typography
        variant="h6"
        gutterBottom
        sx={{
          fontWeight: 600,
          color: 'text.primary',
        }}
      >
        {title}
      </Typography>

      {/* Message */}
      <Typography
        variant="body2"
        color="text.secondary"
        sx={{
          mb: 3,
          maxWidth: 400,
        }}
      >
        {message}
      </Typography>

      {/* Actions */}
      {(actionLabel || secondaryActionLabel) && (
        <Box display="flex" gap={2} flexWrap="wrap" justifyContent="center">
          {actionLabel && onAction && (
            <Button
              variant="contained"
              onClick={onAction}
              startIcon={ActionIcon ? <ActionIcon /> : null}
              sx={{
                minWidth: 150,
              }}
            >
              {actionLabel}
            </Button>
          )}
          {secondaryActionLabel && onSecondaryAction && (
            <Button
              variant="outlined"
              onClick={onSecondaryAction}
              sx={{
                minWidth: 150,
              }}
            >
              {secondaryActionLabel}
            </Button>
          )}
        </Box>
      )}
    </Box>
  );
};

export default EmptyState;
