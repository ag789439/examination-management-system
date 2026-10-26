"""
==========================================================================
 EXAM MANAGER  -  web edition  (Flask + SQLite)
--------------------------------------------------------------------------
 The same examination module as the desktop app, but running in a browser
 so it can be deployed (Render / Railway / PythonAnywhere) and opened from
 any device.

 Pages
   Dashboard   counts, recent admissions, exams
   Students    admission + student master data
   Exams       exam master (the exam type is the exam's name)
   Subjects    subject master
   Schedule    one paper per subject with max / pass marks
   Marks       bulk marks entry per exam + subject
   Results     total, percentage, grade, rank, pass/fail + CSV export

 Environment variables
   APP_PASSWORD   if set, a login screen is required (strongly recommended)
   SCHOOL_NAME    name shown in the header
   SECRET_KEY     session signing key (set this in production)
   DB_PATH        where the SQLite file lives (default: next to app.py)

 Run locally
   pip install -r requirements.txt
   python app.py            ->  http://127.0.0.1:5000
==========================================================================
"""

import csv
import io
import os
import secrets
import sqlite3
from datetime import datetime

from flask import (Flask, Response, flash, g, redirect, render_template,
                   request, session, url_for)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("DB_PATH") or os.path.join(BASE_DIR, "exam_manager.db")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "").strip()
SCHOOL_NAME = os.environ.get("SCHOOL_NAME", "Examination Management System")

GENDERS = ["Male", "Female", "Other"]
STUDENT_STATUS = ["Active", "Inactive", "Passed Out", "Left"]
EXAM_TYPES = ["Unit Test", "Mid Term", "Half Yearly", "Annual / Final",
              "Pre-Board", "Practical", "Internal Assessment"]
EXAM_STATUS = ["Scheduled", "Ongoing", "Completed", "Result Declared", "Cancelled"]
SECTIONS = ["A", "B", "C", "D", "E"]

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)


# --------------------------------------------------------------------------
#  small helpers
# --------------------------------------------------------------------------
def norm_date(text):
    """dd/mm/yyyy, dd-mm-yyyy, dd.mm.yyyy or yyyy-mm-dd -> yyyy-mm-dd."""
    text = (text or "").strip()
    if not text:
        return ""
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%Y-%m-%d", "%d/%m/%y"):
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def disp_date(text):
    text = (text or "").strip()
    if not text:
        return ""
    try:
        return datetime.strptime(text, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return text


def norm_time(text):
    text = (text or "").strip()
    if not text:
        return ""
    for fmt in ("%H:%M", "%I:%M %p", "%I:%M%p", "%H.%M"):
        try:
            return datetime.strptime(text.upper(), fmt).strftime("%H:%M")
        except ValueError:
            continue
    return None


def to_float(text, default=None):
    text = (text or "").strip()
    if not text:
        return default
    try:
        return float(text)
    except ValueError:
        return None


def grade_for(percentage):
    if percentage is None:
        return "-"
    if percentage >= 91:
        return "A1"
    if percentage >= 81:
        return "A2"
    if percentage >= 71:
        return "B1"
    if percentage >= 61:
        return "B2"
    if percentage >= 51:
        return "C1"
    if percentage >= 41:
        return "C2"
    if percentage >= 33:
        return "D"
    return "E"


def fmt_num(value, digits=2):
    if value is None:
        return ""
    value = float(value)
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.{digits}f}".rstrip("0").rstrip(".")


def exam_label(row):
    """Type · Class · Year - how an exam is written everywhere."""
    if row is None:
        return ""
    etype = row["exam_type"] or row["exam_name"] or "Exam"
    parts = [etype]
    if (row["class_name"] or "").strip():
        parts.append(f"Class {row['class_name'].strip()}")
    if (row["academic_year"] or "").strip():
        parts.append(row["academic_year"].strip())
    return "  ·  ".join(parts)


