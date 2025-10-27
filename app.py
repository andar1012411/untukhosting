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
from flask import send_from_directory
import pandas as pd
from io import StringIO

# Load environment variables
load_dotenv()  # Ensure this is called before using os.getenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your_default_secret_key_here')

# Debug: Print environment variables to verify they are loaded
# print("Loaded environment variables:")
# print(f"EMAIL_USERNAME: {os.getenv('EMAIL_USERNAME')}")
# print(f"EMAIL_PASSWORD: {os.getenv('EMAIL_PASSWORD')}")
# print(f"EMAIL_RECIPIENT: {os.getenv('EMAIL_RECIPIENT')}")

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
        # Tampilkan hanya 3 kelas unggulan (upcoming/ongoing terbaru)
        schedules = list(db.kelas.find({"status": {"$in": ["upcoming", "ongoing"]}}).sort("start_date", 1).limit(3))
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
        nama = request.form.get('nama')
        email = request.form.get('email')
        whatsapp = request.form.get('whatsapp')  # Tambahkan ini
        level = request.form.get('level')
        try:
            kelas = db.kelas.find_one({"level": level, "status": "upcoming", "spots_available": {"$gt": 0}})
            if kelas:
                # Kurangi spot available
                db.kelas.update_one({"_id": kelas["_id"]}, {"$inc": {"spots_available": -1}})
                # Simpan data pendaftaran
                db.registrations.insert_one({
                    "nama": nama,
                    "email": email,
                    "whatsapp": whatsapp,  # Tambahkan ini
                    "level": level,
                    "status": "pending",
                    "tanggal": datetime.utcnow(),
                    "batch_id": kelas.get("batch_id")
                })
                # Kirim email konfirmasi (opsional, sesuaikan jika perlu)
                flash("Pendaftaran berhasil! Kami akan menghubungi Anda.", "success")
                return redirect(url_for('daftar'))
            else:
                flash("Kelas penuh atau tidak tersedia.", "error")
        except Exception as e:
            print(f"Pendaftaran error: {e}")
            flash(f"Gagal mendaftar: {str(e)}", "error")
    try:
        available_levels = list(db.kelas.find({"status": "upcoming", "spots_available": {"$gt": 0}}))
    except Exception as e:
        flash("Gagal memuat kelas tersedia.", "error")
        available_levels = []
    return render_template('daftar.html', available_levels=available_levels)

@app.route('/kelas/<kelas_id>')
def kelas_detail(kelas_id):
    try:
        kelas = db.kelas.find_one({"_id": ObjectId(kelas_id)})
        if not kelas:
            flash("Kelas tidak ditemukan.", "error")
            return redirect(url_for('kelas'))
        return render_template('kelas_detail.html', kelas=kelas)
    except Exception as e:
        flash("Gagal memuat detail kelas.", "error")
        return redirect(url_for('kelas'))

@app.route('/placement-test', methods=['GET', 'POST'])
def placement_test():
    if request.method == 'POST':
        flash("Hasil: Kamu cocok untuk N5! Daftar kelas sekarang.", "info")
        return redirect(url_for('kelas'))
    return render_template('placement_test.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password').encode('utf-8')  # Konversi input password ke bytes
        admin = db.admins.find_one({"username": username})
        if admin:
            # Ambil hashed password dari database dan konversi ke bytes jika perlu
            stored_password = admin['password']
            if isinstance(stored_password, str):
                # Asumsi password disimpan sebagai string (misalnya base64 atau hex), decode kembali
                try:
                    stored_password = stored_password.encode('utf-8')  # Jika string biasa
                    # Atau jika disimpan sebagai base64: stored_password = base64.b64decode(stored_password)
                except Exception as e:
                    flash(f"Error decoding password: {str(e)}", "error")
                    return render_template('admin_login.html')
            if admin and bcrypt.checkpw(password, stored_password):
                user = User(admin['_id'], admin['username'])
                login_user(user)
                session.pop('_flashes', None)  # Clear any previous flashes
                flash('Login berhasil!', 'success')
                return redirect(url_for('admin_kelas'))
            else:
                flash('Username atau password salah.', 'error')
        else:
            flash('Username tidak ditemukan.', 'error')
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
                    "image_id": str(image_id) if image_id else None,
                    # TAMBAHAN BARU
                    "batch_id": request.form.get('batch_id'),
                    "prerequisite_level": request.form.get('prerequisite_level') or None
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
                    "price": float(request.form.get('price', 0)),
                    # TAMBAHAN BARU
                    "batch_id": request.form.get('batch_id'),
                    "prerequisite_level": request.form.get('prerequisite_level') or None
                }
                
                if image_id:
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

    # GET Request
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

