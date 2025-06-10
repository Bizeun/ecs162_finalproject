<script lang="ts">
import { onMount } from 'svelte';
import { authStore, userVotesStore, flaggedReviewsStore, voteOnReview, flagReview, loadUserVotesForProduct, commentsStore } from '../lib/store';

export let product: any;

let isAuthenticated = false;
let userVotes: Record<string, string | null> = {};
let flaggedReviews: Record<string, boolean> = {};
let showFlagModal = false;
let currentReviewId = '';
let flagReason = '';
let showSuccessToast = false;
let showErrorToast = false;
let showWarningToast = false;
let toastMessage = '';

$: userCommentsCount = $commentsStore.length;
$: totalReviewsCount = (product.reviews?.length || 0) + userCommentsCount;

// Subscribe to stores
authStore.subscribe(auth => {
    isAuthenticated = auth.isAuthenticated;
});

userVotesStore.subscribe(votes => {
    userVotes = votes;
});

flaggedReviewsStore.subscribe(flagged => {
    flaggedReviews = flagged;
});

onMount(async () => {
    if (isAuthenticated && product) {
        await loadUserVotesForProduct(product);
    }
});


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

async function handleVote(reviewId: string, voteType: 'up' | 'down') {
  if (!isAuthenticated) {
    showToast('Please log in to vote on reviews', 'warning');
    return;
  }

  const result = await voteOnReview(reviewId, voteType);
  if (result.success) {
    // Update the review votes in the product object
    const reviewIndex = product.reviews.findIndex((r: any) => r.id === reviewId);
    if (reviewIndex !== -1) {
      product.reviews[reviewIndex].votes = result.votes;
    }
    
    // Force reactivity update
    product = { ...product };
  } else {
    showToast('Failed to vote. Please try again.', 'error');
  }
}

function openFlagModal(reviewId: string) {
  if (!isAuthenticated) {
    showToast('Please log in to flag reviews', 'warning');
    return;
  }
  
  currentReviewId = reviewId;
  flagReason = '';
  showFlagModal = true;
}

function closeFlagModal() {
  showFlagModal = false;
  currentReviewId = '';
  flagReason = '';
}

async function submitFlag() {
    if (!flagReason.trim()) {
        showToast('Please provide a reason for flagging this review', 'warning');
        return;
    }

    const success = await flagReview(currentReviewId, flagReason);
    if (success) {
        showToast('Review flagged successfully. Thank you for helping maintain review quality.', 'success');
        closeFlagModal();
    } else {
        showToast('Failed to flag review. Please try again.', 'error');
    }
}

function showToast(message: string, type: 'success' | 'error' | 'warning') {
  toastMessage = message;
  if (type === 'success') {
    showSuccessToast = true;
    setTimeout(() => showSuccessToast = false, 3000);
  } else if (type === 'error') {
    showErrorToast = true;
    setTimeout(() => showErrorToast = false, 3000);
  } else if (type === 'warning') {
    showWarningToast = true;
    setTimeout(() => showWarningToast = false, 3000);
  }
}

function getUserVoteForReview(reviewId: string): string | null {
    return userVotes[reviewId] || null;
}

function isReviewFlagged(reviewId: string): boolean {
    return flaggedReviews[reviewId] || false;
}
</script>

