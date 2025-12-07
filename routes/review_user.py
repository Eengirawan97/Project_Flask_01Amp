from flask import Blueprint, render_template, redirect, url_for, flash, request
from db import get_db
from werkzeug.security import generate_password_hash
from routes.send_email import send_email
import os

review_user_bp = Blueprint('review_user', __name__)

# =============================
# Template Email
# =============================
ACCEPT_TEMPLATE = """
Halo {nama},

Selamat! Akun Anda telah berhasil diaktifkan oleh admin.

Berikut detail login Anda:
Username: {username}
Password: {password}

Keterangan dari admin: {keterangan}

Silakan login dan ubah password Anda segera. Terima kasih!

⚠️ Jangan membalas email ini.
"""

REJECT_TEMPLATE = """
Halo {nama},

Mohon maaf, permintaan pembuatan akun Anda belum disetujui.

Alasan: {keterangan}

Silakan hubungi admin jika ada pertanyaan atau klarifikasi lebih lanjut.

Terima kasih atas pengertiannya.

⚠️ Jangan membalas email ini.
"""

# =============================
# 1. TAMPILKAN USER PENDING
# =============================
@review_user_bp.route('/review_user')
def review_user():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT id, nama_toko, divisi, nama, no_hp, email, username, keterangan, created_at
        FROM data_user
        ORDER BY created_at DESC
    """)
    data = cursor.fetchall()
    return render_template('review_user.html', data=data)

# =============================
# 2. ACCEPT USER
# =============================
@review_user_bp.route('/accept_user/<int:id>', methods=["POST"])
def accept_user(id):
    db = get_db()
    cursor = db.cursor()

    # Ambil user pending
    cursor.execute("""
        SELECT username, password, nama, email, keterangan
        FROM data_user
        WHERE id = %s
    """, (id,))
    user = cursor.fetchone()

    if not user:
        flash("User tidak ditemukan!", "danger")
        return redirect(url_for('review_user.review_user'))

    username = user['username'] if isinstance(user, dict) else user[0]
    password = user['password'] if isinstance(user, dict) else user[1]
    nama     = user['nama']     if isinstance(user, dict) else user[2]
    email    = user['email']    if isinstance(user, dict) else user[3]
    keterangan = user['keterangan'] if isinstance(user, dict) else user[4]

    try:
        # Insert ke users (hanya kolom yang ada)
        cursor.execute("""
            INSERT INTO users (username, password, role, created_at)
            VALUES (%s, %s, 'user', NOW())
        """, (username, password))

        # Update keterangan di data_user
        cursor.execute("""
            UPDATE data_user
            SET keterangan = 'accepted'
            WHERE id = %s
        """, (id,))
        db.commit()

        # Kirim email
        email_body = ACCEPT_TEMPLATE.format(
            nama=nama,
            username=username,
            password=password,
            keterangan=keterangan or "Tidak ada keterangan tambahan"
        )
        if email and '@' in email:
            send_email(email, "Akun Anda Berhasil Diaktifkan", email_body)
            flash(f"User '{username}' berhasil di-ACCEPT dan email terkirim!", "success")
        else:
            flash("Email penerima tidak valid!", "danger")

    except Exception as e:
        db.rollback()
        flash("Terjadi kesalahan: " + str(e), "danger")

    return redirect(url_for('review_user.review_user'))

# =============================
# 3. REJECT USER (TIDAK DIHAPUS)
# =============================
@review_user_bp.route('/reject_user/<int:id>', methods=["POST"])
def reject_user(id):
    db = get_db()
    cursor = db.cursor()

    keterangan = request.form.get("keterangan", "").strip()
    if not keterangan:
        flash("Keterangan wajib diisi saat melakukan reject!", "danger")
        return redirect(url_for('review_user.review_user'))

    try:
        cursor.execute("""
            UPDATE data_user 
            SET keterangan = %s
            WHERE id = %s
        """, (keterangan, id))
        db.commit()

        cursor.execute("SELECT nama, email FROM data_user WHERE id = %s", (id,))
        result = cursor.fetchone()

        if result:
            if isinstance(result, dict):
                nama = result['nama']
                email = result['email']
            else:
                nama, email = result

            email_body = REJECT_TEMPLATE.format(nama=nama, keterangan=keterangan)

            if email and '@' in email:
                send_email(email, "Permintaan Akun Anda Ditolak", email_body)
                flash("User berhasil di-REJECT dan email terkirim!", "warning")
            else:
                flash("Email penerima tidak valid!", "danger")

    except Exception as e:
        db.rollback()
        flash("Gagal melakukan reject! Error: " + str(e), "danger")

    return redirect(url_for('review_user.review_user'))
