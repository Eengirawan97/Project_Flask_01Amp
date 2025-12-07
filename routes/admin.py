from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash
import os
import pandas as pd
from sqlalchemy import create_engine, text

# --- MySQL Config ---
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'monitoring_produk_eeng'
}

# Buat engine MySQL
engine = create_engine(
    f"mysql+pymysql://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}@{MYSQL_CONFIG['host']}/{MYSQL_CONFIG['database']}"
)

admin_bp = Blueprint('admin', __name__)
PASSWORD_SAKTI = os.getenv('PASSWORD_SAKTI', '33ngamp123!')

@admin_bp.route('/reset_user', methods=['GET', 'POST'])
def reset_user():
    if request.method == 'POST':
        master_password = request.form.get('master_password', '').strip()
        user_id = request.form.get('user_id', '').strip()
        new_username = request.form.get('new_username', '').strip()
        new_password = request.form.get('new_password', '').strip()

        if master_password != PASSWORD_SAKTI:
            flash("Password sakti salah!", "danger")
            return redirect(url_for('admin.reset_user'))

        if not all([user_id, new_username, new_password]):
            flash("Semua kolom wajib diisi!", "warning")
            return redirect(url_for('admin.reset_user'))

        try:
            hashed_password = generate_password_hash(new_password)
            with engine.begin() as conn:
                conn.execute(
                    text("UPDATE users SET username=:username, password=:password WHERE id=:id"),
                    {"username": new_username, "password": hashed_password, "id": user_id}
                )
            flash(f"User ID {user_id} berhasil direset.", "success")
        except Exception as e:
            flash(f"Gagal reset user: {e}", "danger")

        return redirect(url_for('admin.reset_user'))

    # GET: ambil daftar user
    try:
        df_users = pd.read_sql("SELECT id, username, role FROM users", engine)
        users = df_users.to_dict(orient='records')
    except Exception as e:
        flash(f"Gagal mengambil daftar user: {e}", "danger")
        users = []

    return render_template("reset_user.html", users=users)
