import { render, screen, waitFor } from '../test-utils';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import Login from './Login';

// Mock useNavigate
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

// Helper to render component with router
const renderWithRouter = (component) => {
  return render(<MemoryRouter>{component}</MemoryRouter>);
};

// Mock fetch
global.fetch = jest.fn();
global.alert = jest.fn();

describe('Login Component', () => {
  const mockSetUser = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch.mockClear();
    global.alert.mockClear();
    mockNavigate.mockClear();
  });

  afterEach(() => {
    global.fetch.mockRestore();
  });

  describe('Rendering', () => {
    test('renders login form with username and password fields', () => {
      renderWithRouter(<Login setUser={mockSetUser} />);

      expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /submit/i })).toBeInTheDocument();
    });

    test('username field has correct type', () => {
      renderWithRouter(<Login setUser={mockSetUser} />);

      const usernameInput = screen.getByLabelText(/username/i);
      expect(usernameInput).toHaveAttribute('type', 'text');
    });

    test('password field has correct type for security', () => {
      renderWithRouter(<Login setUser={mockSetUser} />);

      const passwordInput = screen.getByLabelText(/password/i);
      expect(passwordInput).toHaveAttribute('type', 'password');
    });
  });

  describe('User Input', () => {
    test('allows user to type username', async () => {
      renderWithRouter(<Login setUser={mockSetUser} />);

      const usernameInput = screen.getByLabelText(/username/i);
      await userEvent.type(usernameInput, 'testuser');

      expect(usernameInput).toHaveValue('testuser');
    });

    test('allows user to type password', async () => {
      // Using userEvent directly (v13 API)
      renderWithRouter(<Login setUser={mockSetUser} />);

      const passwordInput = screen.getByLabelText(/password/i);
      await userEvent.type(passwordInput, 'password123');

      expect(passwordInput).toHaveValue('password123');
    });
  });

  describe('Form Submission - Successful Login', () => {
    test('calls login API with correct credentials on submit', async () => {
      // Using userEvent directly (v13 API)
      const mockUser = { id: 1, username: 'testuser', role: 'administrator' };

      global.fetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({}),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockUser,
        });

      renderWithRouter(<Login setUser={mockSetUser} />);

      const usernameInput = screen.getByLabelText(/username/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /submit/i });

      await userEvent.type(usernameInput, 'testuser');
      await userEvent.type(passwordInput, 'password123');
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith('/api/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ username: 'testuser', password: 'password123' }),
        });
      });
    });

    test('fetches user session after successful login', async () => {
      // Using userEvent directly (v13 API)
      const mockUser = { id: 1, username: 'testuser', role: 'administrator' };

      global.fetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({}),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockUser,
        });

      renderWithRouter(<Login setUser={mockSetUser} />);

      const usernameInput = screen.getByLabelText(/username/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /submit/i });

      await userEvent.type(usernameInput, 'testuser');
      await userEvent.type(passwordInput, 'password123');
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith('/api/check_session');
      });
    });

    test('calls setUser with user data on successful login', async () => {
      // Using userEvent directly (v13 API)
      const mockUser = { id: 1, username: 'testuser', role: 'administrator' };

      global.fetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({}),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockUser,
        });

      renderWithRouter(<Login setUser={mockSetUser} />);

      const usernameInput = screen.getByLabelText(/username/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /submit/i });

      await userEvent.type(usernameInput, 'testuser');
      await userEvent.type(passwordInput, 'password123');
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(mockSetUser).toHaveBeenCalledWith(mockUser);
      });
    });

    test('navigates to home page after successful login', async () => {
      // Using userEvent directly (v13 API)
      const mockUser = { id: 1, username: 'testuser', role: 'administrator' };

      global.fetch
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({}),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockUser,
        });

      renderWithRouter(<Login setUser={mockSetUser} />);

      const usernameInput = screen.getByLabelText(/username/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /submit/i });

      await userEvent.type(usernameInput, 'testuser');
      await userEvent.type(passwordInput, 'password123');
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/');
      });
    });
  });

  describe('Form Submission - Failed Login', () => {
    test('shows alert when login fails', async () => {
      // Using userEvent directly (v13 API)

      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
      });

      renderWithRouter(<Login setUser={mockSetUser} />);

      const usernameInput = screen.getByLabelText(/username/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /submit/i });

      await userEvent.type(usernameInput, 'wronguser');
      await userEvent.type(passwordInput, 'wrongpass');
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(global.alert).toHaveBeenCalledWith('Login failed');
      });
    });

    test('does not call setUser when login fails', async () => {
      // Using userEvent directly (v13 API)

      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
      });

      renderWithRouter(<Login setUser={mockSetUser} />);

      const usernameInput = screen.getByLabelText(/username/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /submit/i });

      await userEvent.type(usernameInput, 'wronguser');
      await userEvent.type(passwordInput, 'wrongpass');
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(global.alert).toHaveBeenCalled();
      });

      expect(mockSetUser).not.toHaveBeenCalled();
    });

    test('does not navigate when login fails', async () => {
      // Using userEvent directly (v13 API)

      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
      });

      renderWithRouter(<Login setUser={mockSetUser} />);

      const usernameInput = screen.getByLabelText(/username/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /submit/i });

      await userEvent.type(usernameInput, 'wronguser');
      await userEvent.type(passwordInput, 'wrongpass');
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(global.alert).toHaveBeenCalled();
      });

      expect(mockNavigate).not.toHaveBeenCalled();
    });
  });

  describe('Form Submission - Empty Fields', () => {
    test('submits form even with empty fields (backend validation)', async () => {
      // Using userEvent directly (v13 API)

      global.fetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
      });

      renderWithRouter(<Login setUser={mockSetUser} />);

      const submitButton = screen.getByRole('button', { name: /submit/i });
      await userEvent.click(submitButton);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith('/api/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ username: '', password: '' }),
        });
      });
    });
  });
});
