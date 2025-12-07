from flask import Blueprint, render_template, request, session, redirect, url_for
from pymysql.cursors import DictCursor
from db import get_db

cari_bp = Blueprint('cari', __name__)

# ============================
# POST → proses pencarian
# ============================
@cari_bp.route('/cari', methods=['POST'])
def cari_post():
    import re
    query = request.form.get('query', '').strip()

    products = []
    product_error = None
    form_type = 'cari'

    # ============================
    # Validasi minimal
    # ============================
    if not query:
        product_error = "❌ Masukkan Prodcode, Barcode atau Nama Produk."
    else:
        db = get_db()
        cursor = db.cursor(DictCursor)

        try:
            # ambil angka saja
            clean = re.sub(r'\D', '', query)

            is_barcode = clean.isdigit() and len(clean) == 13
            is_prodcode = clean.isdigit() and len(clean) == 10

            # ================
            # BARCODE 13 DIGIT
            # ================
            if is_barcode:
                sql = """
                    SELECT * FROM all_product
                    WHERE barcode = %s
                    ORDER BY nama_produk ASC
                """
                cursor.execute(sql, (clean,))

            # ================
            # PROD CODE 10 DIGIT
            # ================
            elif is_prodcode:
                sql = """
                    SELECT * FROM all_product
                    WHERE REPLACE(prodcode, '-', '') = %s
                    ORDER BY nama_produk ASC
                """
                cursor.execute(sql, (clean,))

            # ================
            # NAMA PRODUK (1 kata, exact match)
            # ================
            else:
                sql = """
                    SELECT * FROM all_product
                    WHERE LOWER(nama_produk) REGEXP CONCAT('[[:<:]]', %s, '[[:>:]]')
                    ORDER BY nama_produk ASC
                """
                cursor.execute(sql, (query.lower(),))

            products = cursor.fetchall()

            if not products:
                product_error = "❌ Produk tidak ditemukan."

        except Exception as e:
            product_error = f"❌ Error: {str(e)}"

        finally:
            cursor.close()
            db.close()

    # simpan session
    session['products'] = products
    session['product_error'] = product_error
    session['form_type'] = form_type
    session['query'] = query

    return redirect(url_for('cari.cari_page'))

@cari_bp.route('/cari', methods=['GET'])
def cari_page():
    return render_template(
        'cari_produk.html',
        products=session.pop('products', []),
        product_error=session.pop('product_error', None),
        form_type=session.pop('form_type', 'cari'),
        query=session.pop('query', '')
    )
