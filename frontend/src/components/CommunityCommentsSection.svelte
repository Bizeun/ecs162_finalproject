<script lang="ts">
import { commentsStore, authStore, addComment, removeComment, redactComment, flagComment, voteOnComment, getCommentVotes, getUserCommentVote } from '../lib/store';

export let productId: string;

let commentContent = '';
let replyContent = '';
let replyingToId: string | null = null;
let redactingCommentId: string | null = null;
let redactedContent = '';
let showFlagModal = false;
let currentCommentId = '';
let flagReason = '';
let showSuccessToast = false;
let showErrorToast = false;
let showWarningToast = false;
let toastMessage = '';
let commentVotes: Record<string, any> = {};
let userCommentVotes: Record<string, string | null> = {}; 

async function handleCommentSubmit(event: Event) {
  event.preventDefault();
  
  if (!commentContent.trim()) return;
  
  const success = await addComment(productId, commentContent);
  
  if (success) {
    commentContent = '';
  }
}

async function handleReplySubmit(event: Event, parentId: string) {
  event.preventDefault();
  
  if (!replyContent.trim()) return;
  
  const success = await addComment(productId, replyContent, parentId);
  
  if (success) {
    replyContent = '';
    replyingToId = null;
  }
}

async function handleRemoveComment(commentId: string) {
  await removeComment(commentId, productId);
}

async function handleRedactComment(event: Event) {
  event.preventDefault();
  
  if (!redactingCommentId || !redactedContent.trim()) return;
  
  const success = await redactComment(redactingCommentId, redactedContent, productId);
  
  if (success) {
    redactedContent = '';
    redactingCommentId = null;
  }
}

function setReplyMode(commentId: string) {
  replyingToId = commentId;
  redactingCommentId = null;
}

function setRedactMode(commentId: string, content: string) {
  redactingCommentId = commentId;
  redactedContent = content;
  replyingToId = null;
}

function hasRedactions(content: string) {
  return content.includes('█');
}

function getNestedComments(comments: any[]) {
  const commentMap = new Map();
  const rootComments: any[] = [];
  
  comments.forEach(comment => {
    commentMap.set(comment._id, {
      ...comment,
      replies: []
    });
  });
  
  comments.forEach(comment => {
    if (comment.parent_id) {
      const parent = commentMap.get(comment.parent_id);
      if (parent) {
        parent.replies.push(commentMap.get(comment._id));
      } else {
        rootComments.push(commentMap.get(comment._id));
      }
    } else {
      rootComments.push(commentMap.get(comment._id));
    }
  });
  
  return rootComments;
}

function openFlagModal(commentId: string) {
  if (!$authStore.isAuthenticated) {
    showToast('Please log in to flag comments', 'warning');
    return;
  }
  
  currentCommentId = commentId;
  flagReason = '';
  showFlagModal = true;
}

function closeFlagModal() {
  showFlagModal = false;
  currentCommentId = '';
  flagReason = '';
}

