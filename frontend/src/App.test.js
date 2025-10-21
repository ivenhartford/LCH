import { render, screen } from '@testing-library/react';
import App from './App';

beforeEach(() => {
  jest.spyOn(window, 'fetch').mockImplementation(url => {
    if (url === '/api/appointments') {
      return Promise.resolve({
        ok: true,
        json: async () => [],
      });
    }
    return Promise.resolve({
      ok: true,
      json: async () => ({ id: 1, username: 'testuser', role: 'user' }),
    });
  });
});

afterEach(() => {
  jest.restoreAllMocks();
});

test('renders learn react link', async () => {
  render(<App />);
  const linkElement = await screen.findByText(/Application/i);
  expect(linkElement).toBeInTheDocument();
});
