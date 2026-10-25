
import os
from functools import wraps

from flask import (
    Flask, request, redirect, url_for, session,
    flash, render_template_string
)
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg
from psycopg.rows import dict_row

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("Set SECRET_KEY in Render environment variables.")

DATABASE_URL = os.environ.get("DATABASE_URL")


def get_db():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured.")
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def init_db():
    """Add authentication tables without deleting existing academic records."""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id BIGSERIAL PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL
                    CHECK (role IN ('admin', 'teacher', 'student')),
                student_id INTEGER UNIQUE
                    REFERENCES students(id) ON DELETE CASCADE,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                CHECK (
                    (role = 'student' AND student_id IS NOT NULL)
                    OR
                    (role IN ('admin', 'teacher') AND student_id IS NULL)
                )
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS polls (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL UNIQUE
                    REFERENCES users(id) ON DELETE CASCADE,
                choice TEXT NOT NULL CHECK (
                    choice IN (
                        'Physics', 'Chemistry', 'Mathematics',
                        'Biology', 'English'
                    )
                ),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        conn.commit()


def create_initial_admin():
    username = os.environ.get("ADMIN_USERNAME", "").strip()
    password = os.environ.get("ADMIN_PASSWORD", "")

    if not username or not password:
        return

    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM users WHERE role = 'admin' LIMIT 1"
        ).fetchone()

        if not existing:
            conn.execute(
                """
                INSERT INTO users (username, password_hash, role)
                VALUES (%s, %s, 'admin')
                """,
                (username, generate_password_hash(password))
            )
            conn.commit()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please log in first.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def roles_required(*roles):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if session.get("role") not in roles:
                flash("You do not have permission to access this page.", "error")
                return redirect(url_for("dashboard"))
            return view(*args, **kwargs)
        return wrapped
    return decorator


def page(title, content, **context):
    inner = render_template_string(content, **context)
    return render_template_string(
        BASE, title=title, content=inner
    )

