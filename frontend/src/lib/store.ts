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

export const authStore = writable<AuthState>({
    isAuthenticated: false,
    user: null,
    isModerator: false
});

// Changed from articles to products
export const productsStore = writable<any[]>([]);
export const currentProductStore = writable<any>(null);
export const commentsStore = writable<any[]>([]);

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

// TODO: Week 2 - Add voting functions for community validation
/*
export const voteOnComment = async (commentId: string, voteType: 'helpful' | 'not_helpful'): Promise<boolean> => {
    // Will be implemented in Week 2
    return false;
};

export const flagComment = async (commentId: string, reason: string): Promise<boolean> => {
    // Will be implemented in Week 2  
    return false;
};
*/