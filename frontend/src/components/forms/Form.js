import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Box, Button, CircularProgress } from '@mui/material';
import logger from '../../utils/logger';

/**
 * Form Component
 *
 * Reusable form wrapper with React Hook Form and Zod validation.
 *
 * Props:
 * - schema: Zod validation schema (required)
 * - onSubmit: Submit handler function (required)
 * - defaultValues: Default form values
 * - children: Form fields (function that receives { control, formState })
 * - submitButtonText: Text for submit button
 * - resetAfterSubmit: Boolean to reset form after successful submit
 * - disabled: Boolean to disable entire form
 *
 * Features:
 * - Automatic validation with Zod
 * - Error handling and display
 * - Loading states
 * - Form reset capability
 * - Comprehensive logging
 *
 * Usage:
 *   <Form
 *     schema={myZodSchema}
 *     onSubmit={handleSubmit}
 *     defaultValues={{ name: '', email: '' }}
 *   >
 *     {({ control }) => (
 *       <>
 *         <FormTextField name="name" control={control} label="Name" />
 *         <FormTextField name="email" control={control} label="Email" />
 *       </>
 *     )}
 *   </Form>
 */
const Form = ({
  schema,
  onSubmit,
  defaultValues = {},
  children,
  submitButtonText = 'Submit',
  resetAfterSubmit = false,
  disabled = false,
}) => {
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  const { control, handleSubmit, reset, formState } = useForm({
    resolver: zodResolver(schema),
    defaultValues,
    mode: 'onBlur', // Validate on blur
  });

  React.useEffect(() => {
    logger.logLifecycle('Form', 'mounted', {
      hasSchema: !!schema,
      defaultValues,
    });

    return () => {
      logger.logLifecycle('Form', 'unmounted');
    };
  }, [schema, defaultValues]);

  const handleFormSubmit = async (data) => {
    logger.info('Form submission started', { data });
    setIsSubmitting(true);

    try {
      await onSubmit(data);

      logger.info('Form submission successful', { data });

      if (resetAfterSubmit) {
        reset();
        logger.debug('Form reset after successful submit');
      }
    } catch (error) {
      logger.error('Form submission failed', error, { data });
      throw error; // Re-throw to allow error handling in parent
    } finally {
      setIsSubmitting(false);
    }
  };

  const { errors, isDirty, isValid } = formState;

  // Log validation errors
  React.useEffect(() => {
    if (Object.keys(errors).length > 0) {
      logger.warn('Form validation errors', { errors });
    }
  }, [errors]);

  return (
    <Box component="form" onSubmit={handleSubmit(handleFormSubmit)} noValidate>
      {/* Render children with control and formState */}
      {typeof children === 'function' ? children({ control, formState }) : children}

      {/* Submit button */}
      <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
        <Button
          type="submit"
          variant="contained"
          color="primary"
          disabled={disabled || isSubmitting || !isValid}
          startIcon={isSubmitting && <CircularProgress size={20} />}
        >
          {isSubmitting ? 'Submitting...' : submitButtonText}
        </Button>

        {isDirty && !isSubmitting && (
          <Button
            type="button"
            variant="outlined"
            onClick={() => {
              reset();
              logger.info('Form reset by user');
            }}
            disabled={disabled || isSubmitting}
          >
            Reset
          </Button>
        )}
      </Box>
    </Box>
  );
};

export default Form;
