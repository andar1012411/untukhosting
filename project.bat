@echo off
echo ==============================
echo 🚀 Menjalankan Proyek Flask + Tailwind
echo ==============================

REM --- Aktifkan environment Python ---
call venv\Scripts\activate

REM --- Jalankan Tailwind (watch mode) ---
echo 🔧 Menjalankan Tailwind CSS Compiler...
start cmd /k "npx tailwindcss -i ./static/css/input.css -o ./static/css/output.css --watch"

REM --- Jalankan server Flask ---
echo Menjalankan Flask server...
python app.py

pause
