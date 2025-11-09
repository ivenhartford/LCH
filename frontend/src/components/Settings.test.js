import { render, screen, waitFor } from '../test-utils';
import userEvent from '@testing-library/user-event';
import Settings from './Settings';

// Mock fetch
global.fetch = jest.fn();

describe('Settings Component', () => {
  const mockUser = {
    username: 'testuser',
    email: 'test@example.com',
    first_name: 'Test',
    last_name: 'User',
    role: 'administrator',
    last_login: '2025-10-27T10:00:00',
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  afterEach(() => {
    global.fetch.mockRestore();
  });

  describe('Rendering', () => {
    test('renders settings page with title', () => {
      render(<Settings user={mockUser} />);

      expect(screen.getByText('Settings')).toBeInTheDocument();
    });

    test('renders profile and password tabs', () => {
      render(<Settings user={mockUser} />);

      expect(screen.getByText('Profile')).toBeInTheDocument();
      expect(screen.getByText('Password')).toBeInTheDocument();
    });

    test('shows user role and last login', () => {
      render(<Settings user={mockUser} />);

      expect(screen.getByText(/Role:/)).toBeInTheDocument();
      expect(screen.getByText(/administrator/)).toBeInTheDocument();
      expect(screen.getByText(/Last Login:/)).toBeInTheDocument();
    });
  });

  describe('Profile Tab', () => {
    test('displays profile form fields', () => {
      render(<Settings user={mockUser} />);

      expect(screen.getByLabelText(/Username/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/First Name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Last Name/i)).toBeInTheDocument();
    });

    test('populates form with user data', () => {
      render(<Settings user={mockUser} />);

      expect(screen.getByLabelText(/Username/i)).toHaveValue('testuser');
      expect(screen.getByLabelText(/Email/i)).toHaveValue('test@example.com');
      expect(screen.getByLabelText(/First Name/i)).toHaveValue('Test');
      expect(screen.getByLabelText(/Last Name/i)).toHaveValue('User');
    });

    test('username field is disabled', () => {
      render(<Settings user={mockUser} />);

      expect(screen.getByLabelText(/Username/i)).toBeDisabled();
    });

    test('shows save changes button', () => {
      render(<Settings user={mockUser} />);

      expect(screen.getByText(/Save Changes/i)).toBeInTheDocument();
    });
  });

  describe('Password Tab', () => {
    test('displays password form fields when tab is clicked', async () => {
      render(<Settings user={mockUser} />);

      // Click on Password tab
      await userEvent.click(screen.getByText('Password'));

      await waitFor(() => {
        expect(screen.getByLabelText(/Current Password/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/New Password/i, { selector: 'input[name="new_password"]' })).toBeInTheDocument();
        expect(screen.getByLabelText(/Confirm New Password/i)).toBeInTheDocument();
      });
    });

    test('shows change password button in password tab', async () => {
      render(<Settings user={mockUser} />);

      await userEvent.click(screen.getByText('Password'));

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Change Password/i })).toBeInTheDocument();
      });
    });

    test('shows validation error for mismatched passwords', async () => {
      render(<Settings user={mockUser} />);

      await userEvent.click(screen.getByText('Password'));

      await waitFor(() => {
        expect(screen.getByLabelText(/Current Password/i)).toBeInTheDocument();
      });

      await userEvent.type(screen.getByLabelText(/Current Password/i), 'oldpass');
      await userEvent.type(screen.getByLabelText(/New Password/i, { selector: 'input[name="new_password"]' }), 'newpassword123');
      await userEvent.type(screen.getByLabelText(/Confirm New Password/i), 'differentpass');
      await userEvent.click(screen.getByRole('button', { name: /Change Password/i }));

      await waitFor(() => {
        expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument();
      });
    });

    test('shows validation error for short password', async () => {
      render(<Settings user={mockUser} />);

      await userEvent.click(screen.getByText('Password'));

      await waitFor(() => {
        expect(screen.getByLabelText(/Current Password/i)).toBeInTheDocument();
      });

      await userEvent.type(screen.getByLabelText(/Current Password/i), 'oldpass');
      await userEvent.type(screen.getByLabelText(/New Password/i, { selector: 'input[name="new_password"]' }), 'short');
      await userEvent.type(screen.getByLabelText(/Confirm New Password/i), 'short');
      await userEvent.click(screen.getByRole('button', { name: /Change Password/i }));

      await waitFor(() => {
        expect(screen.getByText('Password must be at least 8 characters long')).toBeInTheDocument();
      });
    });
  });

  describe('Tab Switching', () => {
    test('shows profile tab by default', () => {
      render(<Settings user={mockUser} />);

      expect(screen.getByText('Profile Information')).toBeInTheDocument();
    });

    test('switches to password tab when clicked', async () => {
      render(<Settings user={mockUser} />);

      await userEvent.click(screen.getByText('Password'));

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /Change Password/i })).toBeInTheDocument();
      });
    });

    test('switches back to profile tab', async () => {
      render(<Settings user={mockUser} />);

      await userEvent.click(screen.getByText('Password'));
      await userEvent.click(screen.getByText('Profile'));

      await waitFor(() => {
        expect(screen.getByText('Profile Information')).toBeInTheDocument();
      });
    });
  });
});
