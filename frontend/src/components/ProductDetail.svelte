<script lang="ts">

import { currentProductStore, fetchComments, loadUserVotesForProduct, fetchProductById } from '../lib/store';
import ProductImageGallery from './ProductGalleryImage.svelte';
import ProductInfoSection from './ProductInfoSection.svelte';
import ProductReviewsSection from './ProductReviewsSection.svelte';
import CommunityCommentsSection from './CommunityCommentsSection.svelte';

let product: any = null;

currentProductStore.subscribe(async value => {
  product = value;
  if (product) {
    fetchComments(product.id.toString());
    await loadUserVotesForProduct(product);
  }
});

function goBack() {
  currentProductStore.set(null);
}

async function refreshProduct() {
  if (product && product.id) {
    await fetchProductById(product.id.toString());
    await loadUserVotesForProduct(product);
  }
}

</script>

<div class="product-detail">
  <button class="back-button" on:click={goBack}>&larr; Back to Products</button>
  
  {#if product}
    <div class="product-info">
      <ProductImageGallery {product} />
      <ProductInfoSection {product} />
    </div>

    <ProductReviewsSection {product} />
    <CommunityCommentsSection productId={product.id.toString()} />
  {:else}
    <div class="loading">Loading product details...</div>
  {/if}
</div>

<style>
  .product-detail {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
  }
  
  .back-button {
    background: none;
    border: none;
    color: #000;
    cursor: pointer;
    font-size: 16px;
    padding: 0;
    margin-bottom: 30px;
    display: inline-block;
  }
  
  .back-button:hover {
    text-decoration: underline;
  }
  
  .product-info {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 40px;
    margin-bottom: 40px;
  }
  
  .loading {
    text-align: center;
    padding: 50px;
    color: #666;
    font-style: italic;
  }
  
  @media (max-width: 768px) {
    .product-info {
      grid-template-columns: 1fr;
      gap: 20px;
    }
  }
</style>