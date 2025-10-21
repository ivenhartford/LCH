import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import MyCalendar from './Calendar';

beforeEach(() => {
  jest.spyOn(window, 'fetch').mockImplementation(url => {
    if (url === '/api/appointments') {
      return Promise.resolve({
        ok: true,
        json: async () => [
          {
            id: 1,
            title: 'Test Appointment',
            start: '2025-01-01T10:00:00',
            end: '2025-01-01T11:00:00',
            description: 'A test appointment',
          },
        ],
      });
    }
    return Promise.resolve({
      ok: true,
      json: async () => ({}),
    });
  });
});

afterEach(() => {
  jest.restoreAllMocks();
});

test('renders without crashing', () => {
  render(<MyCalendar />);
});
