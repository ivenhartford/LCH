import { render, screen } from '../test-utils';
import NavigationBar from './NavigationBar';

test('renders all navigation buttons', () => {
  render(<NavigationBar />);

  expect(screen.getByRole('button', { name: 'Add User' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Administrative Menus' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Whiteboard' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Inventory' })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Options' })).toBeInTheDocument();
});