# --------------------------------------------------------------------------
#  database
# --------------------------------------------------------------------------
SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    admission_no   TEXT NOT NULL UNIQUE,
    roll_no        TEXT NOT NULL,
    name           TEXT NOT NULL,
    class_name     TEXT NOT NULL,
    section        TEXT,
    dob            TEXT,
    gender         TEXT,
    father_name    TEXT,
    mother_name    TEXT,
    phone          TEXT,
    email          TEXT,
    address        TEXT,
    admission_date TEXT,
    status         TEXT DEFAULT 'Active',
    created_at     TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS exams (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_name     TEXT NOT NULL,
    exam_type     TEXT,
    academic_year TEXT,
    class_name    TEXT,
    start_date    TEXT,
    end_date      TEXT,
    status        TEXT DEFAULT 'Scheduled',
    remarks       TEXT,
    created_at    TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS subjects (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_code TEXT NOT NULL UNIQUE,
    subject_name TEXT NOT NULL,
    class_name   TEXT,
    created_at   TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS exam_schedule (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_id     INTEGER NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
    subject_id  INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    exam_date   TEXT,
    start_time  TEXT,
    duration    INTEGER,
    room        TEXT,
    invigilator TEXT,
    max_marks   REAL DEFAULT 100,
    pass_marks  REAL DEFAULT 33,
    UNIQUE(exam_id, subject_id)
);
CREATE TABLE IF NOT EXISTS marks (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_id        INTEGER NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
    student_id     INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    subject_id     INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    marks_obtained REAL,
    remarks        TEXT,
    updated_at     TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(exam_id, student_id, subject_id)
);
"""


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def query(sql, params=(), one=False):
    cur = get_db().execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    return (rows[0] if rows else None) if one else rows


def execute(sql, params=()):
    db = get_db()
    cur = db.execute(sql, params)
    db.commit()
    last = cur.lastrowid
    cur.close()
    return last


# --------------------------------------------------------------------------
#  business logic
# --------------------------------------------------------------------------
def compute_results(exam_id, class_name):
    schedule = query("SELECT subject_id, max_marks, pass_marks FROM exam_schedule"
                     " WHERE exam_id=?", (exam_id,))
    if not schedule:
        return []
    max_by_sub = {r["subject_id"]: (r["max_marks"] or 0) for r in schedule}
    pass_by_sub = {r["subject_id"]: (r["pass_marks"] or 0) for r in schedule}

    students = query(
        "SELECT id, admission_no, roll_no, name FROM students WHERE class_name=?"
        " ORDER BY CAST(roll_no AS INTEGER), roll_no", (class_name,))
    marks = query("SELECT * FROM marks WHERE exam_id=?", (exam_id,))
    by_student = {}
    for m in marks:
        by_student.setdefault(m["student_id"], {})[m["subject_id"]] = m

    results = []
    for st in students:
        smap = by_student.get(st["id"], {})
        if not smap:
            continue
        obtained = total_max = 0.0
        failed = 0
        for sub_id, mx in max_by_sub.items():
            row = smap.get(sub_id)
            if row is None or row["marks_obtained"] is None:
                continue
            got = float(row["marks_obtained"])
            obtained += got
            total_max += float(mx)
            if got < float(pass_by_sub.get(sub_id, 0)):
                failed += 1
        if total_max <= 0:
            continue
        pct = round(obtained / total_max * 100, 2)
        results.append({
            "student_id": st["id"],
            "admission_no": st["admission_no"],
            "roll_no": st["roll_no"],
            "name": st["name"],
            "obtained": round(obtained, 2),
            "total_max": round(total_max, 2),
            "percentage": pct,
            "grade": grade_for(pct),
            "failed_subjects": failed,
            "result": "Pass" if (failed == 0 and pct >= 33) else "Fail",
        })

    results.sort(key=lambda r: (-r["percentage"], r["roll_no"]))
    rank, last_pct = 0, None
    for i, r in enumerate(results, start=1):
        if last_pct is None or r["percentage"] != last_pct:
            rank, last_pct = i, r["percentage"]
        r["rank"] = rank
    return results


# --------------------------------------------------------------------------
#  auth + shared template values
# --------------------------------------------------------------------------
@app.before_request
def require_login():
    if not APP_PASSWORD:
        return None
    if request.endpoint in ("login", "static", "healthz"):
        return None
    if session.get("auth"):
        return None
    return redirect(url_for("login", next=request.path))


@app.context_processor
def inject_globals():
    return {
        "school_name": SCHOOL_NAME,
        "auth_enabled": bool(APP_PASSWORD),
        "no_password": not APP_PASSWORD,
        "today": datetime.now().strftime("%d/%m/%Y"),
    }


@app.route("/login", methods=["GET", "POST"])
def login():
    if not APP_PASSWORD:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        if request.form.get("password", "") == APP_PASSWORD:
            session["auth"] = True
            return redirect(request.args.get("next") or url_for("dashboard"))
        flash("Wrong password.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# --------------------------------------------------------------------------
#  dashboard
# --------------------------------------------------------------------------
@app.route("/")
def dashboard():
    stats = {
        "students": query("SELECT COUNT(*) c FROM students", one=True)["c"],
        "exams": query("SELECT COUNT(*) c FROM exams", one=True)["c"],
        "subjects": query("SELECT COUNT(*) c FROM subjects", one=True)["c"],
        "papers": query("SELECT COUNT(*) c FROM exam_schedule", one=True)["c"],
    }
    recent = query("SELECT * FROM students ORDER BY id DESC LIMIT 10")
    exams = query("SELECT * FROM exams ORDER BY id DESC LIMIT 10")
    return render_template("dashboard.html", stats=stats, recent=recent,
                           exams=exams, disp_date=disp_date)


# --------------------------------------------------------------------------
#  students
# --------------------------------------------------------------------------
@app.route("/students")
def students():
    term = request.args.get("q", "").strip()
    if term:
        like = f"%{term}%"
        rows = query(
            "SELECT * FROM students WHERE name LIKE ? OR roll_no LIKE ?"
            " OR admission_no LIKE ? OR class_name LIKE ?"
            " ORDER BY class_name, CAST(roll_no AS INTEGER), roll_no",
            (like, like, like, like))
    else:
        rows = query("SELECT * FROM students ORDER BY class_name,"
                     " CAST(roll_no AS INTEGER), roll_no")
    classes = [r["class_name"] for r in query(
        "SELECT DISTINCT class_name FROM students WHERE class_name<>''"
        " ORDER BY class_name")]
    edit_id = request.args.get("edit", type=int)
    editing = query("SELECT * FROM students WHERE id=?", (edit_id,),
                    one=True) if edit_id else None
    return render_template("students.html", students=rows, q=term,
                           classes=classes, disp_date=disp_date,
                           genders=GENDERS, sections=SECTIONS,
                           statuses=STUDENT_STATUS, editing=editing)


@app.route("/students/save", methods=["POST"])
def student_save():
    f = request.form
    sid = f.get("id") or ""
    values = (
        f.get("admission_no", "").strip(), f.get("roll_no", "").strip(),
        f.get("name", "").strip(), f.get("class_name", "").strip(),
        f.get("section", "").strip(), norm_date(f.get("dob")),
        f.get("gender", "").strip(), f.get("father_name", "").strip(),
        f.get("mother_name", "").strip(), f.get("phone", "").strip(),
        f.get("email", "").strip(), f.get("address", "").strip(),
        norm_date(f.get("admission_date")),
        f.get("status", "").strip() or "Active",
    )
    adm, roll, name, cls, _sec, dob, _g, _f, _m, phone, email, _a, adm_date, _s = values
    if not adm or not roll or not name or not cls:
        flash("Admission No, Roll No, Name and Class are required.", "error")
        return redirect(url_for("students"))
    if dob is None:
        flash("Date of birth is not a valid date (use dd/mm/yyyy).", "error")
        return redirect(url_for("students"))
    if not adm_date:
        flash("Date of admission is required - type it as dd/mm/yyyy.", "error")
        return redirect(url_for("students"))
    if adm_date is None:
        flash("Date of admission is not a valid date (use dd/mm/yyyy).", "error")
        return redirect(url_for("students"))
    if phone and not phone.replace("+", "").replace("-", "").replace(" ", "").isdigit():
        flash("Phone must contain digits only.", "error")
        return redirect(url_for("students"))
    if email and "@" not in email:
        flash("Email does not look valid.", "error")
        return redirect(url_for("students"))

    dup = query("SELECT id FROM students WHERE admission_no=? AND id<>?",
                (adm, int(sid) if sid else 0), one=True)
    if dup:
        flash(f"Admission No {adm} already exists.", "error")
        return redirect(url_for("students"))

    if sid:
        execute("""UPDATE students SET admission_no=?, roll_no=?, name=?,
                   class_name=?, section=?, dob=?, gender=?, father_name=?,
                   mother_name=?, phone=?, email=?, address=?, admission_date=?,
                   status=? WHERE id=?""", values + (int(sid),))
        flash(f"Student '{name}' updated.", "ok")
    else:
        execute("""INSERT INTO students (admission_no, roll_no, name, class_name,
                   section, dob, gender, father_name, mother_name, phone, email,
                   address, admission_date, status)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", values)
        flash(f"Student '{name}' added.", "ok")
    return redirect(url_for("students"))


@app.route("/students/<int:sid>/delete", methods=["POST"])
def student_delete(sid):
    row = query("SELECT name FROM students WHERE id=?", (sid,), one=True)
    execute("DELETE FROM students WHERE id=?", (sid,))
    flash(f"Student '{row['name'] if row else sid}' deleted.", "ok")
    return redirect(url_for("students"))


@app.route("/students.csv")
def students_csv():
    rows = query("SELECT * FROM students ORDER BY class_name,"
                 " CAST(roll_no AS INTEGER), roll_no")
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["Admission No", "Roll No", "Name", "Class", "Section",
                "Date of Admission", "DOB", "Gender", "Father's Name",
                "Mother's Name", "Phone", "Email", "Address", "Status"])
    for r in rows:
        w.writerow([r["admission_no"], r["roll_no"], r["name"], r["class_name"],
                    r["section"], disp_date(r["admission_date"]),
                    disp_date(r["dob"]), r["gender"], r["father_name"],
                    r["mother_name"], r["phone"], r["email"], r["address"],
                    r["status"]])
    return Response("\ufeff" + out.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition":
                             "attachment; filename=students.csv"})


