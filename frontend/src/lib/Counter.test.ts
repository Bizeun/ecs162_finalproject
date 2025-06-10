import { render, screen, fireEvent } from '@testing-library/svelte';
import { describe, it, expect } from 'vitest';
import Counter from './Counter.svelte';

describe('Counter', () => {
  it('renders initial count', () => {
    render(Counter);
    expect(screen.getByText(/Count is 0/i)).toBeInTheDocument();
  });

  it('increments count on button click', async () => {
    render(Counter);

    const button = screen.getByText(/count is/i);
    await fireEvent.click(button);

    expect(screen.getByText(/Count is 1/i)).toBeInTheDocument();
  });
});