@app.route('/admin/laporan')
@login_required
def admin_laporan():
    try:
        # Aggregate: Group by batch_id, count pendaftar, list siswa, dll.
        pipeline = [
            {"$group": {
                "_id": "$batch_id",
                "total_pendaftar": {"$sum": 1},
                "pending": {"$sum": {"$cond": [{"$eq": ["$status", "pending"]}, 1, 0]}},
                "completed": {"$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}},
                "siswa_list": {"$push": {
                    "nama": "$nama",
                    "email": "$email",
                    "level": "$level",
                    "status": "$status",
                    "tanggal": "$tanggal"
                }}
            }},
            {"$sort": {"_id": 1}}  # Sort by batch_id
        ]
        laporan = list(db.registrations.aggregate(pipeline))
        
        # Ambil info kelas per batch (misalnya total spot dari kelas terkait)
        for item in laporan:
            batch_id = item['_id']
            kelas = db.kelas.find_one({"batch_id": batch_id})
            if kelas:
                item['kelas_info'] = {
                    "level": kelas['level'],
                    "spots_total": 10,  # Asumsi max 10, atau ambil dari kelas['spots_available'] + terisi
                    "spots_terisi": item['total_pendaftar'],
                    "start_date": kelas['start_date']
                }
            else:
                item['kelas_info'] = {"level": "Tidak ditemukan", "spots_total": 0, "spots_terisi": 0}
        
    except Exception as e:
        print(f"Laporan error: {e}")
        flash("Gagal memuat laporan.", "error")
        laporan = []
    
    return render_template('admin_laporan.html', laporan=laporan)

@app.route('/admin/update_status', methods=['POST'])
@login_required
def admin_update_status():
    try:
        batch_id = request.form.get('batch_id')
        action = request.form.get('action')
        if action == 'complete_all':
            db.registrations.update_many(
                {"batch_id": batch_id},
                {"$set": {"status": "completed"}}
            )
            flash('Status semua siswa di batch ini diupdate ke Completed!', 'success')
    except Exception as e:
        print(f"Update status error: {e}")
        flash("Gagal update status.", "error")
    return redirect(url_for('admin_laporan'))

# Import tambahan di atas
import pandas as pd
from io import StringIO  # Untuk generate CSV in-memory

# Route baru untuk export
@app.route('/admin/export_laporan', methods=['GET'])
@login_required
def admin_export_laporan():
    try:
        # Ambil data laporan sama seperti di admin_laporan
        pipeline = [
            {"$group": {
                "_id": "$batch_id",
                "total_pendaftar": {"$sum": 1},
                "pending": {"$sum": {"$cond": [{"$eq": ["$status", "pending"]}, 1, 0]}},
                "completed": {"$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}},
                "siswa_list": {"$push": {
                    "nama": "$nama",
                    "email": "$email",
                    "level": "$level",
                    "status": "$status",
                    "tanggal": "$tanggal"
                }}
            }},
            {"$sort": {"_id": 1}}
        ]
        laporan = list(db.registrations.aggregate(pipeline))
        
        # Tambah info kelas seperti di admin_laporan
        for item in laporan:
            batch_id = item['_id']
            kelas = db.kelas.find_one({"batch_id": batch_id})
            if kelas:
                item['kelas_info'] = {
                    "level": kelas['level'],
                    "spots_total": 10,  # Asumsi, atau sesuaikan
                    "spots_terisi": item['total_pendaftar'],
                    "start_date": kelas['start_date']
                }
            else:
                item['kelas_info'] = {"level": "Tidak ditemukan", "spots_total": 0, "spots_terisi": 0}
        
        # Flatten data untuk CSV (buat list of dicts)
        flattened_data = []
        for item in laporan:
            kelas_info = item.get('kelas_info', {})
            row = {
                'Batch ID': item['_id'],
                'Total Pendaftar': item['total_pendaftar'],
                'Pending': item['pending'],
                'Completed': item['completed'],
                'Level Kelas': kelas_info.get('level', 'N/A'),
                'Spots Terisi/Total': f"{kelas_info.get('spots_terisi', 0)}/{kelas_info.get('spots_total', 0)}",
                'Tanggal Mulai': kelas_info.get('start_date', 'N/A')
            }
            # Tambah siswa list sebagai kolom terpisah jika perlu, tapi untuk sederhana, kita buat row per siswa
            for siswa in item['siswa_list']:
                siswa_row = row.copy()
                siswa_row.update({
                    'Nama Siswa': siswa['nama'],
                    'Email Siswa': siswa['email'],
                    'Level Siswa': siswa['level'],
                    'Status Siswa': siswa['status'],
                    'Tanggal Daftar': siswa['tanggal'].strftime('%Y-%m-%d')
                })
                flattened_data.append(siswa_row)
        
        # Generate CSV
        output = StringIO()
        df = pd.DataFrame(flattened_data)
        df.to_csv(output, index=False)
        output.seek(0)
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'laporan_pendaftaran_{datetime.now().strftime("%Y%m%d")}.csv'
        )
    except Exception as e:
        print(f"Export error: {e}")
        flash("Gagal export laporan.", "error")
        return redirect(url_for('admin_laporan'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)