# --------------------------------------------------------------------------
#  exams
# --------------------------------------------------------------------------
@app.route("/exams")
def exams():
    rows = query("SELECT * FROM exams ORDER BY id DESC")
    edit_id = request.args.get("edit", type=int)
    editing = query("SELECT * FROM exams WHERE id=?", (edit_id,),
                    one=True) if edit_id else None
    return render_template("exams.html", exams=rows, disp_date=disp_date,
                           exam_types=EXAM_TYPES, statuses=EXAM_STATUS,
                           editing=editing)


@app.route("/exams/save", methods=["POST"])
def exam_save():
    f = request.form
    eid = f.get("id") or ""
    etype = f.get("exam_type", "").strip()
    year = f.get("academic_year", "").strip()
    cls = f.get("class_name", "").strip()
    sd = norm_date(f.get("start_date"))
    ed = norm_date(f.get("end_date"))

    if not etype:
        flash("Exam type is required.", "error")
        return redirect(url_for("exams"))
    if sd is None or ed is None:
        flash("Dates must be dd/mm/yyyy.", "error")
        return redirect(url_for("exams"))
    if sd and ed and ed < sd:
        flash("End date cannot be before start date.", "error")
        return redirect(url_for("exams"))
    dup = query("""SELECT id FROM exams WHERE exam_type=?
                   AND IFNULL(academic_year,'')=? AND IFNULL(class_name,'')=?
                   AND id<>?""", (etype, year, cls, int(eid) if eid else 0),
                one=True)
    if dup:
        flash(f"'{etype}' already exists for class {cls or '-'} "
              f"in {year or '-'}.", "error")
        return redirect(url_for("exams"))

    if eid:
        execute("""UPDATE exams SET exam_name=?, exam_type=?, academic_year=?,
                   class_name=?, start_date=?, end_date=?, status=?, remarks=?
                   WHERE id=?""",
                (etype, etype, year, cls, sd, ed,
                 f.get("status") or "Scheduled", f.get("remarks", "").strip(),
                 int(eid)))
        flash(f"Exam '{etype}' updated.", "ok")
    else:
        execute("""INSERT INTO exams (exam_name, exam_type, academic_year,
                   class_name, start_date, end_date, status, remarks)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (etype, etype, year, cls, sd, ed,
                 f.get("status") or "Scheduled", f.get("remarks", "").strip()))
        flash(f"Exam '{etype}' saved.", "ok")
    return redirect(url_for("exams"))


@app.route("/exams/<int:eid>/delete", methods=["POST"])
def exam_delete(eid):
    row = query("SELECT exam_type FROM exams WHERE id=?", (eid,), one=True)
    execute("DELETE FROM exams WHERE id=?", (eid,))
    flash(f"Exam '{row['exam_type'] if row else eid}' deleted.", "ok")
    return redirect(url_for("exams"))


# --------------------------------------------------------------------------
#  subjects
# --------------------------------------------------------------------------
@app.route("/subjects")
def subjects():
    rows = query("SELECT * FROM subjects ORDER BY subject_code")
    edit_id = request.args.get("edit", type=int)
    editing = query("SELECT * FROM subjects WHERE id=?", (edit_id,),
                    one=True) if edit_id else None
    return render_template("subjects.html", subjects=rows, editing=editing)


@app.route("/subjects/save", methods=["POST"])
def subject_save():
    f = request.form
    sid = f.get("id") or ""
    code = f.get("subject_code", "").strip().upper()
    name = f.get("subject_name", "").strip()
    cls = f.get("class_name", "").strip()
    if not code or not name:
        flash("Subject code and name are both required.", "error")
        return redirect(url_for("subjects"))
    dup = query("SELECT id FROM subjects WHERE subject_code=? AND id<>?",
                (code, int(sid) if sid else 0), one=True)
    if dup:
        flash(f"Subject code {code} already exists.", "error")
        return redirect(url_for("subjects"))
    if sid:
        execute("UPDATE subjects SET subject_code=?, subject_name=?,"
                " class_name=? WHERE id=?", (code, name, cls, int(sid)))
        flash(f"Subject '{name}' updated.", "ok")
    else:
        execute("INSERT INTO subjects (subject_code, subject_name, class_name)"
                " VALUES (?,?,?)", (code, name, cls))
        flash(f"Subject '{name}' added.", "ok")
    return redirect(url_for("subjects"))


@app.route("/subjects/<int:sid>/delete", methods=["POST"])
def subject_delete(sid):
    row = query("SELECT subject_name FROM subjects WHERE id=?", (sid,), one=True)
    execute("DELETE FROM subjects WHERE id=?", (sid,))
    flash(f"Subject '{row['subject_name'] if row else sid}' deleted.", "ok")
    return redirect(url_for("subjects"))


@app.route("/subjects/defaults", methods=["POST"])
def subject_defaults():
    defaults = [("ENG", "English"), ("HIN", "Hindi"), ("MAT", "Mathematics"),
                ("SCI", "Science"), ("SST", "Social Science"),
                ("CS", "Computer Science")]
    added = 0
    for code, name in defaults:
        if not query("SELECT id FROM subjects WHERE subject_code=?", (code,),
                     one=True):
            execute("INSERT INTO subjects (subject_code, subject_name)"
                    " VALUES (?,?)", (code, name))
            added += 1
    flash(f"{added} default subject(s) added.", "ok")
    return redirect(url_for("subjects"))


# --------------------------------------------------------------------------
#  schedule
# --------------------------------------------------------------------------
@app.route("/schedule")
def schedule():
    exams_rows = query("SELECT * FROM exams ORDER BY id DESC")
    subjects_rows = query("SELECT * FROM subjects ORDER BY subject_code")
    rows = query("""SELECT sc.*, e.exam_name, e.exam_type, e.academic_year,
                           e.class_name, s.subject_name
                    FROM exam_schedule sc
                    JOIN exams e ON e.id = sc.exam_id
                    JOIN subjects s ON s.id = sc.subject_id
                    ORDER BY e.id DESC, sc.exam_date, sc.start_time""")
    return render_template("schedule.html", papers=rows, exams=exams_rows,
                           subjects=subjects_rows, exam_label=exam_label,
                           disp_date=disp_date, fmt_num=fmt_num)


@app.route("/schedule/save", methods=["POST"])
def schedule_save():
    f = request.form
    exam_id = f.get("exam_id", "")
    subject_id = f.get("subject_id", "")
    if not exam_id or not subject_id:
        flash("Select both an exam and a subject.", "error")
        return redirect(url_for("schedule"))
    exam_id, subject_id = int(exam_id), int(subject_id)

    ed = norm_date(f.get("exam_date"))
    st = norm_time(f.get("start_time"))
    duration = to_float(f.get("duration"), 0)
    mx = to_float(f.get("max_marks"), 100)
    ps = to_float(f.get("pass_marks"), 33)
    if ed is None:
        flash("Exam date must be dd/mm/yyyy.", "error")
        return redirect(url_for("schedule"))
    if st is None:
        flash("Start time must be HH:MM (24 hour).", "error")
        return redirect(url_for("schedule"))
    if duration is None or mx is None or ps is None:
        flash("Duration, max marks and pass marks must be numbers.", "error")
        return redirect(url_for("schedule"))
    if mx <= 0:
        flash("Max marks must be greater than 0.", "error")
        return redirect(url_for("schedule"))
    if ps < 0 or ps > mx:
        flash("Pass marks must be between 0 and max marks.", "error")
        return redirect(url_for("schedule"))
    if query("SELECT id FROM exam_schedule WHERE exam_id=? AND subject_id=?",
             (exam_id, subject_id), one=True):
        flash("That subject is already scheduled for this exam.", "error")
        return redirect(url_for("schedule"))

    execute("""INSERT INTO exam_schedule (exam_id, subject_id, exam_date,
               start_time, duration, room, invigilator, max_marks, pass_marks)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (exam_id, subject_id, ed, st, int(duration),
             f.get("room", "").strip(), f.get("invigilator", "").strip(),
             mx, ps))
    flash("Paper added to the schedule.", "ok")
    return redirect(url_for("schedule"))


