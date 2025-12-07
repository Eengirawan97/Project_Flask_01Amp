# routes/validitas.py
from flask import Blueprint, render_template, request
import pandas as pd
from datetime import datetime
import logging
import mysql.connector
from mysql.connector import Error
from oauth2client.service_account import ServiceAccountCredentials
import gspread

validitas_bp = Blueprint('validitas', __name__)

# --- MySQL Config ---
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'monitoring_produk_eeng'
}

# --- Google Sheets ---
GOOGLE_CREDENTIALS_FILE = 'flaskexpiredprojecteeng-63cbf1a35088.json'
SPREADSHEET_ID = '1zjzTLXve-UUWIZEbTO09e4PA-2EjAwXZdLMi4B2LPYM'

logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def get_gsheet_client():
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            GOOGLE_CREDENTIALS_FILE, scope
        )
        return gspread.authorize(credentials)
    except Exception as e:
        logger.error(f"❌ Gagal koneksi Google Sheets: {e}")
        return None


# ======================================================================
#                            ROUTE VALIDITAS
# ======================================================================
@validitas_bp.route('/input', methods=['GET', 'POST'])
def input_page():
    selected_product = {'category': '', 'prodcode': '', 'barcode': '', 'nama_produk': ''}
    message = ''
    message_type = ''  
    search_barcode = ''

    # -------------------------------------------------------------
    # LOAD ALL PRODUCT
    # -------------------------------------------------------------
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        df_data = pd.read_sql(
            "SELECT id, category, prodcode, barcode, nama_produk FROM all_product",
            conn
        )
        conn.close()

        df_data['barcode'] = df_data['barcode'].astype(str).str.strip()
        df_data['barcode_norm'] = df_data['barcode'].str.lstrip('0')

    except Error as e:
        logger.error(f"❌ ERROR READ DB: {e}")
        df_data = pd.DataFrame(columns=['category', 'prodcode', 'barcode', 'nama_produk'])

    # -------------------------------------------------------------
    # POST ACTIONS
    # -------------------------------------------------------------
    if request.method == 'POST':
        action = request.form.get('action')

        # =========================================================
        # SEARCH PRODUK
        # =========================================================
        if action == 'search':
            barcode_input = request.form.get('barcode_input', '').strip()
            search_barcode = barcode_input
            barcode_norm = barcode_input.lstrip('0')

            df_match = df_data[
                (df_data['barcode'] == barcode_input) |
                (df_data['barcode_norm'] == barcode_norm)
            ]

            if not df_match.empty:
                row = df_match.iloc[0]
                selected_product = {
                    'category': row['category'],
                    'prodcode': row['prodcode'],
                    'barcode': row['barcode'],
                    'nama_produk': row['nama_produk']
                }
            else:
                message = f"❌Produk {barcode_input} tidak ditemukan."
                message_type = "error"

        # =========================================================
        # SAVE DATA
        # =========================================================
        elif action == 'save':
            kategori = request.form.get('kategori', '').strip()
            prodcode = request.form.get('prodcode', '').strip()
            barcode = request.form.get('barcode', '').strip()
            barcode = barcode.zfill(13)
            nama_produk = request.form.get('nama_produk', '').strip()
            expired_input = request.form.get('expired', '').strip()
            izin_edar = request.form.get('izin_edar', '').strip()
            no_gang = request.form.get('no_gang', '').strip()
            tanggal = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # -------------------------------------------------------------
            # PARSING EXPIRED DATE
            # -------------------------------------------------------------
            expired_date = None
            if expired_input:
                s = expired_input.replace(' ', '').strip()
                formats = ["%d%m%y", "%Y-%m-%d", "%d-%m-%Y", "%Y%m%d"]
                for fmt in formats:
                    try:
                        expired_date = datetime.strptime(s, fmt).date()
                        break
                    except ValueError:
                        continue

            expired_db = expired_date.strftime("%Y-%m-%d") if expired_date else None

            # -------------------------------------------------------------
            # SAVE KE MYSQL
            # -------------------------------------------------------------
            try:
                conn = mysql.connector.connect(**MYSQL_CONFIG)
                cursor = conn.cursor()

                insert_query = """
                    INSERT INTO result_validitas
                    (CATEGORY, prod_code, BARCODE, nama_produk, EXPIRED, `IZIN EDAR`, entry_date, nomor_gang)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """

                cursor.execute(insert_query, (
                    kategori, prodcode, barcode, nama_produk,
                    expired_db, izin_edar, tanggal, no_gang
                ))

                conn.commit()
                cursor.close()
                conn.close()

                message = "✅Berhasil simpan ke database"
                message_type = "success"

                # -------------------------------------------------------------
                # SAVE GOOGLE SHEETS
                # -------------------------------------------------------------
                data_row = [
                    kategori, prodcode, barcode, nama_produk,
                    expired_db, izin_edar, tanggal, no_gang
                ]

                gc = get_gsheet_client()
                if gc:
                    try:
                        sh = gc.open_by_key(SPREADSHEET_ID)
                        sh.sheet1.append_row(data_row)

                        # TAMBAHKAN LINK LANGSUNG
                        gs_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}"
                        message += f' & (<a href="{gs_url}" target="_blank">Google Spreadsheet</a>)'

                    except Exception as e:
                        message += f" ❗ Google Sheets error ({e})"

            except Error as e:
                message = f"❌ Gagal simpan ke database: {e}"
                message_type = "error"

    return render_template(
        'validitas.html',
        selected_product=selected_product,
        message=message,
        message_type=message_type,
        search_barcode=search_barcode,
        gsheet_url=f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}"
    )
