import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import logger from '../utils/logger';

/**
 * Query Client Configuration
 *
 * Configures React Query with:
 * - Logging for all queries and mutations
 * - Default retry logic
 * - Stale time configuration
 * - Error handling
 * - Cache time settings
 */

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Retry failed queries 3 times
      retry: 3,

      // Data considered stale after 5 minutes
      staleTime: 5 * 60 * 1000,

      // Cache data for 10 minutes
      cacheTime: 10 * 60 * 1000,

      // Refetch on window focus
      refetchOnWindowFocus: true,

      // Refetch on reconnect
      refetchOnReconnect: true,

      // Don't refetch on mount if data is fresh
      refetchOnMount: true,

      // Callbacks for logging
      onError: (error) => {
        logger.error('React Query Error', error, {
          type: 'query',
        });
      },

      onSuccess: (data) => {
        logger.debug('React Query Success', {
          type: 'query',
          dataLength: Array.isArray(data) ? data.length : 'N/A',
        });
      },
    },

    mutations: {
      // Retry mutations once
      retry: 1,

      // Callbacks for logging
      onError: (error, variables, context) => {
        logger.error('React Query Mutation Error', error, {
          type: 'mutation',
          variables,
          context,
        });
      },

      onSuccess: (data, variables, context) => {
        logger.info('React Query Mutation Success', {
          type: 'mutation',
          variables,
          context,
        });
      },
    },
  },

  // Query Cache callbacks
  queryCache: {
    onError: (error, query) => {
      logger.error('Query Cache Error', error, {
        queryKey: query.queryKey,
        queryHash: query.queryHash,
      });
    },

    onSuccess: (data, query) => {
      logger.debug('Query Cache Success', {
        queryKey: query.queryKey,
        queryHash: query.queryHash,
      });
    },
  },

  // Mutation Cache callbacks
  mutationCache: {
    onError: (error, variables, context, mutation) => {
      logger.error('Mutation Cache Error', error, {
        mutationKey: mutation.options.mutationKey,
        variables,
      });
    },

    onSuccess: (data, variables, context, mutation) => {
      logger.info('Mutation Cache Success', {
        mutationKey: mutation.options.mutationKey,
        variables,
      });
    },
  },
});

/**
 * QueryProvider Component
 *
 * Wraps application with React Query client and dev tools.
 *
 * Features:
 * - Provides React Query client to all components
 * - Includes dev tools in development mode
 * - Comprehensive logging of all queries and mutations
 * - Error tracking and reporting
 */
const QueryProvider = ({ children }) => {
  React.useEffect(() => {
    logger.info('React Query Provider initialized', {
      defaultOptions: {
        queries: {
          retry: 3,
          staleTime: '5min',
          cacheTime: '10min',
        },
        mutations: {
          retry: 1,
        },
      },
    });

    return () => {
      logger.debug('React Query Provider unmounted');
    };
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {/* Only show dev tools in development */}
      {process.env.NODE_ENV === 'development' && (
        <ReactQueryDevtools initialIsOpen={false} position="bottom-right" />
      )}
    </QueryClientProvider>
  );
};

export default QueryProvider;
export { queryClient };
