# routes/tambah_produk.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import get_db

tambah_bp = Blueprint('tambah', __name__)

@tambah_bp.route('/tambah', methods=['GET', 'POST'])
def tambah_produk():
    if request.method == 'POST':
        kategori = request.form.get('kategori', '').strip()
        prodcode = request.form.get('prodcode', '').strip()
        barcode = request.form.get('barcode', '').strip()
        nama_produk = request.form.get('nama_produk', '').strip()

        if not nama_produk or not prodcode or not barcode:
            flash("⚠️ Nama Produk, ProdCode, dan Barcode wajib diisi!", 'danger')
            return redirect(url_for('tambah.tambah_produk'))

        db = get_db()
        cursor = db.cursor()

        try:
            # Cek apakah prodcode sudah ada
            cursor.execute("SELECT * FROM product_new WHERE prodcode=%s", (prodcode,))
            exists = cursor.fetchone()
            if exists:
                flash(f"⚠️ Produk dengan PROD CODE '{prodcode}' sudah ada di daftar sementara!", "warning")
            else:
                cursor.execute("""
                    INSERT INTO product_new (category, prodcode, barcode, nama_produk)
                    VALUES (%s, %s, %s, %s)
                """, (kategori, prodcode, barcode, nama_produk))
                db.commit()
                flash("✅ Produk berhasil disimpan!", "success")

        except Exception as e:
            db.rollback()
            flash(f"❌ Terjadi error saat menyimpan data: {e}", "danger")
        finally:
            cursor.close()
            db.close()

        return redirect(url_for('tambah.tambah_produk'))

    return render_template('tambah_produk.html')
