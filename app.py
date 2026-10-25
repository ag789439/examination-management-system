

@app.route("/students", methods=["GET", "POST"])
def student_page():
    if request.method == "POST":
        values = [
            request.form.get("admission_no", "").strip(),
            request.form.get("name", "").strip(),
            request.form.get("class_name", "").strip(),
            request.form.get("roll_no", "").strip()
        ]

        if not all(values):
            flash("Please fill in every field.")
        else:
            try:
                with get_db() as conn:
                    conn.execute("""
                        INSERT INTO students
                        (admission_no, name, class_name, roll_no)
                        VALUES (%s, %s, %s, %s)
                    """, values)
                flash("Student added successfully.")
            except psycopg.errors.UniqueViolation:
                flash("Admission number already exists.")

        return redirect(url_for("student_page"))

    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM students ORDER BY id DESC"
        ).fetchall()

    template = """
    <div class="panel">
      <h2>Add Student</h2>
      <form method="POST">
        <label>Admission Number
          <input name="admission_no" required>
        </label>
        <label>Student Name
          <input name="name" required>
        </label>
        <label>Class
          <input name="class_name" required>
        </label>
        <label>Roll Number
          <input name="roll_no" required>
        </label>
        <button type="submit">Save Student</button>
      </form>
    </div>

    <div class="panel">
      <h2>Student Records</h2>
      <div class="tablewrap">
        <table>
          <tr>
            <th>ID</th>
            <th>Admission No.</th>
            <th>Name</th>
            <th>Class</th>
            <th>Roll No.</th>
          </tr>
          {% for s in rows %}
          <tr>
            <td>{{ s.id }}</td>
            <td>{{ s.admission_no }}</td>
            <td>{{ s.name }}</td>
            <td>{{ s.class_name }}</td>
            <td>{{ s.roll_no }}</td>
          </tr>
          {% endfor %}
        </table>
      </div>
    </div>
    """
    return page("Student Management", template, rows=rows)

    <section class="panel"><h2>Add Student</h2>
    <form method="post">
      <label>Admission Number<input name="admission_no" required></label>
      <label>Student Name<input name="name" required></label>
      <label>Class<input name="class_name" placeholder="XII-A" required></label>
      <label>Roll Number<input name="roll_no" required></label>
      <button type="submit">Save Student</button>
    </form></section>
    <section class="panel"><h2>Student Records</h2><div class="tablewrap"><table>
    <tr><th>Admission No.</th><th>Name</th><th>Class</th><th>Roll No.</th></tr>
    {% for s in rows %}<tr><td>{{ s.admission_no }}</td><td>{{ s.name }}</td>
    <td>{{ s.class_name }}</td><td>{{ s.roll_no }}</td></tr>
    {% else %}<tr><td colspan="4">No students yet.</td></tr>{% endfor %}
    </table></div></section>
    """
    return page("Students", template, rows=rows)


@app.route("/exams", methods=["GET", "POST"])
def exam_page():
    if request.method == "POST":
        name = request.form.get("exam_name", "").strip()
        subject = request.form.get("subject", "").strip()
        exam_date = request.form.get("exam_date", "")
        try:
            maximum = float(request.form.get("max_marks", ""))
            if not name or not subject or not exam_date or maximum <= 0:
                raise ValueError
            with get_db() as conn:
                conn.execute("""
                    INSERT INTO exams(exam_name,subject,exam_date,max_marks)
                    VALUES (%s,%s,%s,%s)
                """, (name, subject, exam_date, maximum))
            flash("Exam added successfully.")
        except ValueError:
            flash("Enter valid exam details and maximum marks.")
        return redirect(url_for("exam_page"))

    with get_db() as conn:
        rows = conn.execute("SELECT * FROM exams ORDER BY exam_date DESC").fetchall()

    template = """
    <section class="panel"><h2>Add Exam</h2>
    <form method="post">
      <label>Exam Name<input name="exam_name" required></label>
      <label>Subject<input name="subject" required></label>
      <label>Exam Date<input type="date" name="exam_date" required></label>
      <label>Maximum Marks<input type="number" min="0.01" step="0.01" name="max_marks" required></label>
      <button type="submit">Save Exam</button>
    </form></section>
    <section class="panel"><h2>Exam Schedule</h2><div class="tablewrap"><table>
    <tr><th>Exam</th><th>Subject</th><th>Date</th><th>Maximum Marks</th></tr>
    {% for e in rows %}<tr><td>{{ e.exam_name }}</td><td>{{ e.subject }}</td>
    <td>{{ e.exam_date }}</td><td>{{ e.max_marks }}</td></tr>
    {% else %}<tr><td colspan="4">No exams yet.</td></tr>{% endfor %}
    </table></div></section>
    """
    return page("Exams", template, rows=rows)


@app.route("/marks", methods=["GET", "POST"])
def marks_page():
    if request.method == "POST":
        try:
            sid = int(request.form.get("student_id", ""))
            eid = int(request.form.get("exam_id", ""))
            obtained = float(request.form.get("marks_obtained", ""))
            if obtained < 0:
                raise ValueError

            with get_db() as conn:
                exam = conn.execute(
                    "SELECT max_marks FROM exams WHERE id=%s", (eid,)
                ).fetchone()
                student = conn.execute(
                    "SELECT id FROM students WHERE id=%s", (sid,)
                ).fetchone()

                if not exam or not student:
                    flash("Select a valid student and exam.")
                elif obtained > float(exam["max_marks"]):
                    flash("Marks exceed the maximum marks.")
                else:
                    conn.execute("""
                        INSERT INTO marks(student_id,exam_id,marks_obtained)
                        VALUES (%s,%s,%s)
                        ON CONFLICT(student_id,exam_id)
                        DO UPDATE SET marks_obtained=EXCLUDED.marks_obtained
                    """, (sid, eid, obtained))
                    flash("Marks saved successfully.")
        except ValueError:
            flash("Please enter valid marks.")
        return redirect(url_for("marks_page"))

    with get_db() as conn:
        students = conn.execute(
            "SELECT id,name,admission_no FROM students ORDER BY name"
        ).fetchall()
        exams = conn.execute(
            "SELECT id,exam_name,subject,max_marks FROM exams ORDER BY exam_date DESC"
        ).fetchall()

    template = """
    <section class="panel"><h2>Marks Entry</h2>
    {% if not students or not exams %}
    <p>First add at least one student and one exam.</p>
    {% else %}
    <form method="post">
      <label>Student<select name="student_id" required>
      {% for s in students %}<option value="{{ s.id }}">{{ s.name }} ({{ s.admission_no }})</option>{% endfor %}
      </select></label>
      <label>Exam<select name="exam_id" required>
      {% for e in exams %}<option value="{{ e.id }}">{{ e.exam_name }} - {{ e.subject }} (Max {{ e.max_marks }})</option>{% endfor %}
      </select></label>
      <label>Marks Obtained<input type="number" name="marks_obtained" min="0" step="0.01" required></label>
      <button type="submit">Save Marks</button>
    </form>
    {% endif %}</section>
    """
    return page("Marks Entry", template, students=students, exams=exams)


@app.route("/results")
def results_page():
    with get_db() as conn:
        rows = conn.execute("""
            SELECT s.admission_no,s.name,s.class_name,e.exam_name,e.subject,
                   e.max_marks,m.marks_obtained,
                   ROUND((m.marks_obtained/e.max_marks*100)::numeric,2) AS percentage
            FROM marks m
            JOIN students s ON s.id=m.student_id
            JOIN exams e ON e.id=m.exam_id
            ORDER BY s.name,e.exam_name
        """).fetchall()

    template = """
    <section class="panel"><h2>Results</h2><div class="tablewrap"><table>
    <tr><th>Admission No.</th><th>Student</th><th>Class</th><th>Exam</th>
    <th>Subject</th><th>Marks</th><th>Percentage</th></tr>
    {% for r in rows %}<tr><td>{{ r.admission_no }}</td><td>{{ r.name }}</td>
    <td>{{ r.class_name }}</td><td>{{ r.exam_name }}</td><td>{{ r.subject }}</td>
    <td>{{ r.marks_obtained }} / {{ r.max_marks }}</td><td>{{ r.percentage }}%</td></tr>
    {% else %}<tr><td colspan="7">No results yet. Add marks first.</td></tr>{% endfor %}
    </table></div></section>
    """
    return page("Results", template, rows=rows)


@app.route("/health")
def health():
    try:
        with get_db() as conn:
            conn.execute("SELECT 1")
        return {"status": "ok", "database": "connected"}
    except Exception:
        app.logger.exception("Database health check failed")
        return {"status": "error", "message": "Database connection failed"}, 503


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
