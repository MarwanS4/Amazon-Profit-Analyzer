from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin
import sqlite3, os

auth_bp = Blueprint('auth', __name__, template_folder='templates')
bcrypt = Bcrypt()
DB_FILE = 'users.db'

# ---------------- DATABASE ----------------
def init_db():
    db_path = "users.db"
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT UNIQUE,
                email_verified INTEGER DEFAULT 0,
                verification_token TEXT,
                theme TEXT DEFAULT 'light'
            )
        """)
        conn.commit()
        conn.close()
    except sqlite3.DatabaseError as e:
        print("⚠️ Database is corrupted. Rebuilding clean version...")
        try:
            conn.close()
        except: pass
        if os.path.exists(db_path):
            os.remove(db_path)
        init_db()


def update_user_theme(user_id, theme):
    """Update the saved theme for a specific user"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET theme=? WHERE id=?", (theme, user_id))
    conn.commit()
    conn.close()

def get_user_theme(user_id):
    """Get the saved theme for a specific user"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT theme FROM users WHERE id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row and row[0] else 'light'


# ---------------- USER MODEL ----------------
class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password


def load_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, username, password FROM users WHERE id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return User(*row)
    return None


# ---------------- ROUTES ----------------
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password_raw = request.form['password']

        if not username or not password_raw:
            flash("Please fill in all fields.", "danger")
            return redirect(url_for('auth.register'))

        password = bcrypt.generate_password_hash(password_raw).decode('utf-8')

        try:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            conn.close()
            # silent success — go to login
            return redirect(url_for('auth.login'))
        except sqlite3.IntegrityError:
            flash("Username already exists!", "danger")

    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT id, username, password FROM users WHERE username=?", (username,))
        row = c.fetchone()
        conn.close()

        if row and bcrypt.check_password_hash(row[2], password):
            user = User(*row)
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash("Invalid username or password.", "danger")

    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
def ensure_theme_column():
    """Add theme column to users table if missing"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in c.fetchall()]
    if "theme" not in columns:
        c.execute("ALTER TABLE users ADD COLUMN theme TEXT DEFAULT 'light'")
    conn.commit()
    conn.close()
