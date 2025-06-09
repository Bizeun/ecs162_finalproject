from flask import Flask, redirect, url_for, session, request, jsonify, send_from_directory
from authlib.integrations.flask_client import OAuth
from authlib.common.security import generate_token
from pymongo import MongoClient
import os
import requests
from bson import ObjectId
from datetime import datetime, timezone
from functools import wraps

app = Flask(__name__, static_folder='../frontend/dist', static_url_path='')
app.secret_key = os.urandom(24)

DUMMYJSON_BASE_URL = "https://dummyjson.com"

mongo_uri = os.environ.get('MONGO_URI')
mongo_client = MongoClient(mongo_uri)
db = mongo_client.mydatabase
comments_collection = db.comments
votes_collection = db.votes  
flags_collection = db.flags
hidden_reviews_collection = db.hidden_reviews

oauth = OAuth(app)
nonce = generate_token()

oauth.register(
    name=os.getenv('OIDC_CLIENT_NAME'),
    client_id=os.getenv('OIDC_CLIENT_ID'),
    client_secret=os.getenv('OIDC_CLIENT_SECRET'),
    #server_metadata_url='http://dex:5556/.well-known/openid-configuration',
    authorization_endpoint="http://localhost:5556/auth",
    token_endpoint="http://dex:5556/token",
    jwks_uri="http://dex:5556/keys",
    userinfo_endpoint="http://dex:5556/userinfo",
    device_authorization_endpoint="http://dex:5556/device/code",
    client_kwargs={'scope': 'openid email profile'}
)



def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function

def moderator_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return jsonify({"error": "Authentication required"}), 401
        if session['user'].get('email') != 'moderator@hw3.com' and session['user'].get('email') != 'admin@hw3.com':
            return jsonify({"error": "Moderator privileges required"}), 403
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    user = session.get('user')
    if user:
        return f"<h2>Logged in as {user['email']}</h2><a href='/logout'>Logout</a>"
    return '<a href="/login">Login with Dex</a>'

@app.route('/<path:path>')
def static_files(path):
    """Serve static frontend files"""
    return send_from_directory(app.static_folder, path)

# Authentication routes
@app.route('/api/auth/status')
def auth_status():
    if 'user' in session:
        is_moderator = session['user'].get('email') == 'moderator@hw3.com' or session['user'].get('email') == 'admin@hw3.com'
        return jsonify({
            "authenticated": True,
            "user": {
                "email": session['user'].get('email'),
                "name": session['user'].get('name', session['user'].get('email')),
                "is_moderator": is_moderator
            }
        })
    return jsonify({"authenticated": False})

@app.route('/login')
def login():
    session['nonce'] = nonce
    redirect_uri = 'http://localhost:8000/authorize'
    client_name = os.getenv('OIDC_CLIENT_NAME')
    return oauth.create_client(client_name).authorize_redirect(redirect_uri, nonce=nonce)

@app.route('/api/auth/login')
def api_login():
    """API endpoint for login"""
    session['nonce'] = nonce
    redirect_uri = 'http://localhost:8000/authorize'
    client_name = os.getenv('OIDC_CLIENT_NAME')
    return oauth.create_client(client_name).authorize_redirect(redirect_uri, nonce=nonce)


@app.route('/authorize')
def authorize():
    client_name = os.getenv('OIDC_CLIENT_NAME')
    token = oauth.create_client(client_name).authorize_access_token()
    nonce = session.get('nonce')
    user_info = oauth.create_client(client_name).parse_id_token(token, nonce=nonce)  # or use .get('userinfo').json()
    session['user'] = user_info
    return redirect('http://localhost:5173')

@app.route('/api/auth/logout')
def logout():
    session.clear()
    return jsonify({"success": True})

@app.route('/logout')
def logout_redirect():
    session.clear()
    return redirect('/')


