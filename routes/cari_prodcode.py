from flask import Blueprint, render_template, request, session, redirect, url_for
from pymysql.cursors import DictCursor
from db import get_db

cari_produk_bp = Blueprint('cari_prodcode', __name__)

@cari_produk_bp.route('/cari-prodcode', methods=['POST'])
def cari_prodcode():
    products = []
    product_error = None
    form_type = 'prodcode'

    prodcode_input = request.form.get('prodcode_search','').strip()
    if not prodcode_input:
        product_error = "❌ Prodcode tidak boleh kosong."
    else:
        clean_prod = prodcode_input.replace('-','')
        if len(clean_prod) < 10:
            clean_prod = clean_prod.ljust(10,'0')
        elif len(clean_prod) > 10:
            product_error = "❌ Prodcode tidak boleh lebih dari 10 digit."
            session['products'] = []
            session['product_error'] = product_error
            session['form_type'] = form_type
            return redirect(url_for('cari_prodcode.cari_prodcode_page'))

        db = get_db()
        cursor = db.cursor(DictCursor)
        try:
            sql = "SELECT * FROM all_product WHERE REPLACE(prodcode,'-','') = %s"
            cursor.execute(sql, (clean_prod,))
            result = cursor.fetchall()
            if result:
                products = result
            else:
                product_error = "❌ Produk tidak ditemukan."
        except Exception as e:
            product_error = f"❌ Error: {str(e)}"
        finally:
            cursor.close()
            db.close()

    # simpan hasil sementara di session
    session['products'] = products
    session['product_error'] = product_error
    session['form_type'] = form_type

    # redirect ke GET untuk menampilkan hasil
    return redirect(url_for('cari_prodcode.cari_prodcode_page'))


# GET → tampilkan form + hasil (bisa di-refresh tanpa error 405)
@cari_produk_bp.route('/cari-prodcode', methods=['GET'])
def cari_prodcode_page():
    products = session.pop('products', [])
    product_error = session.pop('product_error', None)
    form_type = session.pop('form_type', 'prodcode')
    return render_template('cari.html', products=products, product_error=product_error, form_type=form_type)