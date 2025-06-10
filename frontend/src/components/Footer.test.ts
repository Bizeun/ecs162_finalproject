import { render, screen } from '@testing-library/svelte';
import { describe, it, expect } from 'vitest';
import Footer from './Footer.svelte';

describe('Footer', () => {
  it('renders footer text', () => {
    render(Footer);

    expect(screen.getByText(/Community Product Reviews/i)).toBeInTheDocument();
  });
});
