from flask import Flask, render_template, jsonify, request
from flask_login import LoginManager, login_required, current_user
import os, csv

# Import from auth blueprint
from auth import (
    auth_bp, User, load_user, init_db,
    update_user_theme, get_user_theme, ensure_theme_column
)

# ---------------- APP SETUP ----------------
app = Flask(__name__)
app.secret_key = "supersecretkey"  # ⚠️ Change this in production

# Register authentication routes
app.register_blueprint(auth_bp)

# Initialize database and ensure theme column
init_db()
ensure_theme_column()

# ---------------- LOGIN CONFIG ----------------
login_manager = LoginManager(app)
login_manager.login_view = "auth.login"

@login_manager.user_loader
def user_loader(user_id):
    return load_user(user_id)

# ---------------- FILE SETTINGS ----------------
UPLOADS_FOLDER = "uploads"
CSV_FILE = "eurolots_test.csv"

if not os.path.exists(UPLOADS_FOLDER):
    os.makedirs(UPLOADS_FOLDER)

# ---------------- THEME MANAGEMENT ----------------
@app.route("/save_preferences", methods=["POST"])
@login_required
def save_preferences():
    """Save the user's theme preference to the database"""
    data = request.get_json()
    theme = data.get("theme", "light")
    update_user_theme(current_user.id, theme)
    return jsonify({"status": "success", "theme": theme})


# ---------------- ROUTES ----------------
@app.route("/")
@login_required
def index():
    """Main dashboard page"""
    theme = get_user_theme(current_user.id)
    return render_template("index.html", username=current_user.username, theme=theme)


@app.route("/get_products")
@login_required
def get_products():
    """Serve CSV data to frontend"""
    path = os.path.join(UPLOADS_FOLDER, CSV_FILE)
    products = []

    try:
        with open(path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                products.append(row)
    except FileNotFoundError:
        print(f"⚠️ CSV file not found: {path}")

    return jsonify(products)


@app.route("/user_center")
@login_required
def user_center():
    """Render the user center page"""
    theme = get_user_theme(current_user.id)
    return render_template("user_center.html", username=current_user.username, theme=theme)


@app.errorhandler(404)
def not_found(error):
    """Custom 404 page"""
    return render_template("404.html"), 404


# ---------------- MAIN ENTRY ----------------
if __name__ == "__main__":
    print("🚀 Starting Flask server at http://127.0.0.1:5000")
    app.run(debug=True)
