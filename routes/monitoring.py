from flask import Blueprint, render_template, request, jsonify, send_file
import pandas as pd
from datetime import datetime, date
from io import BytesIO
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,KeepInFrame, PageBreak)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER
from datetime import datetime
from sqlalchemy import create_engine, text

# ==========================================================
#  Blueprint
# ==========================================================
monitoring_bp = Blueprint('monitoring', __name__)  

from sqlalchemy import create_engine

# --- MySQL Config ---
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'monitoring_produk_eeng'
}

# Buat SQLAlchemy engine menggunakan config di atas
engine = create_engine(
    f"mysql+pymysql://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}@{MYSQL_CONFIG['host']}/{MYSQL_CONFIG['database']}"
)

# ==========================================================
#  Menu Monitoring
# ==========================================================
@monitoring_bp.route('/menu')
def monitoring_menu():
    return render_template('monitoring_menu.html')


# ==========================================================
#  Fungsi Bantuan
# ==========================================================
def title_name(text):
    """Capitalize setiap kata yang dipisah tanda '-' """
    return ' - '.join([w.capitalize() for w in text.strip().split(' - ')]) if text else ''


# ==========================================================
#  Input Expired
# ==========================================================
@monitoring_bp.route('/expired', methods=['GET', 'POST'])
def expired_input():
    message, error, invalid_rows = None, None, []

    # Load existing result_expired
    try:
        df = pd.read_sql("SELECT * FROM result_expired", engine)
    except Exception:
        df = pd.DataFrame(columns=[
            'id', 'No', 'Prodcode', 'Barcode', 'Nama Produk',
            'Expired', 'Petugas', 'Posisi', 'No Gang', 'Entry Date'
        ])

    if request.method == 'POST':
        has_error = False

        for i in range(1, 6):
            barcode = request.form.get(f'barcode_{i}')
            expired = request.form.get(f'expired_{i}')
            prodcode = request.form.get(f'prodcode_{i}')
            nama_produk = request.form.get(f'nama_produk_{i}')
            petugas_input = request.form.get('petugas')
            posisi_input = request.form.get('posisi')
            gang = request.form.get('gang')

            if barcode and prodcode:

                # --------------------------------------------------
                # PARSING EXPIRED DATE
                # --------------------------------------------------
                expired_date = None
                if expired:
                    s = expired.replace(' ', '').strip()
                    formats = ["%d%m%y", "%d-%m-%y", "%d-%m-%Y", "%Y-%m-%d", "%y%m%d"]
                    for fmt in formats:
                        try:
                            expired_date = datetime.strptime(s, fmt).date()
                            break
                        except ValueError:
                            continue

                if not expired_date:
                    invalid_rows.append(i)
                    has_error = True
                    continue

                expired_db = expired_date.strftime("%Y-%m-%d")
                petugas = title_name(petugas_input)
                posisi = title_name(posisi_input)
                gang_normalized = str(gang).strip().zfill(2)

                next_no = len(df) + 1

                try:
                    with engine.begin() as conn:
                        conn.execute(
                            text("""
                                INSERT INTO result_expired
                                (`Prodcode`, `Barcode`, `Nama Produk`,
                                 `Expired`, `Petugas`, `Posisi`, `No Gang`, `Entry Date`)
                                VALUES (:prodcode, :barcode, :nama_produk,
                                        :expired, :petugas, :posisi, :no_gang, :entry_date)
                            """),
                            {
                                'prodcode': prodcode,
                                'barcode': barcode,
                                'nama_produk': nama_produk,
                                'expired': expired_db,          # simpan format YYYY-MM-DD
                                'petugas': petugas,
                                'posisi': posisi,
                                'no_gang': gang_normalized,
                                'entry_date': datetime.now()
                            }
                        )

                    # Tambahkan ke DataFrame
                    df = pd.concat([df, pd.DataFrame([{
                        'Prodcode': prodcode,
                        'Barcode': barcode,
                        'Nama Produk': nama_produk,
                        'Expired': expired_db,
                        'Petugas': petugas,
                        'Posisi': posisi,
                        'No Gang': gang_normalized,
                        'Entry Date': datetime.now()
                    }])], ignore_index=True)

                except Exception as e:
                    print("DB Insert Error:", e)
                    error = f"Terjadi kesalahan saat menyimpan ke DB: {str(e)}"
                    has_error = True

        if has_error and not error:
            error = f"Kolom Expired harus valid! Periksa baris: {', '.join(map(str, invalid_rows))}"
        elif not has_error:
            message = "Data berhasil disimpan ke database!"

    return render_template('expired.html', message=message, error=error, invalid_rows=invalid_rows)