{#if product.reviews && product.reviews.length > 0}
  <div class="original-reviews-section">
    <h3>Reviews & Comments ({totalReviewsCount} total)</h3>
    <div class="reviews-list">
      {#each product.reviews as review}
        <div class="review-item">
          <div class="review-header">
            <span class="reviewer-name">{review.reviewerName}</span>
            <span class="review-rating">{getStarRating(review.rating)}</span>
            <span class="review-date">{new Date(review.date).toLocaleDateString()}</span>
          </div>
          <p class="review-comment">{review.comment}</p>
          
          <div class="review-actions">
            <div class="vote-section">
              <button 
                  class="vote-button upvote {getUserVoteForReview(review.id) === 'up' ? 'active' : ''}"
                  on:click={() => handleVote(review.id, 'up')}
                  disabled={!isAuthenticated}
                  title={isAuthenticated ? 'Mark as helpful' : 'Login to vote'}
              >
                  👍 {review.votes?.upvotes || 0}
              </button>
              
              <button 
                  class="vote-button downvote {getUserVoteForReview(review.id) === 'down' ? 'active' : ''}"
                  on:click={() => handleVote(review.id, 'down')}
                  disabled={!isAuthenticated}
                  title={isAuthenticated ? 'Mark as not helpful' : 'Login to vote'}
              >
                  👎 {review.votes?.downvotes || 0}
              </button>
              
              <span class="vote-score">
                  Score: {review.votes?.score || 0}
              </span>
            </div>
              
            <div class="flag-section">
              {#if isReviewFlagged(review.id)}
                  <span class="flagged-indicator">🚩 Flagged</span>
              {:else}
                  <button 
                      class="flag-button"
                      on:click={() => openFlagModal(review.id)}
                      disabled={!isAuthenticated}
                      title={isAuthenticated ? 'Report inappropriate content' : 'Login to flag reviews'}
                  >
                      🚩 Flag
                  </button>
              {/if}
            </div>
          </div>
        </div>
      {/each}
    </div>
  </div>
{/if}

<!-- Flag Modal -->
{#if showFlagModal}
<div 
  class="modal-overlay" 
  role="dialog" 
  aria-modal="true" 
  aria-labelledby="modal-title"
  tabindex="-1"
  on:click={closeFlagModal}
  on:keydown={(e) => e.key === 'Escape' && closeFlagModal()}
>
  <div 
    class="modal-content"
    on:click|stopPropagation
  >
    <h4>Flag Review</h4>
    <p>Why are you flagging this review?</p>
    <select 
      bind:value={flagReason} 
      class="reason-select"
      aria-label="Select reason for flagging"
    >
      <option value="">Select a reason...</option>
      <option value="spam">Spam or fake review</option>
      <option value="inappropriate">Inappropriate content</option>
      <option value="off-topic">Off-topic or irrelevant</option>
      <option value="misleading">Misleading information</option>
      <option value="harassment">Harassment or abuse</option>
      <option value="other">Other</option>
    </select>
    
    {#if flagReason === 'other'}
    <textarea 
      bind:value={flagReason} 
      placeholder="Please describe the issue..."
      class="reason-textarea"
      aria-label="Describe the issue"
    ></textarea>
    {/if}
    
    <div class="modal-actions">
      <button class="cancel-button" on:click={closeFlagModal}>Cancel</button>
      <button class="submit-button" on:click={submitFlag}>Submit Flag</button>
    </div>
  </div>
</div>
{/if}

<style>
.original-reviews-section {
  margin-bottom: 40px;
  border-top: 2px solid #e2e2e2;
  padding-top: 30px;
}

.original-reviews-section h3 {
  margin-bottom: 20px;
  color: #333;
}

.review-item {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 15px;
}

.review-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 10px;
}

.reviewer-name {
  font-weight: bold;
  color: #333;
}

.review-rating {
  color: #ffc107;
}

.review-date {
  color: #666;
  font-size: 0.9rem;
}

.review-comment {
  margin-bottom: 15px;
  line-height: 1.5;
}

.review-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.vote-section {
    display: flex;
    align-items: center;
    gap: 10px;
}

.vote-button {
  background: #f8f9fa;
  border: 1px solid #ddd;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 4px;
}

.vote-button:hover:not(:disabled) {
  background: #e9ecef;
  transform: translateY(-1px);
}

.vote-button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.vote-button.upvote.active {
  background: #d4edda;
  border-color: #28a745;
  color: #155724;
}

.vote-button.downvote.active {
  background: #f8d7da;
  border-color: #dc3545;
  color: #721c24;
}

.vote-score {
  font-weight: bold;
  color: #495057;
  font-size: 0.9rem;
}

.flag-section {
  display: flex;
  align-items: center;
}

.flag-button {
  background: transparent;
  border: 1px solid #ffc107;
  color: #856404;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.flag-button:hover:not(:disabled) {
  background: #fff3cd;
}

.flag-button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.flagged-indicator {
  color: #dc3545;
  font-size: 0.8rem;
  font-weight: bold;
}
  /* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 20px;
  border-radius: 8px;
  width: 90%;
  max-width: 400px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.modal-content h4 {
  margin: 0 0 10px 0;
  color: #333;
}

.modal-content p {
  margin: 0 0 15px 0;
  color: #666;
}

.reason-select {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  margin-bottom: 15px;
}

.reason-textarea {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  margin-bottom: 15px;
  min-height: 80px;
  resize: vertical;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.cancel-button {
  background: #6c757d;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.submit-button {
  background: #dc3545;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.cancel-button:hover {
  background: #5a6268;
}

.submit-button:hover {
  background: #c82333;
}
  
@media (max-width: 768px) {
  .review-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 5px;
  }
  
  .review-actions {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .vote-section {
    width: 100%;
    justify-content: space-between;
  }
  
  .modal-content {
    width: 95%;
    margin: 20px;
  }
}
</style>