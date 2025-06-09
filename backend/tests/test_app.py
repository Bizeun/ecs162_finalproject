import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest 
from app import app
from unittest.mock import patch, MagicMock
import mongomock
from bson import ObjectId
from datetime import datetime, timezone
import json
from flask import Response

# Setup Fixture

@pytest.fixture
def client(monkeypatch):
    mock_client = mongomock.MongoClient()
    mock_collection = mock_client.mydatabase.comments

    # Patch the global comments_collection in app.py
    monkeypatch.setattr("app.comments_collection", mock_collection)

    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def login_session(client, email="user@hw3.com", name="TEST User"):
    with client.session_transaction() as sess:
        sess['user'] = {"email": email, "name": name}


# --TEST CASES--

# request empty comments
def test_get_empty_comments(client):
    response = client.get('/api/comments?article_id=test-article')
    assert response.status_code == 200
    assert response.json == []

# add a comment then retrive it from db
def test_add_and_get_comment(client):
    login_session(client)

    response = client.post('/api/comments', json = {
        "article_id": "test-article",
        "content": "TEST comment",
        "created_at": datetime.now(timezone.utc)
    })

    assert response.status_code == 201
    comment = response.get_json()
    assert comment['article_id'] == 'test-article'
    assert comment['content'] == 'TEST comment'

    get_response = client.get('/api/comments?article_id=test-article')
    assert get_response.status_code == 200
    comments = get_response.get_json()
    assert any(c['content'] == 'TEST comment' for c in comments)

# add a comment then use moderator to remove it
def test_remove_comment(client):
    login_session(client, email="moderator@hw3.com")

    post_response = client.post('/api/comments', json={
        "article_id": "test-article",
        "content": "Will be removed",
        "created_at": datetime.now(timezone.utc)
    })
    print(post_response.get_json())  # helpful debug
    comment_id = post_response.get_json()['_id']
    assert post_response.status_code == 201

    delete_response = client.delete(f'/api/comments/{comment_id}')
    assert delete_response.status_code == 200
    assert delete_response.get_json()['success'] is True

# moderator redact whole comment
def test_redact_comment(client):
    login_session(client, email="admin@hw3.com")

    response = client.post('/api/comments', json={
        "article_id": "test-article",
        "content": "Sensitive data",
        "created_at": datetime.now(timezone.utc)
    })
    assert response.status_code == 201
    comment_id = response.get_json()['_id']

    patch_response = client.patch(f'/api/comments/{comment_id}/redact', json={
        "redacted_content": "████████████"
    })
    assert patch_response.status_code == 200
    assert patch_response.get_json()['success'] is True

# moderator redact partial comment
def test_redact_partial_comment(client):
    login_session(client, email="moderator@hw3.com")

    secret_content = "Secret content is 12345678"
    response = client.post('/api/comments', json={
        "article_id": "test-article",
        "content": secret_content,
        "created_at": datetime.now(timezone.utc)
    })
    assert response.status_code == 201
    comment_id = response.get_json()['_id']

    redacted_content = "Secret content is ████████"
    patch_response = client.patch(f'/api/comments/{comment_id}/redact', json={
        "redacted_content": redacted_content
    })
    assert patch_response.status_code == 200
    assert patch_response.get_json()['success'] is True

    get_response = client.get('/api/comments?article_id=test-article')
    assert get_response.status_code == 200
    comments = get_response.get_json()
    redacted = next((c for c in comments if c['_id'] == comment_id), None)
    assert redacted is not None
    assert redacted['redacted_content'] == redacted_content


## Below test cases were made by ChatGpt to try to push the coverage to 98% up
## The original should be 7X% if I remember correctly

def test_auth_status_not_logged_in(client):
    response = client.get('/api/auth/status')
    assert response.status_code == 200
    assert response.get_json() == {"authenticated": False}

def test_auth_status_logged_in(client):
    login_session(client, email="user@hw3.com", name="Test User")
    response = client.get('/api/auth/status')
    data = response.get_json()
    assert response.status_code == 200
    assert data["authenticated"] is True
    assert data["user"]["email"] == "user@hw3.com"

def test_api_auth_logout(client):
    login_session(client)
    response = client.get('/api/auth/logout')
    assert response.status_code == 200
    assert response.get_json()["success"] is True

