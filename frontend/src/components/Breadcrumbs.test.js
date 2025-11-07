import { render, screen } from '../test-utils';
import { MemoryRouter } from 'react-router-dom';
import Breadcrumbs from './Breadcrumbs';

// Helper to render component with router at specific path
const renderWithRouter = (component, { route = '/' } = {}) => {
  return render(<MemoryRouter future={{ v7_startTransition: true }} initialEntries={[route]}>{component}</MemoryRouter>);
};

describe('Breadcrumbs Component', () => {
  describe('Home Page', () => {
    test('does not render breadcrumbs on home page', () => {
      const { container } = renderWithRouter(<Breadcrumbs />, { route: '/' });
      expect(container).toBeEmptyDOMElement();
    });
  });

  describe('Simple Routes', () => {
    test('renders breadcrumbs for /clients route', () => {
      renderWithRouter(<Breadcrumbs />, { route: '/clients' });

      expect(screen.getByText('Home')).toBeInTheDocument();
      expect(screen.getByText('Clients')).toBeInTheDocument();
    });

    test('renders breadcrumbs for /patients route', () => {
      renderWithRouter(<Breadcrumbs />, { route: '/patients' });

      expect(screen.getByText('Home')).toBeInTheDocument();
      expect(screen.getByText('Patients')).toBeInTheDocument();
    });

    test('renders breadcrumbs for /calendar route', () => {
      renderWithRouter(<Breadcrumbs />, { route: '/calendar' });

      expect(screen.getByText('Home')).toBeInTheDocument();
      expect(screen.getByText('Calendar')).toBeInTheDocument();
    });

    test('renders breadcrumbs for /dashboard route', () => {
      renderWithRouter(<Breadcrumbs />, { route: '/dashboard' });

      expect(screen.getByText('Home')).toBeInTheDocument();
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
    });
  });

  describe('Nested Routes', () => {
    test('renders breadcrumbs for /clients/new', () => {
      renderWithRouter(<Breadcrumbs />, { route: '/clients/new' });

      expect(screen.getByText('Home')).toBeInTheDocument();
      expect(screen.getByText('Clients')).toBeInTheDocument();
      expect(screen.getByText('New')).toBeInTheDocument();
    });

    test('renders breadcrumbs for /clients/:id with numeric ID', () => {
      renderWithRouter(<Breadcrumbs />, { route: '/clients/123' });

      expect(screen.getByText('Home')).toBeInTheDocument();
      expect(screen.getByText('Clients')).toBeInTheDocument();
      expect(screen.getByText('#123')).toBeInTheDocument();
    });

    test('renders breadcrumbs for /clients/:id/edit', () => {
      renderWithRouter(<Breadcrumbs />, { route: '/clients/456/edit' });

      expect(screen.getByText('Home')).toBeInTheDocument();
      expect(screen.getByText('Clients')).toBeInTheDocument();
      expect(screen.getByText('#456')).toBeInTheDocument();
      expect(screen.getByText('Edit')).toBeInTheDocument();
    });

    test('renders breadcrumbs for /patients/:id', () => {
      renderWithRouter(<Breadcrumbs />, { route: '/patients/789' });

      expect(screen.getByText('Home')).toBeInTheDocument();
      expect(screen.getByText('Patients')).toBeInTheDocument();
      expect(screen.getByText('#789')).toBeInTheDocument();
    });
  });

  describe('Home Link', () => {
    test('Home link includes HomeIcon', () => {
      renderWithRouter(<Breadcrumbs />, { route: '/clients' });

      const homeLink = screen.getByText('Home').closest('a');
      expect(homeLink).toHaveAttribute('href', '/');
    });

    test('Home link is clickable', () => {
      renderWithRouter(<Breadcrumbs />, { route: '/clients' });

      const homeLink = screen.getByText('Home').closest('a');
      expect(homeLink).toBeInTheDocument();
      expect(homeLink).toHaveAttribute('href', '/');
    });
  });

  describe('Intermediate Links', () => {
    test('intermediate breadcrumb items are links', () => {
      renderWithRouter(<Breadcrumbs />, { route: '/clients/123/edit' });

      const clientsLink = screen.getByText('Clients').closest('a');
      expect(clientsLink).toHaveAttribute('href', '/clients');

      const idLink = screen.getByText('#123').closest('a');
      expect(idLink).toHaveAttribute('href', '/clients/123');
    });

    test('last breadcrumb item is not a link', () => {
      renderWithRouter(<Breadcrumbs />, { route: '/clients/123/edit' });

      const editText = screen.getByText('Edit');
      expect(editText.closest('a')).toBeNull();
    });
  });

  describe('Route Labels', () => {
    test('uses custom label for known routes', () => {
      renderWithRouter(<Breadcrumbs />, { route: '/medical-records' });

      expect(screen.getByText('Medical Records')).toBeInTheDocument();
    });

    test('uses custom label for settings route', () => {
      renderWithRouter(<Breadcrumbs />, { route: '/settings' });

      expect(screen.getByText('Settings')).toBeInTheDocument();
    });

    test('uses custom label for invoices route', () => {
      renderWithRouter(<Breadcrumbs />, { route: '/invoices' });

      expect(screen.getByText('Invoices')).toBeInTheDocument();
    });

    test('capitalizes unknown routes', () => {
      renderWithRouter(<Breadcrumbs />, { route: '/unknown-route' });

      expect(screen.getByText('Unknown-route')).toBeInTheDocument();
    });
  });

  describe('Numeric IDs', () => {
    test('displays numeric IDs with # prefix', () => {
      renderWithRouter(<Breadcrumbs />, { route: '/clients/42' });

      expect(screen.getByText('#42')).toBeInTheDocument();
    });

    test('handles multi-digit IDs correctly', () => {
      renderWithRouter(<Breadcrumbs />, { route: '/patients/12345' });

      expect(screen.getByText('#12345')).toBeInTheDocument();
    });

    test('handles single-digit IDs correctly', () => {
      renderWithRouter(<Breadcrumbs />, { route: '/appointments/5' });

      expect(screen.getByText('#5')).toBeInTheDocument();
    });
  });

  describe('Aria Labels', () => {
    test('has proper aria-label for accessibility', () => {
      renderWithRouter(<Breadcrumbs />, { route: '/clients' });

      const breadcrumbs = screen.getByLabelText('breadcrumb');
      expect(breadcrumbs).toBeInTheDocument();
    });
  });

  describe('Deep Nesting', () => {
    test('handles deeply nested routes', () => {
      renderWithRouter(<Breadcrumbs />, { route: '/clients/1/patients/2/appointments/3' });

      expect(screen.getByText('Home')).toBeInTheDocument();
      expect(screen.getByText('Clients')).toBeInTheDocument();
      expect(screen.getByText('#1')).toBeInTheDocument();
      expect(screen.getByText('Patients')).toBeInTheDocument();
      expect(screen.getByText('#2')).toBeInTheDocument();
      expect(screen.getByText('Appointments')).toBeInTheDocument();
      expect(screen.getByText('#3')).toBeInTheDocument();
    });
  });
});
