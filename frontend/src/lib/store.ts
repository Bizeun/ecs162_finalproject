import { writable } from 'svelte/store';

interface User {
  email: string;
  name?: string;
  is_moderator: boolean;
}

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  isModerator: boolean;
}

interface VoteInfo {
  upvotes: number;
  downvotes: number;
  score: number;
}

export const authStore = writable<AuthState>({
    isAuthenticated: false,
    user: null,
    isModerator: false
});

// Changed from articles to products
export const productsStore = writable<any[]>([]);
export const currentProductStore = writable<any>(null);
export const commentsStore = writable<any[]>([]);
export const userVotesStore = writable<Record<string, string | null>>({});
export const flaggedReviewsStore = writable<Record<string, boolean>>({});

export const checkAuthStatus = async (): Promise<void> => {
    try {
        const response = await fetch('/api/auth/status');
        const data = await response.json();
        
        if (data.authenticated) {
            authStore.set({
                isAuthenticated: true,
                user: data.user,
                isModerator: data.user.is_moderator
            });
        } else {
            authStore.set({
                isAuthenticated: false,
                user: null,
                isModerator: false
            });
        }
    } catch (error) {
        console.error('Error checking auth status:', error);
    }
};

// Fetch products from DummyJSON API
export const fetchProducts = async (): Promise<void> => {
    try {
        const response = await fetch('/api/products?limit=30');
        const data = await response.json();
        
        if (data.products && data.products.length > 0) {
            productsStore.set(data.products);
        }
    } catch (error) {
        console.error('Error fetching products:', error);
        // Set empty array on error to prevent loading state
        productsStore.set([]);
    }
};

// Search products by query
export const searchProducts = async (query: string): Promise<void> => {
    try {
        const response = await fetch(`/api/products/search?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        
        if (data.products) {
            productsStore.set(data.products);
        } else {
            productsStore.set([]);
        }
    } catch (error) {
        console.error('Error searching products:', error);
        productsStore.set([]);
    }
};

export const fetchProductById = async (productId: string): Promise<any> => {
    try {
        const response = await fetch(`/api/products/${productId}`);
        if (!response.ok) {
            throw new Error(`Product not found: ${productId}`);
        }
        const product = await response.json();
        currentProductStore.set(product);
        return product;
    } catch (error) {
        console.error('Error fetching product:', error);
        return null;
    }
};

// Fetch comments for a product (reusing existing comment system)
// Using product ID with 'product_' prefix to differentiate from article comments
export const fetchComments = async (productId: string): Promise<void> => {
    try {
        const response = await fetch(`/api/comments?article_id=product_${productId}`);
        const data = await response.json();
        commentsStore.set(data);
    } catch (error) {
        console.error('Error fetching comments:', error);
        commentsStore.set([]);
    }
};

// Add comment/review to a product
export const addComment = async (productId: string, content: string, parentId: string | null = null): Promise<boolean> => {
    try {
        const response = await fetch('/api/comments', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                article_id: `product_${productId}`,
                content,
                parent_id: parentId
            })
        });
        
        if (response.ok) {
            await fetchComments(productId);
            return true;
        }
        return false;
    } catch (error) {
        console.error('Error adding comment:', error);
        return false;
    }
};

// Remove comment (moderator only)
export const removeComment = async (commentId: string, productId: string): Promise<boolean> => {
    try {
        const response = await fetch(`/api/comments/${commentId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            await fetchComments(productId);
            return true;
        }
        return false;
    } catch (error) {
        console.error('Error removing comment:', error);
        return false;
    }
};

// Redact comment (moderator only)
export const redactComment = async (commentId: string, redactedContent: string, productId: string): Promise<boolean> => {
    try {
        const response = await fetch(`/api/comments/${commentId}/redact`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                redacted_content: redactedContent
            })
        });
        
        if (response.ok) {
            await fetchComments(productId);
            return true;
        }
        return false;
    } catch (error) {
        console.error('Error redacting comment:', error);
        return false;
    }
};

// Flag comment
export const flagComment = async (commentId: string, reason: string): Promise<boolean> => {
    try {
        const response = await fetch(`/api/comments/${commentId}/flag`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                reason: reason
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            return true;
        } else {
            console.error('Flag failed:', data.error);
            return false;
        }
    } catch (error) {
        console.error('Error flagging comment:', error);
        return false;
    }
};

export const voteOnReview = async (reviewId: string, voteType: 'up' | 'down'): Promise<{ success: boolean; votes?: VoteInfo; action?: string }> => {
    try {
        const response = await fetch(`/api/reviews/${reviewId}/vote`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                vote_type: voteType
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            // Update user vote state
            userVotesStore.update(votes => {
                const newVotes = { ...votes };
                if (data.action === 'removed') {
                    newVotes[reviewId] = null;
                } else {
                    newVotes[reviewId] = voteType;
                }
                return newVotes;
            });
            
            return {
                success: true,
                votes: data.votes,
                action: data.action
            };
        } else {
            console.error('Vote failed:', data.error);
            return { success: false };
        }
    } catch (error) {
        console.error('Error voting on review:', error);
        return { success: false };
    }
};

