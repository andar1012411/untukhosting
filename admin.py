# create_admin.py
import bcrypt
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv('MONGO_URI'))
db = client['genkan_institute']

username = "admin"
password = "genkan2025"  # Ganti!

# JANGAN DECODE! Simpan sebagai BYTES
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

db.admins.insert_one({
    "username": username,
    "password": hashed  # Simpan bytes, bukan str(hashed)
})

print(f"Admin '{username}' berhasil dibuat!")
print("Password hash disimpan sebagai BYTES (benar).")