# -*- coding: utf-8 -*-
from flask import Flask, request, redirect, session, render_template_string, url_for
import sqlite3, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "lawyer_final_gold_2025"
PASSWORD = "1234"

# إعداد قاعدة البيانات
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "lawyer_final_2025.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# إنشاء الجدول وتحديث الهيكل
with get_db() as conn:
    try:
        conn.execute("ALTER TABLE cases ADD COLUMN manual_action TEXT DEFAULT ''")
    except:
        pass
    try:
        conn.execute("ALTER TABLE cases ADD COLUMN sessions_manual TEXT DEFAULT ''")
    except:
        pass
    try:
        conn.execute("ALTER TABLE cases ADD COLUMN action TEXT DEFAULT 'بدون'")
    except:
        pass
    try:
        conn.execute("ALTER TABLE cases ADD COLUMN deduction TEXT DEFAULT 'لا'")
    except:
        pass
    try:
        conn.execute("ALTER TABLE cases ADD COLUMN deduction_amount REAL DEFAULT 0")
    except:
        pass
    try:
        conn.execute("ALTER TABLE cases ADD COLUMN compensation TEXT DEFAULT 'لا'")
    except:
        pass
    try:
        conn.execute("ALTER TABLE cases ADD COLUMN compensation_amount REAL DEFAULT 0")
    except:
        pass
    try:
        conn.execute("ALTER TABLE cases ADD COLUMN court_fees_amount REAL DEFAULT 0")
    except:
        pass
    # إضافة عمود المنطوق
    try:
        conn.execute("ALTER TABLE cases ADD COLUMN verdict TEXT DEFAULT ''")
    except:
        pass

    conn.execute("""
                 CREATE TABLE IF NOT EXISTS cases
                 (
                     id
                     INTEGER
                     PRIMARY
                     KEY
                     AUTOINCREMENT,
                     title
                     TEXT,
                     phone
                     TEXT,
                     court
                     TEXT,
                     action
                     TEXT
                     DEFAULT
                     'بدون',
                     manual_action
                     TEXT
                     DEFAULT
                     '',
                     sessions_manual
                     TEXT
                     DEFAULT
                     '',
                     deduction
                     TEXT
                     DEFAULT
                     'لا',
                     deduction_amount
                     REAL
                     DEFAULT
                     0,
                     compensation
                     TEXT
                     DEFAULT
                     'لا',
                     compensation_amount
                     REAL
                     DEFAULT
                     0,
                     court_fees_amount
                     REAL
                     DEFAULT
                     0,
                     total_fee
                     REAL
                     DEFAULT
                     0,
                     status
                     TEXT
                     DEFAULT
                     'جارية',
                     payment_status
                     TEXT
                     DEFAULT
                     'غير مسددة',
                     notes
                     TEXT,
                     date
                     TEXT,
                     verdict
                     TEXT
                     DEFAULT
                     ''
                 )""")

