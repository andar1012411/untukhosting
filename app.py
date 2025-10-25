from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, make_response
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from pymongo import MongoClient
from bson.objectid import ObjectId
import bcrypt
from dotenv import load_dotenv
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your_default_secret_key_here')

# Session configuration
app.config['SESSION_PERMANENT'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = 3600

# MongoDB Atlas configuration from .env
app.config['MONGO_URI'] = os.getenv('MONGO_URI')
mongo_client = MongoClient(app.config['MONGO_URI'])
db = mongo_client['genkan_institute']

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username):
        self.id = str(id)
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    admin = db.admins.find_one({"_id": ObjectId(user_id)})
    if admin:
        return User(admin['_id'], admin['username'])
    return None

@app.route('/')
def index():
    try:
        schedules = list(db.kelas.find().sort("start_date", 1))
    except Exception as e:
        print(f"Database error: {e}")
        flash(f"Database error: {e}", 'error')
        schedules = []
    return render_template('index.html', schedules=schedules)

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
        return redirect(url_for('admin_kelas'))
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
                return redirect(url_for('admin_kelas'))
            else:
                flash('Invalid username or password', 'error')
        except ValueError as e:
            flash('Login error: Invalid password hash. Please contact support.', 'error')
            print(f"ValueError in bcrypt.checkpw: {e}")
    return render_template('admin_login.html')

@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    if current_user.is_authenticated:
        return redirect(url_for('admin_kelas'))
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

@app.route('/admin/kelas', methods=['GET', 'POST'])
@login_required
def admin_kelas():
    if request.method == 'POST':
        action = request.form.get('action')
        level = request.form.get('level')
        title = request.form.get('title')
        description = request.form.get('description')
        status = request.form.get('status')
        start_date = request.form.get('start_date')
        schedule = request.form.get('schedule')
        spots_available = int(request.form.get('spots_available'))
        price = float(request.form.get('price'))
        image_url = request.form.get('image_url')
        item_id = request.form.get('id')
        try:
            if action == 'create':
                db.kelas.insert_one({
                    "level": level,
                    "title": title,
                    "description": description,
                    "status": status,
                    "start_date": start_date,
                    "schedule": schedule,
                    "spots_available": spots_available,
                    "price": price,
                    "image_url": image_url
                })
                flash('Kelas added successfully!', 'success')
            elif action == 'update' and item_id:
                db.kelas.update_one(
                    {"_id": ObjectId(item_id)},
                    {"$set": {
                        "level": level,
                        "title": title,
                        "description": description,
                        "status": status,
                        "start_date": start_date,
                        "schedule": schedule,
                        "spots_available": spots_available,
                        "price": price,
                        "image_url": image_url
                    }}
                )
                flash('Kelas updated successfully!', 'success')
            elif action == 'delete' and item_id:
                db.kelas.delete_one({"_id": ObjectId(item_id)})
                flash('Kelas deleted successfully!', 'success')
        except Exception as e:
            flash(f"Error: {e}", 'error')
    kelas_items = list(db.kelas.find().sort("start_date", 1))
    return render_template('admin_kelas.html', kelas_items=kelas_items)

@app.route('/kelas')
def kelas():
    try:
        schedules = list(db.kelas.find().sort("start_date", 1))
    except Exception as e:
        print(f"Database error: {e}")
        schedules = []
    return render_template('kelas.html', schedules=schedules)

@app.route('/placement-test', methods=['GET', 'POST'])
def placement_test():
    if request.method == 'POST':
        level = request.form['previous_level']
        score = int(request.form['score'])
        flash(f'Terima kasih! Kamu direkomendasikan ke {level} batch upcoming.', 'success')
        return redirect(url_for('kelas'))
    return render_template('placement_test.html')

@app.route('/kontak', methods=['GET', 'POST'])
def kontak():
    if request.method == 'POST':
        print("Form data received:", dict(request.form))  # Log data form
        nama = request.form.get('nama')
        email = request.form.get('email')
        pesan = request.form.get('pesan')
        
        if not nama or not email or not pesan:
            print("Validation failed: Missing fields")  # Log validasi gagal
            flash('Semua field harus diisi!', 'error')
            return redirect(url_for('index') + '#kontak')
        
        from_email = os.getenv('EMAIL_USERNAME')
        password = os.getenv('EMAIL_PASSWORD')
        to_email = os.getenv('EMAIL_RECIPIENT')
        
        print(f"Email config: from={from_email}, to={to_email}, password={password[:4]}...")  # Log kredensial (sembunyikan sebagian password)
        if not from_email or not password or not to_email:
            print("Email config missing in .env")  # Log konfigurasi hilang
            flash('Konfigurasi email belum diset. Hubungi admin.', 'error')
            return redirect(url_for('index') + '#kontak')
        
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = 'Pesan Baru dari Kontak Form Genkan Institute'
        body = f"Nama: {nama}\nEmail: {email}\nPesan: {pesan}"
        msg.attach(MIMEText(body, 'plain'))
        
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(from_email, password)
            text = msg.as_string()
            server.sendmail(from_email, to_email, text)
            server.quit()
            print(f"Email sent successfully to {to_email}!")  # Log sukses
            flash('Pesan berhasil dikirim! Kami akan balas segera.', 'success')
        except Exception as e:
            print(f"SMTP Error: {str(e)}")  # Log error
            flash(f'Error mengirim pesan: {str(e)}', 'error')
        return redirect(url_for('index') + '#kontak')
    print("GET request to /kontak, redirecting to index#kontak")  # Log GET
    return redirect(url_for('index') + '#kontak')

@app.route('/tentang')
def tentang():
    return render_template('tentang.html')

@app.route('/pengajar')
def pengajar():
    return render_template('pengajar.html')

# Middleware to set session cookie
@app.after_request
def set_session_cookie(response):
    response.set_cookie('session', '', expires=0)
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)