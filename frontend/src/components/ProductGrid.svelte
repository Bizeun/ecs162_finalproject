<script lang="ts">
  import { onMount } from 'svelte';
  import { productsStore, currentProductStore, searchProducts, fetchProducts } from '../lib/store';
  
  export let searchQuery = '';
  
  let currentPage = 0;
  let isLoadingMore = false;
  let allProductsLoaded = false;
  let isInitialLoading = true; 
  
  $: if (searchQuery) {
    performSearch(searchQuery);
  }
  
  async function performSearch(query: string) {
    if (query.trim()) {
      await searchProducts(query);
      isInitialLoading = false;
    } else {
      isInitialLoading = true;
      await fetchProducts();
      isInitialLoading = false;
    }
  }
  
  function viewProduct(product: any) {
    currentProductStore.set(product);
  }
  
  function setupInfiniteScroll() {
    window.addEventListener('scroll', () => {
      if (isLoadingMore) return;
      const { scrollTop, scrollHeight, clientHeight } = document.documentElement;
      
      if (scrollTop + clientHeight >= scrollHeight - 100) {
        loadMoreProducts();
      }
    });
  }
  
  async function loadMoreProducts() {
    if (isLoadingMore || allProductsLoaded) return;
    
    isLoadingMore = true;
    
    try {
      const skip = $productsStore.length;
      const limit = 20;
      
      const response = await fetch(`/api/products?limit=${limit}&skip=${skip}`);
      const data = await response.json();
      
      if (data.products && data.products.length > 0) {
        productsStore.update(products => [...products, ...data.products]);
        
        // Check if we've loaded all products
        if (data.products.length < limit || skip + data.products.length >= data.total) {
          allProductsLoaded = true;
        }
      } else {
        allProductsLoaded = true;
      }
    } catch (error) {
      console.error('Error loading more products:', error);
    } finally {
      isLoadingMore = false;
    }
  }

  function getStarRating(rating: number) {
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 >= 0.5;
    let stars = '';
    
    for (let i = 0; i < fullStars; i++) {
      stars += '★';
    }
    if (hasHalfStar) {
      stars += '☆';
    }
    for (let i = fullStars + (hasHalfStar ? 1 : 0); i < 5; i++) {
      stars += '☆';
    }
    
    return stars;
  }
  
  onMount(async() => {
    if ($productsStore.length === 0) {
      await fetchProducts();
    }
    isInitialLoading = false;
    setupInfiniteScroll();
  });
</script>