LAYOUT = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>منظومة مكتب المنازعات المحترف | 2025</title>
<style>
:root { --primary: #1a2a3a; --accent: #c9a66b; --success: #27ae60; --danger: #e74c3c; --info: #3498db; --bg: #f4f7f6; }
body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: var(--bg); margin: 0; padding: 10px; direction: rtl; }
.container { max-width: 1450px; margin: auto; }
.header { background: var(--primary); color: white; padding: 15px; border-radius: 12px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; margin-bottom: 15px; }
.stat-card { padding: 8px; border-radius: 8px; text-align: center; text-decoration: none; color: white !important; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
.stat-card h3 { font-size: 11px; margin: 0; opacity: 0.9; }
.stat-card p { margin: 2px 0 0; font-size: 15px; font-weight: bold; }
.card-total { background: #34495e; }
.card-next  { background: var(--danger); }
.card-fin   { background: var(--success); }
.card-ong   { background: var(--info); }
.main-card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 20px; }
input, select, textarea { padding: 8px; border: 1px solid #ddd; border-radius: 6px; width: 100%; margin: 5px 0; font-size: 13px; box-sizing: border-box; }
button { background: var(--info); color: white; border: none; padding: 4px 10px; cursor: pointer; border-radius: 4px; font-weight: bold; font-size: 12px; }
button[type="submit"] { background: var(--success); }
table { width: 100%; border-collapse: collapse; background: white; border-radius: 10px; overflow: hidden; font-size: 11px; }
th { background: #f8fafc; padding: 8px; border-bottom: 2px solid #edf2f7; color: var(--primary); text-align: center; }
td { padding: 8px; border-bottom: 1px solid #edf2f7; text-align: center; }
.badge { padding: 4px 8px; border-radius: 15px; font-size: 10px; font-weight: bold; color: white; }
.st-جارية { background: var(--info); } .st-منتهية { background: var(--success); }
.pay-مسددة { background: var(--success); } .pay-غيرمسددة { background: var(--danger); }
@media print { .no-print { display: none !important; } }
</style>
</head>
<body><div class="container">{{ content | safe }}</div></body>
</html>
"""

COURTS_LIST = ["ابتدائي", "مجلس قضائي", "المحكمة الادارية", "مجلس الدولة", "المحكمة العليا", "محكمة التنازع",
               "الغرفة المدنية", "الغرفة العقارية", "الغرفة التجارية"]
ACTIONS_LIST = ["بدون", "معارضة", "استئناف", "طعن", "طعن بالنقض"]


@app.route("/")
def index():
    if not session.get("login"): return redirect(url_for("login"))
    search = request.args.get("q", "")
    conn = get_db()
    cases = conn.execute(
        "SELECT * FROM cases WHERE title LIKE ? OR court LIKE ? OR status LIKE ? OR action LIKE ? ORDER BY date ASC",
        (f'%{search}%', f'%{search}%', f'%{search}%', f'%{search}%')).fetchall()

    today = datetime.now().strftime('%Y-%m-%d')
    next_s = conn.execute(
        "SELECT sessions_manual FROM cases WHERE sessions_manual >= ? ORDER BY sessions_manual ASC LIMIT 1",
        (today,)).fetchone()

    stats = {
        "total": conn.execute("SELECT COUNT(*) FROM cases").fetchone(),
        "fin": conn.execute("SELECT COUNT(*) FROM cases WHERE status = 'منتهية'").fetchone(),
        "ong": conn.execute("SELECT COUNT(*) FROM cases WHERE status = 'جارية'").fetchone(),
        "next": next_s['sessions_manual'] if next_s else "لا يوجد"
    }

    rows = ""
    for c in cases:
        rows += f"""<tr>
            <td>{c['id']}</td>
            <td>{c['title']}</td>
            <td>{c['court']}</td>
            <td>{c['action']}</td>
            <td>{c['manual_action']}</td>
            <td style="color:red; font-weight:bold;">{c['sessions_manual']}</td>
            <td>{c['deduction']} : {c['deduction_amount']}</td>
            <td>{c['compensation']} : {c['compensation_amount']}</td>
            <td>{c['court_fees_amount']}</td>
            <td><span class="badge st-{c['status']}">{c['status']}</span></td>
            <td><b>{c['total_fee']}</b></td>
            <td><span class="badge pay-{c['payment_status'].replace(' ', '')}">{c['payment_status']}</span></td>
            <td>{c['date']}</td>
            <td>{c['verdict']}</td>
            <td class="no-print">
                <a href="/edit/{c['id']}" title="تعديل">📝</a> | 
                <a href="javascript:window.print()" title="طباعة الجدول">🖨️</a> | 
                <a href="/print_report/{c['id']}" target="_blank" title="تقرير القضية">📄</a> |
                <a href="/delete/{c['id']}" onclick="return confirm('حذف؟')" style="color:red; text-decoration:none;">🗑️</a>
            </td>
        </tr>"""

    content = f'''
    <div class="header no-print"><h2>⚖️ مكتب المنازعات 2025</h2> <a href="/logout" style="color:white; text-decoration:none;">خروج</a></div>
    <div class="stats-grid no-print">
        <a href="/" class="stat-card card-total"><h3>إجمالي القضايا</h3><p>{stats['total'][0]}</p></a>
        <a href="#" class="stat-card card-next"><h3>الجلسة القادمة</h3><p>{stats['next']}</p></a>
        <a href="/?q=منتهية" class="stat-card card-fin"><h3>المنتهية</h3><p>{stats['fin'][0]}</p></a>
        <a href="/?q=جارية" class="stat-card card-ong"><h3>الجارية</h3><p>{stats['ong'][0]}</p></a>
    </div>

    <div class="main-card no-print">
        <h3>➕ إضافة ملف قضية جديد</h3>
        <form method="post" action="/add">
            <div style="display:grid; grid-template-columns: repeat(5, 1fr); gap:10px;">
                <input name="title" placeholder="قضية السيد" required>
                <input name="phone" placeholder="رقم الهاتف">
                <select name="court">{"".join([f"<option>{ct}</option>" for ct in COURTS_LIST])}</select>
                <select name="action">{"".join([f"<option>{ac}</option>" for ac in ACTIONS_LIST])}</select>
                <input name="manual_action" placeholder="الإجراءات (يدوي)">
                <input type="date" name="sessions_manual" title="تاريخ الجلسة">
                <select name="deduction"><option>اقتطاع: لا</option><option>اقتطاع: نعم</option></select>
                <input type="number" step="0.01" name="deduction_amount" placeholder="مبلغ الاقتطاع">
                <select name="compensation"><option>تعويض: لا</option><option>تعويض: نعم</option></select>
                <input type="number" step="0.01" name="compensation_amount" placeholder="مبلغ التعويض">
                <input type="number" step="0.01" name="court_fees_amount" placeholder="مبلغ الأتعاب">
                <input type="number" step="0.01" name="total_fee" placeholder="الأتعاب النهائية">
                <input name="verdict" placeholder="المنطوق">
                <select name="status"><option>جارية</option><option>منتهية</option></select>
                <button type="submit">حفظ البيانات</button>
            </div>
        </form>
    </div>

    <div class="main-card">
        <table>
            <thead>
                <tr>
                    <th>الرقم</th><th>الموكل</th><th>المحكمة</th><th>الإجراء</th><th>إجراء يدوي</th><th>الجلسة</th>
                    <th>الاقتطاع</th><th>التعويض</th><th>أتعاب</th><th>الحالة</th><th>الإجمالي</th><th>الدفع</th>
                    <th>التاريخ</th><th>المنطوق</th><th class="no-print">عمليات</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
    </div>
    '''
    return render_template_string(LAYOUT, content=content)


@app.route("/add", methods=["POST"])
def add():
    d = request.form
    with get_db() as conn:
        conn.execute("""INSERT INTO cases
                        (title, phone, court, action, manual_action, sessions_manual, deduction, deduction_amount,
                         compensation, compensation_amount, court_fees_amount, total_fee, verdict, status, date)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                     (d['title'], d['phone'], d['court'], d['action'], d['manual_action'], d['sessions_manual'],
                      d['deduction'], d.get('deduction_amount', 0) or 0,
                      d['compensation'], d.get('compensation_amount', 0) or 0, d.get('court_fees_amount', 0) or 0,
                      d.get('total_fee', 0) or 0, d.get('verdict', ''), d['status'],
                      datetime.now().strftime('%Y-%m-%d')))
    return redirect(url_for("index"))


@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    conn = get_db()
    if request.method == "POST":
        d = request.form
        conn.execute(
            "UPDATE cases SET title=?, manual_action=?, sessions_manual=?, total_fee=?, verdict=?, status=? WHERE id=?",
            (d['title'], d['manual_action'], d['sessions_manual'], d['total_fee'], d.get('verdict', ''), d['status'],
             id))
        conn.commit()
        return redirect(url_for("index"))
    case = conn.execute("SELECT * FROM cases WHERE id=?", (id,)).fetchone()
    return render_template_string(LAYOUT,
                                  content=f'<h3>تعديل {case["title"]}</h3><form method="post"><input name="title" value="{case["title"]}"><input name="verdict" value="{case["verdict"]}"><button type="submit">تحديث</button></form>')


@app.route("/print_report/<int:id>")
def print_report(id):
    case = get_db().execute("SELECT * FROM cases WHERE id=?", (id,)).fetchone()
    return f"<div style='direction:rtl; padding:40px;'><h2>تقرير القضية: {case['title']}</h2><p>الجلسة القادمة: {case['sessions_manual']}</p><p>المنطوق: {case['verdict']}</p><hr><button onclick='window.print()'>طباعة</button></div>"


@app.route("/delete/<int:id>")
def delete(id):
    with get_db() as conn: conn.execute("DELETE FROM cases WHERE id = ?", (id,))
    return redirect(url_for("index"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST" and request.form.get("password") == PASSWORD:
        session["login"] = True
        return redirect(url_for("index"))
    return '<form method="post" style="text-align:center;padding:50px;"><input type="password" name="password" placeholder="1234"><button>دخول</button></form>'


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)

