import os
from flask import Flask, redirect, url_for, session, request, jsonify
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_secret_key")

# ---------------- OAuth ----------------
oauth = OAuth(app)

# Configure Google properly with OpenID config URL (fixes jwks_uri issue)
google = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",  # loads jwks_uri
    client_kwargs={
        "scope": "openid email profile",
    },
)

# ---------------- Routes ----------------
@app.route("/login")
def login():
    redirect_uri = url_for("authorize", _external=True)
    return google.authorize_redirect(redirect_uri, nonce="secure-nonce")  # pass nonce

@app.route("/authorize")
def authorize():
    # Exchange code for token
    token = google.authorize_access_token()
    
    # Verify and decode ID token
    userinfo = google.parse_id_token(token, nonce="secure-nonce")  # nonce provided

    # Save user info in session
    session["user"] = {
        "email": userinfo["email"],
        "name": userinfo.get("name", ""),
    }

    # Redirect back to Streamlit with user info in query params
    redirect_url = f"http://localhost:8501?email={userinfo['email']}&name={userinfo.get('name','')}"
    return redirect(redirect_url)

@app.route("/me")
def me():
    """Return logged-in user info if available"""
    if "user" in session:
        return jsonify(session["user"])
    return jsonify({"error": "Unauthorized"}), 401

@app.route("/logout")
def logout():
    """Clear server session and redirect back"""
    session.clear()
    return jsonify({"success": True, "message": "Logged out"}), 200

if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=True)