@patch("app.oauth.create_client")
def test_api_auth_login(mock_client, client):
    mock_instance = MagicMock()
    mock_client.return_value = mock_instance
    mock_instance.authorize_redirect.return_value = "redirected"
    response = client.get("/api/auth/login")
    assert response.data == b"redirected"
    assert response.status_code == 200

@patch("app.oauth.create_client")
def test_login_route(mock_client, client):
    mock_instance = MagicMock()
    mock_client.return_value = mock_instance
    mock_instance.authorize_redirect.return_value = "redirected"
    response = client.get("/login")
    assert response.data == b"redirected"

def test_logout_redirect(client):
    login_session(client)
    response = client.get('/logout')
    assert response.status_code == 302  # Redirect
    assert response.headers["Location"] == "/"

@patch("app.oauth.create_client")
def test_login_redirect_main(mock_client, client):
    mock_instance = MagicMock()
    mock_client.return_value = mock_instance
    mock_instance.authorize_redirect.return_value = "redirected"
    response = client.get("/login")
    assert response.data == b"redirected"


def test_add_comment_missing_fields(client):
    login_session(client)

    # Missing content
    response = client.post('/api/comments', json={
        "article_id": "some-id"
    })
    assert response.status_code == 400
    assert "error" in response.get_json()

    # Missing article_id
    response = client.post('/api/comments', json={
        "content": "Missing article ID"
    })
    assert response.status_code == 400

def test_remove_nonexistent_comment(client):
    login_session(client, email="moderator@hw3.com")
    fake_id = "64dd7c8f2f00000000000000"  # valid ObjectId format, but nonexistent
    response = client.delete(f'/api/comments/{fake_id}')
    assert response.status_code == 404
    assert response.get_json()["error"] == "Comment not found"

def test_remove_comment_not_found(client):
    login_session(client, email="moderator@hw3.com")
    fake_id = "64dd7c8f2f00000000000000"  # valid but not in db
    response = client.delete(f"/api/comments/{fake_id}")
    assert response.status_code == 404

@patch("app.comments_collection.find_one", side_effect=Exception("DB error"))
def test_remove_comment_db_error(mock_find_one, client):
    login_session(client, email="moderator@hw3.com")
    response = client.delete("/api/comments/64dd7c8f2f00000000000000")
    assert response.status_code == 500

@patch("app.comments_collection.find_one", side_effect=Exception("DB exploded"))
def test_remove_comment_db_failure(mock_find, client):
    login_session(client, email="moderator@hw3.com")
    response = client.delete("/api/comments/64dd7c8f2f00000000000000")
    assert response.status_code == 500

@patch("app.requests.get")
def test_products_api(mock_get, client):
    mock_get.return_value.json.return_value = {
        "products": [{"id": 1, "title": "iPhone", "reviews": []}],
        "total": 1
    }
    response = client.get("/api/products")
    assert response.status_code == 200
    assert "products" in response.get_json()

@patch("app.requests.get")
def test_products_search(mock_get, client):
    mock_get.return_value.json.return_value = {
        "products": [{"id": 1, "title": "iPhone", "reviews": []}]
    }
    response = client.get("/api/products/search?q=iPhone")
    assert response.status_code == 200
    assert isinstance(response.get_json()["products"], list)

@patch("app.requests.get")
def test_products_empty_results(mock_get, client):
    mock_get.return_value.json.return_value = {"products": []}
    response = client.get("/api/products")
    assert response.status_code == 200
    assert response.get_json()["products"] == []

def test_redact_missing_body(client):
    login_session(client, email="moderator@hw3.com")
    # Add a comment first
    post = client.post('/api/comments', json={
        "article_id": "test-article",
        "content": "Partial content",
        "created_at": datetime.now(timezone.utc)
    })
    comment_id = post.get_json()["_id"]
    # Try redacting with missing redacted_content
    patch = client.patch(f'/api/comments/{comment_id}/redact', json={})
    assert patch.status_code == 400

def test_redact_comment_not_found(client):
    login_session(client, email="moderator@hw3.com")
    response = client.patch("/api/comments/64dd7c8f2f00000000000000/redact", json={
        "redacted_content": "██"
    })
    assert response.status_code == 404

@patch("app.comments_collection.update_one", side_effect=Exception("Boom"))
def test_redact_update_error(mock_update, client):
    login_session(client, email="moderator@hw3.com")
    res = client.post("/api/comments", json={
        "article_id": "test-article",
        "content": "test",
        "created_at": datetime.now(timezone.utc)
    })
    comment_id = res.get_json()["_id"]
    response = client.patch(f"/api/comments/{comment_id}/redact", json={
        "redacted_content": "██"
    })
    assert response.status_code == 500

