from flask import Blueprint, render_template, request, session, redirect, url_for
from pymysql.cursors import DictCursor
from db import get_db

cari_keyword_bp = Blueprint('cari_keyword', __name__)

# POST → proses form, simpan hasil di session, lalu redirect
@cari_keyword_bp.route('/cari-keyword', methods=['POST'])
def cari_keyword_post():
    products = []
    product_error = None
    form_type = 'keyword'

    keyword_input = request.form.get('keyword_search','').strip()
    if not keyword_input:
        product_error = "❌ Barcode / Nama Produk tidak boleh kosong."
    else:
        db = get_db()
        cursor = db.cursor(DictCursor)
        try:
            sql = "SELECT * FROM all_product WHERE barcode LIKE %s OR nama_produk LIKE %s"
            like_kw = f"%{keyword_input}%"
            cursor.execute(sql, (like_kw, like_kw))
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

    # redirect ke GET (endpoint harus sesuai nama Blueprint)
    return redirect(url_for('cari_keyword.cari_keyword_page'))


# GET → tampilkan form + hasil (aman di refresh)
@cari_keyword_bp.route('/cari-keyword', methods=['GET'])
def cari_keyword_page():
    products = session.pop('products', [])
    product_error = session.pop('product_error', None)
    form_type = session.pop('form_type', 'keyword')
    return render_template('cari.html', products=products, product_error=product_error, form_type=form_type)