async function submitFlag() {
  if (!flagReason.trim()) {
    showToast('Please provide a reason for flagging this comment', 'warning');
    return;
  }

  const success = await flagComment(currentCommentId, flagReason);
  if (success) {
    showToast('Comment flagged successfully. Thank you for helping maintain community standards.', 'success');
    closeFlagModal();
  } else {
    showToast('Failed to flag comment. Please try again.', 'error');
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

async function handleCommentVote(commentId: string, voteType: 'up' | 'down') {
  if (!$authStore.isAuthenticated) {
    showToast('Please log in to vote on comments', 'warning');
    return;
  }

  const result = await voteOnComment(commentId, voteType);
  if (result.success) {
    // Update local vote data
    commentVotes[commentId] = result.votes;
    
    // Update user vote state
    if (result.action === 'removed') {
      userCommentVotes[commentId] = null;
    } else {
      userCommentVotes[commentId] = voteType;
    }
    
    // Force reactivity
    commentVotes = { ...commentVotes };
    userCommentVotes = { ...userCommentVotes };
  } else {
    showToast('Failed to vote. Please try again.', 'error');
  }
}

// Load vote data when comments change
$: if ($commentsStore.length > 0) {
  loadCommentVotes();
}

async function loadCommentVotes() {
  for (const comment of $commentsStore) {
    // Load vote counts
    const votes = await getCommentVotes(comment._id);
    if (votes) {
      commentVotes[comment._id] = votes;
    }
    
    // Load user vote if authenticated
    if ($authStore.isAuthenticated) {
      const userVote = await getUserCommentVote(comment._id);
      userCommentVotes[comment._id] = userVote;
    }
  }
  
  // Force reactivity
  commentVotes = { ...commentVotes };
  userCommentVotes = { ...userCommentVotes };
}

</script>

<div class="comments-section">
  <h3>Community Discussion</h3>
  
  {#if $authStore.isAuthenticated}
    <form class="comment-form" on:submit={handleCommentSubmit}>
      <textarea 
        bind:value={commentContent} 
        placeholder="Share your thoughts about this product..." 
        rows="3"
      ></textarea>
      <button type="submit" class="submit-button">Post Comment</button>
    </form>
  {:else}
    <div class="login-prompt">
      <p>Please <a href="/api/auth/login">login</a> to join the discussion.</p>
    </div>
  {/if}
  
  <div class="comments-list">
    {#if $commentsStore.length === 0}
      <p class="no-comments">No community comments yet. Be the first to share your thoughts!</p>
    {:else}
      {#each getNestedComments($commentsStore) as comment (comment._id)}
        <div class="comment">
          <div class="comment-header">
            <span class="comment-author">{comment.user_name}</span>
            <span class="comment-date">{new Date(comment.created_at).toLocaleString()}</span>
          </div>
          
          <div class="comment-content">
            {#if comment.is_removed}
              <p class="removed-comment">COMMENT REMOVED BY MODERATOR</p>
            {:else if comment.redacted_content}
              <p>{comment.redacted_content}</p>
              {#if hasRedactions(comment.redacted_content)}
                <span class="redacted-note">(This comment has been redacted by a moderator)</span>
              {/if}
            {:else}
              <p>{comment.content}</p>
            {/if}
          </div>
          
          <div class="comment-actions">
            <div class="vote-section">
              <button 
                class="vote-button upvote {userCommentVotes[comment._id] === 'up' ? 'active' : ''}"
                on:click={() => handleCommentVote(comment._id, 'up')}
                disabled={!$authStore.isAuthenticated || comment.is_removed}
                title={$authStore.isAuthenticated ? 'Mark as helpful' : 'Login to vote'}
              >
                👍 {commentVotes[comment._id]?.upvotes || 0}
              </button>
              
              <button 
                class="vote-button downvote {userCommentVotes[comment._id] === 'down' ? 'active' : ''}"
                on:click={() => handleCommentVote(comment._id, 'down')}
                disabled={!$authStore.isAuthenticated || comment.is_removed}
                title={$authStore.isAuthenticated ? 'Mark as not helpful' : 'Login to vote'}
              >
                👎 {commentVotes[comment._id]?.downvotes || 0}
              </button>
              
              <span class="vote-score">
                Score: {commentVotes[comment._id]?.score || 0}
              </span>
            </div>
            <div class="action-section">
              {#if $authStore.isAuthenticated && !comment.is_removed}
                <button class="action-button" on:click={() => setReplyMode(comment._id)}>
                  Reply
                </button>
                <button class="action-button flag-button" on:click={() => openFlagModal(comment._id)}>
                  🚩 Flag
                </button>
              {/if}
            
              {#if $authStore.isModerator && !comment.is_removed}
                <button class="action-button moderator-action" on:click={() => handleRemoveComment(comment._id)}>
                  Remove
                </button>
                <button class="action-button moderator-action" on:click={() => setRedactMode(comment._id, comment.content)}>
                  Redact
                </button>
              {/if}
            </div>
          </div>
          
          {#if replyingToId === comment._id && $authStore.isAuthenticated}
            <form class="reply-form" on:submit={(e) => handleReplySubmit(e, comment._id)}>
              <textarea 
                bind:value={replyContent} 
                placeholder="Write a reply..." 
                rows="2"
              ></textarea>
              <div class="form-actions">
                <button type="submit" class="submit-button">Post Reply</button>
                <button type="button" class="cancel-button" on:click={() => replyingToId = null}>
                  Cancel
                </button>
              </div>
            </form>
          {/if}
          
          {#if redactingCommentId === comment._id && $authStore.isModerator}
            <form class="redact-form" on:submit={handleRedactComment}>
              <textarea 
                bind:value={redactedContent} 
                placeholder="Edit content (use █ character for redactions)" 
                rows="3"
              ></textarea>
              <div class="form-info">
                <p>To redact text, replace it with the █ character (FULL BLOCK, U+2588)</p>
              </div>
              <div class="form-actions">
                <button type="submit" class="submit-button">Save Redaction</button>
                <button type="button" class="cancel-button" on:click={() => redactingCommentId = null}>
                  Cancel
                </button>
              </div>
            </form>
          {/if}
          
          {#if comment.replies && comment.replies.length > 0}
            <div class="replies">
              {#each comment.replies as reply (reply._id)}
                <div class="comment reply">
                  <div class="comment-header">
                    <span class="comment-author">{reply.user_name}</span>
                    <span class="comment-date">{new Date(reply.created_at).toLocaleString()}</span>
                  </div>
                  
                  <div class="comment-content">
                    {#if reply.is_removed}
                      <p class="removed-comment">COMMENT REMOVED BY MODERATOR</p>
                    {:else if reply.redacted_content}
                      <p>{reply.redacted_content}</p>
                      {#if hasRedactions(reply.redacted_content)}
                        <span class="redacted-note">(This comment has been redacted by a moderator)</span>
                      {/if}
                    {:else}
                      <p>{reply.content}</p>
                    {/if}
                  </div>
                  
                  <div class="comment-actions">
                    <div class="vote-section">
                      <button 
                        class="vote-button upvote {userCommentVotes[reply._id] === 'up' ? 'active' : ''}"
                        on:click={() => handleCommentVote(reply._id, 'up')}
                        disabled={!$authStore.isAuthenticated || reply.is_removed}
                      >
                        👍 {commentVotes[reply._id]?.upvotes || 0}
                      </button>
                      
                      <button 
                        class="vote-button downvote {userCommentVotes[reply._id] === 'down' ? 'active' : ''}"
                        on:click={() => handleCommentVote(reply._id, 'down')}
                        disabled={!$authStore.isAuthenticated || reply.is_removed}
                      >
                        👎 {commentVotes[reply._id]?.downvotes || 0}
                      </button>
                      
                      <span class="vote-score">
                        Score: {commentVotes[reply._id]?.score || 0}
                      </span>
                    </div>
                      {#if $authStore.isAuthenticated && !reply.is_removed}
                        <button class="action-button flag-button" on:click={() => openFlagModal(reply._id)}>
                          🚩 Flag
                        </button>
                      {/if}
                      <div class="action-section">
                      {#if $authStore.isModerator &&  !reply.is_removed}
                        <button class="action-button moderator-action" on:click={() => handleRemoveComment(reply._id)}>
                          Remove
                        </button>
                        <button class="action-button moderator-action" on:click={() => setRedactMode(reply._id, reply.content)}>
                          Redact
                        </button>
                      {/if}
                    </div>
                  </div>
                  
                  {#if redactingCommentId === reply._id && $authStore.isModerator}
                    <form class="redact-form" on:submit={handleRedactComment}>
                      <textarea 
                        bind:value={redactedContent} 
                        placeholder="Edit content (use █ character for redactions)" 
                        rows="3"
                      ></textarea>
                      <div class="form-info">
                        <p>To redact text, replace it with the █ character (FULL BLOCK, U+2588)</p>
                      </div>
                      <div class="form-actions">
                        <button type="submit" class="submit-button">Save Redaction</button>
                        <button type="button" class="cancel-button" on:click={() => redactingCommentId = null}>
                          Cancel
                        </button>
                      </div>
                    </form>
                  {/if}
                </div>
              {/each}
            </div>
          {/if}
        </div>
      {/each}
    {/if}
  </div>
</div>

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
  <div class="modal-content">
    <h4 id="modal-title">Flag Comment</h4>
    <p>Why are you flagging this comment?</p>
    
    <select 
      bind:value={flagReason} 
      class="reason-select"
      aria-label="Select reason for flagging"
    >
      <option value="">Select a reason...</option>
      <option value="spam">Spam or fake comment</option>
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

<!-- Toast Notifications -->
{#if showSuccessToast}
<div class="toast success-toast">
  <div class="toast-content">
    <span class="toast-icon">✅</span>
    <span class="toast-message">{toastMessage}</span>
  </div>
</div>
{/if}

{#if showErrorToast}
<div class="toast error-toast">
  <div class="toast-content">
    <span class="toast-icon">❌</span>
    <span class="toast-message">{toastMessage}</span>
  </div>
</div>
{/if}

{#if showWarningToast}
<div class="toast warning-toast">
  <div class="toast-content">
    <span class="toast-icon">⚠️</span>
    <span class="toast-message">{toastMessage}</span>
  </div>
</div>
{/if}

<style>
  .comments-section {
    border-top: 2px solid #e2e2e2;
    padding-top: 30px;
  }
  
  .comments-section h3 {
    font-size: 1.5rem;
    margin-bottom: 20px;
    color: #333;
  }
  
  .comment-form, .reply-form, .redact-form {
    margin-bottom: 30px;
  }
  
  textarea {
    width: 100%;
    padding: 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    margin-bottom: 10px;
    font-family: inherit;
    font-size: 14px;
    resize: vertical;
  }
  
  .submit-button {
    background-color: #007bff;
    color: #fff;
    border: none;
    padding: 10px 20px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
  }
  
  .submit-button:hover {
    background-color: #0056b3;
  }
  
  .cancel-button {
    background-color: #f0f0f0;
    color: #000;
    border: 1px solid #ddd;
    padding: 10px 20px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    margin-left: 10px;
  }
  
  .form-actions {
    display: flex;
    justify-content: flex-start;
  }
  
  .form-info {
    font-size: 12px;
    color: #666;
    margin-bottom: 10px;
  }
  
  .login-prompt {
    background-color: #f8f9fa;
    padding: 20px;
    border-radius: 4px;
    margin-bottom: 20px;
    text-align: center;
  }
  
  .login-prompt a {
    color: #007bff;
    text-decoration: underline;
    font-weight: bold;
  }
  
  .comments-list {
    margin-top: 20px;
  }
  
  .comment {
    margin-bottom: 25px;
    padding-bottom: 20px;
    border-bottom: 1px solid #e2e2e2;
  }
  
  .comment:last-child {
    border-bottom: none;
  }
  
  .comment-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 10px;
  }
  
  .comment-author {
    font-weight: bold;
    color: #333;
  }
  
  .comment-date {
    color: #666;
    font-size: 0.9rem;
  }
  
  .comment-content {
    margin-bottom: 10px;
    line-height: 1.5;
  }
  
  .comment-actions {
    display: flex;
    gap: 15px;
  }
  
  .action-button {
    background: none;
    border: none;
    color: #666;
    cursor: pointer;
    font-size: 14px;
    padding: 0;
    text-decoration: underline;
  }
  
  .action-button:hover {
    color: #333;
  }
  
  .moderator-action {
    color: #dc3545;
  }
  
  .moderator-action:hover {
    color: #a71e2a;
  }
  
  .replies {
    margin-top: 20px;
    padding-left: 30px;
    border-left: 2px solid #e2e2e2;
  }
  
  .reply {
    padding-bottom: 15px;
    margin-bottom: 15px;
  }
  
  .removed-comment {
    color: #dc3545;
    font-style: italic;
  }
  
  .redacted-note {
    font-size: 0.8rem;
    color: #666;
    font-style: italic;
    display: block;
    margin-top: 5px;
  }
  
  .no-comments {
    color: #666;
    font-style: italic;
    text-align: center;
    padding: 30px;
  }

  /* Vote Button Styles */
.vote-section {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-right: 15px;
}

.vote-button {
  background: #f8f9fa;
  border: 1px solid #ddd;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
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
  font-size: 0.85rem;
}

.action-section {
  display: flex;
  gap: 15px;
  align-items: center;
}

.flag-button {
  color: #856404;
}

.flag-button:hover {
  color: #533f03;
}

.comment-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

@media (max-width: 768px) {
  .comment-actions {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .vote-section {
    width: 100%;
    justify-content: space-between;
  }
}
</style>