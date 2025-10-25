from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from pymongo import MongoClient
from bson.objectid import ObjectId
from gridfs import GridFS
import bcrypt
from dotenv import load_dotenv
import os
import io
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load environment variables
load_dotenv()  # Ensure this is called before using os.getenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your_default_secret_key_here')

# Debug: Print environment variables to verify they are loaded
print("Loaded environment variables:")
print(f"EMAIL_USERNAME: {os.getenv('EMAIL_USERNAME')}")
print(f"EMAIL_PASSWORD: {os.getenv('EMAIL_PASSWORD')}")
print(f"EMAIL_RECIPIENT: {os.getenv('EMAIL_RECIPIENT')}")

# Session config
app.config['SESSION_PERMANENT'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = 3600

# MongoDB
app.config['MONGO_URI'] = os.getenv('MONGO_URI')
mongo_client = MongoClient(app.config['MONGO_URI'])
db = mongo_client['genkan_institute']
fs = GridFS(db)  # GridFS for images

# Email configuration
EMAIL_USERNAME = os.getenv('EMAIL_USERNAME')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
EMAIL_RECIPIENT = os.getenv('EMAIL_RECIPIENT')

if not all([EMAIL_USERNAME, EMAIL_PASSWORD, EMAIL_RECIPIENT]):
    print("Warning: One or more email configuration variables are missing!")

# Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'  # HANYA ADMIN

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

@app.route('/image/<image_id>')
def serve_image(image_id):
    try:
        grid_out = fs.get(ObjectId(image_id))
        return send_file(io.BytesIO(grid_out.read()), mimetype=grid_out.content_type, download_name=grid_out.filename)
    except Exception as e:
        print(f"Image serve error: {e}")
        return send_file(os.path.join(app.root_path, 'static/image/placeholder.jpg'), mimetype='image/jpeg')

@app.route('/')
def index():
    try:
        schedules = list(db.kelas.find().sort("start_date", 1))
    except Exception as e:
        print(f"DB Error: {e}")
        flash("Gagal memuat jadwal kelas.", "error")
        schedules = []
    return render_template('index.html', schedules=schedules)

@app.route('/kelas')
def kelas():
    try:
        schedules = list(db.kelas.find().sort("start_date", 1))
    except Exception as e:
        flash("Gagal memuat kelas.", "error")
        schedules = []
    return render_template('kelas.html', schedules=schedules)

@app.route('/tentang')
def tentang():
    return render_template('tentang.html')

@app.route('/pengajar')
def pengajar():
    return render_template('pengajar.html')

@app.route('/kontak', methods=['GET', 'POST'])
def kontak():
    if request.method == 'POST':
        nama = request.form.get('nama')
        email = request.form.get('email')
        pesan = request.form.get('pesan')
        try:
            # Save to MongoDB
            db.kontak.insert_one({
                "nama": nama,
                "email": email,
                "pesan": pesan,
                "tanggal": datetime.utcnow()
            })

            # Send email
            msg = MIMEMultipart()
            msg['From'] = EMAIL_USERNAME
            msg['To'] = EMAIL_RECIPIENT
            msg['Subject'] = f'New Contact Form Submission from {nama}'
            body = f"""
            New message from contact form:
            Name: {nama}
            Email: {email}
            Message: {pesan}
            Submitted on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}
            """
            msg.attach(MIMEText(body, 'plain'))

            # Connect to Gmail's SMTP server
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
            server.sendmail(EMAIL_USERNAME, EMAIL_RECIPIENT, msg.as_string())
            server.quit()

            flash("Pesan terkirim! Kami akan balas secepatnya.", "success")
            return redirect(url_for('kontak'))
        except Exception as e:
            print(f"Kontak error: {e}")
            flash(f"Gagal mengirim pesan: {str(e)}", "error")
    return render_template('kontak.html')

@app.route('/daftar', methods=['GET', 'POST'])
def daftar():
    if request.method == 'POST':
        data = {
            "nama": request.form.get('nama'),
            "email": request.form.get('email'),
            "telepon": request.form.get('telepon'),
            "level": request.form.get('level'),
            "tanggal": datetime.utcnow()
        }
        try:
            db.pendaftaran.insert_one(data)
            flash("Pendaftaran berhasil! Kami akan hubungi kamu.", "success")
            return redirect(url_for('index'))
        except Exception as e:
            print(f"Daftar error: {e}")
            flash("Gagal mendaftar.", "error")
    return render_template('index.html')

@app.route('/placement-test', methods=['GET', 'POST'])
def placement_test():
    if request.method == 'POST':
        flash("Hasil: Kamu cocok untuk N5! Daftar kelas sekarang.", "info")
        return redirect(url_for('kelas'))
    return render_template('placement_test.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_kelas'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin = db.admins.find_one({"username": username})

        if admin and admin.get('password'):
            try:
                hashed = admin['password']
                if isinstance(hashed, str):
                    hashed = hashed.encode('utf-8')
                if bcrypt.checkpw(password.encode('utf-8'), hashed):
                    login_user(User(admin['_id'], admin['username']))
                    flash('Admin login berhasil!', 'success')
                    return redirect(url_for('admin_kelas'))
            except Exception as e:
                print(f"Bcrypt error: {e}")
        flash('Username atau password salah.', 'error')
    return render_template('admin_login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    session.clear()
    flash('Logout berhasil.', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin/kelas', methods=['GET', 'POST'])
@login_required
def admin_kelas():
    if request.method == 'POST':
        action = request.form.get('action')
        image_id = None

        # Handle image upload
        if 'image_file' in request.files:
            image_file = request.files['image_file']
            if image_file.filename != '':
                try:
                    image_id = fs.put(image_file, filename=image_file.filename, content_type=image_file.content_type)
                except Exception as e:
                    print(f"GridFS put error: {e}")
                    flash("Gagal upload gambar.", "error")
                    return redirect(url_for('admin_kelas'))

        try:
            if action == 'create':
                kelas = {
                    "level": request.form.get('level'),
                    "title": request.form.get('title'),
                    "description": request.form.get('description'),
                    "status": request.form.get('status'),
                    "start_date": request.form.get('start_date'),
                    "schedule": request.form.get('schedule'),
                    "spots_available": int(request.form.get('spots_available', 0)),
                    "price": float(request.form.get('price', 0)),
                    "image_id": str(image_id) if image_id else None
                }
                db.kelas.insert_one(kelas)
                flash('Kelas berhasil ditambahkan!', 'success')

            elif action == 'update':
                kelas_id = request.form.get('id')
                if not kelas_id:
                    raise ValueError("ID kelas tidak ditemukan.")
                update_data = {
                    "level": request.form.get('level'),
                    "title": request.form.get('title'),
                    "description": request.form.get('description'),
                    "status": request.form.get('status'),
                    "start_date": request.form.get('start_date'),
                    "schedule": request.form.get('schedule'),
                    "spots_available": int(request.form.get('spots_available', 0)),
                    "price": float(request.form.get('price', 0))
                }
                if image_id:
                    # Hapus gambar lama
                    existing_kelas = db.kelas.find_one({"_id": ObjectId(kelas_id)})
                    if existing_kelas and existing_kelas.get('image_id'):
                        try:
                            fs.delete(ObjectId(existing_kelas['image_id']))
                        except Exception as del_e:
                            print(f"Delete old image error: {del_e}")
                    update_data['image_id'] = str(image_id)
                db.kelas.update_one({"_id": ObjectId(kelas_id)}, {"$set": update_data})
                flash('Kelas berhasil diupdate!', 'success')

            elif action == 'delete':
                kelas_id = request.form.get('id')
                existing_kelas = db.kelas.find_one({"_id": ObjectId(kelas_id)})
                if existing_kelas and existing_kelas.get('image_id'):
                    try:
                        fs.delete(ObjectId(existing_kelas['image_id']))
                    except Exception as del_e:
                        print(f"Delete image error: {del_e}")
                db.kelas.delete_one({"_id": ObjectId(kelas_id)})
                flash('Kelas berhasil dihapus!', 'success')

        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
            print(e)

        return redirect(url_for('admin_kelas'))

    try:
        kelas_items = list(db.kelas.find())
    except Exception as e:
        print(f"DB fetch error: {e}")
        kelas_items = []
        flash("Gagal memuat daftar kelas.", "error")
    return render_template('admin_kelas.html', kelas_items=kelas_items)

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', message="Something went wrong. Please try again."), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)