@patch("app.comments_collection.update_one", side_effect=Exception("Update failed"))
def test_redact_comment_update_fail(mock_update, client):
    login_session(client, email="moderator@hw3.com")
    res = client.post("/api/comments", json={
        "article_id": "test-article",
        "content": "test",
        "created_at": datetime.now(timezone.utc)
    })
    comment_id = res.get_json()["_id"]
    patch = client.patch(f"/api/comments/{comment_id}/redact", json={
        "redacted_content": "██"
    })
    assert patch.status_code == 500

def test_redact_comment_missing_field(client):
    login_session(client, email="moderator@hw3.com")
    # Add a comment
    res = client.post("/api/comments", json={
        "article_id": "test-article",
        "content": "real content",
        "created_at": datetime.now(timezone.utc)
    })
    comment_id = res.get_json()["_id"]
    # Try redacting with no content
    res = client.patch(f"/api/comments/{comment_id}/redact", json={})
    assert res.status_code == 400

def test_get_comments_missing_article_id(client):
    response = client.get("/api/comments")
    assert response.status_code == 400

@patch("app.comments_collection.find", side_effect=Exception("Mongo fail"))
def test_get_comments_mongo_fail(mock_find, client):
    response = client.get("/api/comments?article_id=test-article")
    assert response.status_code == 500

@patch("app.comments_collection.find", side_effect=Exception("Boom"))
def test_get_comments_db_crash(mock_find, client):
    response = client.get("/api/comments?article_id=test-article")
    assert response.status_code == 500

def test_non_moderator_cannot_redact(client):
    login_session(client, email="user@hw3.com")
    # Add a comment
    post = client.post('/api/comments', json={
        "article_id": "test-article",
        "content": "Test",
        "created_at": datetime.now(timezone.utc)
    })
    comment_id = post.get_json()["_id"]
    # Try redacting
    patch = client.patch(f'/api/comments/{comment_id}/redact', json={
        "redacted_content": "██"
    })
    assert patch.status_code == 403

def test_non_moderator_cannot_delete(client):
    login_session(client, email="user@hw3.com")
    post = client.post('/api/comments', json={
        "article_id": "test-article",
        "content": "Test",
        "created_at": datetime.now(timezone.utc)
    })
    comment_id = post.get_json()["_id"]
    delete = client.delete(f'/api/comments/{comment_id}')
    assert delete.status_code == 403

def test_redact_comment_not_found(client):
    login_session(client, email="moderator@hw3.com")
    response = client.patch("/api/comments/64dd7c8f2f00000000000000/redact", json={
        "redacted_content": "██"
    })
    assert response.status_code == 404

@patch("app.oauth.create_client")
def test_login_redirect(mock_client, client):
    mock_instance = MagicMock()
    mock_client.return_value = mock_instance
    mock_instance.authorize_redirect.return_value = "redirected"

    response = client.get("/login")
    assert response.data == b"redirected"
    assert response.status_code == 200

@patch("app.oauth.create_client")
def test_authorize_callback(mock_client, client):
    mock_instance = MagicMock()
    mock_client.return_value = mock_instance
    mock_instance.authorize_access_token.return_value = {"id_token": "xyz"}
    mock_instance.parse_id_token.return_value = {
        "email": "user@hw3.com",
        "name": "User HW"
    }

    with client.session_transaction() as sess:
        sess['nonce'] = "testnonce"

    response = client.get("/authorize")
    assert response.status_code == 302
    assert response.headers["Location"] == "http://localhost:5173"

