<script lang="ts">
  const currentYear = new Date().getFullYear();

  function handleLinkClick(e: Event) {
    e.preventDefault();
    const linkText = (e.currentTarget as HTMLAnchorElement).textContent;
    console.log(`Clicked on: ${linkText}`);
  }
</script>

<footer>
  <div class="footer-content">
    <div class="footer-section">
      <h4>About</h4>
      <ul>
        <li><a href="/about" on:click={handleLinkClick}>About Us</a></li>
        <li><a href="/contact" on:click={handleLinkClick}>Contact Us</a></li>
        <li><a href="/careers" on:click={handleLinkClick}>Work With Us</a></li>
        <li><a href="/advertise" on:click={handleLinkClick}>Advertise</a></li>
      </ul>
    </div>
    
    <div class="footer-section">
      <h4>Categories</h4>
      <ul>
        <li><a href="/electronics" on:click={handleLinkClick}>Electronics</a></li>
        <li><a href="/beauty" on:click={handleLinkClick}>Beauty & Personal Care</a></li>
        <li><a href="/home-garden" on:click={handleLinkClick}>Home & Garden</a></li>
        <li><a href="/clothing" on:click={handleLinkClick}>Fashion & Clothing</a></li>
      </ul>
    </div>
    
    <div class="footer-section">
      <h4>Community</h4>
      <ul>
        <li><a href="/how-to-review" on:click={handleLinkClick}>How to Write Reviews</a></li>
        <li><a href="/community-guidelines" on:click={handleLinkClick}>Community Guidelines</a></li>
        <li><a href="/top-reviewers" on:click={handleLinkClick}>Top Reviewers</a></li>
        <li><a href="/help" on:click={handleLinkClick}>Help & Support</a></li>
      </ul>
    </div>
    
    <div class="footer-section">
      <h4>Connect</h4>
      <ul>
        <li><a href="/newsletter" on:click={handleLinkClick}>Email Newsletter</a></li>
        <li><a href="https://facebook.com" target="_blank" rel="noopener noreferrer">Facebook</a></li>
        <li><a href="https://twitter.com" target="_blank" rel="noopener noreferrer">Twitter</a></li>
        <li><a href="https://instagram.com" target="_blank" rel="noopener noreferrer">Instagram</a></li>
      </ul>
    </div>
  </div>
  
  <div class="footer-bottom">
    <p>&copy; {currentYear} Community Product Reviews. All Rights Reserved.</p>
    <p>This website is created for educational purposes as part of ECS 162 Final Project.</p>
  </div>
</footer>

<style>
  footer {
    margin-top: 40px;
    padding: 30px 0;
    border-top: 2px solid #000;
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
  }
  
  .footer-content {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    margin-bottom: 20px;
  }
  
  .footer-section {
    flex: 1;
    min-width: 200px;
    margin-bottom: 20px;
    padding: 0 15px;
  }
  
  .footer-section h4 {
    font-size: 14px;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 15px;
  }
  
  .footer-section ul {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  
  .footer-section li {
    margin-bottom: 8px;
  }
  
  .footer-section a {
    color: #333;
    text-decoration: none;
    font-size: 14px;
  }
  
  .footer-section a:hover {
    text-decoration: underline;
  }
  
  .footer-bottom {
    text-align: center;
    border-top: 1px solid #e2e2e2;
    padding-top: 20px;
    font-size: 12px;
    color: #666;
  }
  
  .footer-bottom p {
    margin: 5px 0;
  }
  
  @media (max-width: 767px) {
    .footer-content {
      flex-direction: column;
    }
    
    .footer-section {
      width: 100%;
    }
  }
</style>