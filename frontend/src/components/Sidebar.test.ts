import { render, screen, fireEvent } from '@testing-library/svelte';
import { describe, it, expect } from 'vitest';
import Sidebar from './Sidebar.svelte';

describe('Sidebar', () => {
  it('renders sidebar with sections', () => {
    render(Sidebar);

    // Check that key section headings exist
    expect(screen.getByText(/Categories/i)).toBeInTheDocument();
    expect(screen.getByText(/Community/i)).toBeInTheDocument();
  });

  it('closes sidebar when close button is clicked', async () => {
    render(Sidebar);

    const closeButton = screen.getByText('×');
    expect(closeButton).toBeInTheDocument();

    await fireEvent.click(closeButton);
  });
});