<div class="grid-container" id="products-container">
  {#if $productsStore.length === 0}
    <div class="no-products">No products found</div>
  {:else}
    <div class="column">
      {#each $productsStore.filter((_, i) => i % 3 === 0) as product}
        <article class="product">
          <img 
            src={product.thumbnail} 
            alt={product.title} 
            class="product-image"
          />
          <h3>{product.title}</h3>
          <p class="brand">{product.brand || 'Generic Brand'}</p>
          <div class="product-info">
            <p class="price">${product.price}</p>
            <div class="rating">
              <span class="stars">{getStarRating(product.rating)}</span>
              <span class="rating-text">({product.rating}/5)</span>
            </div>
          </div>
          <p class="description">{product.description}</p>
          <div class="product-actions">
            <button class="view-button" on:click={() => viewProduct(product)}>
              View Details & Reviews ({(product.reviews?.length || 0 )+ (product.community_comments_count || 0)})
            </button>
          </div>
        </article>
      {/each}
    </div>
    
    <div class="column">
      {#each $productsStore.filter((_, i) => i % 3 === 1) as product}
        <article class="product">
          <img 
            src={product.thumbnail} 
            alt={product.title} 
            class="product-image"
          />
          <h3>{product.title}</h3>
          <p class="brand">{product.brand || 'Generic Brand'}</p>
          <div class="product-info">
            <p class="price">${product.price}</p>
            <div class="rating">
              <span class="stars">{getStarRating(product.rating)}</span>
              <span class="rating-text">({product.rating}/5)</span>
            </div>
          </div>
          <p class="description">{product.description}</p>
          <div class="product-actions">
            <button class="view-button" on:click={() => viewProduct(product)}>
              View Details & Reviews ({(product.reviews?.length || 0 )+ (product.community_comments_count || 0)})
            </button>
          </div>
        </article>
      {/each}
    </div>
    
    <div class="column">
      {#each $productsStore.filter((_, i) => i % 3 === 2) as product}
        <article class="product">
          <img 
            src={product.thumbnail} 
            alt={product.title} 
            class="product-image"
          />
          <h3>{product.title}</h3>
          <p class="brand">{product.brand || 'Generic Brand'}</p>
          <div class="product-info">
            <p class="price">${product.price}</p>
            <div class="rating">
              <span class="stars">{getStarRating(product.rating)}</span>
              <span class="rating-text">({product.rating}/5)</span>
            </div>
          </div>
          <p class="description">{product.description}</p>
          <div class="product-actions">
            <button class="view-button" on:click={() => viewProduct(product)}>
              View Details & Reviews ({(product.reviews?.length || 0 )+(product.community_comments_count || 0)})
            </button>
          </div>
        </article>
      {/each}
    </div>
  {/if}
  
  {#if isLoadingMore}
    <div class="loading-more">Loading more products...</div>
  {/if}
  
  {#if allProductsLoaded}
    <div class="end-message">No more products</div>
  {/if}
</div>

<style>
  .grid-container {
    display: grid;
    gap: 20px;
    grid-template-columns: 1fr;
    padding: 20px;
    font-family: Georgia, serif;
  }

  .product {
    margin-bottom: 30px;
    padding-bottom: 20px;
    border-bottom: 1px solid #e2e2e2;
    border-radius: 8px;
    background: #fff;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    padding: 15px;
  }

  .product:last-child {
    border-bottom: none;
  }

  .product-image {
    width: 100%;
    height: 200px;
    object-fit: cover;
    margin-bottom: 15px;
    border-radius: 4px;
  }

  .product h3 {
    font-size: 1.2rem;
    margin-bottom: 8px;
    font-weight: bold;
    color: #333;
  }

  .brand {
    font-style: italic;
    font-size: 0.9rem;
    margin-bottom: 10px;
    color: #666;
  }

  .product-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
  }

  .price {
    font-size: 1.4rem;
    font-weight: bold;
    color: #2c5aa0;
    margin: 0;
  }

  .rating {
    display: flex;
    align-items: center;
    gap: 5px;
  }

  .stars {
    color: #ffc107;
    font-size: 1.1rem;
  }

  .rating-text {
    font-size: 0.9rem;
    color: #666;
  }

  .description {
    font-size: 0.95rem;
    line-height: 1.4;
    color: #555;
    margin-bottom: 15px;
  }

  .product-actions {
    display: flex;
    justify-content: center;
  }

  .view-button {
    background-color: #007bff;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.9rem;
    font-weight: 500;
    transition: background-color 0.2s;
  }

  .view-button:hover {
    background-color: #0056b3;
  }

  .column {
    margin-bottom: 20px;
    border-bottom: 1px solid #e2e2e2; 
    padding-bottom: 20px;
  }

  .column:last-child {
    border-bottom: none;
  }

  .no-products, .loading-more, .end-message {
    grid-column: 1 / -1;
    text-align: center;
    padding: 2rem;
    font-size: 1.1rem;
    color: #666;
  }

  .end-message {
    border-top: 1px solid #e2e2e2;
    margin-top: 1rem;
  }

  @media (max-width: 767px) {
    .product-info {
      flex-direction: column;
      align-items: flex-start;
      gap: 8px;
    }
    
    .product-image {
      height: 150px;
    }
  }

  @media (min-width: 768px) {
    .grid-container {
      grid-template-columns: repeat(2, 1fr);
    }
    
    .column {
      position: relative;
      padding: 0 20px; 
      border-bottom: none; 
    }
    
    .column:not(:last-child)::after {
      content: '';
      position: absolute;
      top: 0;
      right: 0;
      height: 100%;
      width: 1px;
      background-color: #e2e2e2;
    }
  }

  @media (min-width: 1025px) {
    .grid-container {
      grid-template-columns: repeat(3, 1fr);
    }
    
    .column {
      position: relative;
      padding: 0 20px; 
      border-bottom: none; 
    }
    
    .column:first-child {
      padding-left: 0;
    }
    
    .column:last-child {
      padding-right: 0;
    }
  }
</style>