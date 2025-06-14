<script lang="ts">
import { onMount } from 'svelte';
import { checkAuthStatus, fetchProducts, searchProducts, authStore, productsStore, currentProductStore } from './lib/store';
import Header from './components/Header.svelte';
import ProductGrid from './components/ProductGrid.svelte';
import ProductDetail from './components/ProductDetail.svelte';
import Footer from './components/Footer.svelte';
import Sidebar from './components/Sidebar.svelte';
import ModerationPanel from './components/ModeratorPanel.svelte';

let isLoading = true;
let searchQuery = '';
let isSidebarOpen = false;
let viewingProduct = false;
let viewingModeration = false;

currentProductStore.subscribe(product => {
  viewingProduct = !!product;
});

function checkCurrentRoute() {
  const path = window.location.pathname;
  if (path === '/moderation') {
    viewingModeration = true;
    viewingProduct = false;
  } else {
    viewingModeration = false;
  }
}

const handleSearch = (e: CustomEvent<string>) => {
  const query = e.detail;
  searchQuery = query;
  if (query) {
    searchProducts(query);
  } else {
    fetchProducts();
  }
};

const toggleSidebar = () => {
  isSidebarOpen = !isSidebarOpen;
};

const closeSidebar = () => {
  isSidebarOpen = false;
};

onMount(async () => {
  await checkAuthStatus();
  checkCurrentRoute();
  await fetchProducts();
  isLoading = false;
  document.title = "Community Product Reviews";
  window.addEventListener('popstate', checkCurrentRoute);
});
</script>

<main class:sidebar-open={isSidebarOpen}>
  <div class="container">
    <Header on:search={handleSearch} on:toggleSidebar={toggleSidebar} />
    <Sidebar isOpen={isSidebarOpen} on:closeSidebar={() => isSidebarOpen = false} />
    
    {#if isLoading}
      <div class="loading">Loading products...</div>
    {:else}
      {#if viewingModeration}
        <ModerationPanel />
      {:else if viewingProduct}
        <ProductDetail />
      {:else}
        <ProductGrid searchQuery={searchQuery} />
      {/if}
    {/if}
    <Footer />
  </div>
</main>

<style>
:global(body) {
  font-family: Georgia, 'Times New Roman', Times, serif;
  line-height: 1.6;
  color: #333;
  background-color: #fff;
  padding: 0 15px;
  position: relative;
  overflow-x: hidden;
  margin: 0;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  transition: transform 0.3s ease;
}

main.sidebar-open .container {
  transform: translateX(250px);
}

.loading {
  text-align: center;
  padding: 2rem;
  font-size: 1.2rem;
}

@media (max-width: 767px) {
  main.sidebar-open .container {
    transform: translateX(250px);
  }
}
</style>