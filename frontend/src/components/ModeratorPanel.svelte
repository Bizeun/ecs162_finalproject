<script lang="ts">
import { onMount } from 'svelte';
import { authStore, getFlags, resolveWithAction, getContentForModeration } from '../lib/store';

let flags: any[] = [];
let isLoading = true;
let isModerator = false;

let showSuccessToast = false;
let showErrorToast = false;
let toastMessage = '';

let showResolveModal = false;
let currentFlag: any = null;
let selectedAction = 'resolve_only';
let redactContent = '';
let originalContent = '';

authStore.subscribe(auth => {
    isModerator = auth.isModerator;
});

onMount(async () => {
    if (isModerator) {
        await loadFlags();
    }
    isLoading = false;
});

async function loadFlags() {
    isLoading = true;
    flags = await getFlags();
    isLoading = false;
}

async function showActionModal(flag: any) {
    currentFlag = flag;
    selectedAction = 'resolve_only';
    redactContent = '';
    originalContent = '';
    
    // If content type is comment, fetch original content for redaction
    if (flag.content_type === 'comment') {
        const content = await getContentForModeration('comment', flag.content_id);
        if (content) {
            originalContent = content.content || '';
            redactContent = originalContent;
        }
    }
    
    showResolveModal = true;
}

function closeResolveModal() {
    showResolveModal = false;
    currentFlag = null;
    selectedAction = 'resolve_only';
    redactContent = '';
    originalContent = '';
}

async function handleResolveWithAction() {
    if (!currentFlag) return;
    
    if (selectedAction === 'redact_content' && !redactContent.trim()) {
        showToast('Please provide redacted content', 'error');
        return;
    }
    
    const result = await resolveWithAction(
        currentFlag._id, 
        selectedAction, 
        selectedAction === 'redact_content' ? redactContent : undefined
    );
    
    if (result.success) {
        showToast(result.message || 'Flag resolved successfully', 'success');
        await loadFlags(); // Refresh the list
        closeResolveModal();
    } else {
        showToast(result.message || 'Failed to resolve flag', 'error');
    }
}

function showToast(message: string, type: 'success' | 'error') {
    toastMessage = message;
    if (type === 'success') {
        showSuccessToast = true;
        setTimeout(() => showSuccessToast = false, 3000);
    } else {
        showErrorToast = true;
        setTimeout(() => showErrorToast = false, 3000);
    }
}   

function formatDate(dateString: string) {
    return new Date(dateString).toLocaleString();
}


</script>