// Comment voting functions (add to store.js)
export const voteOnComment = async (commentId: string, voteType: 'up' | 'down'): Promise<{ success: boolean; votes?: any; action?: string }> => {
    try {
        const response = await fetch(`/api/comments/${commentId}/vote`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                vote_type: voteType
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            return {
                success: true,
                votes: data.votes,
                action: data.action
            };
        } else {
            console.error('Vote failed:', data.error);
            return { success: false };
        }
    } catch (error) {
        console.error('Error voting on comment:', error);
        return { success: false };
    }
};

export const getCommentVotes = async (commentId: string): Promise<any | null> => {
    try {
        const response = await fetch(`/api/comments/${commentId}/votes`);
        
        if (response.ok) {
            const data = await response.json();
            return data;
        }
    } catch (error) {
        console.error('Error getting comment votes:', error);
    }
    return null;
};

export const getUserCommentVote = async (commentId: string): Promise<string | null> => {
    try {
        const response = await fetch(`/api/comments/${commentId}/user-vote`);
        
        if (response.ok) {
            const data = await response.json();
            return data.vote_type;
        } else if (response.status === 401) {
            return null; // Not authenticated
        }
    } catch (error) {
        console.error('Error getting user comment vote:', error);
    }
    return null;
};

// Get user's vote status
export const getUserVote = async (reviewId: string): Promise<string | null> => {
    try {
        const response = await fetch(`/api/reviews/${reviewId}/user-vote`);
        
        if (response.ok) {
            const data = await response.json();
            
            // Update user vote state store
            userVotesStore.update(votes => ({
                ...votes,
                [reviewId]: data.vote_type
            }));
            
            return data.vote_type;
        } else if (response.status === 401) {
            // Unauthenticated user
            return null;
        }
    } catch (error) {
        console.error('Error getting user vote:', error);
    }
    return null;
};

// Get review voting info
export const getReviewVotes = async (reviewId: string): Promise<VoteInfo | null> => {
    try {
        const response = await fetch(`/api/reviews/${reviewId}/votes`);
        
        if (response.ok) {
            const data = await response.json();
            return data;
        }
    } catch (error) {
        console.error('Error getting review votes:', error);
    }
    return null;
};

// Flag review
export const flagReview = async (reviewId: string, reason: string): Promise<boolean> => {
    try {
        const response = await fetch(`/api/reviews/${reviewId}/flag`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                reason: reason
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            // Update flagged review state
            flaggedReviewsStore.update(flagged => ({
                ...flagged,
                [reviewId]: true
            }));
            return true;
        } else {
            console.error('Flag failed:', data.error);
            return false;
        }
    } catch (error) {
        console.error('Error flagging review:', error);
        return false;
    }
};

// Load all user vote states for product (used in product detail page)
export const loadUserVotesForProduct = async (product: any): Promise<void> => {
    try {
        if (!product || !product.reviews) return;
        
        const votePromises = product.reviews.map(async (review: any) => {
            if (review.id) {
                const voteType = await getUserVote(review.id);
                return { reviewId: review.id, voteType };
            }
            return null;
        });
        
        const results = await Promise.all(votePromises);
        
        userVotesStore.update(votes => {
            const newVotes = { ...votes };
            results.forEach(result => {
                if (result) {
                    newVotes[result.reviewId] = result.voteType;
                }
            });
            return newVotes;
        });
    } catch (error) {
        console.error('Error loading user votes for product:', error);
    }
};

// Moderator only: Get flagged reviews list
export const getFlags = async (): Promise<any[]> => {
    try {
        const response = await fetch('/api/moderation/flags');
        
        if (response.ok) {
            const data = await response.json();
            return data;
        } else {
            console.error('Failed to fetch flags');
            return [];
        }
    } catch (error) {
        console.error('Error fetching flags:', error);
        return [];
    }
};

// Moderator only: Resolve flag
export const resolveFlag = async (flagId: string): Promise<boolean> => {
    try {
        const response = await fetch(`/api/moderation/flags/${flagId}/resolve`, {
            method: 'PATCH'
        });
        
        const data = await response.json();
        return response.ok && data.success;
    } catch (error) {
        console.error('Error resolving flag:', error);
        return false;
    }
};

// Advanced moderation functions 
export const resolveWithAction = async (flagId: string, action: string, redactedContent?: string): Promise<{ success: boolean; message?: string }> => {
    try {
        const body: any = { action };
        if (action === 'redact_content' && redactedContent) {
            body.redacted_content = redactedContent;
        }

        const response = await fetch(`/api/moderation/flags/${flagId}/resolve`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(body)
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            return {
                success: true,
                message: data.message
            };
        } else {
            console.error('Resolve failed:', data.error);
            return { 
                success: false, 
                message: data.error 
            };
        }
    } catch (error) {
        console.error('Error resolving flag:', error);
        return { 
            success: false, 
            message: 'Network error occurred' 
        };
    }
};

export const getContentForModeration = async (contentType: string, contentId: string): Promise<any | null> => {
    try {
        const response = await fetch(`/api/moderation/content/${contentType}/${contentId}`);
        
        if (response.ok) {
            const data = await response.json();
            return data;
        } else {
            console.error('Failed to fetch content for moderation');
            return null;
        }
    } catch (error) {
        console.error('Error fetching content for moderation:', error);
        return null;
    }
};