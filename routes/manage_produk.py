from flask import Blueprint, render_template, session, redirect, url_for, flash

manage_bp = Blueprint('manage', __name__)

@manage_bp.route('/manage_produk')
def manage_produk():
    # Pastikan user login dan role admin
    role = session.get('role')
    if role != 'admin':
        flash("Akses ditolak. Hanya admin yang dapat mengakses.", "danger")
        return redirect(url_for('index_menu'))

    return render_template('manage_produk.html')
