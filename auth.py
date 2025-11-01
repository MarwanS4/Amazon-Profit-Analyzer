from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin
import sqlite3

auth_bp = Blueprint('auth', __name__, template_folder='templates')
bcrypt = Bcrypt()
DB_FILE = 'users.db'

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')
    conn.commit()
    conn.close()


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
