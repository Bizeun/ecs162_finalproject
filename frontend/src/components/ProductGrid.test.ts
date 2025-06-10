import { render, screen } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import ProductGrid from './ProductGrid.svelte';
import * as store from '../lib/store';

describe('ProductGrid', () => {
  it('renders no products message when store is empty', () => {
    store.productsStore.set([]);
    render(ProductGrid, { props: { products: [] } });
    expect(screen.getByText('No products found')).toBeInTheDocument();
  });

  describe('with products', () => {
    beforeEach(() => {
      vi.spyOn(store, 'fetchProducts').mockImplementation(async () => {
        store.productsStore.set([
          { id: 1, title: 'Test Product 1', price: 10 },
          { id: 2, title: 'Test Product 2', price: 20 }
        ]);
      });
    });

    it('renders product items', async () => {
      render(ProductGrid, { props: { products: [] } });

      expect(await screen.findByText('Test Product 1')).toBeInTheDocument();
      expect(await screen.findByText('Test Product 2')).toBeInTheDocument();
    });
  });
});
