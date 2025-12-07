# routes/review_produk.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from db import get_db

review_bp = Blueprint('review', __name__)

@review_bp.route('/review', methods=['GET', 'POST'])
def review_produk():
    if session.get('user') != 'eeng':
        flash("Hanya admin bisa akses Review Produk", 'danger')
        return redirect(url_for('index_menu'))

    db = get_db()
    cursor = db.cursor()

    try:
        if request.method == 'POST':
            try:
                row_id = int(request.form.get('row_id', -1))
            except ValueError:
                flash("ID produk tidak valid.", "danger")
                return redirect(url_for('review.review_produk'))

            action = request.form.get('action')  # accept atau reject
            cursor.execute("SELECT * FROM product_new ORDER BY id ASC")
            temp_rows = cursor.fetchall()

            if not (0 <= row_id < len(temp_rows)):
                flash("ID produk tidak valid.", "danger")
                return redirect(url_for('review.review_produk'))

            row_data = temp_rows[row_id]

            # ==========================
            #     ACCEPT PRODUK
            # ==========================
            if action == "accept":

                # Cek apakah prodcode sudah ada di all_product
                cursor.execute("SELECT * FROM all_product WHERE prodcode=%s", (row_data['prodcode'],))
                exists = cursor.fetchone()

                if exists:
                    # Jika sudah ada → batalkan, beri peringatan
                    flash(
                        f"⚠️ Produk dengan Prod Code {row_data['prodcode']} sudah ada! Tidak dapat diterima.",
                        "warning"
                    )
                    return redirect(url_for('review.review_produk'))

                # Jika aman → masukkan ke all_product
                cursor.execute("""
                    INSERT INTO all_product (category, prodcode, barcode, nama_produk)
                    VALUES (%s, %s, %s, %s)
                """, (
                    row_data['category'],
                    row_data['prodcode'],
                    row_data['barcode'],
                    row_data['nama_produk']
                ))

                # Masukkan ke product_reject sebagai catatan "Diterima"
                cursor.execute("""
                    INSERT INTO product_reject (category, prodcode, barcode, nama_produk, keterangan)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    row_data['category'],
                    row_data['prodcode'],
                    row_data['barcode'],
                    row_data['nama_produk'],
                    "Diterima"
                ))

                # Hapus dari product_new
                cursor.execute("DELETE FROM product_new WHERE id=%s", (row_data['id'],))
                db.commit()

                flash(f"✅ Produk '{row_data['nama_produk']}' berhasil diterima!", "success")
                return redirect(url_for('review.review_produk'))

            # ==========================
            #     REJECT PRODUK
            # ==========================
            elif action == "reject":
                keterangan = request.form.get('keterangan', '')

                cursor.execute("""
                    INSERT INTO product_reject (category, prodcode, barcode, nama_produk, keterangan)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    row_data['category'],
                    row_data['prodcode'],
                    row_data['barcode'],
                    row_data['nama_produk'],
                    keterangan
                ))

                cursor.execute("DELETE FROM product_new WHERE id=%s", (row_data['id'],))
                db.commit()

                flash(
                    f"❌ Produk '{row_data['nama_produk']}' ditolak dan disimpan ke daftar produk ditolak!",
                    "danger"
                )

                return redirect(url_for('review.review_produk'))

        # GET request: tampilkan semua produk baru
        cursor.execute("SELECT * FROM product_new ORDER BY id ASC")
        product_new = cursor.fetchall()

    except Exception as e:
        flash(f"Terjadi error: {str(e)}", "danger")
        product_new = []

    finally:
        cursor.close()
        db.close()

    return render_template('review_produk.html', all_product=product_new)