@app.route("/schedule/<int:pid>/delete", methods=["POST"])
def schedule_delete(pid):
    execute("DELETE FROM exam_schedule WHERE id=?", (pid,))
    flash("Paper removed.", "ok")
    return redirect(url_for("schedule"))


# --------------------------------------------------------------------------
#  marks
# --------------------------------------------------------------------------
@app.route("/marks", methods=["GET", "POST"])
def marks():
    exams_rows = query("SELECT * FROM exams ORDER BY id DESC")
    subjects_rows = query("SELECT * FROM subjects ORDER BY subject_code")
    exam_id = request.values.get("exam_id") or ""
    subject_id = request.values.get("subject_id") or ""

    sheet, info, ctx = [], "", None
    if exam_id and subject_id:
        exam_id, subject_id = int(exam_id), int(subject_id)
        sched = query("SELECT * FROM exam_schedule WHERE exam_id=? AND"
                      " subject_id=?", (exam_id, subject_id), one=True)
        exam = query("SELECT * FROM exams WHERE id=?", (exam_id,), one=True)

        if request.method == "POST" and sched:
            saved = 0
            max_marks = float(sched["max_marks"] or 100)
            for st in query("SELECT id FROM students WHERE class_name=?",
                            ((exam["class_name"] or "").strip(),)):
                raw = request.form.get(f"marks_{st['id']}", "").strip()
                remark = request.form.get(f"remarks_{st['id']}", "").strip()
                if raw == "":
                    value = None
                else:
                    value = to_float(raw)
                    if value is None or value < 0 or value > max_marks:
                        continue
                existing = query("SELECT id FROM marks WHERE exam_id=? AND"
                                 " student_id=? AND subject_id=?",
                                 (exam_id, st["id"], subject_id), one=True)
                if existing:
                    execute("UPDATE marks SET marks_obtained=?, remarks=?,"
                            " updated_at=CURRENT_TIMESTAMP WHERE id=?",
                            (value, remark, existing["id"]))
                else:
                    execute("""INSERT INTO marks (exam_id, student_id,
                               subject_id, marks_obtained, remarks)
                               VALUES (?,?,?,?,?)""",
                            (exam_id, st["id"], subject_id, value, remark))
                saved += 1
            flash(f"Marks saved for {saved} student(s).", "ok")
            return redirect(url_for("marks", exam_id=exam_id,
                                    subject_id=subject_id))

        if not sched:
            info = ("That subject is not scheduled for this exam - add it in "
                    "Exam schedule first.")
        else:
            max_marks = float(sched["max_marks"] or 100)
            pass_marks = float(sched["pass_marks"] or 33)
            ctx = {"max_marks": max_marks, "pass_marks": pass_marks}
            rows = query("SELECT * FROM students WHERE status='Active'"
                         " AND class_name=? ORDER BY CAST(roll_no AS INTEGER),"
                         " roll_no", ((exam["class_name"] or "").strip(),))
            for st in rows:
                m = query("SELECT * FROM marks WHERE exam_id=? AND student_id=?"
                          " AND subject_id=?", (exam_id, st["id"], subject_id),
                          one=True)
                sheet.append({"student": st, "mark": m})
            info = (f"{len(sheet)} student(s) · max {fmt_num(max_marks)} · "
                    f"pass {fmt_num(pass_marks)}")

    return render_template("marks.html", exams=exams_rows,
                           subjects=subjects_rows, exam_id=str(exam_id),
                           subject_id=str(subject_id), sheet=sheet,
                           info=info, ctx=ctx, exam_label=exam_label,
                           fmt_num=fmt_num)


