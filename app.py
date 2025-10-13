from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import pymysql
import bcrypt
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your_default_secret_key_here')  # Replace with a secure key in .env

# Database configuration
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', '')  # Set in .env
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'vitaleather')

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

# Load user for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM admins WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user:
        return User(user['id'], user['username'])
    return None

# Database connection
def get_db_connection():
    return pymysql.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        db=app.config['MYSQL_DB'],
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route('/')
def index():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch sliders
        cursor.execute("SELECT image_url, title, subtitle FROM slider")
        sliders = cursor.fetchall()

        # Fetch products
        cursor.execute("SELECT name, price, image_url FROM products")
        products = cursor.fetchall()

        # Fetch events
        cursor.execute("SELECT name, date, image_url FROM events")
        events = cursor.fetchall()

        # Fetch catalog items
        cursor.execute("SELECT id, name, price, image_url, description FROM catalog")
        catalog_items = cursor.fetchall()

    except pymysql.Error as e:
        print(f"Database error: {e}")
        flash(f"Database error: {e}", 'error')
        sliders = []
        products = []
        events = []
        catalog_items = []
    finally:
        cursor.close()
        conn.close()

    return render_template('index.html', sliders=sliders, products=products, events=events, catalog_items=catalog_items)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_catalog'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password FROM admins WHERE username = %s", (username,))
        admin = cursor.fetchone()
        cursor.close()
        conn.close()
        
        try:
            if admin and bcrypt.checkpw(password.encode('utf-8'), admin['password'].encode('utf-8')):
                user = User(admin['id'], admin['username'])
                login_user(user)
                flash('Login successful!', 'success')
                return redirect(url_for('admin_catalog'))
            else:
                flash('Invalid username or password', 'error')
        except ValueError as e:
            flash(f'Login error: Invalid password hash. Please contact support.', 'error')
            print(f"ValueError in bcrypt.checkpw: {e}, Stored hash: {admin['password'] if admin else 'No admin found'}")
    
    return render_template('admin_login.html')

@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    if current_user.is_authenticated:
        return redirect(url_for('admin_catalog'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO admins (username, password) VALUES (%s, %s)", (username, hashed))
            conn.commit()
            flash('Admin registered successfully! Please log in.', 'success')
            return redirect(url_for('admin_login'))
        except pymysql.Error as e:
            conn.rollback()
            flash(f'Error: {e}', 'error')
        finally:
            cursor.close()
            conn.close()
    
    return render_template('admin_register.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    flash('You have been logged out', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin/catalog', methods=['GET', 'POST'])
@login_required
def admin_catalog():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        action = request.form.get('action')
        name = request.form.get('name')
        price = request.form.get('price')
        image_url = request.form.get('image_url')
        description = request.form.get('description')
        item_id = request.form.get('id')

        try:
            if action == 'create':
                cursor.execute(
                    "INSERT INTO catalog (name, price, image_url, description) VALUES (%s, %s, %s, %s)",
                    (name, price, image_url, description)
                )
                conn.commit()
                flash('Item added successfully!', 'success')
            elif action == 'update' and item_id:
                cursor.execute(
                    "UPDATE catalog SET name = %s, price = %s, image_url = %s, description = %s WHERE id = %s",
                    (name, price, image_url, description, item_id)
                )
                conn.commit()
                flash('Item updated successfully!', 'success')
            elif action == 'delete' and item_id:
                cursor.execute("DELETE FROM catalog WHERE id = %s", (item_id,))
                conn.commit()
                flash('Item deleted successfully!', 'success')
        except pymysql.Error as e:
            conn.rollback()
            flash(f"Error: {e}", 'error')

    cursor.execute("SELECT id, name, price, image_url, description FROM catalog")
    catalog_items = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('katalog.html', catalog_items=catalog_items)

if __name__ == '__main__':
    app.run(debug=True)