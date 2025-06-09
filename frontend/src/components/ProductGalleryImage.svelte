<script lang="ts">
  export let product: any;
  
  let selectedImage = product.thumbnail;
  
  function selectImage(imageUrl: string) {
    selectedImage = imageUrl;
  }
</script>

<div class="product-images">
  <div class="main-image">
    <img src={selectedImage} alt={product.title} />
  </div>
  
  {#if product.images && product.images.length > 1}
    <div class="image-gallery">
      <img 
        src={product.thumbnail} 
        alt={product.title} 
        class="gallery-image {selectedImage === product.thumbnail ? 'active' : ''}"
        on:click={() => selectImage(product.thumbnail)}
      />
      {#each product.images.slice(0, 3) as image}
        <img 
          src={image} 
          alt={product.title} 
          class="gallery-image {selectedImage === image ? 'active' : ''}"
          on:click={() => selectImage(image)}
        />
      {/each}
    </div>
  {/if}
</div>

<style>
  .product-images {
    display: flex;
    flex-direction: column;
    gap: 15px;
  }
  
  .main-image img {
    width: 100%;
    max-height: 400px;
    object-fit: cover;
    border-radius: 8px;
  }
  
  .image-gallery {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
  }
  
  .gallery-image {
    width: 100%;
    height: 80px;
    object-fit: cover;
    border-radius: 4px;
    cursor: pointer;
    border: 2px solid transparent;
    transition: border-color 0.2s;
  }
  
  .gallery-image:hover {
    border-color: #007bff;
  }
  
  .gallery-image.active {
    border-color: #007bff;
  }
  
  @media (max-width: 768px) {
    .image-gallery {
      grid-template-columns: repeat(3, 1fr);
    }
  }
</style>