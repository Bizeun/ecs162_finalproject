<script lang='ts'>
  export let isOpen = false;
  export let onClose = () => {};

  function closeSidebar() {
    onClose();
  }
</script>

<div class="sidebar {isOpen ? 'active' : ''}">
  <button class="close-sidebar" on:click={closeSidebar}>×</button>
  
  <div class="sidebar-section">
    <h4>Categories</h4>
    <ul>
      <li><a href="/" on:click|preventDefault={closeSidebar}>All Products</a></li>
      <li><a href="/beauty" on:click|preventDefault={closeSidebar}>Beauty</a></li>
      <li><a href="/smartphones" on:click|preventDefault={closeSidebar}>Smartphones</a></li>
      <li><a href="/laptops" on:click|preventDefault={closeSidebar}>Laptops</a></li>
      <li><a href="/fragrances" on:click|preventDefault={closeSidebar}>Fragrances</a></li>
      <li><a href="/furniture" on:click|preventDefault={closeSidebar}>Furniture</a></li>
      <li><a href="/groceries" on:click|preventDefault={closeSidebar}>Groceries</a></li>
      <li><a href="/home-decoration" on:click|preventDefault={closeSidebar}>Home Decoration</a></li>
    </ul>
  </div>
  
  <div class="sidebar-section">
    <h4>Fashion & Accessories</h4>
    <ul>
      <li><a href="/mens-shirts" on:click|preventDefault={closeSidebar}>Men's Shirts</a></li>
      <li><a href="/mens-shoes" on:click|preventDefault={closeSidebar}>Men's Shoes</a></li>
      <li><a href="/mens-watches" on:click|preventDefault={closeSidebar}>Men's Watches</a></li>
      <li><a href="/womens-dresses" on:click|preventDefault={closeSidebar}>Women's Dresses</a></li>
      <li><a href="/womens-shoes" on:click|preventDefault={closeSidebar}>Women's Shoes</a></li>
      <li><a href="/womens-bags" on:click|preventDefault={closeSidebar}>Women's Bags</a></li>
      <li><a href="/sunglasses" on:click|preventDefault={closeSidebar}>Sunglasses</a></li>
    </ul>
  </div>
  
  <div class="sidebar-section">
    <h4>Community</h4>
    <ul>
      <li><a href="/top-rated" on:click|preventDefault={closeSidebar}>Top Rated Products</a></li>
      <li><a href="/recent-reviews" on:click|preventDefault={closeSidebar}>Recent Reviews</a></li>
      <li><a href="/trending" on:click|preventDefault={closeSidebar}>Trending Now</a></li>
      <li><a href="/most-reviewed" on:click|preventDefault={closeSidebar}>Most Reviewed</a></li>
    </ul>
  </div>
</div>

<style>
  .sidebar {
    position: fixed;
    top: 0;
    left: -250px;
    width: 250px;
    height: 100%;
    background-color: #f8f8f8;
    box-shadow: 2px 0 5px rgba(0,0,0,0.2);
    transition: left 0.3s ease;
    z-index: 1000;
    padding: 20px;
    overflow-y: auto;
  }
  
  .sidebar.active {
    left: 0;
  }

  .close-sidebar {
    position: absolute;
    top: 10px;
    right: 10px;
    font-size: 24px;
    cursor: pointer;
    background: none;
    border: none;
  }

  .sidebar-section {
    margin-bottom: 20px;
    padding-bottom: 15px;
    border-bottom: 1px solid #e2e2e2;
  }

  .sidebar-section h4 {
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    font-size: 14px;
    font-weight: bold;
    margin-bottom: 10px;
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  .sidebar-section ul {
    list-style: none;
    padding: 0;
    margin: 0;
  }

  .sidebar-section li {
    margin-bottom: 8px;
  }

  .sidebar-section a {
    color: #333;
    text-decoration: none;
    font-size: 16px;
  }

  .sidebar-section a:hover {
    text-decoration: underline;
  }
  
  @media (min-width: 1024px) {
    .sidebar {
      display: none;
    }
  }

  .sidebar.active {
    left: 0;
  } 
</style>