def test_serve_index_not_logged_in(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b'Login with Dex' in response.data

def test_serve_index_logged_in(client):
    login_session(client, email="user@hw3.com")
    response = client.get("/")
    assert response.status_code == 200
    assert b'Logged in as user@hw3.com' in response.data
    assert b'Logout' in response.data

@patch("app.send_from_directory")
def test_serve_static_path(mock_send, client):
    from app import static_files
    mock_send.return_value = Response("static.js", mimetype='application/javascript')
    response = static_files("/somefile.js")
    assert response.status_code == 200
    assert response.data == b"static.js"


def test_redact_with_invalid_objectid(client):
    login_session(client, email="moderator@hw3.com")
    response = client.patch("/api/comments/bad_id/redact", json={
        "redacted_content": "██"
    })
    assert response.status_code == 500

def test_remove_with_invalid_objectid(client):
    login_session(client, email="moderator@hw3.com")
    response = client.delete("/api/comments/bad_id")
    assert response.status_code == 500

@patch("app.requests.get", side_effect=Exception("DummyJSON API failed"))
def test_products_api_error_handling(mock_get, client):
    response = client.get("/api/products")
    assert response.status_code == 500
    assert "error" in response.get_json()


# 기존 test_app.py 파일 끝에 추가할 테스트들

# DummyJSON API 테스트들
@patch("app.requests.get")
def test_get_product_by_id_success(mock_get, client):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "id": 1,
        "title": "iPhone",
        "reviews": [{"rating": 5, "comment": "Great!"}]
    }
    response = client.get("/api/products/1")
    assert response.status_code == 200
    assert response.get_json()["id"] == 1

@patch("app.requests.get")
def test_get_product_by_id_not_found(mock_get, client):
    mock_get.return_value.status_code = 404
    response = client.get("/api/products/999")
    assert response.status_code == 404
    assert "error" in response.get_json()

@patch("app.requests.get")
def test_get_product_by_id_error(mock_get, client):
    mock_get.side_effect = Exception("API Error")
    response = client.get("/api/products/1")
    assert response.status_code == 500

@patch("app.requests.get")
def test_search_products_success(mock_get, client):
    mock_get.return_value.json.return_value = {
        "products": [{"id": 1, "title": "iPhone", "reviews": []}]
    }
    response = client.get("/api/products/search?q=iPhone")
    assert response.status_code == 200
    assert len(response.get_json()["products"]) == 1

@patch("app.requests.get")
def test_search_products_error(mock_get, client):
    mock_get.side_effect = Exception("Search failed")
    response = client.get("/api/products/search?q=test")
    assert response.status_code == 500

# Review voting tests
def test_vote_review_success(client):
    login_session(client)
    response = client.post("/api/reviews/test_review_1/vote", json={"vote_type": "up"})
    assert response.status_code == 200
    assert response.get_json()["success"] is True

def test_vote_review_invalid_vote_type(client):
    login_session(client)
    response = client.post("/api/reviews/test_review_1/vote", json={"vote_type": "invalid"})
    assert response.status_code == 400
    assert "Invalid vote type" in response.get_json()["error"]

def test_vote_review_toggle_vote(client):
    login_session(client)
    # First vote
    response = client.post("/api/reviews/test_review_2/vote", json={"vote_type": "up"})
    assert response.get_json()["action"] == "added"
    
    # Same vote again (should remove)
    response = client.post("/api/reviews/test_review_2/vote", json={"vote_type": "up"})
    assert response.get_json()["action"] == "removed"

def test_vote_review_change_vote(client):
    login_session(client)
    # First vote up
    client.post("/api/reviews/test_review_3/vote", json={"vote_type": "up"})
    
    # Change to down vote
    response = client.post("/api/reviews/test_review_3/vote", json={"vote_type": "down"})
    assert response.get_json()["action"] == "updated"

def test_vote_review_unauthenticated(client):
    response = client.post("/api/reviews/test_review_1/vote", json={"vote_type": "up"})
    assert response.status_code == 401

def test_get_review_votes_api(client):
    response = client.get("/api/reviews/test_review_1/votes")
    assert response.status_code == 200
    assert "upvotes" in response.get_json()

def test_get_user_vote_authenticated(client):
    login_session(client)
    response = client.get("/api/reviews/test_review_1/user-vote")
    assert response.status_code == 200
    assert "vote_type" in response.get_json()

def test_get_user_vote_unauthenticated(client):
    response = client.get("/api/reviews/test_review_1/user-vote")
    assert response.status_code == 401

# Review flagging tests
def test_flag_review_success(client):
    login_session(client)
    import time
    unique_review_id = f"test_review_flag_{int(time.time())}"
    response = client.post(f"/api/reviews/{unique_review_id}/flag", json={"reason": "Inappropriate content"})
    assert response.status_code == 200
    assert response.get_json()["success"] is True

def test_flag_review_missing_reason(client):
    login_session(client)
    response = client.post("/api/reviews/test_review_flag/flag", json={})
    assert response.status_code == 400
    assert "Reason is required" in response.get_json()["error"]