BASE = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ title }} | ExamPortal</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:#f3f6fc;color:#172033;font-family:Segoe UI,Arial,sans-serif}
header{background:#14213d;color:white;padding:16px 5%;display:flex;
justify-content:space-between;align-items:center;gap:15px;flex-wrap:wrap}
.brand{font-size:21px;font-weight:800}
nav{display:flex;gap:7px;flex-wrap:wrap}
nav a{color:#eaf0ff;text-decoration:none;padding:8px 10px;border-radius:8px}
nav a:hover{background:#304263}
.wrap{max-width:1150px;margin:28px auto;padding:0 18px}
h1{font-size:28px;margin-bottom:8px}
.sub,.muted{color:#69758b}
.sub{margin-bottom:22px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:15px;margin:20px 0}
.columns{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:18px}
.card{background:white;padding:20px;border-radius:14px;border:1px solid #e3e9f3;margin-bottom:16px}
.metric{font-size:30px;font-weight:800;margin-top:8px}
label{font-size:13px;font-weight:700}
input,select{width:100%;padding:11px;border:1px solid #d6deeb;border-radius:8px;background:white}
button,.btn{background:#2563eb;color:white;border:0;border-radius:8px;padding:10px 14px;cursor:pointer;text-decoration:none;display:inline-block}
form.stack{display:grid;gap:12px}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{text-align:left;padding:11px 8px;border-bottom:1px solid #e4eaf3}
th{font-size:12px;color:#69758b}
.table-wrap{overflow-x:auto}
.notice{background:#e8f1ff;color:#17449b;padding:12px;border-radius:8px;margin-bottom:12px}
.notice.error{background:#fff0f0;color:#9b2222}
.actions{display:flex;gap:9px;flex-wrap:wrap}
footer{text-align:center;padding:25px;color:#69758b;font-size:12px}
</style>
</head>
<body>
<header>
 <div class="brand">◈ ExamPortal</div>
 {% if session.get('user_id') %}
 <nav>
  <a href="{{ url_for('dashboard') }}">Dashboard</a>
  {% if session.get('role') in ['admin','teacher'] %}
   <a href="{{ url_for('students') }}">Students</a>
   <a href="{{ url_for('exams') }}">Exams</a>
   <a href="{{ url_for('marks') }}">Marks</a>
   <a href="{{ url_for('results') }}">Results</a>
  {% endif %}
  {% if session.get('role') == 'admin' %}
   <a href="{{ url_for('accounts') }}">Accounts</a>
  {% endif %}
  <a href="{{ url_for('poll') }}">My Poll</a>
  <a href="{{ url_for('logout') }}">Logout</a>
 </nav>
 <span>{{ session.get('display_name') }} · {{ session.get('role')|title }}</span>
 {% endif %}
</header>
<div class="wrap">
 {% for category,message in get_flashed_messages(with_categories=true) %}
 <div class="notice {{ 'error' if category == 'error' else '' }}">{{ message }}</div>
 {% endfor %}
 {{ content|safe }}
</div>
<footer>ExamPortal · Examination Management System</footer>
</body>
</html>
"""

@app.route("/health")
def health():
    try:
        with get_db() as conn:
            conn.execute("SELECT 1")
        return {"status": "ok"}, 200
    except Exception:
        app.logger.exception("Health check failed")
        return {"status": "database_error"}, 500


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        with get_db() as conn:
            user = conn.execute("""
                SELECT u.id,u.username,u.password_hash,u.role,u.student_id,
                       s.name AS student_name
                FROM users u
                LEFT JOIN students s ON s.id=u.student_id
                WHERE u.username=%s
            """, (username,)).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            session["student_id"] = user["student_id"]
            session["display_name"] = user["student_name"] or user["username"]
            return redirect(url_for("dashboard"))

        flash("Incorrect username or password.", "error")

    return page("Login", """
    <div class="card" style="max-width:430px;margin:40px auto">
      <h1>Welcome back</h1>
      <p class="sub">Sign in to your personal examination dashboard.</p>
      <form method="post" class="stack">
        <div><label>Username / Admission number</label>
        <input name="username" required autocomplete="username"></div>
        <div><label>Password</label>
        <input type="password" name="password" required autocomplete="current-password"></div>
        <button>Sign in</button>
      </form>
      <p class="muted">Students sign in using their admission number.</p>
    </div>
    """)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def dashboard():
    if session["role"] == "student":
        sid = session["student_id"]

        with get_db() as conn:
            student = conn.execute(
                "SELECT * FROM students WHERE id=%s", (sid,)
            ).fetchone()

            marks = conn.execute("""
                SELECT e.exam_name,e.subject,e.exam_date,e.max_marks,
                       m.marks_obtained,
                       ROUND(
                         m.marks_obtained::numeric /
                         NULLIF(e.max_marks,0) * 100, 2
                       ) AS percentage
                FROM marks m
                JOIN exams e ON e.id=m.exam_id
                WHERE m.student_id=%s
                ORDER BY e.exam_date DESC
            """, (sid,)).fetchall()

            summary = conn.execute("""
                SELECT COUNT(*) AS total,
                       ROUND(AVG(
                         m.marks_obtained::numeric /
                         NULLIF(e.max_marks,0) * 100
                       ),2) AS average
                FROM marks m JOIN exams e ON e.id=m.exam_id
                WHERE m.student_id=%s
            """, (sid,)).fetchone()

            upcoming = conn.execute("""
                SELECT exam_name,subject,exam_date
                FROM exams WHERE exam_date >= CURRENT_DATE
                ORDER BY exam_date LIMIT 5
            """).fetchall()

        return page("My Dashboard", """
        <h1>Hello, {{ student.name }}!</h1>
        <p class="sub">Your personal results and upcoming exams.</p>
        <div class="grid">
          <div class="card"><div class="muted">Admission number</div>
            <div class="metric">{{ student.admission_no }}</div></div>
          <div class="card"><div class="muted">Class</div>
            <div class="metric">{{ student.class_name }}</div></div>
          <div class="card"><div class="muted">Results recorded</div>
            <div class="metric">{{ summary.total }}</div></div>
          <div class="card"><div class="muted">Average</div>
            <div class="metric">{{ summary.average if summary.average is not none else '—' }}{% if summary.average is not none %}%{% endif %}</div></div>
        </div>
        <div class="columns">
          <div class="card"><h2>My results</h2><div class="table-wrap"><table>
          <tr><th>Exam</th><th>Subject</th><th>Marks</th><th>%</th></tr>
          {% for m in marks %}
          <tr><td>{{ m.exam_name }}</td><td>{{ m.subject }}</td>
          <td>{{ m.marks_obtained }}/{{ m.max_marks }}</td>
          <td>{{ m.percentage if m.percentage is not none else '—' }}</td></tr>
          {% else %}<tr><td colspan="4">No results yet.</td></tr>{% endfor %}
          </table></div></div>
          <div class="card"><h2>Upcoming exams</h2><table>
          <tr><th>Exam</th><th>Subject</th><th>Date</th></tr>
          {% for e in upcoming %}
          <tr><td>{{ e.exam_name }}</td><td>{{ e.subject }}</td><td>{{ e.exam_date }}</td></tr>
          {% else %}<tr><td colspan="3">No upcoming exams.</td></tr>{% endfor %}
          </table></div>
        </div>
        """, student=student, marks=marks, summary=summary, upcoming=upcoming)

    with get_db() as conn:
        stats = conn.execute("""
            SELECT
              (SELECT COUNT(*) FROM students) AS students,
              (SELECT COUNT(*) FROM exams) AS exams,
              (SELECT COUNT(*) FROM marks) AS entries,
              (SELECT ROUND(AVG(
                m.marks_obtained::numeric/NULLIF(e.max_marks,0)*100
              ),2) FROM marks m JOIN exams e ON e.id=m.exam_id) AS average
        """).fetchone()

        classes = conn.execute("""
            SELECT s.class_name,
                   ROUND(AVG(m.marks_obtained::numeric /
                   NULLIF(e.max_marks,0)*100),2) AS average
            FROM marks m JOIN exams e ON e.id=m.exam_id
            JOIN students s ON s.id=m.student_id
            GROUP BY s.class_name ORDER BY s.class_name
        """).fetchall()

        subjects = conn.execute("""
            SELECT e.subject,
                   ROUND(AVG(m.marks_obtained::numeric /
                   NULLIF(e.max_marks,0)*100),2) AS average
            FROM marks m JOIN exams e ON e.id=m.exam_id
            GROUP BY e.subject ORDER BY e.subject
        """).fetchall()

    return page("Dashboard", """
    <h1>{{ session.role|title }} Dashboard</h1>
    <p class="sub">School-wide examination analytics.</p>
    <div class="grid">
      <div class="card"><div class="muted">Students</div><div class="metric">{{ stats.students }}</div></div>
      <div class="card"><div class="muted">Exams</div><div class="metric">{{ stats.exams }}</div></div>
      <div class="card"><div class="muted">Marks entries</div><div class="metric">{{ stats.entries }}</div></div>
      <div class="card"><div class="muted">Average</div><div class="metric">{{ stats.average if stats.average is not none else '—' }}{% if stats.average is not none %}%{% endif %}</div></div>
    </div>
    <div class="columns">
      <div class="card"><h2>Performance by class</h2><canvas id="classes"></canvas></div>
      <div class="card"><h2>Performance by subject</h2><canvas id="subjects"></canvas></div>
    </div>
    <div class="card"><h2>Quick actions</h2><div class="actions">
      <a class="btn" href="{{ url_for('students') }}">Students</a>
      <a class="btn" href="{{ url_for('exams') }}">Exams</a>
      <a class="btn" href="{{ url_for('marks') }}">Marks entry</a>
      <a class="btn" href="{{ url_for('results') }}">Results</a>
      {% if session.role == 'admin' %}<a class="btn" href="{{ url_for('accounts') }}">Manage accounts</a>{% endif %}
    </div></div>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
    const classLabels={{ classes|map(attribute='class_name')|list|tojson }};
    const classData={{ classes|map(attribute='average')|list|tojson }};
    const subjectLabels={{ subjects|map(attribute='subject')|list|tojson }};
    const subjectData={{ subjects|map(attribute='average')|list|tojson }};
    if(window.Chart){
      new Chart(document.getElementById('classes'),{type:'bar',
        data:{labels:classLabels,datasets:[{label:'Average %',data:classData,
        backgroundColor:'#2563eb'}]},options:{scales:{y:{beginAtZero:true,max:100}}}});
      new Chart(document.getElementById('subjects'),{type:'doughnut',
        data:{labels:subjectLabels,datasets:[{data:subjectData}]},
        options:{plugins:{legend:{position:'bottom'}}}});
    }
    </script>
    """, stats=stats, classes=classes, subjects=subjects)
