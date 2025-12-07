# routes/tolak.py
from flask import Blueprint, render_template, session, redirect, url_for
from db import get_db  # gunakan db.py

tolak_bp = Blueprint('tolak', __name__, template_folder='../templates')

@tolak_bp.route('/tolak')
def tolak():
    # Pastikan user login
    if not session.get('user'):
        return redirect(url_for('login'))  # arahkan ke halaman login jika belum login

    # Ambil data produk dari tabel product_reject
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT category, prodcode, barcode, nama_produk, keterangan
        FROM product_reject
        ORDER BY id DESC
    """)
    rejected_products = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('tolak.html', rejected_products=rejected_products)
