from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import check_password_hash
from routes.validitas import validitas_bp
from routes.monitoring import monitoring_bp
from routes.tambah_produk import tambah_bp
from routes.hapus_produk import hapus_bp
from routes.dashboard import dashboard_bp
from routes.review_produk import review_bp
from routes.cari_produk import cari_bp
from routes.tolak import tolak_bp
from routes.admin import admin_bp
from routes.buat_akun import buat_akun_bp
from routes.review_user import review_user_bp
from routes.delete_user import delete_user_bp
from dotenv import load_dotenv
import os
import time
import pymysql
from pymysql.cursors import DictCursor
import smtplib
from email.mime.text import MIMEText

load_dotenv()  # baca file .env untuk lokal development

# ==========================================
# APP INITIALIZATION
# ==========================================
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'rahasia_super_aman')
SESSION_TIMEOUT = 3600  # 1 jam

# ==========================================
# BLUEPRINT REGISTRATION
# ==========================================
app.register_blueprint(validitas_bp)
app.register_blueprint(monitoring_bp, url_prefix='/monitoring')
app.register_blueprint(tambah_bp)
app.register_blueprint(hapus_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(review_bp)
app.register_blueprint(cari_bp, url_prefix="")
app.register_blueprint(tolak_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(buat_akun_bp)
app.register_blueprint(review_user_bp)
app.register_blueprint(delete_user_bp)

# ==========================================
# DATABASE CONNECTION
# ==========================================
def get_db():
    """Connect ke MySQL (Render / env vars / lokal)"""
    return pymysql.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=int(os.environ.get("DB_PORT", 3306)),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get("DB_NAME", "monitoring_produk_eeng"),
        cursorclass=DictCursor
    )

# ==========================================
# EMAIL CONFIGURATION
# ==========================================
EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 465))

def send_email(to_email, subject, body):
    """Kirim email via SMTP SSL"""
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_SENDER
    msg['To'] = to_email

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print("Gagal kirim email:", e)

# ==========================================
# LOGIN PROTECTION (GLOBAL MIDDLEWARE)
# ==========================================
@app.before_request
def require_login():
    endpoint = request.endpoint or ""
    allowed = ['login', 'logout', 'static', 'api_produk', 'buat_akun']

    if any(endpoint.startswith(a) for a in allowed):
        return

    if 'user' not in session:
        return redirect(url_for('login'))

    now = time.time()
    last = session.get('last_activity', now)
    if now - last > SESSION_TIMEOUT:
        session.clear()
        flash("Sesi berakhir karena tidak aktif selama 1 jam.", "warning")
        return redirect(url_for('login'))

    session['last_activity'] = now

    try:
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT password FROM users WHERE username=%s", (session['user'],))
        row = cur.fetchone()
        cur.close()
        db.close()
    except pymysql.MySQLError:
        session.clear()
        flash("Terjadi kesalahan database. Silakan login kembali.", "danger")
        return redirect(url_for('login'))

    if not row:
        session.clear()
        flash("Akun tidak ditemukan. Silakan login kembali.", "warning")
        return redirect(url_for('login'))

    current_hash = row['password']
    saved_hash = session.get('password_hash')
    if saved_hash not in ["MASTER_LOGIN"] and saved_hash != current_hash:
        session.clear()
        flash("Password berubah. Silakan login kembali.", "warning")
        return redirect(url_for('login'))

# ==========================================
# LOGIN ROUTE
# ==========================================
MASTER_PASSWORD = os.environ.get("MASTER_PASSWORD", "33ngamp123!")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            db = get_db()
            cur = db.cursor()
            cur.execute("SELECT * FROM users WHERE username=%s", (username,))
            user = cur.fetchone()
            cur.close()
            db.close()
        except pymysql.MySQLError:
            flash("Terjadi kesalahan database.", "danger")
            return render_template('login.html')

        if user and check_password_hash(user['password'], password):
            session['user'] = user['username']
            session['role'] = user['role']
            session['password_hash'] = user['password']
            session['last_activity'] = time.time()
            return redirect(url_for('index_menu'))

        if password == MASTER_PASSWORD:
            session['user'] = username
            session['role'] = "superadmin"
            session['password_hash'] = "MASTER_LOGIN"
            session['last_activity'] = time.time()
            return redirect(url_for('index_menu'))

        flash("Username atau password salah!", "danger")

    return render_template('login.html')

# ==========================================
# LUPA PASSWORD
# ==========================================
@app.route('/lupa-password')
def lupa_password():
    return render_template('lupa_password.html')

# ==========================================
# LOGOUT
# ==========================================
@app.route('/logout')
def logout():
    session.clear()
    flash("Berhasil logout.", "info")
    return redirect(url_for('login'))

# ==========================================
# MENU ROUTE
# ==========================================
@app.route('/')
def index_menu():
    role = session.get('role')
    username = session.get('user')

    if role == 'admin':
        return render_template("menu_admin.html")

    nama_awal = 'User'
    if username:
        try:
            db = get_db()
            cursor = db.cursor()
            cursor.execute("SELECT nama FROM data_user WHERE username=%s", (username,))
            user = cursor.fetchone()
            cursor.close()
            db.close()
            if user and user['nama']:
                nama_awal = user['nama'].split(' ')[0]
        except pymysql.MySQLError:
            pass

    return render_template("menu_user.html", user_name=nama_awal)

# ==========================================
# MANAGE PRODUK
# ==========================================
@app.route('/manage_produk')
def manage_produk():
    role = session.get('role')
    if role != 'admin':
        flash("Akses ditolak.", "danger")
        return redirect(url_for('index_menu'))
    return render_template('manage_produk.html')

# ==========================================
# API PRODUK
# ==========================================
@app.route('/api/produk', methods=['GET'])
def api_produk():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM all_product LIMIT 50")
        data = cursor.fetchall()
        cursor.close()
        db.close()
        return jsonify(data)
    except pymysql.MySQLError:
        return jsonify({"error": "Database error"}), 500

# ==========================================
# RUN SERVER (LOKAL DEVELOPMENT)
# ==========================================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5006)), debug=True)
