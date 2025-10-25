import logger from './logger';

// Mock localStorage
const localStorageMock = (() => {
  let store = {};
  return {
    getItem: jest.fn((key) => store[key] || null),
    setItem: jest.fn((key, value) => {
      store[key] = value.toString();
    }),
    removeItem: jest.fn((key) => {
      delete store[key];
    }),
    clear: jest.fn(() => {
      store = {};
    }),
  };
})();

global.localStorage = localStorageMock;

// Mock fetch
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({}),
  })
);

describe('Logger', () => {
  beforeEach(() => {
    // Clear mocks before each test
    jest.clearAllMocks();
    localStorageMock.clear();
    console.log = jest.fn();
    console.error = jest.fn();
    console.warn = jest.fn();
  });

  describe('Logging Methods', () => {
    it('should log debug messages', () => {
      logger.debug('Debug message', { test: 'data' });
      expect(console.log).toHaveBeenCalled();
    });

    it('should log info messages', () => {
      logger.info('Info message', { test: 'data' });
      expect(console.log).toHaveBeenCalled();
    });

    it('should log warn messages', () => {
      logger.warn('Warning message', { test: 'data' });
      expect(console.log).toHaveBeenCalled();
    });

    it('should log error messages with error object', () => {
      const testError = new Error('Test error');
      logger.error('Error message', testError, { test: 'data' });
      expect(console.log).toHaveBeenCalled();
      expect(console.error).toHaveBeenCalled();
    });
  });

  describe('LocalStorage', () => {
    it('should save logs to localStorage', () => {
      logger.info('Test message');
      expect(localStorage.setItem).toHaveBeenCalled();
      const [[key, value]] = localStorage.setItem.mock.calls;
      expect(key).toBe('app_logs');
      const logs = JSON.parse(value);
      expect(logs).toBeInstanceOf(Array);
      expect(logs.length).toBeGreaterThan(0);
    });

    it('should retrieve logs from localStorage', () => {
      logger.info('Test message 1');
      logger.info('Test message 2');
      const logs = logger.getAllLogs();
      expect(logs).toBeInstanceOf(Array);
    });

    it('should clear all logs', () => {
      logger.info('Test message');
      logger.clearLogs();
      expect(localStorage.removeItem).toHaveBeenCalledWith('app_logs');
    });
  });

  describe('Log Entry Structure', () => {
    it('should create properly structured log entries', () => {
      const entry = logger.createLogEntry(
        1, // INFO level
        'Test message',
        { testData: 'value' },
        null
      );

      expect(entry).toHaveProperty('timestamp');
      expect(entry).toHaveProperty('level');
      expect(entry).toHaveProperty('message');
      expect(entry).toHaveProperty('url');
      expect(entry).toHaveProperty('userAgent');
      expect(entry.level).toBe('INFO');
      expect(entry.message).toBe('Test message');
    });

    it('should include error details when provided', () => {
      const testError = new Error('Test error');
      const entry = logger.createLogEntry(
        3, // ERROR level
        'Error occurred',
        null,
        testError
      );

      expect(entry).toHaveProperty('error');
      expect(entry.error).toHaveProperty('name');
      expect(entry.error).toHaveProperty('message');
      expect(entry.error).toHaveProperty('stack');
    });
  });

  describe('Special Logging Methods', () => {
    it('should log user actions', () => {
      logger.logAction('Button clicked', { buttonId: 'submit' });
      expect(console.log).toHaveBeenCalled();
    });

    it('should log API calls', () => {
      logger.logAPICall('GET', '/api/users', 200, 150);
      expect(console.log).toHaveBeenCalled();
    });

    it('should log API call errors', () => {
      const error = new Error('Network error');
      logger.logAPICall('POST', '/api/users', 500, 300, error);
      expect(console.log).toHaveBeenCalled();
      expect(console.error).toHaveBeenCalled();
    });

    it('should log component lifecycle events', () => {
      logger.logLifecycle('UserList', 'mounted', { count: 10 });
      expect(console.log).toHaveBeenCalled();
    });
  });

  describe('Statistics', () => {
    it('should return correct log statistics', () => {
      logger.clearLogs();
      logger.debug('Debug message');
      logger.info('Info message');
      logger.warn('Warning message');
      logger.error('Error message');

      const stats = logger.getStats();
      expect(stats).toHaveProperty('total');
      expect(stats).toHaveProperty('debug');
      expect(stats).toHaveProperty('info');
      expect(stats).toHaveProperty('warn');
      expect(stats).toHaveProperty('error');
      expect(stats.total).toBeGreaterThan(0);
    });

    it('should handle empty log statistics', () => {
      logger.clearLogs();
      const stats = logger.getStats();
      expect(stats.total).toBe(0);
      expect(stats.oldest).toBeNull();
      expect(stats.newest).toBeNull();
    });
  });

  describe('Log Management', () => {
    it('should rotate logs when exceeding max entries', () => {
      logger.clearLogs();
      // Log more than maxLocalStorageEntries
      for (let i = 0; i < 600; i++) {
        logger.info(`Message ${i}`);
      }
      const logs = logger.getAllLogs();
      expect(logs.length).toBeLessThanOrEqual(500);
    });
  });
});
