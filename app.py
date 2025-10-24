from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, make_response
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from pymongo import MongoClient
from bson.objectid import ObjectId
import bcrypt
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your_default_secret_key_here')

# Session configuration
app.config['SESSION_PERMANENT'] = False  # Non-permanent session
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # Session lifetime in seconds (1 hour)

# MongoDB Atlas configuration from .env
app.config['MONGO_URI'] = os.getenv('MONGO_URI')
mongo_client = MongoClient(app.config['MONGO_URI'])
db = mongo_client['genkan_institute']  # Explicitly set database name

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username):
        self.id = str(id)  # Convert ObjectId to string for Flask-Login
        self.username = username

# Load user for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    admin = db.admins.find_one({"_id": ObjectId(user_id)})
    if admin:
        return User(admin['_id'], admin['username'])
    return None

@app.route('/')
def index():
    try:
        catalog_items = list(db.catalog.find())
    except Exception as e:
        print(f"Database error: {e}")
        flash(f"Database error: {e}", 'error')
        catalog_items = []
    return render_template('index.html', catalog_items=catalog_items)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        try:
            if db.users.find_one({"username": username}):
                flash('Username already exists', 'error')
            else:
                db.users.insert_one({"username": username, "password": hashed})
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
        except Exception as e:
            flash(f'Error: {e}', 'error')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = db.users.find_one({"username": username})
        try:
            if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                login_user(User(user['_id'], user['username']), remember=False)
                session.permanent = False
                flash('Login successful!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password', 'error')
        except ValueError as e:
            flash('Login error: Invalid password hash. Please contact support.', 'error')
            print(f"ValueError in bcrypt.checkpw: {e}")
    return render_template('login.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_catalog'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = db.admins.find_one({"username": username})
        try:
            if admin and bcrypt.checkpw(password.encode('utf-8'), admin['password'].encode('utf-8')):
                user = User(admin['_id'], admin['username'])
                login_user(user, remember=False)
                session.permanent = False
                flash('Login successful!', 'success')
                return redirect(url_for('admin_catalog'))
            else:
                flash('Invalid username or password', 'error')
        except ValueError as e:
            flash('Login error: Invalid password hash. Please contact support.', 'error')
            print(f"ValueError in bcrypt.checkpw: {e}")
    return render_template('admin_login.html')

@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    if current_user.is_authenticated:
        return redirect(url_for('admin_catalog'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        try:
            if db.admins.find_one({"username": username}):
                flash('Username already exists', 'error')
            else:
                db.admins.insert_one({"username": username, "password": hashed})
                flash('Admin registered successfully! Please log in.', 'success')
                return redirect(url_for('admin_login'))
        except Exception as e:
            flash(f'Error: {e}', 'error')
    return render_template('admin_register.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    session.clear()
    logout_user()
    flash('You have been logged out', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin/catalog', methods=['GET', 'POST'])
@login_required
def admin_catalog():
    if request.method == 'POST':
        action = request.form.get('action')
        name = request.form.get('name')
        price = float(request.form.get('price'))  # Convert to float
        image_url = request.form.get('image_url')
        description = request.form.get('description')
        item_id = request.form.get('id')
        try:
            if action == 'create':
                db.catalog.insert_one({
                    "name": name,
                    "price": price,
                    "image_url": image_url,
                    "description": description
                })
                flash('Item added successfully!', 'success')
            elif action == 'update' and item_id:
                db.catalog.update_one(
                    {"_id": ObjectId(item_id)},
                    {"$set": {
                        "name": name,
                        "price": price,
                        "image_url": image_url,
                        "description": description
                    }}
                )
                flash('Item updated successfully!', 'success')
            elif action == 'delete' and item_id:
                db.catalog.delete_one({"_id": ObjectId(item_id)})
                flash('Item deleted successfully!', 'success')
        except Exception as e:
            flash(f"Error: {e}", 'error')
    catalog_items = list(db.catalog.find())
    return render_template('katalog.html', catalog_items=catalog_items)

# Middleware to set session cookie
@app.after_request
def set_session_cookie(response):
    response.set_cookie('session', '', expires=0)
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)