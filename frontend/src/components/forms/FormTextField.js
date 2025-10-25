import React from 'react';
import { TextField } from '@mui/material';
import { Controller } from 'react-hook-form';
import logger from '../../utils/logger';

/**
 * FormTextField Component
 *
 * Reusable text field integrated with React Hook Form.
 *
 * Props:
 * - name: Field name (required)
 * - control: React Hook Form control object (required)
 * - label: Field label
 * - type: Input type (text, email, password, etc.)
 * - multiline: Boolean for multiline textarea
 * - rows: Number of rows for multiline
 * - disabled: Boolean to disable field
 * - required: Boolean to mark as required
 * - ...other Material-UI TextField props
 *
 * Features:
 * - Automatic error display from validation
 * - Integration with React Hook Form
 * - Material-UI styling
 * - Comprehensive logging
 */
const FormTextField = ({
  name,
  control,
  label,
  type = 'text',
  multiline = false,
  rows = 1,
  disabled = false,
  required = false,
  ...otherProps
}) => {
  React.useEffect(() => {
    logger.debug('FormTextField mounted', { name, label });
  }, [name, label]);

  return (
    <Controller
      name={name}
      control={control}
      render={({ field, fieldState: { error } }) => (
        <TextField
          {...field}
          {...otherProps}
          label={label}
          type={type}
          multiline={multiline}
          rows={multiline ? rows : undefined}
          disabled={disabled}
          required={required}
          error={!!error}
          helperText={error?.message}
          fullWidth
          margin="normal"
          variant="outlined"
          onChange={(e) => {
            field.onChange(e);
            logger.debug('FormTextField value changed', {
              name,
              valueLength: e.target.value?.length,
            });
          }}
          onBlur={(e) => {
            field.onBlur();
            logger.debug('FormTextField blurred', { name });
          }}
        />
      )}
    />
  );
};

export default FormTextField;