# --------------------------------------------------------------------------
#  results
# --------------------------------------------------------------------------
@app.route("/results")
def results():
    exams_rows = query("SELECT * FROM exams ORDER BY id DESC")
    exam_id = request.args.get("exam_id") or ""
    class_name = (request.args.get("class_name") or "").strip()
    rows, info, exam = [], "", None

    if exam_id:
        exam = query("SELECT * FROM exams WHERE id=?", (int(exam_id),), one=True)
        class_name = class_name or (exam["class_name"] or "").strip()
        if class_name:
            rows = compute_results(int(exam_id), class_name)
            if rows:
                passed = sum(1 for r in rows if r["result"] == "Pass")
                info = (f"{len(rows)} student(s) · Pass {passed} · "
                        f"Fail {len(rows) - passed} · Topper: {rows[0]['name']} "
                        f"({rows[0]['percentage']:.2f}%)")
            else:
                info = "No marks found for this exam and class."

    classes = [r["class_name"] for r in query(
        "SELECT DISTINCT class_name FROM students WHERE class_name<>''"
        " ORDER BY class_name")]
    return render_template("results.html", exams=exams_rows, results=rows,
                           exam_id=str(exam_id), class_name=class_name,
                           classes=classes, info=info, exam_label=exam_label,
                           fmt_num=fmt_num)


@app.route("/results.csv")
def results_csv():
    exam_id = request.args.get("exam_id", type=int)
    class_name = (request.args.get("class_name") or "").strip()
    if not exam_id:
        flash("Pick an exam first.", "error")
        return redirect(url_for("results"))
    exam = query("SELECT * FROM exams WHERE id=?", (exam_id,), one=True)
    class_name = class_name or (exam["class_name"] or "").strip()
    rows = compute_results(exam_id, class_name)
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["Rank", "Roll No", "Admission No", "Name", "Obtained", "Max",
                "Percentage", "Grade", "Failed Subjects", "Result"])
    for r in rows:
        w.writerow([r["rank"], r["roll_no"], r["admission_no"], r["name"],
                    fmt_num(r["obtained"]), fmt_num(r["total_max"]),
                    f"{r['percentage']:.2f}", r["grade"], r["failed_subjects"],
                    r["result"]])
    name = f"results_{class_name or 'all'}.csv".replace(" ", "_")
    return Response("\ufeff" + out.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition":
                             f"attachment; filename={name}"})


# --------------------------------------------------------------------------
#  health check (used by Render)
# --------------------------------------------------------------------------
@app.route("/healthz")
def healthz():
    return {"status": "ok"}


init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
