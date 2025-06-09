<script lang="ts">
  export let product: any;

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

  function formatPrice(price: number, discountPercentage?: number) {
    if (discountPercentage) {
      const discountedPrice = price * (1 - discountPercentage / 100);
      return {
        original: price.toFixed(2),
        discounted: discountedPrice.toFixed(2),
        savings: (price - discountedPrice).toFixed(2)
      };
    }
    return { original: price.toFixed(2) };
  }
</script>

<div class="product-details">
  <h1>{product.title}</h1>
  <p class="brand">{product.brand || 'Generic Brand'}</p>
  
  <div class="rating-section">
    <span class="stars">{getStarRating(product.rating)}</span>
    <span class="rating-text">({product.rating}/5)</span>
    <span class="stock-info">• {product.stock} in stock</span>
  </div>
  
  <div class="price-section">
    {#if product.discountPercentage}
      {@const pricing = formatPrice(product.price, product.discountPercentage)}
      <span class="price-original">${pricing.original}</span>
      <span class="price-current">${pricing.discounted}</span>
      <span class="discount-badge">-{product.discountPercentage}%</span>
      <div class="savings">You save: ${pricing.savings}</div>
    {:else}
      <span class="price-current">${product.price}</span>
    {/if}
  </div>
  
  <div class="description">
    <h3>Description</h3>
    <p>{product.description}</p>
  </div>
  
  <div class="product-specs">
    <h3>Product Information</h3>
    <ul>
      <li><strong>Category:</strong> {product.category}</li>
      <li><strong>SKU:</strong> {product.sku || 'N/A'}</li>
      <li><strong>Weight:</strong> {product.weight || 'N/A'} kg</li>
      <li><strong>Dimensions:</strong> {product.dimensions ? `${product.dimensions.width} × ${product.dimensions.height} × ${product.dimensions.depth} cm` : 'N/A'}</li>
    </ul>
  </div>
</div>

<style>
  .product-details h1 {
    font-size: 2rem;
    margin-bottom: 10px;
    color: #333;
  }
  
  .brand {
    font-size: 1.1rem;
    color: #666;
    font-style: italic;
    margin-bottom: 15px;
  }
  
  .rating-section {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 20px;
  }
  
  .stars {
    color: #ffc107;
    font-size: 1.2rem;
  }
  
  .rating-text {
    color: #666;
    font-size: 0.9rem;
  }
  
  .stock-info {
    color: #28a745;
    font-size: 0.9rem;
  }
  
  .price-section {
    margin-bottom: 30px;
  }
  
  .price-original {
    text-decoration: line-through;
    color: #999;
    font-size: 1.1rem;
    margin-right: 10px;
  }
  
  .price-current {
    font-size: 2rem;
    font-weight: bold;
    color: #2c5aa0;
  }
  
  .discount-badge {
    background-color: #dc3545;
    color: white;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 0.8rem;
    margin-left: 10px;
  }
  
  .savings {
    color: #28a745;
    font-size: 0.9rem;
    margin-top: 5px;
  }
  
  .description {
    margin-bottom: 30px;
  }
  
  .description h3 {
    margin-bottom: 10px;
    color: #333;
  }
  
  .description p {
    line-height: 1.6;
    color: #555;
  }
  
  .product-specs {
    margin-bottom: 30px;
  }
  
  .product-specs h3 {
    margin-bottom: 15px;
    color: #333;
  }
  
  .product-specs ul {
    list-style: none;
    padding: 0;
  }
  
  .product-specs li {
    padding: 8px 0;
    border-bottom: 1px solid #eee;
  }
  
  @media (max-width: 768px) {
    .product-details h1 {
      font-size: 1.5rem;
    }
  }
</style>