# ==========================================================
#  Lookup Barcode
# ==========================================================
@monitoring_bp.route('/lookup_barcode/<barcode>')
def lookup_barcode(barcode):
    try:
        df = pd.read_sql("SELECT * FROM all_product", engine)
        df['barcode'] = df['barcode'].str.strip()
        barcode = barcode.strip()

        row = df[df['barcode'] == barcode]

        if not row.empty:
            row = row.iloc[0]
            return jsonify({
                'status': 'success',
                'data': {
                    'prodcode': row['prodcode'],
                    'nama_produk': row['nama_produk'],
                    'barcode': row['barcode']
                }
            })
        return jsonify({'status': 'error', 'message': 'Barcode tidak ditemukan'})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


# ==========================================================
#  Preview PDF Menu
# ==========================================================
@monitoring_bp.route('/pdf')
def preview_pdf_menu():
    gang_list = []
    selected_date_str = None
    try:
        df = pd.read_sql("SELECT * FROM result_expired", engine)
        print("DATA DARI DB:", df.head())  # debug

        df['entry_date_only'] = pd.to_datetime(df['Entry Date'], errors='coerce').dt.date
        print("ENTRY_DATE_ONLY:", df['entry_date_only'].unique())  # debug

        dates_available = sorted(df['entry_date_only'].dropna().unique(), reverse=True)
        print("DATES_AVAILABLE:", dates_available)  # debug

        if dates_available:
            selected_date = dates_available[0]
            selected_date_str = selected_date.strftime('%Y-%m-%d')
            gang_list = sorted(
                df[df['entry_date_only'] == selected_date]['No Gang'].astype(str).str.strip().unique()
            )
            print("GANG_LIST:", gang_list)  # debug

    except Exception as e:
        print("Error membaca DB:", e)

    return render_template('pdf.html', gang_list=gang_list, selected_date=selected_date_str)

# ==========================================================
# Route AJAX untuk mengambil daftar No Gang berdasarkan Entry Date
# Digunakan di halaman preview PDF agar dropdown No Gang hanya menampilkan gang
# yang memiliki data pada tanggal yang dipilih user.
# Request: GET /monitoring/get_gang_list/<entry_date>
# Response: JSON {'status': 'success', 'gang_list': [list gang]} atau {'status': 'error', 'message': ...}
# entry_date harus dalam format YYYY-MM-DD
# ==========================================================
@monitoring_bp.route('/get_gang_list/<entry_date>')
def get_gang_list(entry_date):
    """
    Mengembalikan list No Gang berdasarkan Entry Date.
    entry_date: format YYYY-MM-DD
    """
    try:
        df = pd.read_sql("SELECT * FROM result_expired", engine)
        df['Entry Date'] = pd.to_datetime(df['Entry Date'], errors='coerce').dt.date
        entry_date_obj = pd.to_datetime(entry_date, errors='coerce').date()

        gang_list = sorted(
            df[df['Entry Date'] == entry_date_obj]['No Gang'].astype(str).str.strip().unique()
        )

        return jsonify({'status': 'success', 'gang_list': gang_list})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# ==========================================================
