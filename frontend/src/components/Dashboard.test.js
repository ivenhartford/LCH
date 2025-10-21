import { render, screen } from '@testing-library/react';
import Dashboard from './Dashboard';

jest.mock('./NavigationBar', () => () => <nav>NavigationBar</nav>);
jest.mock('./Calendar', () => () => <div>Calendar</div>);

test('renders NavigationBar and Calendar', () => {
  render(<Dashboard />);

  expect(screen.getByText('NavigationBar')).toBeInTheDocument();
  expect(screen.getByText('Calendar')).toBeInTheDocument();
});
