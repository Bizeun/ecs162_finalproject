<script lang="ts">
  import { authStore, currentProductStore } from '../lib/store';
  
  export let onSearch = (query: string) => {};
  export let onToggleSidebar = () => {};

  let searchInput = '';
  let isSearchVisible = false;

  const handleSubmit = (e: Event) => {
    e.preventDefault();
    onSearch(searchInput);
  };
  
  const toggleSearch = () => {
    isSearchVisible = !isSearchVisible;
  };
  
  const toggleSidebar = () => {
    onToggleSidebar();
  };
  
  const handleLogin = () => {
    window.location.href = '/api/auth/login';
  };
  
  const handleLogout = async () => {
    await fetch('/api/auth/logout');
    window.location.reload();
  };
  
  const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' } as const;
  const currentDate = new Date().toLocaleDateString('en-US', options);

  function goToModeration() {
    window.history.pushState({}, '', '/moderation');
    window.dispatchEvent(new PopStateEvent('popstate'));
  }

  function goHome() {
    window.history.pushState({}, '', '/');
    window.dispatchEvent(new PopStateEvent('popstate'));
    currentProductStore.set(null);
  }
</script>

<header>
  <div class="date-container">
    <div class="date-display" id="current-date">{currentDate}</div>
    <div class="todays-reviews">TODAY'S REVIEWS</div>
  </div>
  
  <div class="logo-container">
    <button class="home-link" on:click={goHome}>
      <h1 class="site-title">Community Product Reviews</h1>
      <p class="site-subtitle">Trusted Reviews by Real Users</p>
    </button>
  </div>
  
  <div class="auth-container">
    {#if $authStore.isAuthenticated}
      <span class="user-info">
        Welcome, {$authStore.user?.name || $authStore.user?.email}
        {#if $authStore.isModerator}
          <span class="moderator-badge">Moderator</span>
        {/if}
      </span>
      {#if $authStore.isModerator}
        <button class="moderation-link" on:click={goToModeration}>Moderation Panel</button>
      {/if}
      <button class="auth-button" on:click={handleLogout}>Logout</button>
    {:else}
      <button class="auth-button" on:click={handleLogin}>Login</button>
    {/if}
  </div>
  
  <button 
    class="menu-icon" 
    on:click={toggleSidebar}
    aria-label="Toggle navigation menu"
    type="button">
    <div></div>
    <div></div>
    <div></div>
  </button>
  
  <div class="search-bar {isSearchVisible ? 'visible' : ''}">
    <form on:submit={handleSubmit}>
      <input 
        type="text" 
        placeholder="Search for products..." 
        bind:value={searchInput}
        aria-label="Search for products"
      />
      <button type="submit">Search</button>
    </form>
  </div>
</header>

<style>
header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  border-bottom: 2px solid #000;
  padding-bottom: 10px;
  margin-bottom: 20px;
  position: relative;
  flex-wrap: wrap;
}

.logo-container {
  flex-grow: 1;
  text-align: center;
  margin: 20px 0;
}

.site-title {
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 2.5rem;
  font-weight: bold;
  margin: 0;
  color: #000;
  letter-spacing: -1px;
}

.site-subtitle {
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
  font-size: 1rem;
  color: #666;
  margin: 5px 0 0 0;
  font-style: italic;
}

.date-container {
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
  padding: 30px 0 0 0;
  text-align: left;
  width: 200px;
}

.date-display {
  font-size: 0.9rem;
  color: #666;
}

.todays-reviews {
  font-size: 0.9rem;
  color: #666;
  font-weight: bold;
  margin-top: 5px;
}

.auth-container {
  padding: 30px 0 0 0;
  width: 200px;
  text-align: right;
}

.user-info {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  margin-bottom: 5px;
  font-size: 0.9rem;
}

.moderator-badge {
  display: inline-block;
  background-color: #007bff;
  color: white;
  font-size: 0.7rem;
  padding: 0.1rem 0.3rem;
  border-radius: 3px;
  margin-top: 3px;
}

.auth-button {
  background: none;
  border: 1px solid #000;
  padding: 0.2rem 0.5rem;
  cursor: pointer;
  font-size: 0.8rem;
}

.auth-button:hover {
  background-color: #f0f0f0;
}

.menu-icon {
  display: none;
  cursor: pointer;
  font-size: 24px;
  padding: 30px 10px 0 0;
  background: none;        
  border: none;            
  appearance: none;        
  margin: 0;              
}

.menu-icon div {
  width: 25px;
  height: 3px;
  background-color: #333;
  margin: 5px 0;
  border-radius: 2px;
}

.search-bar {
  width: 100%;
  padding: 1rem 0;
  border-bottom: 1px solid #e2e2e2;
}

.search-bar form {
  display: flex;
  max-width: 600px;
  margin: 0 auto;
}

.search-bar input {
  flex: 1;
  padding: 0.5rem;
  border: 1px solid #ccc;
  border-right: none;
  font-size: 1rem;
}

.search-bar button {
  background-color: #000;
  color: #fff;
  border: 1px solid #000;
  padding: 0.5rem 1rem;
  cursor: pointer;
}
.moderation-link {
  display: inline-block;
  background-color: #dc3545;
  color: white;
  text-decoration: none;
  font-size: 0.8rem;
  padding: 0.2rem 0.5rem;
  border-radius: 3px;
  margin-bottom: 5px;
  transition: background-color 0.2s;
}

.moderation-link:hover {
  background-color: #c82333;
}
.home-link {
  background: none;
  border: none;
  cursor: pointer;
  text-align: center;
  padding: 0;
}

@media (max-width: 767px) {
  .menu-icon {
    display: block;
    order: 1;
  }
  
  .logo-container {
    width: 100%;
    text-align: center;
    order: 2;
    margin: 10px 0;
  }
  
  .site-title {
    font-size: 2rem;
  }
  
  .date-container {
    width: 100%;
    text-align: center;
    order: 3;
    padding: 10px 0;
  }
  
  .auth-container {
    width: 100%;
    text-align: center;
    order: 4;
    padding: 10px 0;
  }
  
  header {
    flex-direction: row;
    flex-wrap: wrap;
    align-items: center;
  }
  
  .search-bar {
    display: none;
  }
  
  .search-bar.visible {
    display: block;
  }
}
</style>