def get_review_votes(review_id):
    upvotes = votes_collection.count_documents({"review_id": review_id, "vote_type": "up"})
    downvotes = votes_collection.count_documents({"review_id": review_id, "vote_type": "down"})
    return {
        "upvotes": upvotes,
        "downvotes": downvotes,
        "score": upvotes - downvotes
    }


@app.route('/api/products')
def get_products():
    limit = request.args.get('limit', 20)
    skip = request.args.get('skip', 0)
    
    url = f"{DUMMYJSON_BASE_URL}/products"
    params = {
        'limit': limit,
        'skip': skip
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()

        hidden_reviews = list(hidden_reviews_collection.find({}, {"review_id": 1}))
        hidden_review_ids = {review["review_id"] for review in hidden_reviews}

        #For reviews
        for product in data.get('products', []):
            filtered_reviews = []
            for i, review in enumerate(product.get('reviews', [])):
                review_id = f"product_{product['id']}_review_{i}"
                if review_id not in hidden_review_ids:
                    review['id'] = review_id
                    review['votes'] = get_review_votes(review_id)
                    filtered_reviews.append(review)
            product['reviews'] = filtered_reviews

            comment_count = comments_collection.count_documents({
                "article_id": f"product_{product['id']}"
            })
            print(f"DEBUG: Product {product['id']} has {comment_count} comments")
            product['community_comments_count'] = comment_count

        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/products/<int:product_id>')
def get_product_by_id(product_id):
    url = f"{DUMMYJSON_BASE_URL}/products/{product_id}"
    
    try:
        response = requests.get(url)
        if response.status_code == 404:
            return jsonify({"error": "Product not found"}), 404
        data = response.json()

        hidden_reviews = list(hidden_reviews_collection.find({}, {"review_id": 1}))
        hidden_review_ids = {review["review_id"] for review in hidden_reviews}

        filtered_reviews = []
        #For reviews
        for i, review in enumerate(data.get('reviews', [])):
            review_id = f"product_{product_id}_review_{i}"
            if review_id not in hidden_review_ids:
                review['id'] = review_id
                review['votes'] = get_review_votes(review_id)
                filtered_reviews.append(review)
        
        data['reviews'] = filtered_reviews

        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/products/search')
def search_products():
    query = request.args.get('q', '')
    
    url = f"{DUMMYJSON_BASE_URL}/products/search"
    params = {'q': query}
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        hidden_reviews = list(hidden_reviews_collection.find({}, {"review_id": 1}))
        hidden_review_ids = {review["review_id"] for review in hidden_reviews}
        
        for product in data.get('products', []):
            filtered_reviews = []
            for i, review in enumerate(product.get('reviews', [])):
                review_id = f"product_{product['id']}_review_{i}"

                if review_id not in hidden_review_ids:
                    review['id'] = review_id
                    review['votes'] = get_review_votes(review_id)
                    filtered_reviews.append(review)
            product['reviews'] = filtered_reviews

            comment_count = comments_collection.count_documents({
                "article_id": f"product_{product['id']}"
            })
            print(f"DEBUG: Product {product['id']} has {comment_count} comments")
            product['community_comments_count'] = comment_count
        
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reviews/<review_id>/vote', methods=['POST'])
@login_required
def vote_review(review_id):
    data = request.json
    vote_type = data.get('vote_type')  # 'up' or 'down'
    
    if vote_type not in ['up', 'down']:
        return jsonify({"error": "Invalid vote type. Must be 'up' or 'down'"}), 400
    
    user_email = session['user'].get('email')
    
    try:
        existing_vote = votes_collection.find_one({
            "review_id": review_id,
            "user_email": user_email
        })
        
        if existing_vote:
            if existing_vote['vote_type'] == vote_type:
                votes_collection.delete_one({"_id": existing_vote['_id']})
                action = "removed"
            else:
                votes_collection.update_one(
                    {"_id": existing_vote['_id']},
                    {
                        "$set": {
                            "vote_type": vote_type,
                            "updated_at": datetime.now(timezone.utc)
                        }
                    }
                )
                action = "updated"
        else:
            votes_collection.insert_one({
                "review_id": review_id,
                "user_email": user_email,
                "vote_type": vote_type,
                "created_at": datetime.now(timezone.utc)
            })
            action = "added"
        votes_info = get_review_votes(review_id)
        
        return jsonify({
            "success": True,
            "action": action,
            "votes": votes_info
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reviews/<review_id>/votes')
def get_review_votes_api(review_id):
    try:
        votes_info = get_review_votes(review_id)
        return jsonify(votes_info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reviews/<review_id>/user-vote')
@login_required
def get_user_vote(review_id):
    try:
        user_email = session['user'].get('email')
        user_vote = votes_collection.find_one({
            "review_id": review_id,
            "user_email": user_email
        })
        
        if user_vote:
            return jsonify({"vote_type": user_vote['vote_type']})
        else:
            return jsonify({"vote_type": None})
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reviews/<review_id>/flag', methods=['POST'])
@login_required
def flag_review(review_id):
    data = request.json
    reason = data.get('reason', '')
    
    if not reason:
        return jsonify({"error": "Reason is required"}), 400
    
    user_email = session['user'].get('email')
    
    try:
        existing_flag = flags_collection.find_one({
            "review_id": review_id,
            "user_email": user_email
        })
        
        if existing_flag:
            return jsonify({"error": "You have already flagged this review"}), 400
        
        flags_collection.insert_one({
            "review_id": review_id,
            "user_email": user_email,
            "reason": reason,
            "created_at": datetime.now(timezone.utc),
            "resolved": False
        })
        
        return jsonify({"success": True, "message": "Review flagged successfully"})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

# Flag comment
@app.route('/api/comments/<comment_id>/flag', methods=['POST'])
@login_required
def flag_comment(comment_id):
    """Flag a comment"""
    data = request.json
    reason = data.get('reason', '')
    
    if not reason:
        return jsonify({"error": "Reason is required"}), 400
    
    user_email = session['user'].get('email')
    
    try:
        # Check if already flagged
        existing_flag = flags_collection.find_one({
            "content_id": comment_id,
            "content_type": "comment",
            "user_email": user_email
        })
        
        if existing_flag:
            return jsonify({"error": "You have already flagged this comment"}), 400
        
        # Add new flag
        flags_collection.insert_one({
            "content_id": comment_id,
            "content_type": "comment", # Distinguish from reviews
            "user_email": user_email,
            "reason": reason,
            "created_at": datetime.now(timezone.utc),
            "resolved": False
        })
        
        return jsonify({"success": True, "message": "Comment flagged successfully"})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#For moderator
@app.route('/api/moderation/flags')
@moderator_required
def get_flags():
    try:
        flags = list(flags_collection.find({"resolved": False}).sort("created_at", -1))
        
        for flag in flags:
            flag['_id'] = str(flag['_id'])
            content_id = flag.get('content_id')
            content_type = flag.get('content_type', 'review')

            # Get content preview
            if content_type == 'comment':
                comment = comments_collection.find_one({"_id": ObjectId(content_id)})
                if comment:
                    flag['content_preview'] = comment.get('content', '')[:100] + '...' if len(comment.get('content', '')) > 100 else comment.get('content', '')
                    flag['content_author'] = comment.get('user_name', 'Unknown')
                else:
                    flag['content_preview'] = 'Content not found'
                    flag['content_author'] = 'Unknown'
            else:
                # For reviews, content preview would need to be fetched differently
                flag['content_preview'] = 'Review content'
                flag['content_author'] = 'Review author'
        
        return jsonify(flags)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/moderation/flags/<flag_id>/resolve', methods=['PATCH'])
@moderator_required
def resolve_flag(flag_id):
    data = request.json or {}
    action = data.get('action', 'resolve_only')
    redacted_content = data.get('redacted_content', '')
    print(f"DEBUG: Received action: {action}")  
    
    try:
        # Get flag information
        flag = flags_collection.find_one({"_id": ObjectId(flag_id)})
        if not flag:
            return jsonify({"error": "Flag not found"}), 404
        
        content_id = flag.get('content_id')
        content_type = flag.get('content_type', 'review')  # 'review' or 'comment'
        
        print(f"DEBUG: content_id={content_id}, content_type={content_type}")

        # Perform action based on selection
        if action == 'remove_content':
            print("DEBUG: Entering remove_content branch")
            if content_type == 'comment':
                print("DEBUG: Removing comment")
                # Remove comment
                comments_collection.update_one(
                    {"_id": ObjectId(content_id)},
                    {"$set": {"is_removed": True}}
                )
            else:
                print(f"DEBUG: Hiding review {content_id}")
                result = hidden_reviews_collection.insert_one({
                    "review_id": content_id,
                    "hidden_by": session['user'].get('email'),
                    "hidden_at": datetime.now(timezone.utc),
                    "reason": "moderation_action"
                })
                print(f"DEBUG: Insert result: {result.inserted_id}")
                
        elif action == 'redact_content':
            if not redacted_content:
                return jsonify({"error": "Redacted content is required for redact action"}), 400
                
            if content_type == 'comment':
                # Redact comment
                comments_collection.update_one(
                    {"_id": ObjectId(content_id)},
                    {"$set": {"redacted_content": redacted_content}}
                )
            else:
                # For reviews, we could store redacted version in our database
                pass
        
        # Mark flag as resolved with action taken
        flags_collection.update_one(
            {"_id": ObjectId(flag_id)},
            {
                "$set": {
                    "resolved": True,
                    "resolved_at": datetime.now(timezone.utc),
                    "resolved_by": session['user'].get('email'),
                    "action_taken": action,
                    "redacted_content": redacted_content if action == 'redact_content' else None
                }
            }
        )
        return jsonify({
            "success": True,
            "action_taken": action,
            "message": f"Flag resolved with action: {action.replace('_', ' ')}"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/moderation/content/<content_type>/<content_id>')
@moderator_required
def get_content_for_moderation(content_type, content_id):
    """Get content details for moderation actions"""
    try:
        if content_type == 'comment':
            content = comments_collection.find_one({"_id": ObjectId(content_id)})
            if content:
                content['_id'] = str(content['_id'])
                return jsonify(content)
        elif content_type == 'review':
            # For reviews, we'd need to fetch from our stored data or DummyJSON
            return jsonify({"error": "Review content retrieval not implemented"}), 501
        
        return jsonify({"error": "Content not found"}), 404
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Comment/Review system
@app.route('/api/comments', methods=['GET'])
def get_comments():
    """Get comments for a specific product"""
    article_id = request.args.get('article_id')
    
    if not article_id:
        return jsonify({"error": "Article ID is required"}), 400
        
    try:
        comments = list(comments_collection.find({"article_id": article_id}).sort("created_at", -1))
        
        for comment in comments:
            comment['_id'] = str(comment['_id'])
        return jsonify(comments)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/comments', methods=['POST'])
@login_required
def add_comment():
    """Add a new comment (requires authentication)"""
    data = request.json
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
        
    article_id = data.get('article_id')
    content = data.get('content')
    parent_id = data.get('parent_id')
    
    if not article_id or not content:
        return jsonify({"error": "Article ID and content are required"}), 400
        
    try:
        comment = {
            "article_id": article_id,
            "content": content,
            "user_email": session['user'].get('email'),
            "user_name": session['user'].get('name', session['user'].get('email')),
            "created_at": datetime.now(timezone.utc),
            "is_removed": False,
            "redacted_content": None
        }
        
        if parent_id:
            comment["parent_id"] = parent_id
            
        result = comments_collection.insert_one(comment)
        comment["_id"] = str(result.inserted_id)
        
        return jsonify(comment), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/comments/<comment_id>', methods=['DELETE'])
@moderator_required
def remove_comment(comment_id):
    """Remove a comment (moderator only)"""
    try:
        comment = comments_collection.find_one({"_id": ObjectId(comment_id)})
        
        if not comment:
            return jsonify({"error": "Comment not found"}), 404
            
        comments_collection.update_one(
            {"_id": ObjectId(comment_id)},
            {"$set": {"is_removed": True}}
        )
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/comments/<comment_id>/redact', methods=['PATCH'])
@moderator_required
def redact_comment(comment_id):
    """Redact a comment (moderator only)"""
    data = request.json
    redacted_content = data.get('redacted_content')
    
    if not redacted_content:
        return jsonify({"error": "Redacted content is required"}), 400
        
    try:
        comment = comments_collection.find_one({"_id": ObjectId(comment_id)})
        
        if not comment:
            return jsonify({"error": "Comment not found"}), 404
            
        comments_collection.update_one(
            {"_id": ObjectId(comment_id)},
            {"$set": {"redacted_content": redacted_content}}
        )
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Comment voting APIs
@app.route('/api/comments/<comment_id>/vote', methods=['POST'])
@login_required
def vote_comment(comment_id):
    """Vote on a comment"""
    data = request.json
    vote_type = data.get('vote_type')  # 'up' or 'down'
    
    if vote_type not in ['up', 'down']:
        return jsonify({"error": "Invalid vote type. Must be 'up' or 'down'"}), 400
    
    user_email = session['user'].get('email')
    
    try:
        # Check existing vote
        existing_vote = votes_collection.find_one({
            "content_id": comment_id,
            "content_type": "comment",
            "user_email": user_email
        })
        
        if existing_vote:
            if existing_vote['vote_type'] == vote_type:
                # Remove vote
                votes_collection.delete_one({"_id": existing_vote['_id']})
                action = "removed"
            else:
                # Update vote
                votes_collection.update_one(
                    {"_id": existing_vote['_id']},
                    {
                        "$set": {
                            "vote_type": vote_type,
                            "updated_at": datetime.now(timezone.utc)
                        }
                    }
                )
                action = "updated"
        else:
            # New vote
            votes_collection.insert_one({
                "content_id": comment_id,
                "content_type": "comment",
                "user_email": user_email,
                "vote_type": vote_type,
                "created_at": datetime.now(timezone.utc)
            })
            action = "added"
        
        # Get updated vote counts
        upvotes = votes_collection.count_documents({
            "content_id": comment_id, 
            "content_type": "comment",
            "vote_type": "up"
        })
        downvotes = votes_collection.count_documents({
            "content_id": comment_id,
            "content_type": "comment", 
            "vote_type": "down"
        })
        
        return jsonify({
            "success": True,
            "action": action,
            "votes": {
                "upvotes": upvotes,
                "downvotes": downvotes,
                "score": upvotes - downvotes
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/comments/<comment_id>/votes')
def get_comment_votes(comment_id):
    """Get comment vote counts"""
    try:
        upvotes = votes_collection.count_documents({
            "content_id": comment_id,
            "content_type": "comment",
            "vote_type": "up"
        })
        downvotes = votes_collection.count_documents({
            "content_id": comment_id,
            "content_type": "comment",
            "vote_type": "down"
        })
        
        return jsonify({
            "upvotes": upvotes,
            "downvotes": downvotes,
            "score": upvotes - downvotes
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/comments/<comment_id>/user-vote')
@login_required
def get_user_comment_vote(comment_id):
    """Get user's vote on comment"""
    try:
        user_email = session['user'].get('email')
        user_vote = votes_collection.find_one({
            "content_id": comment_id,
            "content_type": "comment",
            "user_email": user_email
        })
        
        if user_vote:
            return jsonify({"vote_type": user_vote['vote_type']})
        else:
            return jsonify({"vote_type": None})
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
