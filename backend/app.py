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
    token = oauth.flask_app.authorize_access_token()
    nonce = session.get('nonce')

    client_name = os.getenv('OIDC_CLIENT_NAME')
    user_info = oauth.create_client(client_name).parse_id_token(token, nonce=nonce)  # or use .get('userinfo').json()
    session['user'] = user_info
    return redirect('http://localhost:5173')

@app.route('/api/auth/logout')
def logout():
    session.clear()
    return jsonify({"success": True})

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


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
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Comment/Review system (can be adapted for product reviews later)
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
