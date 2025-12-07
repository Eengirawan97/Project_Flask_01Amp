from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash
from db import get_db

buat_akun_bp = Blueprint('buat_akun', __name__)

@buat_akun_bp.route('/buat_akun', methods=['GET', 'POST'])
def buat_akun():
    db = get_db()
    cursor = db.cursor()

    if request.method == 'POST':
        nama_toko = request.form.get('nama_toko', '').strip()
        divisi = request.form.get('divisi', '').strip()
        nama = request.form.get('nama', '').strip()
        no_hp = request.form.get('no_hp', '').strip()
        email = request.form.get('email', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        # ============================
        # VALIDASI
        # ============================
        if not nama_toko or not divisi or not nama or not no_hp or not email or not username or not password:
            flash("Semua kolom wajib diisi!", "danger")
            return redirect(url_for('buat_akun.buat_akun'))

        # Cek username di data_user (pending)
        cursor.execute("SELECT id FROM data_user WHERE username = %s", (username,))
        if cursor.fetchone():
            flash("Username sudah terdaftar dan menunggu persetujuan admin!", "warning")
            return redirect(url_for('buat_akun.buat_akun'))

        # Cek username di users (aktif)
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            flash("Username sudah digunakan oleh user aktif!", "warning")
            return redirect(url_for('buat_akun.buat_akun'))

        # ============================
        # SIMPAN DATA KE data_user
        # ============================
        hashed_pw = generate_password_hash(password)

        try:
            cursor.execute("""
                INSERT INTO data_user 
                (nama_toko, divisi, nama, no_hp, email, username, password, keterangan, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NULL, NOW())
            """, (nama_toko, divisi, nama, no_hp, email, username, hashed_pw))

            db.commit()

        except Exception as e:
            db.rollback()
            flash("Gagal menyimpan data! Error: " + str(e), "danger")
            return redirect(url_for('buat_akun.buat_akun'))

        flash("Pendaftaran berhasil! Menunggu persetujuan admin.", "success")
        return redirect(url_for('buat_akun.buat_akun'))

    # GET
    return render_template('buat_akun.html')
