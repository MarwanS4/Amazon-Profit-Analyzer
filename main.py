from flask import Flask, render_template, jsonify
from flask_login import LoginManager, login_required, current_user
import csv, os
from auth import auth_bp, User, load_user, init_db

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Change this in production

# Register authentication blueprint
app.register_blueprint(auth_bp)

# Initialize database
init_db()

# Configure Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = "auth.login"

@login_manager.user_loader
def user_loader(user_id):
    return load_user(user_id)

UPLOADS_FOLDER = 'uploads'
CSV_FILE = 'eurolots_test.csv'


# ---------------- ROUTES ----------------
@app.route('/')
@login_required
def index():
    return render_template('index.html', username=current_user.username)


@app.route('/get_products')
@login_required
def get_products():
    path = os.path.join(UPLOADS_FOLDER, CSV_FILE)
    products = []
    with open(path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            products.append(row)
    return jsonify(products)


if __name__ == '__main__':
    app.run(debug=True)