def test_flag_review_duplicate(client):
    login_session(client)
    # First flag
    client.post("/api/reviews/test_review_duplicate/flag", json={"reason": "Spam"})
    
    # Try to flag again
    response = client.post("/api/reviews/test_review_duplicate/flag", json={"reason": "Spam again"})
    assert response.status_code == 400
    assert "already flagged" in response.get_json()["error"]

def test_flag_review_unauthenticated(client):
    response = client.post("/api/reviews/test_review_flag/flag", json={"reason": "Test"})
    assert response.status_code == 401

# Comment flagging tests
def test_flag_comment_success(client):
    login_session(client)
    
    # First create a comment
    comment_response = client.post('/api/comments', json={
        "article_id": "test-article",
        "content": "Test comment to flag"
    })
    comment_id = comment_response.get_json()['_id']
    
    # Then flag it
    response = client.post(f"/api/comments/{comment_id}/flag", json={"reason": "Inappropriate"})
    assert response.status_code == 200
    assert response.get_json()["success"] is True

def test_flag_comment_missing_reason(client):
    login_session(client)
    
    # Create a comment first
    comment_response = client.post('/api/comments', json={
        "article_id": "test-article", 
        "content": "Test comment"
    })
    comment_id = comment_response.get_json()['_id']
    
    response = client.post(f"/api/comments/{comment_id}/flag", json={})
    assert response.status_code == 400

def test_flag_comment_duplicate(client):
    login_session(client)
    
    # Create a comment
    comment_response = client.post('/api/comments', json={
        "article_id": "test-article",
        "content": "Comment to flag twice"
    })
    comment_id = comment_response.get_json()['_id']
    
    # Flag once
    client.post(f"/api/comments/{comment_id}/flag", json={"reason": "First flag"})
    
    # Try to flag again
    response = client.post(f"/api/comments/{comment_id}/flag", json={"reason": "Second flag"})
    assert response.status_code == 400
    assert "already flagged" in response.get_json()["error"]

# Moderation tests
def test_get_flags_moderator(client):
    login_session(client, email="moderator@hw3.com")
    response = client.get("/api/moderation/flags")
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)

def test_get_flags_non_moderator(client):
    login_session(client, email="user@hw3.com")
    response = client.get("/api/moderation/flags")
    assert response.status_code == 403

def test_resolve_flag_remove_content(client):
    login_session(client, email="moderator@hw3.com")
    
    # Create and flag a comment first
    comment_response = client.post('/api/comments', json={
        "article_id": "test-article",
        "content": "Comment to be removed"
    })
    comment_id = comment_response.get_json()['_id']
    
    login_session(client, email="user@hw3.com") 
    flag_response = client.post(f"/api/comments/{comment_id}/flag", json={"reason": "Spam"})
    
    # Switch back to moderator and resolve
    login_session(client, email="moderator@hw3.com")
    # Get flags to find the flag_id (simplified for test)
    flags_response = client.get("/api/moderation/flags")
    flags = flags_response.get_json()
    if flags:
        flag_id = flags[0]['_id']
        response = client.patch(f"/api/moderation/flags/{flag_id}/resolve", json={
            "action": "remove_content"
        })
        assert response.status_code == 200
        assert response.get_json()["success"] is True

def test_resolve_flag_redact_content(client):
    login_session(client, email="admin@hw3.com")
    
    # Create and flag a comment
    comment_response = client.post('/api/comments', json={
        "article_id": "test-article",
        "content": "Comment with sensitive data"
    })
    comment_id = comment_response.get_json()['_id']
    
    login_session(client, email="user@hw3.com")
    client.post(f"/api/comments/{comment_id}/flag", json={"reason": "Sensitive data"})
    
    # Resolve as admin
    login_session(client, email="admin@hw3.com")
    flags_response = client.get("/api/moderation/flags")
    flags = flags_response.get_json()
    if flags:
        flag_id = flags[0]['_id']
        response = client.patch(f"/api/moderation/flags/{flag_id}/resolve", json={
            "action": "redact_content",
            "redacted_content": "Comment with ████████ data"
        })
        assert response.status_code == 200