#  PDF Generate
# ==========================================================
@monitoring_bp.route('/pdf/generate')
def preview_pdf_filtered():
    gang_no = request.args.get('gang_no')
    entry_date_filter = request.args.get('entry_date')

    # Load Data
    df = pd.read_sql("SELECT * FROM result_expired", engine).fillna('')
    # Gunakan nama kolom sesuai DB, jangan zfill
    df['Entry Date'] = pd.to_datetime(df['Entry Date'], errors='coerce').dt.date
    entry_date_obj = pd.to_datetime(entry_date_filter, errors='coerce').date()

    df['No Gang'] = df['No Gang'].astype(str).str.strip()
    gang_no_str = str(gang_no).strip()

    df_gang = df[
        (df['No Gang'] == gang_no_str) &
        (df['Entry Date'] == entry_date_obj)
    ]

    if df_gang.empty:
        return f"Tidak ada data untuk gang {gang_no} pada tanggal {entry_date_filter}", 404

    # Informasi petugas
    petugas_list = sorted(set(df_gang['Petugas'].dropna().str.strip()))
    posisi_list = sorted(set(df_gang['Posisi'].dropna().str.strip()))

    petugas_str = ' - '.join(petugas_list) if petugas_list else '-'
    posisi_str = ' - '.join(posisi_list) if posisi_list else '-'

    # === Setup PDF ===
    buffer = BytesIO()
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepInFrame, PageBreak
    from reportlab.lib.pagesizes import landscape, A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER

    # margins
    page_width, page_height = landscape(A4)
    left_margin = 3 * mm
    right_margin = 12 * mm
    top_margin = 4 * mm
    bottom_margin = 2 * mm

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        topMargin=top_margin,
        bottomMargin=bottom_margin,
        leftMargin=left_margin,
        rightMargin=right_margin
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleCustom',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=colors.HexColor("#004C8C"),
        alignment=TA_CENTER,
        spaceAfter=2 * mm
    )
    label_style = ParagraphStyle('Label', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8)
    value_style = ParagraphStyle('Value', parent=styles['Normal'], fontName='Helvetica', fontSize=8)
    nama_produk_style = ParagraphStyle('NamaProduk', parent=styles['Normal'], fontName='Helvetica', fontSize=8, leading=9)

    # Styles untuk kolom
    no_style = ParagraphStyle('no_style', parent=nama_produk_style, fontSize=7.5, alignment=TA_CENTER)
    barcode_style = ParagraphStyle('barcode_style', parent=nama_produk_style, fontSize=8, alignment=TA_CENTER)
    expired_style = ParagraphStyle('expired_style', parent=nama_produk_style, fontSize=8, alignment=TA_CENTER)
    empty_style = ParagraphStyle('empty_style', parent=nama_produk_style, fontSize=8, alignment=TA_CENTER)

    # tabel settings
    max_rows_per_table = 20
    table_max_height = 160 * mm  # 16 cm
    table_width = 110 * mm       # 11 cm
    header_height = 10 * mm
    default_row_height = (table_max_height - header_height) / max_rows_per_table
    col_widths = [6 * mm, 23 * mm, 58 * mm, 17 * mm, 20 * mm]

    elements = []

    # Split data menjadi batch 40 per halaman (2 tabel per halaman)
    total_rows = len(df_gang)
    batch_size = max_rows_per_table * 2  # 40 baris per halaman
    pages = [df_gang[i:i+batch_size] for i in range(0, total_rows, batch_size)]

    for page_data in pages:
        # Split kiri-kanan
        left_rows = page_data.iloc[:max_rows_per_table]
        right_rows = page_data.iloc[max_rows_per_table:] if len(page_data) > max_rows_per_table else pd.DataFrame()

        tables = []
        for df_page in [left_rows, right_rows]:
            if df_page.empty:
                continue

            # title + info
            title_para = Paragraph(f"LIST PRODUK - (GANG {gang_no})", title_style)
            info_table = Table([
                [Paragraph("Nama Petugas", label_style), Paragraph(":", value_style), Paragraph(petugas_str or '-', value_style)],
                [Paragraph("Posisi", label_style), Paragraph(":", value_style), Paragraph(posisi_str or '-', value_style)],
                [Paragraph("Entry Date", label_style), Paragraph(":", value_style), Paragraph(entry_date_filter or '', value_style)]
            ], colWidths=[28.5*mm, 3*mm, 120*mm], hAlign='LEFT')
            info_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), -4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), -4),
            ]))

            # Build table data
            data = [['NO', 'BARCODE', 'NAMA PRODUK', 'EXPIRED', 'REMARK']]
            row_heights = [header_height]
            for i, (_, row) in enumerate(df_page.iterrows(), 1):
                no_para = Paragraph(str(i), no_style)
                barcode_para = Paragraph(str(row.get('Barcode', '') or ''), barcode_style)
                nama_para = Paragraph(str(row.get('Nama Produk', '') or ''), nama_produk_style)
                expired_para = Paragraph(str(row.get('Expired', '') or ''), expired_style)
                remark_para = Paragraph('', nama_produk_style)

                _, h1 = no_para.wrap(col_widths[0], default_row_height)
                _, h2 = barcode_para.wrap(col_widths[1], default_row_height)
                _, h3 = nama_para.wrap(col_widths[2], default_row_height)
                _, h4 = expired_para.wrap(col_widths[3], default_row_height)
                _, h5 = remark_para.wrap(col_widths[4], default_row_height)
                row_height = max(h1, h2, h3, h4, h5, default_row_height)

                data.append([no_para, barcode_para, nama_para, expired_para, remark_para])
                row_heights.append(row_height)

            current_rows = len(data) - 1
            for i in range(current_rows+1, max_rows_per_table+1):
                data.append([
                    Paragraph(str(i), empty_style),
                    Paragraph('', empty_style),
                    Paragraph('', empty_style),
                    Paragraph('', empty_style),
                    Paragraph('', empty_style)
                ])
                row_heights.append(default_row_height)

            product_table = Table(data, colWidths=col_widths, hAlign='LEFT', repeatRows=1, rowHeights=row_heights)
            tbl_style = TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#D9E6F2")),
                ('GRID', (0,0), (-1,-1), 0.6, colors.black),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 8),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('ALIGN', (0,0), (-1,0), 'CENTER'),
                ('LEFTPADDING', (0,0), (-1,-1), 3),
                ('RIGHTPADDING', (0,0), (-1,-1), 3),
                ('TOPPADDING', (0,0), (-1,-1), 2),
                ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ])
            for row_idx in range(1, max_rows_per_table + 1):
                if row_idx % 2 == 0:
                    tbl_style.add('BACKGROUND', (0, row_idx), (-1, row_idx), colors.HexColor("#D3D3D3"))
                else:
                    tbl_style.add('BACKGROUND', (0, row_idx), (-1, row_idx), colors.white)
            product_table.setStyle(tbl_style)

            content = [title_para, Spacer(1, 0), info_table, Spacer(1, 3*mm), product_table]

            # KeepInFrame & outer box
            pad_l = 2 * mm
            pad_r = 0.1 * mm
            pad_t = 1 * mm
            pad_b = 1.5 * mm

            kif = KeepInFrame(
                table_width - pad_l - pad_r,
                table_max_height - pad_t - pad_b,
                content,
                hAlign='CENTER',
                vAlign='MIDDLE',
                mergeSpace=0
            )

            outer = Table([[kif]], colWidths=[table_width], rowHeights=[table_max_height], hAlign='LEFT')
            outer.setStyle(TableStyle([
                ('BOX', (0,0), (-1,-1), 1.0, colors.black),
                ('BACKGROUND', (0,0), (-1,-1), colors.white),
                ('LEFTPADDING', (0,0), (-1,-1), pad_l),
                ('RIGHTPADDING', (0,0), (-1,-1), pad_r),
                ('TOPPADDING', (0,0), (-1,-1), pad_t),
                ('BOTTOMPADDING', (0,0), (-1,-1), pad_b),
            ]))
            tables.append(outer)

        # Gabungkan kiri-kanan jika ada 2 tabel
        if len(tables) == 2:
            space_between_cols = 5 * mm

            tables_row = Table([[tables[0], Spacer(space_between_cols, 1), tables[1]]],
                               colWidths=[table_width, space_between_cols, table_width],
                                hAlign='LEFT')
            tables_row.setStyle(TableStyle([
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('TOPPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ]))
            elements.append(tables_row)
        else:
            # Jika hanya 1 tabel, rata kiri
            elements.append(tables[0])

        # Tambahkan PageBreak jika masih ada halaman berikutnya
        if page_data is not pages[-1]:
            elements.append(PageBreak())

    # Build PDF
    try:
        doc.build(elements)
    except Exception as e:
        print("[PDF BUILD ERROR]", e)
        raise

    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=False,
        download_name=f'ceklist_gang_{gang_no}.pdf',
        mimetype='application/pdf'
    )
