from flask import Blueprint, render_template
from db import get_db
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
def dashboard():
    total_produk = 0
    produk_expired = 0
    produk_early = 0
    produk_tambah = 0

    today = datetime.today().date()
    early_threshold = today + timedelta(days=30)

    db = get_db()
    cursor = db.cursor()

    # ============================
    # 1. Ambil result_validitas
    # ============================
    try:
        cursor.execute("SELECT BARCODE, nama_produk, EXPIRED FROM result_validitas")
        validitas_rows = cursor.fetchall()
    except Exception as e:
        print("Error result_validitas =", e)
        validitas_rows = []

    # ============================
    # 2. Ambil result_expired
    # ============================
    try:
        cursor.execute("SELECT Barcode, `Nama Produk`, Expired FROM result_expired")
        expired_rows = cursor.fetchall()
    except Exception as e:
        print("Error result_expired =", e)
        expired_rows = []

    # ============================
    # 3. Ambil product_new
    # ============================
    try:
        cursor.execute("SELECT * FROM product_new")
        tambah_rows = cursor.fetchall()
        produk_tambah = len(tambah_rows)
    except Exception as e:
        print("Error product_new =", e)
        produk_tambah = 0

    # ============================
    # 4. Proses merging validitas + expired
    # ============================
    produk_dict = {}
    produk_nama = {}

    combined_rows = (validitas_rows or []) + (expired_rows or [])

    for row in combined_rows:
        barcode = row.get('BARCODE') or row.get('Barcode')
        nama_produk = row.get('nama_produk') or row.get('Nama Produk') or "Unknown"
        expired_raw = row.get('EXPIRED') or row.get('Expired')

        if not barcode or not expired_raw:
            continue

        dt = None
        s = str(expired_raw).strip()

        if s in ("0000-00-00", "", None):
            continue

        # format tanggal fleksibel
        formats = [
            "%Y-%m-%d", "%d%m%y", "%d-%m-%Y", "%Y%m%d",
            "%Y/%m/%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(s, fmt).date()
                break
            except:
                continue

        if not dt:
            continue

        # Ambil expired terbaru untuk barcode
        if barcode not in produk_dict or dt > produk_dict[barcode]:
            produk_dict[barcode] = dt
            produk_nama[barcode] = nama_produk

    # ============================
    # 5. Hitung expired & early expired
    # ============================
    expired_list = []
    early_expired_list = []

    total_produk = len(produk_dict)

    for barcode, dt in produk_dict.items():
        if dt < today:
            produk_expired += 1
            expired_list.append({
                "barcode": barcode,
                "nama_produk": produk_nama.get(barcode, "Unknown"),
                "expired": dt.strftime("%Y-%m-%d")
            })

        elif today <= dt <= early_threshold:
            produk_early += 1
            early_expired_list.append({
                "barcode": barcode,
                "nama_produk": produk_nama.get(barcode, "Unknown"),
                "expired": dt.strftime("%Y-%m-%d")
            })

    cursor.close()
    db.close()

    # ============================
    # 6. Final summary
    # ============================
    summary = {
        "total_produk": total_produk,
        "produk_expired": produk_expired,
        "produk_valid": produk_early,
        "produk_tambah": produk_tambah
    }

    return render_template(
        'dashboard.html',
        summary=summary,
        early_expired=early_expired_list,
        expired_list=expired_list
    )