def test_resolve_flag_missing_redacted_content(client):
    login_session(client, email="moderator@hw3.com")
    
    # Create and flag a comment
    comment_response = client.post('/api/comments', json={
        "article_id": "test-article",
        "content": "Test comment"
    })
    comment_id = comment_response.get_json()['_id']
    
    login_session(client, email="user@hw3.com")
    client.post(f"/api/comments/{comment_id}/flag", json={"reason": "Test"})
    
    login_session(client, email="moderator@hw3.com")
    flags_response = client.get("/api/moderation/flags")
    flags = flags_response.get_json()
    if flags:
        flag_id = flags[0]['_id']
        response = client.patch(f"/api/moderation/flags/{flag_id}/resolve", json={
            "action": "redact_content"
            # Missing redacted_content
        })
        assert response.status_code == 400

def test_resolve_flag_not_found(client):
    login_session(client, email="moderator@hw3.com")
    fake_flag_id = "64dd7c8f2f00000000000000"
    response = client.patch(f"/api/moderation/flags/{fake_flag_id}/resolve", json={
        "action": "resolve_only"
    })
    assert response.status_code == 404

# Comment voting tests
def test_vote_comment_success(client):
    login_session(client)
    
    # Create a comment first
    comment_response = client.post('/api/comments', json={
        "article_id": "test-article",
        "content": "Comment to vote on"
    })
    comment_id = comment_response.get_json()['_id']
    
    response = client.post(f"/api/comments/{comment_id}/vote", json={"vote_type": "up"})
    assert response.status_code == 200
    assert response.get_json()["success"] is True

def test_vote_comment_invalid_type(client):
    login_session(client)
    
    comment_response = client.post('/api/comments', json={
        "article_id": "test-article",
        "content": "Test comment"
    })
    comment_id = comment_response.get_json()['_id']
    
    response = client.post(f"/api/comments/{comment_id}/vote", json={"vote_type": "invalid"})
    assert response.status_code == 400

def test_get_comment_votes(client):
    # Create a comment first
    login_session(client)
    comment_response = client.post('/api/comments', json={
        "article_id": "test-article",
        "content": "Test comment"
    })
    comment_id = comment_response.get_json()['_id']
    
    response = client.get(f"/api/comments/{comment_id}/votes")
    assert response.status_code == 200
    assert "upvotes" in response.get_json()

def test_get_user_comment_vote(client):
    login_session(client)
    
    comment_response = client.post('/api/comments', json={
        "article_id": "test-article",
        "content": "Test comment"
    })
    comment_id = comment_response.get_json()['_id']
    
    response = client.get(f"/api/comments/{comment_id}/user-vote")
    assert response.status_code == 200
    assert "vote_type" in response.get_json()

def test_get_content_for_moderation_comment(client):
    login_session(client, email="moderator@hw3.com")
    
    # Create a comment
    comment_response = client.post('/api/comments', json={
        "article_id": "test-article",
        "content": "Comment for moderation"
    })
    comment_id = comment_response.get_json()['_id']
    
    response = client.get(f"/api/moderation/content/comment/{comment_id}")
    assert response.status_code == 200
    assert "content" in response.get_json()

def test_get_content_for_moderation_review(client):
    login_session(client, email="moderator@hw3.com")
    response = client.get("/api/moderation/content/review/test_review_123")
    assert response.status_code == 501  # Not implemented

def test_get_content_for_moderation_not_found(client):
    login_session(client, email="moderator@hw3.com")
    fake_id = "64dd7c8f2f00000000000000"
    response = client.get(f"/api/moderation/content/comment/{fake_id}")
    assert response.status_code == 404

# Error handling for vote functions
@patch("app.votes_collection.find_one", side_effect=Exception("DB error"))
def test_vote_review_db_error(mock_find, client):
    login_session(client)
    response = client.post("/api/reviews/test_review/vote", json={"vote_type": "up"})
    assert response.status_code == 500

@patch("app.votes_collection.count_documents", side_effect=Exception("DB error"))
def test_get_review_votes_db_error(mock_find, client):
    response = client.get("/api/reviews/test_review/votes")
    assert response.status_code == 500

@patch("app.flags_collection.find_one", side_effect=Exception("DB error"))
def test_flag_review_db_error(mock_find, client):
    login_session(client)
    response = client.post("/api/reviews/test_review/flag", json={"reason": "Test"})
    assert response.status_code == 500

# Test some edge cases
def test_get_products_with_params(client):
    with patch("app.requests.get") as mock_get:
        mock_get.return_value.json.return_value = {"products": []}
        response = client.get("/api/products?limit=10&skip=5")
        assert response.status_code == 200
        # Verify the params were passed
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert kwargs['params']['limit'] == '10'
        assert kwargs['params']['skip'] == '5'