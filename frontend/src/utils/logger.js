/**
 * Comprehensive logging utility for frontend application
 *
 * Features:
 * - Multiple log levels (debug, info, warn, error)
 * - Console output with formatting
 * - LocalStorage persistence with rotation
 * - Backend API integration for server-side logging
 * - Automatic cleanup of old logs
 * - Error tracking with stack traces
 * - User action tracking
 * - API call logging
 *
 * Usage:
 *   import logger from './utils/logger';
 *   logger.info('User logged in', { userId: 123 });
 *   logger.error('API call failed', error, { endpoint: '/api/users' });
 */

const LOG_LEVELS = {
  DEBUG: 0,
  INFO: 1,
  WARN: 2,
  ERROR: 3,
};

const LOG_LEVEL_NAMES = ['DEBUG', 'INFO', 'WARN', 'ERROR'];

class Logger {
  constructor() {
    // Get log level from environment or default to INFO
    this.level = process.env.REACT_APP_LOG_LEVEL
      ? LOG_LEVELS[process.env.REACT_APP_LOG_LEVEL.toUpperCase()]
      : LOG_LEVELS.INFO;

    // Maximum log entries to keep in localStorage
    this.maxLocalStorageEntries = 500;

    // LocalStorage key
    this.storageKey = 'app_logs';

    // Whether to send logs to backend
    this.sendToBackend = process.env.REACT_APP_LOG_TO_BACKEND === 'true';

    // Initialize
    this.cleanupOldLogs();
  }

  /**
   * Create a log entry object
   */
  createLogEntry(level, message, data = null, error = null) {
    const entry = {
      timestamp: new Date().toISOString(),
      level: LOG_LEVEL_NAMES[level],
      message,
      url: window.location.href,
      userAgent: navigator.userAgent,
    };

    // Add additional data if provided
    if (data) {
      entry.data = data;
    }

    // Add error details if provided
    if (error) {
      entry.error = {
        name: error.name,
        message: error.message,
        stack: error.stack,
      };
    }

    return entry;
  }

  /**
   * Output log to console with appropriate styling
   */
  logToConsole(level, message, data, error) {
    const timestamp = new Date().toLocaleTimeString();
    const prefix = `[${timestamp}] [${LOG_LEVEL_NAMES[level]}]`;

    // Style based on level
    const styles = {
      [LOG_LEVELS.DEBUG]: 'color: #666',
      [LOG_LEVELS.INFO]: 'color: #0066cc',
      [LOG_LEVELS.WARN]: 'color: #ff9900',
      [LOG_LEVELS.ERROR]: 'color: #cc0000; font-weight: bold',
    };

    console.log(`%c${prefix}`, styles[level], message);

    if (data) {
      console.log('Data:', data);
    }

    if (error) {
      console.error('Error:', error);
    }
  }

  /**
   * Save log to localStorage
   */
  saveToLocalStorage(logEntry) {
    try {
      const logs = this.getLogsFromStorage();
      logs.push(logEntry);

      // Rotate logs if exceeding max entries
      if (logs.length > this.maxLocalStorageEntries) {
        logs.splice(0, logs.length - this.maxLocalStorageEntries);
      }

      localStorage.setItem(this.storageKey, JSON.stringify(logs));
    } catch (error) {
      // If localStorage is full, clear old logs
      console.warn('Failed to save log to localStorage:', error);
      this.clearLogs();
    }
  }

  /**
   * Get logs from localStorage
   */
  getLogsFromStorage() {
    try {
      const logs = localStorage.getItem(this.storageKey);
      return logs ? JSON.parse(logs) : [];
    } catch (error) {
      console.error('Failed to read logs from localStorage:', error);
      return [];
    }
  }