{#if !isModerator}
<div class="access-denied">
    <h2>Access Denied</h2>
    <p>You must be a moderator to access this panel.</p>
</div>
{:else}
<div class="moderation-panel">
    <h2>Moderation Panel</h2>
    <p>Manage flagged reviews and maintain community standards.</p>
    
    <div class="panel-actions">
        <button class="refresh-button" on:click={loadFlags} disabled={isLoading}>
            {isLoading ? 'Loading...' : 'Refresh'}
        </button>
    </div>
    
    {#if isLoading}
    <div class="loading">Loading flagged reviews...</div>
    {:else if flags.length === 0}
    <div class="no-flags">
        <h3>🎉 All Clear!</h3>
        <p>No flagged reviews to review at this time.</p>
    </div>
    {:else}
    <div class="flags-list">
        <h3>Flagged Reviews ({flags.length})</h3>
        
        {#each flags as flag}
        <div class="flag-item">
            <div class="flag-header">
                <div class="flag-info">
                    <span class="review-id">Review ID: {flag.review_id}</span>
                    <span class="flag-date">Flagged: {formatDate(flag.created_at)}</span>
                </div>
                <div class="flag-actions">
                    <button 
                        class="resolve-button"
                        on:click={() => showActionModal(flag)}
                    >
                        Resolve
                    </button>
                </div>
            </div>
            
            <div class="flag-details">
                <div class="flag-reason">
                    <strong>Reason:</strong> {flag.reason}
                </div>
                <div class="flag-reporter">
                    <strong>Reported by:</strong> {flag.user_email}
                </div>
            </div>
        </div>
        {/each}
    </div>
    {/if}
</div>


<!-- Resolve Action Modal -->
{#if showResolveModal && currentFlag}
<div 
    class="modal-overlay" 
    role="dialog" 
    aria-modal="true" 
    aria-labelledby="resolve-modal-title"
    tabindex="-1"
    on:click={closeResolveModal}
    on:keydown={(e) => e.key === 'Escape' && closeResolveModal()}
>
    <div class="modal-content" on:click|stopPropagation>
        <h4 id="resolve-modal-title">Resolve Flag with Action</h4>
        
        <div class="flag-details">
            <p><strong>Flagged Content:</strong> {currentFlag.content_preview}</p>
            <p><strong>Reason:</strong> {currentFlag.reason}</p>
            <p><strong>Reporter:</strong> {currentFlag.user_email}</p>
        </div>
        
        <div class="action-selection">
            <label>
                <input 
                    type="radio" 
                    bind:group={selectedAction} 
                    value="resolve_only"
                />
                Resolve Only (No content action)
            </label>
            
            <label>
                <input 
                    type="radio" 
                    bind:group={selectedAction} 
                    value="remove_content"
                />
                Remove Content and Resolve
            </label>
            
            <label>
                <input 
                    type="radio" 
                    bind:group={selectedAction} 
                    value="redact_content"
                />
                Redact Content and Resolve
            </label>
        </div>
        
        {#if selectedAction === 'redact_content'}
        <div class="redact-section">
            <label for="redact-textarea">Edit content (use █ for redactions):</label>
            <textarea 
                id="redact-textarea"
                bind:value={redactContent}
                placeholder="Edit the content..."
                rows="4"
                class="redact-textarea"
            ></textarea>
            <p class="redact-info">Original: "{originalContent}"</p>
        </div>
        {/if}
        
        <div class="modal-actions">
            <button class="cancel-button" on:click={closeResolveModal}>Cancel</button>
            <button class="submit-button" on:click={handleResolveWithAction}>
                {selectedAction === 'resolve_only' ? 'Resolve' : 
                 selectedAction === 'remove_content' ? 'Remove & Resolve' : 
                 'Redact & Resolve'}
            </button>
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
{/if}

<style>
.moderation-panel {
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
    font-family: Georgia, serif;
}

.access-denied {
    text-align: center;
    padding: 40px;
    color: #dc3545;
}

.access-denied h2 {
    margin-bottom: 10px;
}

.moderation-panel h2 {
    color: #333;
    margin-bottom: 10px;
}

.moderation-panel > p {
    color: #666;
    margin-bottom: 20px;
}

.panel-actions {
    margin-bottom: 20px;
    padding-bottom: 20px;
    border-bottom: 1px solid #e2e2e2;
}

.refresh-button {
    background: #007bff;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.9rem;
}

.refresh-button:hover:not(:disabled) {
    background: #0056b3;
}

.refresh-button:disabled {
    background: #6c757d;
    cursor: not-allowed;
}

.loading {
    text-align: center;
    padding: 40px;
    color: #666;
    font-style: italic;
}

.no-flags {
    text-align: center;
    padding: 40px;
    background: #f8f9fa;
    border-radius: 8px;
    border: 1px solid #e9ecef;
}

.no-flags h3 {
    color: #28a745;
    margin-bottom: 10px;
}

.no-flags p {
    color: #666;
    margin: 0;
}

.flags-list h3 {
    color: #333;
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 2px solid #e2e2e2;
}

.flag-item {
    background: #fff;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 15px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.flag-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 15px;
}

.flag-info {
    display: flex;
    flex-direction: column;
    gap: 5px;
}

.review-id {
    font-weight: bold;
    color: #333;
    font-family: monospace;
    background: #f8f9fa;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 0.9rem;
}

.flag-date {
    color: #666;
    font-size: 0.85rem;
}

.flag-actions {
    display: flex;
    gap: 10px;
}

.resolve-button {
    background: #28a745;
    color: white;
    border: none;
    padding: 6px 12px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.85rem;
    font-weight: 500;
}

.resolve-button:hover {
    background: #218838;
}

.flag-details {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.flag-reason, .flag-reporter {
    font-size: 0.9rem;
    color: #555;
}

.flag-reason strong, .flag-reporter strong {
    color: #333;
}

@media (max-width: 768px) {
    .moderation-panel {
        padding: 15px;
    }

    .flag-header {
        flex-direction: column;
        gap: 10px;
    }

    .flag-actions {
        align-self: stretch;
    }

    .resolve-button {
        width: 100%;
    }
}
</style>