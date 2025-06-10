import { render, screen } from '@testing-library/svelte';
import Header from './Header.svelte';

describe('Header', () => {
  it('renders header text', () => {
    render(Header);
    expect(screen.getByText(/Community Product Reviews/i)).toBeInTheDocument();
  });
});
