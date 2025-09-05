import os, json, time, hashlib

DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
HISTORY_DIR = os.path.join(DATA_DIR, "history")

os.makedirs(HISTORY_DIR, exist_ok=True)

def _safe_email(email: str) -> str:
    return hashlib.sha256(email.strip().lower().encode()).hexdigest()

def _json_default(obj):
    try:
        return str(obj)
    except Exception:
        return None

def _load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_users(users):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def signup_user(email: str, name: str, password: str):
    users = _load_users()
    if email in users:
        return False, "User already exists"
    users[email] = {"name": name, "password": password}
    _save_users(users)
    return True, "Signup successful. Please log in."

def login_user(email: str, password: str):
    users = _load_users()
    if email not in users:
        return False, "User not found"
    if users[email]["password"] != password:
        return False, "Incorrect password"
    return True, users[email]

def save_history(email: str, entry: dict):
    e = _safe_email(email)
    path = os.path.join(HISTORY_DIR, f"{e}.json")
    hist = []
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                hist = json.load(f)
        except Exception:
            hist = []
    entry["timestamp"] = int(time.time())
    hist.insert(0, entry)
    with open(path, "w") as f:
        json.dump(hist, f, indent=2, default=_json_default)

def load_history(email: str):
    e = _safe_email(email)
    path = os.path.join(HISTORY_DIR, f"{e}.json")
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return []

def clear_history(email: str):
    e = _safe_email(email)
    path = os.path.join(HISTORY_DIR, f"{e}.json")
    try:
        if os.path.exists(path):
            os.remove(path)
        return True
    except Exception:
        return False
