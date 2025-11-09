import { render, screen } from '../test-utils';
import Dashboard from './Dashboard';

describe('Dashboard Component', () => {
  test('renders welcome message', () => {
    render(<Dashboard />);

    expect(screen.getByText('Welcome to Lenox Cat Hospital')).toBeInTheDocument();
    expect(screen.getByText('Select a section to get started')).toBeInTheDocument();
  });

  test('renders all quick link cards', () => {
    render(<Dashboard />);

    expect(screen.getByText('Appointments')).toBeInTheDocument();
    expect(screen.getByText('Clients')).toBeInTheDocument();
    expect(screen.getByText('Patients')).toBeInTheDocument();
    expect(screen.getByText('Invoices')).toBeInTheDocument();
  });

  test('renders card descriptions', () => {
    render(<Dashboard />);

    expect(screen.getByText('View and manage appointments')).toBeInTheDocument();
    expect(screen.getByText('Manage client information')).toBeInTheDocument();
    expect(screen.getByText('View patient records')).toBeInTheDocument();
    expect(screen.getByText('Billing and invoices')).toBeInTheDocument();
  });

  test('renders buttons for each section', () => {
    render(<Dashboard />);

    expect(screen.getByText('Go to Appointments')).toBeInTheDocument();
    expect(screen.getByText('Go to Clients')).toBeInTheDocument();
    expect(screen.getByText('Go to Patients')).toBeInTheDocument();
    expect(screen.getByText('Go to Invoices')).toBeInTheDocument();
  });
});
