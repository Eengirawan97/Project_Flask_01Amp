from flask import Blueprint, render_template, request, flash, redirect, url_for
from db import get_db

delete_user_bp = Blueprint('delete_user', __name__, template_folder='templates')

@delete_user_bp.route('/delete_user', methods=["GET", "POST"])
def delete_user():
    db = get_db()
    cur = db.cursor()
    
    if request.method == "POST":
        username = request.form.get("username")
        if username:
            # Hapus dari data_user
            cur.execute("DELETE FROM data_user WHERE username=%s", (username,))
            # Hapus dari users
            cur.execute("DELETE FROM users WHERE username=%s", (username,))
            db.commit()
            flash(f"User {username} berhasil dihapus.", "success")
        return redirect(url_for("delete_user.delete_user"))

    # GET -> tampilkan semua user
    cur.execute("SELECT * FROM data_user ORDER BY id DESC")
    users = cur.fetchall()
    cur.close()
    db.close()

    return render_template("delete_user.html", users=users)