  /**
   * Send log to backend API
   */
  async sendToBackendAPI(logEntry) {
    if (!this.sendToBackend) {
      return;
    }

    try {
      await fetch('/api/logs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(logEntry),
      });
    } catch (error) {
      // Don't log backend errors to avoid infinite loop
      console.warn('Failed to send log to backend:', error);
    }
  }

  /**
   * Clean up logs older than 7 days
   */
  cleanupOldLogs() {
    try {
      const logs = this.getLogsFromStorage();
      const sevenDaysAgo = new Date();
      sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);

      const recentLogs = logs.filter(log => {
        const logDate = new Date(log.timestamp);
        return logDate > sevenDaysAgo;
      });

      localStorage.setItem(this.storageKey, JSON.stringify(recentLogs));
    } catch (error) {
      console.error('Failed to cleanup old logs:', error);
    }
  }

  /**
   * Core logging method
   */
  log(level, message, data = null, error = null) {
    // Check if this level should be logged
    if (level < this.level) {
      return;
    }

    // Create log entry
    const logEntry = this.createLogEntry(level, message, data, error);

    // Output to console
    this.logToConsole(level, message, data, error);

    // Save to localStorage
    this.saveToLocalStorage(logEntry);

    // Send to backend for ERROR level or if explicitly enabled
    if (level === LOG_LEVELS.ERROR || this.sendToBackend) {
      this.sendToBackendAPI(logEntry);
    }
  }

  /**
   * Debug level logging
   */
  debug(message, data = null) {
    this.log(LOG_LEVELS.DEBUG, message, data);
  }

  /**
   * Info level logging
   */
  info(message, data = null) {
    this.log(LOG_LEVELS.INFO, message, data);
  }

  /**
   * Warning level logging
   */
  warn(message, data = null) {
    this.log(LOG_LEVELS.WARN, message, data);
  }

  /**
   * Error level logging
   */
  error(message, error = null, data = null) {
    this.log(LOG_LEVELS.ERROR, message, data, error);
  }

  /**
   * Log user actions
   */
  logAction(action, details = null) {
    this.info(`User Action: ${action}`, details);
  }

  /**
   * Log API calls
   */
  logAPICall(method, endpoint, status, duration, error = null) {
    const data = {
      method,
      endpoint,
      status,
      duration: `${duration}ms`,
    };

    if (error) {
      this.error(`API Call Failed: ${method} ${endpoint}`, error, data);
    } else if (status >= 400) {
      this.warn(`API Call Warning: ${method} ${endpoint}`, data);
    } else {
      this.debug(`API Call: ${method} ${endpoint}`, data);
    }
  }

  /**
   * Log component lifecycle
   */
  logLifecycle(component, event, details = null) {
    this.debug(`Component ${component}: ${event}`, details);
  }

  /**
   * Get all logs (for debugging or export)
   */
  getAllLogs() {
    return this.getLogsFromStorage();
  }

  /**
   * Export logs as JSON file
   */
  exportLogs() {
    const logs = this.getAllLogs();
    const dataStr = JSON.stringify(logs, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);

    const link = document.createElement('a');
    link.href = url;
    link.download = `logs-${new Date().toISOString()}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  /**
   * Clear all logs
   */
  clearLogs() {
    try {
      localStorage.removeItem(this.storageKey);
      console.log('All logs cleared');
    } catch (error) {
      console.error('Failed to clear logs:', error);
    }
  }

  /**
   * Get log statistics
   */
  getStats() {
    const logs = this.getAllLogs();
    const stats = {
      total: logs.length,
      debug: 0,
      info: 0,
      warn: 0,
      error: 0,
      oldest: logs.length > 0 ? logs[0].timestamp : null,
      newest: logs.length > 0 ? logs[logs.length - 1].timestamp : null,
    };

    logs.forEach(log => {
      const level = log.level.toLowerCase();
      if (stats[level] !== undefined) {
        stats[level]++;
      }
    });

    return stats;
  }
}

// Create singleton instance
const logger = new Logger();

// Add global error handler
window.addEventListener('error', (event) => {
  logger.error(
    'Unhandled Error',
    event.error,
    {
      message: event.message,
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno,
    }
  );
});

// Add unhandled promise rejection handler
window.addEventListener('unhandledrejection', (event) => {
  logger.error(
    'Unhandled Promise Rejection',
    event.reason,
    {
      promise: event.promise,
    }
  );
});

// Log app startup
logger.info('Application started', {
  userAgent: navigator.userAgent,
  viewport: `${window.innerWidth}x${window.innerHeight}`,
  timestamp: new Date().toISOString(),
});

export default logger;
