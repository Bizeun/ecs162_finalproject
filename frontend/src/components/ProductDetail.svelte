<script lang="ts">
  import { onMount } from 'svelte';
  import { currentProductStore, commentsStore, authStore, fetchComments, addComment, removeComment, redactComment } from '../lib/store';
  
  let commentContent = '';
  let replyContent = '';
  let replyingToId: string | null = null;
  let redactingCommentId: string | null = null;
  let redactedContent = '';
  
  let article: any = null;
  
  currentProductStore.subscribe(value => {
    article = value;
    if (article) {
      const articleId = article._id || article.uri || article.web_url;
      fetchComments(articleId);
    }
  });
  
  function goBack() {
    currentProductStore.set(null);
  }
  
  async function handleCommentSubmit(event: Event) {
    event.preventDefault();
    
    if (!commentContent.trim() || !article) return;
    
    const articleId = article._id || article.uri || article.web_url;
    const success = await addComment(articleId, commentContent);
    
    if (success) {
      commentContent = '';
    }
  }
  
  async function handleReplySubmit(event: Event, parentId: string) {
    event.preventDefault();
    
    if (!replyContent.trim() || !article) return;
    
    const articleId = article._id || article.uri || article.web_url;
    const success = await addComment(articleId, replyContent, parentId);
    
    if (success) {
      replyContent = '';
      replyingToId = null;
    }
  }
  
  async function handleRemoveComment(commentId: string) {
    if (!article) return;
    
    const articleId = article._id || article.uri || article.web_url;
    await removeComment(commentId, articleId);
  }
  
  async function handleRedactComment(event: Event) {
    event.preventDefault();
    
    if (!redactingCommentId || !redactedContent.trim() || !article) return;
    
    const articleId = article._id || article.uri || article.web_url;
    const success = await redactComment(redactingCommentId, redactedContent, articleId);
    
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
</script>

<div class="article-detail">
  <button class="back-button" on:click={goBack}>&larr; Back to News</button>
  
  {#if article}
    <article>
      <h2>{article.headline?.main || article.title}</h2>
      <p class="byline">{article.byline?.original || article.byline || 'Staff Reporter'}</p>
      
      {#if article.multimedia && article.multimedia.default && article.multimedia.default.url}
        <img 
          src={article.multimedia.default.url} 
          alt={article.headline?.main || article.title} 
          class="article-image"
        />
      {:else if article.multimedia && article.multimedia.thumbnail && article.multimedia.thumbnail.url}
        <img 
          src={article.multimedia.thumbnail.url} 
          alt={article.headline?.main || article.title} 
          class="article-image"
        />
      {/if}
      
      <div class="article-content">
        <p>{article.abstract || article.snippet || article.lead_paragraph}</p>
        <p>
          <a href={article.web_url || article.url} target="_blank" class="read-more-link">
            Read full article at The New York Times
          </a>
        </p>
      </div>
    </article>
    
    <div class="comments-section">
      <h3>Comments</h3>
      
      {#if $authStore.isAuthenticated}
        <form class="comment-form" on:submit={handleCommentSubmit}>
          <textarea 
            bind:value={commentContent} 
            placeholder="Write a comment..." 
            rows="3"
          ></textarea>
          <button type="submit" class="submit-button">Post Comment</button>
        </form>
      {:else}
        <div class="login-prompt">
          <p>Please <a href="/api/auth/login">login</a> to post comments.</p>
        </div>
      {/if}
      
      <div class="comments-list">
        {#if $commentsStore.length === 0}
          <p class="no-comments">No comments yet. Be the first to share your thoughts!</p>
        {:else}
          {#each getNestedComments($commentsStore) as comment (comment._id)}
            <div class="comment">
              <div class="comment-header">
                <span class="comment-author">{comment.user_name}</span>
                <span class="comment-date">{new Date(comment.created_at).toLocaleString()}</span>
              </div>
              
              <div class="comment-content">
                {#if comment.is_removed}
                  <p class="removed-comment">COMMENT REMOVED BY MODERATOR!</p>
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
                {#if $authStore.isAuthenticated && !comment.is_removed}
                  <button class="action-button" on:click={() => setReplyMode(comment._id)}>
                    Reply
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
                          <p class="removed-comment">COMMENT REMOVED BY MODERATOR!</p>
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
                        {#if $authStore.isModerator && !reply.is_removed}
                          <button class="action-button moderator-action" on:click={() => handleRemoveComment(reply._id)}>
                            Remove
                          </button>
                          <button class="action-button moderator-action" on:click={() => setRedactMode(reply._id, reply.content)}>
                            Redact
                          </button>
                        {/if}
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
  {:else}
    <div class="loading">Loading article...</div>
  {/if}
</div>

<style>
  .article-detail {
    max-width: 800px;
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
    margin-bottom: 20px;
    display: inline-block;
  }
  
  .back-button:hover {
    text-decoration: underline;
  }
  
  article h2 {
    font-size: 2rem;
    margin-bottom: 10px;
    line-height: 1.2;
  }
  
  .byline {
    font-style: italic;
    font-size: 0.9rem;
    margin-bottom: 20px;
    color: #666;
  }
  
  .article-image {
    width: 100%;
    max-height: 500px;
    object-fit: cover;
    margin-bottom: 20px;
  }
  
  .article-content {
    font-size: 1.1rem;
    line-height: 1.6;
    margin-bottom: 30px;
  }
  
  .read-more-link {
    color: #000;
    text-decoration: underline;
    font-weight: bold;
  }
  
  .comments-section {
    margin-top: 40px;
    border-top: 1px solid #e2e2e2;
    padding-top: 20px;
  }
  
  .comments-section h3 {
    font-size: 1.5rem;
    margin-bottom: 20px;
  }
  
  .comment-form, .reply-form, .redact-form {
    margin-bottom: 30px;
  }
  
  textarea {
    width: 100%;
    padding: 10px;
    border: 1px solid #ccc;
    margin-bottom: 10px;
    font-family: inherit;
    font-size: 16px;
    resize: vertical;
  }
  
  .submit-button {
    background-color: #000;
    color: #fff;
    border: none;
    padding: 8px 16px;
    cursor: pointer;
    font-size: 14px;
  }
  
  .cancel-button {
    background-color: #f0f0f0;
    color: #000;
    border: 1px solid #ccc;
    padding: 8px 16px;
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
    background-color: #f8f8f8;
    padding: 15px;
    border-radius: 4px;
    margin-bottom: 20px;
    text-align: center;
  }
  
  .login-prompt a {
    color: #000;
    text-decoration: underline;
    font-weight: bold;
  }
  
  .comments-list {
    margin-top: 20px;
  }
  
  .comment {
    margin-bottom: 20px;
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
  }
  
  .comment-date {
    color: #666;
    font-size: 0.9rem;
  }
  
  .comment-content {
    margin-bottom: 10px;
    line-height: 1.4;
  }
  
  .comment-actions {
    display: flex;
    gap: 10px;
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
  
  .moderator-action {
    color: #d32f2f;
  }
  
  .replies {
    margin-top: 15px;
    padding-left: 20px;
    border-left: 2px solid #e2e2e2;
  }
  
  .reply {
    padding-bottom: 15px;
    margin-bottom: 15px;
  }
  
  .removed-comment {
    color: #d32f2f;
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
    padding: 20px;
  }
  
  .loading {
    text-align: center;
    padding: 50px;
    color: #666;
    font-style: italic;
  }
  
  @media (max-width: 767px) {
    .article-detail {
      padding: 15px;
    }
    
    article h2 {
      font-size: 1.5rem;
    }
    
    .article-content {
      font-size: 1rem;
    }
  }
</style>