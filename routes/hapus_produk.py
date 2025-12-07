from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import get_db
import re
import pymysql.cursors

hapus_bp = Blueprint('hapus', __name__, template_folder='../templates')

@hapus_bp.route('/hapus_produk', methods=['GET', 'POST'])
def hapus_produk():
    import re

    products = []
    query = ''
    no_results = False

    db = get_db()
    cursor = db.cursor(pymysql.cursors.DictCursor)

    try:
        # ===== HANDLE DELETE =====
        if request.method == 'POST' and request.form.get('action') == 'delete':
            prodcode_to_delete = request.form.get('prodcode')
            if prodcode_to_delete:
                cursor.execute("DELETE FROM all_product WHERE prodcode = %s",
                               (prodcode_to_delete,))
                db.commit()
                flash(f"Produk '{prodcode_to_delete}' berhasil dihapus.", "success")
                return redirect(url_for('hapus.hapus_produk'))

        # ===== HANDLE SEARCH =====
        query = request.form.get('query', '').strip() if request.method == 'POST' else ''

        if query:

            # ambil angka saja
            query_digits = re.sub(r'\D', '', query)

            is_13_digit_barcode = query_digits.isdigit() and len(query_digits) == 13
            is_10_digit_prodcode = query_digits.isdigit() and len(query_digits) == 10

            if is_13_digit_barcode:
                # EXACT barcode
                sql = """
                    SELECT * FROM all_product
                    WHERE barcode = %s
                    ORDER BY nama_produk ASC
                """
                cursor.execute(sql, (query_digits,))

            elif is_10_digit_prodcode:
                # EXACT prodcode
                sql = """
                    SELECT * FROM all_product
                    WHERE REPLACE(prodcode, '-', '') = %s
                    ORDER BY nama_produk ASC
                """
                cursor.execute(sql, (query_digits,))

            else:
                # NAMA PRODUK (exact word)
                sql = """
                    SELECT * FROM all_product
                    WHERE LOWER(nama_produk) REGEXP CONCAT('[[:<:]]', %s, '[[:>:]]')
                    ORDER BY nama_produk ASC
                """
                cursor.execute(sql, (query.lower(),))

            products = cursor.fetchall()
            if not products:
                no_results = True

        else:
            products = []

    except Exception as e:
        flash(f"Terjadi error: {str(e)}", "danger")

    finally:
        cursor.close()
        db.close()

    return render_template(
        'hapus_produk.html',
        products=products,
        query=query,
        no_results=no_results
    )


