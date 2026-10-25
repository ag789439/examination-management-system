"""
==========================================================================
 EXAM MANAGER  -  Examination Module Management System  (modern GUI)
--------------------------------------------------------------------------
 A single-file Tkinter desktop application with SQLite storage and a
 flat, modern interface: dark sidebar navigation, cards, KPI tiles and
 clean data tables.

 Pages
   Dashboard      - counts, recent admissions, upcoming exams
   Students       - admission + student master data
   Exams          - exam master (name, type, session, dates)
   Subjects       - subject master
   Exam Schedule  - date / time / room / invigilator / max & pass marks
   Marks Entry    - subject-wise marks entry per student
   Results        - total, percentage, grade, rank, pass/fail + CSV export

 Run:
     python exam_module.py
     python exam_module.py --selftest      (headless check, no window)

 Requirements:
     Python 3.8+ with Tkinter and SQLite3 - both ship with standard
     Python installers. No third-party packages.
==========================================================================
"""

import calendar
import csv
import os
import sqlite3
import sys
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, font as tkfont, messagebox, ttk

# --------------------------------------------------------------------------
#  CONSTANTS
# --------------------------------------------------------------------------
APP_TITLE = "Exam Manager"
APP_VERSION = "2.1"

def _app_dir():
    """Folder the app should treat as "its own".

    Running as a plain .py file that is the script's folder. Running as a
    frozen .exe (PyInstaller) it must be the folder holding the .exe - the
    temporary extraction folder would silently throw the database away when
    the app closes.
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = _app_dir()
DB_FILE = os.path.join(BASE_DIR, "exam_module.db")
ERROR_LOG = os.path.join(BASE_DIR, "exam_module_error.log")

# Window / taskbar icon: a 128x128 PNG embedded as base64 so the app stays a
# single file. If app_icon.ico (or app_icon.png) sits next to this script it is
# used instead - that gives the sharpest taskbar icon on Windows.
ICON_PNG_B64 = (
    "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"
)

GENDERS = ["Male", "Female", "Other"]
STUDENT_STATUS = ["Active", "Inactive", "Passed Out", "Left"]
EXAM_TYPES = ["Unit Test", "Mid Term", "Half Yearly", "Annual / Final",
              "Pre-Board", "Practical", "Internal Assessment"]
EXAM_STATUS = ["Scheduled", "Ongoing", "Completed", "Result Declared", "Cancelled"]
SECTIONS = ["A", "B", "C", "D", "E"]

# ---- palette -------------------------------------------------------------
BG = "#F4F6FB"          # app background
WHITE = "#FFFFFF"
INK = "#0F172A"         # primary text
MUTED = "#64748B"       # secondary text
LINE = "#E2E8F0"        # borders
SOFT = "#F8FAFC"        # zebra / subtle fill
ACCENT = "#4F46E5"      # indigo
ACCENT_DARK = "#4338CA"
ACCENT_SOFT = "#EEF2FF"
SIDEBAR = "#0F172A"
SIDEBAR_HOVER = "#1E293B"
DANGER = "#DC2626"
DANGER_SOFT = "#FEE2E2"
SUCCESS = "#059669"
SUCCESS_SOFT = "#D1FAE5"

NAV = [
    ("dashboard", "Dashboard"),
    ("students", "Students"),
    ("exams", "Exams"),
    ("subjects", "Subjects"),
    ("schedule", "Exam Schedule"),
    ("marks", "Marks Entry"),
    ("results", "Results"),
]


# --------------------------------------------------------------------------
#  SMALL HELPERS  (pure functions - no UI)
# --------------------------------------------------------------------------
def norm_date(text):
    """Accept dd/mm/yyyy, dd-mm-yyyy, dd.mm.yyyy or yyyy-mm-dd.
    Returns 'YYYY-MM-DD', '' when blank, or None when invalid."""
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
    """'YYYY-MM-DD' -> 'DD/MM/YYYY' for display."""
    text = (text or "").strip()
    if not text:
        return ""
    try:
        return datetime.strptime(text, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return text


def norm_time(text):
    """Accept HH:MM or HH:MM AM/PM. Returns 'HH:MM' 24h, '' or None."""
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
    """CBSE style scholastic grade from percentage."""
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


# --------------------------------------------------------------------------
#  DATABASE LAYER
# --------------------------------------------------------------------------
def resolve_db_file():
    """Pick a writable location for the database.

    Normally the folder holding this script. If that folder is read-only
    (e.g. the script sits in Program Files or a shared network drive) the
    user's home folder is used instead, so the app still starts.
    """
    global DB_FILE, ERROR_LOG
    for folder in (BASE_DIR, os.path.expanduser("~"), os.getcwd()):
        path = os.path.join(folder, "exam_module.db")
        try:
            if os.path.exists(path):
                if os.access(path, os.W_OK):
                    DB_FILE = path
                    ERROR_LOG = os.path.join(folder, "exam_module_error.log")
                    return DB_FILE
                continue
            with open(path, "a", encoding="utf-8"):
                pass
            DB_FILE = path
            ERROR_LOG = os.path.join(folder, "exam_module_error.log")
            return DB_FILE
        except OSError:
            continue
    return DB_FILE


def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript(
        """
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
    )
    conn.commit()
    conn.close()


# --- generic query helpers -------------------------------------------------
def fetch_all(sql, params=()):
    conn = get_conn()
    try:
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def fetch_one(sql, params=()):
    conn = get_conn()
    try:
        return conn.execute(sql, params).fetchone()
    finally:
        conn.close()


def execute(sql, params=()):
    """Run an INSERT/UPDATE/DELETE. Returns lastrowid. The connection is
    always closed - even when SQLite raises (e.g. a UNIQUE violation)."""
    conn = get_conn()
    try:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def count_rows(sql, params=()):
    row = fetch_one(sql, params)
    return int(row[0]) if row else 0


# --------------------------------------------------------------------------
#  BUSINESS LOGIC  (pure, testable)
# --------------------------------------------------------------------------
def compute_results(exam_id, class_name):
    """Return a list of result dicts for one exam + class, ranked by percentage.

    Each dict: roll_no, name, admission_no, obtained, total_max, percentage,
               grade, failed_subjects, result, subjects, rank
    """
    schedule = fetch_all(
        "SELECT subject_id, max_marks, pass_marks FROM exam_schedule WHERE exam_id=?",
        (exam_id,),
    )
    if not schedule:
        return []

    max_by_sub = {r["subject_id"]: (r["max_marks"] or 0) for r in schedule}
    pass_by_sub = {r["subject_id"]: (r["pass_marks"] or 0) for r in schedule}

    students = fetch_all(
        "SELECT id, admission_no, roll_no, name FROM students "
        "WHERE class_name=? ORDER BY CAST(roll_no AS INTEGER), roll_no",
        (class_name,),
    )
    marks = fetch_all("SELECT * FROM marks WHERE exam_id=?", (exam_id,))
    marks_by_student = {}
    for m in marks:
        marks_by_student.setdefault(m["student_id"], {})[m["subject_id"]] = m

    results = []
    for st in students:
        smap = marks_by_student.get(st["id"], {})
        if not smap:
            continue
        obtained = 0.0
        total_max = 0.0
        failed = 0
        detail = []
        for sub_id, mx in max_by_sub.items():
            row = smap.get(sub_id)
            if row is None or row["marks_obtained"] is None:
                continue
            got = float(row["marks_obtained"])
            obtained += got
            total_max += float(mx)
            if got < float(pass_by_sub.get(sub_id, 0)):
                failed += 1
            detail.append((sub_id, got, float(mx)))
        if total_max <= 0:
            continue
        pct = round(obtained / total_max * 100, 2)
        passed = failed == 0 and pct >= 33
        results.append(
            {
                "student_id": st["id"],
                "admission_no": st["admission_no"],
                "roll_no": st["roll_no"],
                "name": st["name"],
                "obtained": round(obtained, 2),
                "total_max": round(total_max, 2),
                "percentage": pct,
                "grade": grade_for(pct),
                "failed_subjects": failed,
                "result": "Pass" if passed else "Fail",
                "subjects": detail,
            }
        )

    results.sort(key=lambda r: (-r["percentage"], r["roll_no"]))
    rank = 0
    last_pct = None
    for i, r in enumerate(results, start=1):
        if last_pct is None or r["percentage"] != last_pct:
            rank = i
            last_pct = r["percentage"]
        r["rank"] = rank
    return results


# ==========================================================================
#  UI HELPERS
# ==========================================================================
def pick_font(root):
    """First modern font that actually exists on this machine."""
    try:
        families = set(tkfont.families(root))
    except tk.TclError:
        families = set()
    for name in ("Segoe UI", "Inter", "SF Pro Text", "Helvetica Neue",
                 "DejaVu Sans", "Noto Sans", "Arial"):
        if name in families:
            return name
    return "TkDefaultFont"


def exam_label(row):
    """How an exam is written in dropdowns and lists: type, class, year."""
    try:
        etype = row["exam_type"] or row["exam_name"] or "Exam"
    except (IndexError, KeyError):
        etype = "Exam"
    parts = [etype]
    try:
        cls = (row["class_name"] or "").strip()
    except (IndexError, KeyError):
        cls = ""
    if cls:
        parts.append(f"Class {cls}")
    try:
        year = (row["academic_year"] or "").strip()
    except (IndexError, KeyError):
        year = ""
    if year:
        parts.append(year)
    return "  ·  ".join(parts)


def sync_hscroll(tree):
    """Show the horizontal scrollbar only when the columns really overflow."""
    hs = getattr(tree, "_hscroll", None)
    if hs is None:
        return
    try:
        first, last = tree.xview()
    except tk.TclError:
        return
    if first <= 0.0 and last >= 1.0:
        hs.grid_remove()
    else:
        hs.grid()


def add_row(tree, values, iid=None, tags=()):
    """Insert a row with zebra striping."""
    n = len(tree.get_children())
    all_tags = tuple(tags) + (("odd",) if n % 2 else ())
    return tree.insert("", "end", iid=iid, values=values, tags=all_tags)


def clear_tree(tree):
    for item in tree.get_children():
        tree.delete(item)


# ==========================================================================
#  DATE PICKER
# ==========================================================================
class DatePicker(tk.Toplevel):
    """Small month calendar used by every date field.

    Nothing is ever filled in automatically - the user either types the date
    or clicks a day here.
    """

    WEEKDAYS = ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")

    def __init__(self, master, initial_text, on_pick):
        super().__init__(master)
        self.on_pick = on_pick
        self.font = getattr(master, "font_family", "TkDefaultFont")
        self.title("Pick a date")
        self.configure(bg=WHITE)
        self.resizable(False, False)
        self.transient(master)
        try:
            self.grab_set()
        except tk.TclError:
            pass

        today = datetime.now().date()
        parsed = norm_date(initial_text)
        base = today
        if parsed:
            base = datetime.strptime(parsed, "%Y-%m-%d").date()
        self.year = base.year
        self.month = base.month
        self.selected = base if parsed else None

        self.body = tk.Frame(self, bg=WHITE, highlightthickness=1,
                             highlightbackground=LINE)
        self.body.pack(fill="both", expand=True, padx=1, pady=1)
        self._render()
        self.bind("<Escape>", lambda e: self.destroy())

    # -- drawing ------------------------------------------------------
    def _render(self):
        for child in self.body.winfo_children():
            child.destroy()
        f = self.font

        head = tk.Frame(self.body, bg=WHITE)
        head.pack(fill="x", padx=10, pady=(10, 6))
        ttk.Button(head, text="\u2039", width=2, style="Pick.TButton",
                   command=lambda: self._shift(-1)).pack(side="left")
        tk.Label(head, text=f"{calendar.month_name[self.month]} {self.year}",
                 bg=WHITE, fg=INK, font=(f, 11, "bold")).pack(side="left",
                                                              expand=True)
        ttk.Button(head, text="\u203a", width=2, style="Pick.TButton",
                   command=lambda: self._shift(1)).pack(side="right")

        grid = tk.Frame(self.body, bg=WHITE)
        grid.pack(padx=10, pady=(0, 6))
        for i, name in enumerate(self.WEEKDAYS):
            tk.Label(grid, text=name, bg=WHITE, fg=MUTED, width=3,
                     font=(f, 8, "bold")).grid(row=0, column=i, pady=(0, 4))

        today = datetime.now().date()
        weeks = calendar.Calendar(firstweekday=0).monthdayscalendar(
            self.year, self.month)
        for r, week in enumerate(weeks, start=1):
            for c, day in enumerate(week):
                if day == 0:
                    tk.Label(grid, text="", bg=WHITE, width=3).grid(
                        row=r, column=c, pady=1)
                    continue
                is_sel = bool(self.selected) and self.selected ==                     datetime(self.year, self.month, day).date()
                is_today = today == datetime(self.year, self.month, day).date()
                bg = ACCENT if is_sel else (ACCENT_SOFT if is_today else WHITE)
                fg = WHITE if is_sel else INK
                cell = tk.Label(grid, text=str(day), bg=bg, fg=fg,
                                width=3, pady=4, font=(f, 9), cursor="hand2")
                cell.grid(row=r, column=c, padx=1, pady=1)
                cell.bind("<Button-1>", lambda e, d=day: self._pick(d))
                cell.bind("<Enter>", lambda e, w=cell, s=is_sel:
                          w.configure(bg=ACCENT if s else ACCENT_SOFT))
                cell.bind("<Leave>", lambda e, w=cell, s=is_sel, t=is_today:
                          w.configure(bg=ACCENT if s else
                                      (ACCENT_SOFT if t else WHITE)))

        foot = tk.Frame(self.body, bg=WHITE)
        foot.pack(fill="x", padx=10, pady=(2, 10))
        ttk.Button(foot, text="Today", style="Ghost.TButton",
                   command=lambda: self._pick(datetime.now().day)).pack(
            side="left")
        ttk.Button(foot, text="Clear", style="Ghost.TButton",
                   command=self._clear).pack(side="left", padx=6)
        ttk.Button(foot, text="Close", style="Ghost.TButton",
                   command=self.destroy).pack(side="right")

    # -- actions ------------------------------------------------------
    def _shift(self, months):
        month = self.month + months
        year = self.year
        while month < 1:
            month += 12
            year -= 1
        while month > 12:
            month -= 12
            year += 1
        self.month, self.year = month, year
        self._render()

    def _pick(self, day):
        value = datetime(self.year, self.month, day).date()
        self.on_pick(value)
        self.destroy()

    def _clear(self):
        self.on_pick(None)
        self.destroy()


# ==========================================================================
#  MARKS ENTRY DIALOG
# ==========================================================================
class MarksDialog(tk.Toplevel):
    def __init__(self, master, exam_id, subject_id, student, on_saved):
        super().__init__(master)
        self.exam_id = exam_id
        self.subject_id = subject_id
        self.student = student
        self.on_saved = on_saved
        font = getattr(master, "font_family", "TkDefaultFont")

        self.title("Enter marks")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        sched = fetch_one(
            "SELECT max_marks, pass_marks FROM exam_schedule "
            "WHERE exam_id=? AND subject_id=?",
            (exam_id, subject_id),
        )
        self.max_marks = float(sched["max_marks"] or 100) if sched else 100.0
        self.pass_marks = float(sched["pass_marks"] or 33) if sched else 33.0

        existing = fetch_one(
            "SELECT * FROM marks WHERE exam_id=? AND student_id=? AND subject_id=?",
            (exam_id, student["id"], subject_id),
        )

        card = tk.Frame(self, bg=WHITE, highlightthickness=1,
                        highlightbackground=LINE)
        card.pack(fill="both", expand=True, padx=16, pady=16)
        body = tk.Frame(card, bg=WHITE)
        body.pack(fill="both", expand=True, padx=20, pady=18)

        tk.Label(body, text=student["name"], bg=WHITE, fg=INK,
                 font=(font, 14, "bold")).pack(anchor="w")
        tk.Label(body, text=f"Roll No {student['roll_no']}   ·   "
                            f"Max {fmt_num(self.max_marks)}   ·   "
                            f"Pass {fmt_num(self.pass_marks)}",
                 bg=WHITE, fg=MUTED, font=(font, 9)).pack(anchor="w", pady=(2, 16))

        tk.Label(body, text="MARKS OBTAINED", bg=WHITE, fg=MUTED,
                 font=(font, 8, "bold")).pack(anchor="w")
        self.var_marks = tk.StringVar(
            value="" if not existing or existing["marks_obtained"] is None
            else fmt_num(existing["marks_obtained"]))
        ent = ttk.Entry(body, textvariable=self.var_marks, width=14,
                        style="Modern.TEntry", font=(font, 13))
        ent.pack(anchor="w", pady=(4, 14), ipady=4)
        ent.focus_set()
        ent.bind("<Return>", lambda e: self.save())

        tk.Label(body, text="REMARKS", bg=WHITE, fg=MUTED,
                 font=(font, 8, "bold")).pack(anchor="w")
        self.var_remarks = tk.StringVar(
            value=(existing["remarks"] or "") if existing else "")
        ttk.Entry(body, textvariable=self.var_remarks, width=34,
                  style="Modern.TEntry").pack(anchor="w", pady=(4, 18), ipady=4)

        btns = tk.Frame(body, bg=WHITE)
        btns.pack(fill="x")
        ttk.Button(btns, text="Save marks", style="Accent.TButton",
                   command=self.save).pack(side="right", padx=(8, 0))
        ttk.Button(btns, text="Cancel", style="Ghost.TButton",
                   command=self.destroy).pack(side="right")
        ttk.Button(btns, text="Clear", style="Ghost.TButton",
                   command=lambda: self.var_marks.set("")).pack(
            side="right", padx=(0, 8))

    def save(self):
        raw = self.var_marks.get().strip()
        if raw == "":
            value = None
        else:
            value = to_float(raw)
            if value is None:
                messagebox.showerror("Invalid", "Marks must be a number.", parent=self)
                return
            if value < 0 or value > self.max_marks:
                messagebox.showerror(
                    "Out of range",
                    f"Marks must be between 0 and {fmt_num(self.max_marks)}.",
                    parent=self)
                return

        existing = fetch_one(
            "SELECT id FROM marks WHERE exam_id=? AND student_id=? AND subject_id=?",
            (self.exam_id, self.student["id"], self.subject_id),
        )
        if existing:
            execute(
                "UPDATE marks SET marks_obtained=?, remarks=?, "
                "updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (value, self.var_remarks.get().strip(), existing["id"]),
            )
        else:
            execute(
                "INSERT INTO marks (exam_id, student_id, subject_id, marks_obtained, remarks)"
                " VALUES (?,?,?,?,?)",
                (self.exam_id, self.student["id"], self.subject_id, value,
                 self.var_remarks.get().strip()),
            )
        self.on_saved()
        self.destroy()


# ==========================================================================
#  MAIN APPLICATION
# ==========================================================================
class ExamApp(tk.Tk):
    def __init__(self):
        super().__init__()
        init_db()
        self.report_callback_exception = self._on_tk_error

        self.font_family = pick_font(self)
        self.current_page = None
        self.pages = {}
        self.nav_items = {}

        self._set_window_icon()
        self.title(f"{APP_TITLE}  ·  Examination Module Management")
        self.geometry("1340x820")
        self.minsize(1140, 700)
        self.configure(bg=BG)

        self._setup_theme()
        self._build_sidebar()
        self._build_content()
        self._build_dashboard()
        self._build_students_page()
        self._build_exams_page()
        self._build_subjects_page()
        self._build_schedule_page()
        self._build_marks_page()
        self._build_results_page()

        self.show_page("dashboard")
        self.refresh_all()

    def _set_window_icon(self):
        """Give the window (and its dialogs) a real icon."""
        # 1) embedded PNG - works on Windows, macOS and Linux
        try:
            self._icon_img = tk.PhotoImage(data=ICON_PNG_B64)
            self.iconphoto(True, self._icon_img)
        except tk.TclError:
            self._icon_img = None
        # 2) a multi-size .ico looks better in the Windows taskbar and on
        #    desktop shortcuts. Look next to the script/.exe and - for a
        #    PyInstaller build - inside the bundled data folder too.
        for folder in (BASE_DIR, getattr(sys, "_MEIPASS", BASE_DIR)):
            ico = os.path.join(folder, "app_icon.ico")
            if os.path.exists(ico):
                try:
                    self.iconbitmap(ico)
                    break
                except tk.TclError:
                    continue

    # ------------------------------------------------------------------
    #  theming
    # ------------------------------------------------------------------
    def _setup_theme(self):
        f = self.font_family
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(".", background=BG, foreground=INK, font=(f, 10))
        style.configure("TFrame", background=BG)
        style.configure("Card.TFrame", background=WHITE)
        style.configure("TLabel", background=BG, foreground=INK, font=(f, 10))
        style.configure("Card.TLabel", background=WHITE, foreground=INK,
                        font=(f, 10))
        style.configure("Muted.TLabel", background=WHITE, foreground=MUTED,
                        font=(f, 9))
        style.configure("FieldLabel.TLabel", background=WHITE, foreground=MUTED,
                        font=(f, 9))
        style.configure("H1.TLabel", background=BG, foreground=INK,
                        font=(f, 18, "bold"))
        style.configure("H2.TLabel", background=BG, foreground=INK,
                        font=(f, 11, "bold"))
        style.configure("PageSub.TLabel", background=BG, foreground=MUTED,
                        font=(f, 10))

        # buttons -------------------------------------------------------
        style.configure("Accent.TButton", background=ACCENT, foreground=WHITE,
                        font=(f, 10, "bold"), borderwidth=0, focusthickness=0,
                        padding=(16, 8))
        style.map("Accent.TButton",
                  background=[("pressed", ACCENT_DARK), ("active", ACCENT_DARK),
                              ("disabled", "#C7D2FE")],
                  foreground=[("disabled", WHITE)])
        style.configure("Ghost.TButton", background=WHITE, foreground=INK,
                        font=(f, 10), borderwidth=1, bordercolor=LINE,
                        focusthickness=0, padding=(14, 7))
        style.map("Ghost.TButton",
                  background=[("pressed", SOFT), ("active", SOFT)],
                  bordercolor=[("active", "#CBD5E1")])
        style.configure("Pick.TButton", background=WHITE, foreground=MUTED,
                        font=(f, 9), borderwidth=1, bordercolor=LINE,
                        focusthickness=0, padding=(2, 4))
        style.map("Pick.TButton",
                  background=[("active", SOFT), ("pressed", SOFT)],
                  bordercolor=[("active", "#CBD5E1")],
                  foreground=[("active", ACCENT)])
        style.configure("Danger.TButton", background=WHITE, foreground=DANGER,
                        font=(f, 10), borderwidth=1, bordercolor="#FECACA",
                        focusthickness=0, padding=(14, 7))
        style.map("Danger.TButton",
                  background=[("pressed", DANGER_SOFT), ("active", DANGER_SOFT)])

        # inputs --------------------------------------------------------
        style.configure("Modern.TEntry", fieldbackground=WHITE, background=WHITE,
                        foreground=INK, bordercolor=LINE, lightcolor=WHITE,
                        darkcolor=WHITE, insertcolor=INK, padding=(8, 6),
                        relief="flat")
        style.map("Modern.TEntry",
                  bordercolor=[("focus", ACCENT)],
                  lightcolor=[("focus", ACCENT)],
                  darkcolor=[("focus", ACCENT)])
        style.configure("Modern.TCombobox", fieldbackground=WHITE,
                        background=WHITE, foreground=INK, bordercolor=LINE,
                        lightcolor=WHITE, darkcolor=WHITE, arrowcolor=MUTED,
                        padding=(8, 6), relief="flat")
        style.map("Modern.TCombobox",
                  fieldbackground=[("readonly", WHITE)],
                  bordercolor=[("focus", ACCENT), ("active", "#CBD5E1")],
                  arrowcolor=[("active", ACCENT)])
        self.option_add("*TCombobox*Listbox.background", WHITE)
        self.option_add("*TCombobox*Listbox.foreground", INK)
        self.option_add("*TCombobox*Listbox.selectBackground", ACCENT_SOFT)
        self.option_add("*TCombobox*Listbox.selectForeground", INK)
        self.option_add("*TCombobox*Listbox.font", (f, 10))

        # tables --------------------------------------------------------
        style.configure("Modern.Treeview", background=WHITE,
                        fieldbackground=WHITE, foreground=INK, borderwidth=0,
                        rowheight=30, font=(f, 10))
        style.configure("Modern.Treeview.Heading", background=SOFT,
                        foreground=MUTED, relief="flat", borderwidth=0,
                        font=(f, 9, "bold"), padding=(10, 9))
        style.map("Modern.Treeview.Heading",
                  background=[("active", "#EEF2F7")])
        style.map("Modern.Treeview",
                  background=[("selected", ACCENT_SOFT)],
                  foreground=[("selected", INK)])
        style.layout("Modern.Treeview", [
            ("Modern.Treeview.treearea", {"sticky": "nswe"})])

        style.configure("Modern.Vertical.TScrollbar", background="#CBD5E1",
                        troughcolor=WHITE, borderwidth=0, arrowsize=12,
                        width=10, relief="flat")
        style.map("Modern.Vertical.TScrollbar",
                  background=[("active", "#94A3B8")])
        style.configure("Modern.Horizontal.TScrollbar", background="#CBD5E1",
                        troughcolor=WHITE, borderwidth=0, arrowsize=12,
                        relief="flat")

    # ------------------------------------------------------------------
    #  shell: sidebar + content
    # ------------------------------------------------------------------
    def _build_sidebar(self):
        f = self.font_family
        bar = tk.Frame(self, bg=SIDEBAR, width=238)
        bar.pack(side="left", fill="y")
        bar.pack_propagate(False)

        brand = tk.Frame(bar, bg=SIDEBAR)
        brand.pack(fill="x", padx=22, pady=(26, 22))
        badge = tk.Frame(brand, bg=ACCENT, width=34, height=34)
        badge.pack(anchor="w", pady=(0, 10))
        badge.pack_propagate(False)
        tk.Label(badge, text="EX", bg=ACCENT, fg=WHITE,
                 font=(f, 11, "bold")).pack(expand=True)
        tk.Label(brand, text="Exam Manager", bg=SIDEBAR, fg=WHITE,
                 font=(f, 14, "bold")).pack(anchor="w")
        tk.Label(brand, text="Examination module", bg=SIDEBAR, fg="#7C8BA1",
                 font=(f, 9)).pack(anchor="w", pady=(2, 0))

        tk.Frame(bar, bg="#1E293B", height=1).pack(fill="x", padx=18, pady=(0, 14))

        for key, label in NAV:
            row = tk.Frame(bar, bg=SIDEBAR, cursor="hand2")
            row.pack(fill="x", padx=12, pady=1)
            indicator = tk.Frame(row, bg=SIDEBAR, width=3)
            indicator.pack(side="left", fill="y")
            text = tk.Label(row, text=label, bg=SIDEBAR, fg="#94A3B8",
                            font=(f, 10), anchor="w", padx=14, pady=10,
                            cursor="hand2")
            text.pack(side="left", fill="x", expand=True)
            for widget in (row, text):
                widget.bind("<Button-1>", lambda e, k=key: self.show_page(k))
                widget.bind("<Enter>", lambda e, k=key: self._nav_hover(k, True))
                widget.bind("<Leave>", lambda e, k=key: self._nav_hover(k, False))
            self.nav_items[key] = (row, indicator, text)

        tk.Label(bar, text=f"v{APP_VERSION}  ·  SQLite", bg=SIDEBAR, fg="#475569",
                 font=(f, 8)).pack(side="bottom", pady=16)

    def _nav_hover(self, key, entering):
        if key == self.current_page:
            return
        _row, _ind, text = self.nav_items[key]
        text.configure(fg="#E2E8F0" if entering else "#94A3B8")

    def _build_content(self):
        f = self.font_family
        self.content = tk.Frame(self, bg=BG)
        self.content.pack(side="left", fill="both", expand=True)

        # footer status strip (packed before the page host so it keeps height)
        footer = tk.Frame(self.content, bg=WHITE, height=32,
                          highlightthickness=1, highlightbackground=LINE)
        footer.pack(side="bottom", fill="x")
        footer.pack_propagate(False)
        self.status_dot = tk.Frame(footer, bg=SUCCESS, width=7, height=7)
        self.status_dot.pack(side="left", padx=(16, 8))
        self.status = tk.StringVar(value="Ready")
        tk.Label(footer, textvariable=self.status, bg=WHITE, fg=MUTED,
                 font=(f, 9)).pack(side="left")
        self.lbl_db = tk.Label(footer, text=f"Database: {os.path.basename(DB_FILE)}",
                               bg=WHITE, fg="#94A3B8", font=(f, 9))
        self.lbl_db.pack(side="right", padx=16)

        self.host = tk.Frame(self.content, bg=BG)
        self.host.pack(side="top", fill="both", expand=True)
        self.host.rowconfigure(0, weight=1)
        self.host.columnconfigure(0, weight=1)

    def show_page(self, key):
        for k, (row, indicator, text) in self.nav_items.items():
            active = (k == key)
            bg = SIDEBAR_HOVER if active else SIDEBAR
            row.configure(bg=bg)
            text.configure(bg=bg, fg=WHITE if active else "#94A3B8")
            indicator.configure(bg=ACCENT if active else bg)
        self.current_page = key
        self.pages[key].tkraise()
        if key == "dashboard":
            self.refresh_dashboard()

    # ------------------------------------------------------------------
    #  building blocks
    # ------------------------------------------------------------------
    def _page(self, key):
        """Create and register a page frame."""
        page = tk.Frame(self.host, bg=BG)
        page.grid(row=0, column=0, sticky="nsew")
        self.pages[key] = page
        return page

    def _page_header(self, parent, title, subtitle):
        f = self.font_family
        head = tk.Frame(parent, bg=BG)
        head.pack(fill="x", padx=26, pady=(22, 14))
        left = tk.Frame(head, bg=BG)
        left.pack(side="left", fill="x", expand=True)
        tk.Label(left, text=title, bg=BG, fg=INK,
                 font=(f, 18, "bold")).pack(anchor="w")
        tk.Label(left, text=subtitle, bg=BG, fg=MUTED,
                 font=(f, 10)).pack(anchor="w", pady=(2, 0))
        actions = tk.Frame(head, bg=BG)
        actions.pack(side="right")
        return actions

    def _card(self, parent, pad=18, fill="x", expand=False):
        card = tk.Frame(parent, bg=WHITE, highlightthickness=1,
                        highlightbackground=LINE)
        card.pack(fill="both" if expand else fill,
                  expand=expand, padx=26, pady=(0, 14))
        body = tk.Frame(card, bg=WHITE)
        body.pack(fill="both", expand=True, padx=pad, pady=pad)
        return card, body

    def _card_title(self, parent, text):
        f = self.font_family
        tk.Label(parent, text=text, bg=WHITE, fg=INK,
                 font=(f, 11, "bold")).pack(anchor="w", pady=(0, 12))

    def _field(self, parent, label, row, col, var=None, values=None,
               width=26, kind="entry", state="readonly", colspan=1):
        """Label above the input, input below - modern stacked layout."""
        f = self.font_family
        cell = tk.Frame(parent, bg=WHITE)
        cell.grid(row=row, column=col, columnspan=colspan, sticky="w",
                  padx=(0, 18), pady=(0, 10))
        tk.Label(cell, text=label, bg=WHITE, fg=MUTED,
                 font=(f, 9)).pack(anchor="w", pady=(0, 4))
        if kind == "combo":
            widget = ttk.Combobox(cell, width=width, values=values or [],
                                  state=state, style="Modern.TCombobox")
            if var is not None:
                widget.configure(textvariable=var)
            widget.pack(anchor="w")
            return widget
        if kind == "date":
            row = tk.Frame(cell, bg=WHITE)
            row.pack(anchor="w")
            widget = ttk.Entry(row, width=width, style="Modern.TEntry")
            if var is not None:
                widget.configure(textvariable=var)
            widget.pack(side="left")
            ttk.Button(row, text="\u25be", width=2, style="Pick.TButton",
                       command=lambda w=widget, v=var: self.open_date_picker(w, v)
                       ).pack(side="left", padx=(5, 0))
            return widget
        widget = ttk.Entry(cell, width=width, style="Modern.TEntry")
        if var is not None:
            widget.configure(textvariable=var)
        widget.pack(anchor="w")
        return widget

    def _table(self, parent, columns, widths, height=5, anchors=None):
        wrap = tk.Frame(parent, bg=WHITE)
        tree = ttk.Treeview(wrap, columns=columns, show="headings",
                            style="Modern.Treeview", height=height,
                            selectmode="browse")
        anchors = anchors or ["w"] * len(columns)
        head = tkfont.Font(root=self, family=self.font_family, size=9,
                           weight="bold")
        for col, width, anchor in zip(columns, widths, anchors):
            # never let a heading be clipped by a narrow column
            need = head.measure(col.upper()) + 30
            tree.heading(col, text=col.upper(), anchor=anchor)
            tree.column(col, width=max(width, need), minwidth=need,
                        anchor=anchor, stretch=True)
        vs = ttk.Scrollbar(wrap, orient="vertical", command=tree.yview,
                           style="Modern.Vertical.TScrollbar")
        hs = ttk.Scrollbar(wrap, orient="horizontal", command=tree.xview,
                           style="Modern.Horizontal.TScrollbar")
        tree.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vs.grid(row=0, column=1, sticky="ns")
        hs.grid(row=1, column=0, sticky="ew")
        wrap.rowconfigure(0, weight=1)
        wrap.columnconfigure(0, weight=1)
        tree._hscroll = hs
        tree.bind("<Configure>", lambda e, t=tree: sync_hscroll(t), add="+")
        tree.after_idle(lambda t=tree: sync_hscroll(t))
        tree.tag_configure("odd", background=SOFT)
        tree.tag_configure("fail", foreground=DANGER)
        tree.tag_configure("pass", foreground=SUCCESS)
        return wrap, tree

    def _toolbar(self, parent, buttons):
        """buttons: list of (text, command, style)"""
        bar = tk.Frame(parent, bg=WHITE)
        bar.pack(fill="x", pady=(2, 12))
        for text, command, style in buttons:
            ttk.Button(bar, text=text, command=command,
                       style=style).pack(side="left", padx=(0, 8))
        return bar

    def open_date_picker(self, entry, var):
        """Open the calendar next to a date field and write the choice back."""
        if var is None:
            return

        def on_pick(value):
            var.set("" if value is None else value.strftime("%d/%m/%Y"))

        picker = DatePicker(self, var.get(), on_pick)
        picker.update_idletasks()
        try:
            x = entry.winfo_rootx()
            y = entry.winfo_rooty() + entry.winfo_height() + 4
            picker.geometry(f"+{x}+{y}")
        except tk.TclError:
            pass
        picker.wait_window()

    # ==================================================================
    #  DASHBOARD
    # ==================================================================
    def _build_dashboard(self):
        f = self.font_family
        page = self._page("dashboard")
        self._page_header(page, "Dashboard",
                          "A quick view of your examination data")

        tiles = tk.Frame(page, bg=BG)
        tiles.pack(fill="x", padx=26, pady=(0, 4))
        self.kpi = {}
        specs = [("students", "Students", ACCENT),
                 ("exams", "Exams", "#0EA5E9"),
                 ("subjects", "Subjects", "#10B981"),
                 ("papers", "Papers scheduled", "#F59E0B")]
        for i, (key, label, colour) in enumerate(specs):
            card = tk.Frame(tiles, bg=WHITE, highlightthickness=1,
                            highlightbackground=LINE)
            card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 14, 0))
            tiles.columnconfigure(i, weight=1)
            inner = tk.Frame(card, bg=WHITE)
            inner.pack(fill="both", expand=True, padx=18, pady=16)
            tk.Frame(inner, bg=colour, height=3, width=34).pack(anchor="w",
                                                                pady=(0, 12))
            value = tk.StringVar(value="0")
            tk.Label(inner, textvariable=value, bg=WHITE, fg=INK,
                     font=(f, 24, "bold")).pack(anchor="w")
            tk.Label(inner, text=label, bg=WHITE, fg=MUTED,
                     font=(f, 9)).pack(anchor="w")
            self.kpi[key] = value

        row = tk.Frame(page, bg=BG)
        row.pack(fill="both", expand=True, padx=26, pady=(10, 20))
        row.columnconfigure(0, weight=3)
        row.columnconfigure(1, weight=2)
        row.rowconfigure(0, weight=1)

        left = tk.Frame(row, bg=WHITE, highlightthickness=1,
                        highlightbackground=LINE)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        left_body = tk.Frame(left, bg=WHITE)
        left_body.pack(fill="both", expand=True, padx=18, pady=16)
        self._card_title(left_body, "Recent admissions")
        wrap, self.dash_recent = self._table(
            left_body, ("Admission No", "Name", "Class", "Admitted on"),
            [125, 145, 55, 115], height=6)
        wrap.pack(fill="both", expand=True)

        right = tk.Frame(row, bg=WHITE, highlightthickness=1,
                         highlightbackground=LINE)
        right.grid(row=0, column=1, sticky="nsew")
        right_body = tk.Frame(right, bg=WHITE)
        right_body.pack(fill="both", expand=True, padx=18, pady=16)
        self._card_title(right_body, "Exams")
        wrap2, self.dash_exams = self._table(
            right_body, ("Exam Type", "Class", "Starts", "Status"),
            [135, 50, 100, 90], height=6)
        wrap2.pack(fill="both", expand=True)

    def refresh_dashboard(self):
        self.kpi["students"].set(str(count_rows("SELECT COUNT(*) FROM students")))
        self.kpi["exams"].set(str(count_rows("SELECT COUNT(*) FROM exams")))
        self.kpi["subjects"].set(str(count_rows("SELECT COUNT(*) FROM subjects")))
        self.kpi["papers"].set(str(count_rows("SELECT COUNT(*) FROM exam_schedule")))

        clear_tree(self.dash_recent)
        for r in fetch_all("SELECT * FROM students ORDER BY id DESC LIMIT 12"):
            add_row(self.dash_recent, (r["admission_no"], r["name"],
                                       r["class_name"],
                                       disp_date(r["admission_date"])))
        clear_tree(self.dash_exams)
        for r in fetch_all("SELECT * FROM exams ORDER BY id DESC LIMIT 12"):
            add_row(self.dash_exams, (r["exam_type"] or r["exam_name"],
                                      r["class_name"],
                                      disp_date(r["start_date"]), r["status"]))

    # ==================================================================
    #  STUDENTS
    # ==================================================================
    def _build_students_page(self):
        f = self.font_family
        page = self._page("students")
        actions = self._page_header(
            page, "Students",
            "Admission details and student master data")
        ttk.Button(actions, text="Export CSV", style="Ghost.TButton",
                   command=self.export_students).pack(side="right")

        self.stu_id = None
        _card, body = self._card(page)
        self._card_title(body, "Student details")

        self.sv = {k: tk.StringVar() for k in (
            "admission_no", "roll_no", "name", "class_name", "section", "dob",
            "gender", "father_name", "mother_name", "phone", "email",
            "address", "admission_date", "status")}
        self.sv["status"].set("Active")
        # Date of admission is left blank on purpose - it is typed in by the
        # user for every student instead of defaulting to today.

        grid = tk.Frame(body, bg=WHITE)
        grid.pack(fill="x")
        for c in range(4):
            grid.columnconfigure(c, weight=1)

        self._field(grid, "Admission No *", 0, 0, self.sv["admission_no"], width=20)
        self._field(grid, "Roll No *", 0, 1, self.sv["roll_no"], width=20)
        self._field(grid, "Student name *", 0, 2, self.sv["name"], width=24)
        self._field(grid, "Class *", 0, 3, self.sv["class_name"], width=20)
        self._field(grid, "Section", 1, 0, self.sv["section"], width=20,
                    values=SECTIONS, kind="combo")
        self._field(grid, "Date of birth", 1, 1, self.sv["dob"], width=17,
                    kind="date")
        self._field(grid, "Gender", 1, 2, self.sv["gender"], width=24,
                    values=GENDERS, kind="combo")
        self._field(grid, "Date of admission *", 1, 3,
                    self.sv["admission_date"], width=17, kind="date")
        self._field(grid, "Father's name", 2, 0, self.sv["father_name"], width=20)
        self._field(grid, "Mother's name", 2, 1, self.sv["mother_name"], width=20)
        self._field(grid, "Phone", 2, 2, self.sv["phone"], width=24)
        self._field(grid, "Email", 2, 3, self.sv["email"], width=20)
        self._field(grid, "Address", 3, 0, self.sv["address"], width=46,
                    colspan=2)
        self._field(grid, "Status", 3, 2, self.sv["status"], width=24,
                    values=STUDENT_STATUS, kind="combo")

        self._toolbar(body, [
            ("Save student", self.save_student, "Accent.TButton"),
            ("Update", self.update_student, "Ghost.TButton"),
            ("Delete", self.delete_student, "Danger.TButton"),
            ("Clear form", self.clear_student, "Ghost.TButton"),
        ])

        _card2, body2 = self._card(page, fill="both", expand=True)
        search = tk.Frame(body2, bg=WHITE)
        search.pack(fill="x", pady=(0, 12))
        tk.Label(search, text="Search", bg=WHITE, fg=MUTED,
                 font=(f, 9)).pack(side="left", padx=(0, 8))
        self.stu_search = tk.StringVar()
        ent = ttk.Entry(search, textvariable=self.stu_search, width=34,
                        style="Modern.TEntry")
        ent.pack(side="left")
        ent.bind("<KeyRelease>", lambda e: self.load_students())
        ttk.Button(search, text="Reset", style="Ghost.TButton",
                   command=self.reset_student_search).pack(side="left", padx=8)
        self.stu_count = tk.Label(search, text="", bg=WHITE, fg=MUTED,
                                  font=(f, 9))
        self.stu_count.pack(side="right")

        cols = ("Admission No", "Roll No", "Name", "Class", "Section",
                "Date of Admission", "DOB", "Gender", "Father's Name",
                "Phone", "Email", "Status")
        wrap, self.stu_tree = self._table(
            body2, cols, [105, 70, 165, 60, 70, 120, 95, 75, 135, 110, 160, 75])
        wrap.pack(fill="both", expand=True)
        self.stu_tree.bind("<<TreeviewSelect>>", self.on_student_select)

    def _student_values(self):
        return (
            self.sv["admission_no"].get().strip(),
            self.sv["roll_no"].get().strip(),
            self.sv["name"].get().strip(),
            self.sv["class_name"].get().strip(),
            self.sv["section"].get().strip(),
            norm_date(self.sv["dob"].get()),
            self.sv["gender"].get().strip(),
            self.sv["father_name"].get().strip(),
            self.sv["mother_name"].get().strip(),
            self.sv["phone"].get().strip(),
            self.sv["email"].get().strip(),
            self.sv["address"].get().strip(),
            norm_date(self.sv["admission_date"].get()),
            self.sv["status"].get().strip() or "Active",
        )

    def _validate_student(self, values):
        adm, roll, name, cls, sec, dob, gender, father, mother, phone, email, \
            address, adm_date, status = values
        if not adm:
            return "Admission No is required."
        if not roll:
            return "Roll No is required."
        if not name:
            return "Student name is required."
        if not cls:
            return "Class is required."
        if dob is None:
            return "Date of birth is not a valid date (use dd/mm/yyyy)."
        if not adm_date:
            return "Date of admission is required - type it as dd/mm/yyyy."
        if adm_date is None:
            return "Date of admission is not a valid date (use dd/mm/yyyy)."
        if phone and not phone.replace("+", "").replace("-", "").replace(
                " ", "").isdigit():
            return "Phone must contain digits only."
        if email and "@" not in email:
            return "Email does not look valid."
        return None

    def save_student(self):
        values = self._student_values()
        err = self._validate_student(values)
        if err:
            messagebox.showerror("Validation", err)
            return
        if fetch_one("SELECT id FROM students WHERE admission_no=?", (values[0],)):
            messagebox.showerror("Duplicate",
                                 f"Admission No {values[0]} already exists.")
            return
        execute(
            """INSERT INTO students
               (admission_no, roll_no, name, class_name, section, dob, gender,
                father_name, mother_name, phone, email, address, admission_date, status)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", values)
        self.status.set(f"Student '{values[2]}' saved.")
        self.load_students()
        self.refresh_dashboard()
        self.clear_student()

    def update_student(self):
        if not self.stu_id:
            messagebox.showinfo("Select a row", "Pick a student from the table first.")
            return
        values = self._student_values()
        err = self._validate_student(values)
        if err:
            messagebox.showerror("Validation", err)
            return
        if fetch_one("SELECT id FROM students WHERE admission_no=? AND id<>?",
                     (values[0], self.stu_id)):
            messagebox.showerror(
                "Duplicate",
                f"Admission No {values[0]} belongs to another student.")
            return
        execute(
            """UPDATE students SET admission_no=?, roll_no=?, name=?, class_name=?,
               section=?, dob=?, gender=?, father_name=?, mother_name=?, phone=?,
               email=?, address=?, admission_date=?, status=? WHERE id=?""",
            values + (self.stu_id,))
        self.status.set(f"Student '{values[2]}' updated.")
        self.load_students()
        self.refresh_dashboard()
        self.clear_student()

    def delete_student(self):
        if not self.stu_id:
            messagebox.showinfo("Select a row", "Pick a student from the table first.")
            return
        name = self.sv["name"].get()
        if not messagebox.askyesno(
                "Delete student",
                f"Delete '{name}' and every mark linked to them?"):
            return
        execute("DELETE FROM students WHERE id=?", (self.stu_id,))
        self.status.set(f"Student '{name}' deleted.")
        self.load_students()
        self.refresh_dashboard()
        self.clear_student()

    def clear_student(self):
        self.stu_id = None
        for key, var in self.sv.items():
            var.set("")
        self.sv["status"].set("Active")
        self.stu_tree.selection_remove(self.stu_tree.selection())

    def reset_student_search(self):
        self.stu_search.set("")
        self.load_students()

    def on_student_select(self, _event=None):
        sel = self.stu_tree.selection()
        if not sel:
            return
        sid = int(sel[0])
        row = fetch_one("SELECT * FROM students WHERE id=?", (sid,))
        if not row:
            return
        self.stu_id = sid
        self.sv["admission_no"].set(row["admission_no"] or "")
        self.sv["roll_no"].set(row["roll_no"] or "")
        self.sv["name"].set(row["name"] or "")
        self.sv["class_name"].set(row["class_name"] or "")
        self.sv["section"].set(row["section"] or "")
        self.sv["dob"].set(disp_date(row["dob"]))
        self.sv["gender"].set(row["gender"] or "")
        self.sv["father_name"].set(row["father_name"] or "")
        self.sv["mother_name"].set(row["mother_name"] or "")
        self.sv["phone"].set(row["phone"] or "")
        self.sv["email"].set(row["email"] or "")
        self.sv["address"].set(row["address"] or "")
        self.sv["admission_date"].set(disp_date(row["admission_date"]))
        self.sv["status"].set(row["status"] or "Active")

    def load_students(self):
        term = f"%{self.stu_search.get().strip()}%"
        rows = fetch_all(
            """SELECT * FROM students
               WHERE name LIKE ? OR roll_no LIKE ? OR admission_no LIKE ?
                     OR class_name LIKE ?
               ORDER BY class_name, CAST(roll_no AS INTEGER), roll_no""",
            (term, term, term, term))
        clear_tree(self.stu_tree)
        for r in rows:
            add_row(self.stu_tree, (
                r["admission_no"], r["roll_no"], r["name"], r["class_name"],
                r["section"], disp_date(r["admission_date"]), disp_date(r["dob"]),
                r["gender"], r["father_name"], r["phone"], r["email"],
                r["status"]), iid=str(r["id"]))
        self.stu_count.configure(text=f"{len(rows)} student(s)")

    def export_students(self):
        rows = self.stu_tree.get_children()
        if not rows:
            messagebox.showinfo("Nothing to export", "No student records yet.")
            return
        path = filedialog.asksaveasfilename(
            title="Save student list", defaultextension=".csv",
            initialfile="students_export.csv",
            filetypes=[("CSV file", "*.csv"), ("All files", "*.*")])
        if not path:
            return
        headers = ["Admission No", "Roll No", "Name", "Class", "Section",
                   "Date of Admission", "DOB", "Gender", "Father's Name",
                   "Phone", "Email", "Status"]
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as fh:
                writer = csv.writer(fh)
                writer.writerow(headers)
                for iid in rows:
                    writer.writerow(self.stu_tree.item(iid, "values"))
        except OSError as exc:
            messagebox.showerror("Export failed", f"Could not write the file:\n{exc}")
            return
        self.status.set(f"Exported {len(rows)} row(s) to {os.path.basename(path)}")
        messagebox.showinfo("Exported", f"Saved to:\n{path}")

    # ==================================================================
    #  EXAMS
    # ==================================================================
    def _build_exams_page(self):
        page = self._page("exams")
        self._page_header(page, "Exams",
                          "Create the exam, then schedule its papers")
        self.exam_id = None

        _card, body = self._card(page)
        self._card_title(body, "Exam details")

        self.ev = {k: tk.StringVar() for k in (
            "exam_type", "academic_year", "class_name", "start_date",
            "end_date", "status", "remarks")}
        self.ev["status"].set("Scheduled")
        self.ev["academic_year"].set("2026-27")

        grid = tk.Frame(body, bg=WHITE)
        grid.pack(fill="x")
        for c in range(3):
            grid.columnconfigure(c, weight=1)
        # The exam type is the exam's identity - there is no separate exam name.
        self._field(grid, "Exam type *", 0, 0, self.ev["exam_type"],
                    values=EXAM_TYPES, kind="combo", state="normal", width=30)
        self._field(grid, "Academic year", 0, 1, self.ev["academic_year"],
                    width=26)
        self._field(grid, "Class", 0, 2, self.ev["class_name"], width=26)
        self._field(grid, "Start date", 1, 0, self.ev["start_date"], width=17,
                    kind="date")
        self._field(grid, "End date", 1, 1, self.ev["end_date"], width=17,
                    kind="date")
        self._field(grid, "Status", 1, 2, self.ev["status"],
                    values=EXAM_STATUS, kind="combo", width=26)
        self._field(grid, "Remarks", 2, 0, self.ev["remarks"], width=40,
                    colspan=2)

        self._toolbar(body, [
            ("Save exam", self.save_exam, "Accent.TButton"),
            ("Update", self.update_exam, "Ghost.TButton"),
            ("Delete", self.delete_exam, "Danger.TButton"),
            ("Clear form", self.clear_exam, "Ghost.TButton"),
        ])

        _card2, body2 = self._card(page, fill="both", expand=True)
        self._card_title(body2, "All exams")
        cols = ("Exam Type", "Academic Year", "Class", "Start Date",
                "End Date", "Status", "Remarks")
        wrap, self.exam_tree = self._table(
            body2, cols, [220, 130, 70, 105, 105, 120, 200])
        wrap.pack(fill="both", expand=True)
        self.exam_tree.bind("<<TreeviewSelect>>", self.on_exam_select)

    def save_exam(self):
        etype = self.ev["exam_type"].get().strip()
        if not etype:
            messagebox.showerror("Validation", "Exam type is required.")
            return
        sd = norm_date(self.ev["start_date"].get())
        ed = norm_date(self.ev["end_date"].get())
        if sd is None or ed is None:
            messagebox.showerror("Validation", "Dates must be dd/mm/yyyy.")
            return
        if sd and ed and ed < sd:
            messagebox.showerror("Validation", "End date cannot be before start date.")
            return
        year = self.ev["academic_year"].get().strip()
        cls = self.ev["class_name"].get().strip()
        if self._exam_exists(etype, year, cls):
            messagebox.showerror(
                "Duplicate exam",
                f"'{etype}' already exists for class {cls or '-'} "
                f"in {year or '-'}.")
            return
        # exam_name is kept in step with the type so older databases and
        # reports still show a sensible label.
        execute(
            """INSERT INTO exams (exam_name, exam_type, academic_year, class_name,
               start_date, end_date, status, remarks) VALUES (?,?,?,?,?,?,?,?)""",
            (etype, etype, year, cls, sd, ed,
             self.ev["status"].get() or "Scheduled",
             self.ev["remarks"].get().strip()))
        self.status.set(f"Exam '{etype}' saved.")
        self.load_exams()
        self.refresh_dashboard()
        self.refresh_exam_choices()
        self.clear_exam()

    def update_exam(self):
        if not self.exam_id:
            messagebox.showinfo("Select a row", "Pick an exam from the table first.")
            return
        etype = self.ev["exam_type"].get().strip()
        if not etype:
            messagebox.showerror("Validation", "Exam type is required.")
            return
        sd = norm_date(self.ev["start_date"].get())
        ed = norm_date(self.ev["end_date"].get())
        if sd is None or ed is None:
            messagebox.showerror("Validation", "Dates must be dd/mm/yyyy.")
            return
        year = self.ev["academic_year"].get().strip()
        cls = self.ev["class_name"].get().strip()
        if self._exam_exists(etype, year, cls, skip_id=self.exam_id):
            messagebox.showerror(
                "Duplicate exam",
                f"'{etype}' already exists for class {cls or '-'} "
                f"in {year or '-'}.")
            return
        execute(
            """UPDATE exams SET exam_name=?, exam_type=?, academic_year=?,
               class_name=?, start_date=?, end_date=?, status=?, remarks=?
               WHERE id=?""",
            (etype, etype, year, cls, sd, ed,
             self.ev["status"].get() or "Scheduled",
             self.ev["remarks"].get().strip(), self.exam_id))
        self.status.set(f"Exam '{etype}' updated.")
        self.load_exams()
        self.refresh_dashboard()
        self.refresh_exam_choices()
        self.clear_exam()

    def delete_exam(self):
        if not self.exam_id:
            messagebox.showinfo("Select a row", "Pick an exam from the table first.")
            return
        name = self.ev["exam_type"].get()
        if not messagebox.askyesno(
                "Delete exam",
                f"Delete '{name}' together with its schedule and marks?"):
            return
        execute("DELETE FROM exams WHERE id=?", (self.exam_id,))
        self.status.set(f"Exam '{name}' deleted.")
        self.load_exams()
        self.load_schedule()
        self.refresh_dashboard()
        self.refresh_exam_choices()
        self.refresh_marks_filters()
        self.refresh_results_filters()
        self.clear_exam()

    def clear_exam(self):
        self.exam_id = None
        for var in self.ev.values():
            var.set("")
        self.ev["status"].set("Scheduled")
        self.ev["academic_year"].set("2026-27")
        self.exam_tree.selection_remove(self.exam_tree.selection())

    def on_exam_select(self, _event=None):
        sel = self.exam_tree.selection()
        if not sel:
            return
        eid = int(sel[0])
        row = fetch_one("SELECT * FROM exams WHERE id=?", (eid,))
        if not row:
            return
        self.exam_id = eid
        self.ev["exam_type"].set(row["exam_type"] or row["exam_name"] or "")
        self.ev["academic_year"].set(row["academic_year"] or "")
        self.ev["class_name"].set(row["class_name"] or "")
        self.ev["start_date"].set(disp_date(row["start_date"]))
        self.ev["end_date"].set(disp_date(row["end_date"]))
        self.ev["status"].set(row["status"] or "Scheduled")
        self.ev["remarks"].set(row["remarks"] or "")

    def load_exams(self):
        rows = fetch_all("SELECT * FROM exams ORDER BY id DESC")
        clear_tree(self.exam_tree)
        for r in rows:
            add_row(self.exam_tree, (
                r["exam_type"] or r["exam_name"], r["academic_year"],
                r["class_name"], disp_date(r["start_date"]),
                disp_date(r["end_date"]), r["status"], r["remarks"]),
                iid=str(r["id"]))

    def _exam_exists(self, exam_type, academic_year, class_name, skip_id=None):
        """Same type + class + academic year = the same exam."""
        sql = ("SELECT id FROM exams WHERE exam_type=? AND "
               "IFNULL(academic_year,'')=? AND IFNULL(class_name,'')=?")
        params = [exam_type, academic_year or "", class_name or ""]
        if skip_id:
            sql += " AND id<>?"
            params.append(skip_id)
        return fetch_one(sql, tuple(params)) is not None

    # ==================================================================
    #  SUBJECTS
    # ==================================================================
    def _build_subjects_page(self):
        page = self._page("subjects")
        self._page_header(page, "Subjects",
                          "Subject master used by the exam schedule")
        self.subject_id = None

        _card, body = self._card(page)
        self._card_title(body, "Subject details")

        self.sb = {k: tk.StringVar() for k in
                   ("subject_code", "subject_name", "class_name")}
        grid = tk.Frame(body, bg=WHITE)
        grid.pack(fill="x")
        for c in range(3):
            grid.columnconfigure(c, weight=1)
        self._field(grid, "Subject code *", 0, 0, self.sb["subject_code"])
        self._field(grid, "Subject name *", 0, 1, self.sb["subject_name"], width=32)
        self._field(grid, "Class (blank = all)", 0, 2, self.sb["class_name"],
                    width=30)

        self._toolbar(body, [
            ("Save subject", self.save_subject, "Accent.TButton"),
            ("Update", self.update_subject, "Ghost.TButton"),
            ("Delete", self.delete_subject, "Danger.TButton"),
            ("Clear form", self.clear_subject, "Ghost.TButton"),
            ("Load defaults", self.load_default_subjects, "Ghost.TButton"),
        ])

        _card2, body2 = self._card(page, fill="both", expand=True)
        self._card_title(body2, "All subjects")
        wrap, self.sub_tree = self._table(
            body2, ("Code", "Subject Name", "Class"), [140, 380, 140])
        wrap.pack(fill="both", expand=True)
        self.sub_tree.bind("<<TreeviewSelect>>", self.on_subject_select)

    def save_subject(self):
        code = self.sb["subject_code"].get().strip().upper()
        name = self.sb["subject_name"].get().strip()
        if not code or not name:
            messagebox.showerror("Validation",
                                 "Subject code and name are both required.")
            return
        if fetch_one("SELECT id FROM subjects WHERE subject_code=?", (code,)):
            messagebox.showerror("Duplicate", f"Subject code {code} already exists.")
            return
        execute("INSERT INTO subjects (subject_code, subject_name, class_name)"
                " VALUES (?,?,?)",
                (code, name, self.sb["class_name"].get().strip()))
        self.status.set(f"Subject '{name}' saved.")
        self.load_subjects()
        self.refresh_dashboard()
        self.refresh_subject_choices()
        self.clear_subject()

    def update_subject(self):
        if not self.subject_id:
            messagebox.showinfo("Select a row", "Pick a subject from the table first.")
            return
        code = self.sb["subject_code"].get().strip().upper()
        name = self.sb["subject_name"].get().strip()
        if not code or not name:
            messagebox.showerror("Validation",
                                 "Subject code and name are both required.")
            return
        execute("UPDATE subjects SET subject_code=?, subject_name=?, class_name=?"
                " WHERE id=?",
                (code, name, self.sb["class_name"].get().strip(), self.subject_id))
        self.status.set(f"Subject '{name}' updated.")
        self.load_subjects()
        self.refresh_subject_choices()
        self.clear_subject()

    def delete_subject(self):
        if not self.subject_id:
            messagebox.showinfo("Select a row", "Pick a subject from the table first.")
            return
        name = self.sb["subject_name"].get()
        if not messagebox.askyesno("Delete subject", f"Delete '{name}'?"):
            return
        execute("DELETE FROM subjects WHERE id=?", (self.subject_id,))
        self.status.set(f"Subject '{name}' deleted.")
        self.load_subjects()
        self.load_schedule()
        self.refresh_dashboard()
        self.refresh_subject_choices()
        self.clear_subject()

    def clear_subject(self):
        self.subject_id = None
        for var in self.sb.values():
            var.set("")
        self.sub_tree.selection_remove(self.sub_tree.selection())

    def on_subject_select(self, _event=None):
        sel = self.sub_tree.selection()
        if not sel:
            return
        sid = int(sel[0])
        row = fetch_one("SELECT * FROM subjects WHERE id=?", (sid,))
        if not row:
            return
        self.subject_id = sid
        self.sb["subject_code"].set(row["subject_code"] or "")
        self.sb["subject_name"].set(row["subject_name"] or "")
        self.sb["class_name"].set(row["class_name"] or "")

    def load_subjects(self):
        rows = fetch_all("SELECT * FROM subjects ORDER BY subject_code")
        clear_tree(self.sub_tree)
        for r in rows:
            add_row(self.sub_tree, (r["subject_code"], r["subject_name"],
                                    r["class_name"]), iid=str(r["id"]))

    def load_default_subjects(self):
        defaults = [("ENG", "English"), ("HIN", "Hindi"), ("MAT", "Mathematics"),
                    ("SCI", "Science"), ("SST", "Social Science"),
                    ("CS", "Computer Science")]
        added = 0
        for code, name in defaults:
            if not fetch_one("SELECT id FROM subjects WHERE subject_code=?", (code,)):
                execute("INSERT INTO subjects (subject_code, subject_name)"
                        " VALUES (?,?)", (code, name))
                added += 1
        self.load_subjects()
        self.refresh_dashboard()
        self.refresh_subject_choices()
        self.status.set(f"{added} default subject(s) added.")

    # ==================================================================
    #  EXAM SCHEDULE
    # ==================================================================
    def _build_schedule_page(self):
        page = self._page("schedule")
        self._page_header(page, "Exam schedule",
                          "One paper per subject - date, time, hall and marks")
        self.sched_id = None

        _card, body = self._card(page)
        self._card_title(body, "Add a paper")

        grid = tk.Frame(body, bg=WHITE)
        grid.pack(fill="x")
        for c in range(3):
            grid.columnconfigure(c, weight=1)

        self.sched_exam_cb = self._field(grid, "Exam *", 0, 0,
                                         values=[], kind="combo", width=30)
        self.sched_subject_cb = self._field(grid, "Subject *", 0, 1,
                                            values=[], kind="combo", width=28)

        self.sc = {k: tk.StringVar() for k in (
            "exam_date", "start_time", "duration", "room", "invigilator",
            "max_marks", "pass_marks")}
        self.sc["duration"].set("180")
        self.sc["max_marks"].set("100")
        self.sc["pass_marks"].set("33")

        self._field(grid, "Exam date", 0, 2, self.sc["exam_date"], width=17,
                    kind="date")
        self._field(grid, "Start time (HH:MM)", 1, 0, self.sc["start_time"])
        self._field(grid, "Duration (minutes)", 1, 1, self.sc["duration"])
        self._field(grid, "Room / hall", 1, 2, self.sc["room"], width=30)
        self._field(grid, "Invigilator", 2, 0, self.sc["invigilator"])
        self._field(grid, "Max marks", 2, 1, self.sc["max_marks"])
        self._field(grid, "Pass marks", 2, 2, self.sc["pass_marks"], width=30)

        self._toolbar(body, [
            ("Add paper", self.save_schedule, "Accent.TButton"),
            ("Update", self.update_schedule, "Ghost.TButton"),
            ("Delete", self.delete_schedule, "Danger.TButton"),
            ("Clear form", self.clear_schedule, "Ghost.TButton"),
        ])

        _card2, body2 = self._card(page, fill="both", expand=True)
        self._card_title(body2, "Scheduled papers")
        cols = ("Exam Type", "Subject", "Date", "Time", "Duration", "Room",
                "Invigilator", "Max", "Pass")
        wrap, self.sched_tree = self._table(
            body2, cols, [235, 135, 100, 62, 82, 92, 120, 58, 58],
            anchors=["w", "w", "w", "w", "w", "w", "w", "e", "e"])
        wrap.pack(fill="both", expand=True)
        self.sched_tree.bind("<<TreeviewSelect>>", self.on_schedule_select)

    def refresh_exam_choices(self):
        rows = fetch_all("SELECT id, exam_name, exam_type, academic_year, "
                         "class_name FROM exams ORDER BY id DESC")
        self.exam_map = {}
        for r in rows:
            label = exam_label(r)
            if label in self.exam_map:      # two exams with the same label
                label = f"{label}  #{r['id']}"
            self.exam_map[label] = r["id"]
        values = list(self.exam_map.keys())
        for cb in (getattr(self, "sched_exam_cb", None),
                   getattr(self, "marks_exam_cb", None),
                   getattr(self, "res_exam_cb", None)):
            if cb is not None:
                current = cb.get()
                cb["values"] = values
                if current not in values:
                    cb.set("")

    def refresh_subject_choices(self):
        rows = fetch_all("SELECT id, subject_code, subject_name FROM subjects "
                         "ORDER BY subject_code")
        self.subject_map = {
            f"{r['subject_name']} ({r['subject_code']})": r["id"] for r in rows}
        values = list(self.subject_map.keys())
        for cb in (getattr(self, "sched_subject_cb", None),
                   getattr(self, "marks_subject_cb", None)):
            if cb is not None:
                current = cb.get()
                cb["values"] = values
                if current not in values:
                    cb.set("")

    def save_schedule(self):
        exam_label = self.sched_exam_cb.get()
        sub_label = self.sched_subject_cb.get()
        if not exam_label or not sub_label:
            messagebox.showerror("Validation", "Select both an exam and a subject.")
            return
        exam_id = self.exam_map[exam_label]
        sub_id = self.subject_map[sub_label]
        if fetch_one("SELECT id FROM exam_schedule WHERE exam_id=? AND subject_id=?",
                     (exam_id, sub_id)):
            messagebox.showerror("Duplicate",
                                 "That subject is already scheduled for this exam.")
            return
        values = self._schedule_values()
        if isinstance(values, str):
            messagebox.showerror("Validation", values)
            return
        execute("""INSERT INTO exam_schedule
                   (exam_id, subject_id, exam_date, start_time, duration, room,
                    invigilator, max_marks, pass_marks)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (exam_id, sub_id) + values)
        self.status.set("Paper added to the schedule.")
        self.load_schedule()
        self.refresh_dashboard()
        self.clear_schedule()

    def update_schedule(self):
        if not self.sched_id:
            messagebox.showinfo("Select a row", "Pick a paper from the table first.")
            return
        values = self._schedule_values()
        if isinstance(values, str):
            messagebox.showerror("Validation", values)
            return
        execute("""UPDATE exam_schedule SET exam_date=?, start_time=?, duration=?,
                   room=?, invigilator=?, max_marks=?, pass_marks=? WHERE id=?""",
                values + (self.sched_id,))
        self.status.set("Paper updated.")
        self.load_schedule()
        self.clear_schedule()

    def _schedule_values(self):
        ed = norm_date(self.sc["exam_date"].get())
        st = norm_time(self.sc["start_time"].get())
        if ed is None:
            return "Exam date must be dd/mm/yyyy."
        if st is None:
            return "Start time must be HH:MM (24 hour)."
        duration = to_float(self.sc["duration"].get(), 0)
        mx = to_float(self.sc["max_marks"].get(), 100)
        ps = to_float(self.sc["pass_marks"].get(), 33)
        if duration is None or mx is None or ps is None:
            return "Duration, max marks and pass marks must be numbers."
        if mx <= 0:
            return "Max marks must be greater than 0."
        if ps < 0 or ps > mx:
            return "Pass marks must be between 0 and max marks."
        return (ed, st, int(duration), self.sc["room"].get().strip(),
                self.sc["invigilator"].get().strip(), mx, ps)

    def delete_schedule(self):
        if not self.sched_id:
            messagebox.showinfo("Select a row", "Pick a paper from the table first.")
            return
        if not messagebox.askyesno("Delete paper",
                                   "Delete this paper and the marks entered for it?"):
            return
        execute("DELETE FROM exam_schedule WHERE id=?", (self.sched_id,))
        self.load_schedule()
        self.refresh_dashboard()
        self.clear_schedule()

    def clear_schedule(self):
        self.sched_id = None
        for var in self.sc.values():
            var.set("")
        self.sc["duration"].set("180")
        self.sc["max_marks"].set("100")
        self.sc["pass_marks"].set("33")
        self.sched_tree.selection_remove(self.sched_tree.selection())

    def on_schedule_select(self, _event=None):
        sel = self.sched_tree.selection()
        if not sel:
            return
        rid = int(sel[0])
        row = fetch_one("SELECT * FROM exam_schedule WHERE id=?", (rid,))
        if not row:
            return
        self.sched_id = rid
        for label, eid in self.exam_map.items():
            if eid == row["exam_id"]:
                self.sched_exam_cb.set(label)
                break
        for label, sid in self.subject_map.items():
            if sid == row["subject_id"]:
                self.sched_subject_cb.set(label)
                break
        self.sc["exam_date"].set(disp_date(row["exam_date"]))
        self.sc["start_time"].set(row["start_time"] or "")
        self.sc["duration"].set(str(row["duration"] or ""))
        self.sc["room"].set(row["room"] or "")
        self.sc["invigilator"].set(row["invigilator"] or "")
        self.sc["max_marks"].set(fmt_num(row["max_marks"]))
        self.sc["pass_marks"].set(fmt_num(row["pass_marks"]))

    def load_schedule(self):
        rows = fetch_all(
            """SELECT sc.*, e.exam_name, e.exam_type, e.class_name,
                      e.academic_year, s.subject_name
               FROM exam_schedule sc
               JOIN exams e ON e.id = sc.exam_id
               JOIN subjects s ON s.id = sc.subject_id
               ORDER BY e.id DESC, sc.exam_date, sc.start_time""")
        clear_tree(self.sched_tree)
        for r in rows:
            add_row(self.sched_tree, (
                exam_label(r), r["subject_name"], disp_date(r["exam_date"]),
                r["start_time"], r["duration"], r["room"], r["invigilator"],
                fmt_num(r["max_marks"]), fmt_num(r["pass_marks"])),
                iid=str(r["id"]))

    # ==================================================================
    #  MARKS ENTRY
    # ==================================================================
    def _build_marks_page(self):
        f = self.font_family
        page = self._page("marks")
        self._page_header(page, "Marks entry",
                          "Pick an exam and a subject, then double-click a row")

        _card, body = self._card(page)
        picker = tk.Frame(body, bg=WHITE)
        picker.pack(fill="x")
        for c in range(3):
            picker.columnconfigure(c, weight=1)

        self.marks_exam_cb = self._field(picker, "Exam", 0, 0, values=[],
                                         kind="combo", width=36)
        self.marks_exam_cb.bind("<<ComboboxSelected>>",
                                lambda e: self.load_marks_sheet())
        self.marks_subject_cb = self._field(picker, "Subject", 0, 1, values=[],
                                            kind="combo", width=28)
        self.marks_subject_cb.bind("<<ComboboxSelected>>",
                                   lambda e: self.load_marks_sheet())

        btn_cell = tk.Frame(picker, bg=WHITE)
        btn_cell.grid(row=0, column=2, sticky="w", padx=(0, 22), pady=(16, 12))
        ttk.Button(btn_cell, text="Refresh sheet", style="Ghost.TButton",
                   command=self.load_marks_sheet).pack(anchor="w")

        _card2, body2 = self._card(page, fill="both", expand=True)
        self.marks_info = tk.Label(body2, text="", bg=WHITE, fg=MUTED,
                                   font=(f, 9), anchor="w")
        self.marks_info.pack(fill="x", pady=(0, 10))
        cols = ("Roll No", "Name", "Marks Obtained", "Max Marks", "Result",
                "Remarks")
        wrap, self.marks_tree = self._table(
            body2, cols, [90, 230, 140, 110, 110, 250],
            anchors=["w", "w", "e", "e", "center", "w"])
        wrap.pack(fill="both", expand=True)
        self.marks_tree.bind("<Double-1>", self.edit_marks)

    def refresh_marks_filters(self):
        self.load_marks_sheet()

    def load_marks_sheet(self):
        clear_tree(self.marks_tree)
        exam_label = self.marks_exam_cb.get()
        sub_label = self.marks_subject_cb.get()
        if not exam_label or not sub_label:
            self.marks_info.configure(
                text="Select an exam and a subject to load the sheet.")
            return
        exam_id = self.exam_map[exam_label]
        sub_id = self.subject_map[sub_label]

        sched = fetch_one(
            "SELECT * FROM exam_schedule WHERE exam_id=? AND subject_id=?",
            (exam_id, sub_id))
        if not sched:
            self.marks_info.configure(
                text="That subject is not scheduled for this exam - add it in "
                     "Exam schedule first.")
            return
        max_marks = float(sched["max_marks"] or 100)
        pass_marks = float(sched["pass_marks"] or 33)

        exam = fetch_one("SELECT * FROM exams WHERE id=?", (exam_id,))
        class_name = (exam["class_name"] or "").strip()
        sql = ("SELECT id, admission_no, roll_no, name FROM students "
               "WHERE status='Active'")
        params = ()
        if class_name:
            sql += " AND class_name=?"
            params = (class_name,)
        sql += " ORDER BY CAST(roll_no AS INTEGER), roll_no"
        students = fetch_all(sql, params)

        if not students:
            self.marks_info.configure(
                text=f"No active students found"
                     f"{' for class ' + class_name if class_name else ''}.")
            return

        self.marks_students = {str(s["id"]): s for s in students}
        self.marks_ctx = (exam_id, sub_id, max_marks, pass_marks)

        entered = 0
        for s in students:
            row = fetch_one(
                "SELECT * FROM marks WHERE exam_id=? AND student_id=? AND subject_id=?",
                (exam_id, s["id"], sub_id))
            if row and row["marks_obtained"] is not None:
                got = float(row["marks_obtained"])
                passed = got >= pass_marks
                entered += 1
                add_row(self.marks_tree, (
                    s["roll_no"], s["name"], fmt_num(got), fmt_num(max_marks),
                    "Pass" if passed else "Fail", row["remarks"] or ""),
                    iid=str(s["id"]), tags=() if passed else ("fail",))
            else:
                add_row(self.marks_tree, (
                    s["roll_no"], s["name"], "", fmt_num(max_marks), "-", ""),
                    iid=str(s["id"]))

        self.marks_info.configure(
            text=f"{len(students)} student(s)   ·   {entered} marks entered   ·   "
                 f"max {fmt_num(max_marks)}   ·   pass {fmt_num(pass_marks)}")

    def edit_marks(self, _event=None):
        sel = self.marks_tree.selection()
        if not sel:
            return
        if not getattr(self, "marks_ctx", None):
            messagebox.showinfo("Select", "Load an exam and subject first.")
            return
        student = self.marks_students.get(sel[0])
        if not student:
            return
        exam_id, sub_id, _mx, _ps = self.marks_ctx
        MarksDialog(self, exam_id, sub_id, student, self.load_marks_sheet)

    # ==================================================================
    #  RESULTS
    # ==================================================================
    def _build_results_page(self):
        f = self.font_family
        page = self._page("results")
        actions = self._page_header(
            page, "Results",
            "Totals, percentage, grade, rank and pass / fail")
        ttk.Button(actions, text="Export CSV", style="Ghost.TButton",
                   command=self.export_results).pack(side="right", padx=(8, 0))
        ttk.Button(actions, text="Generate", style="Accent.TButton",
                   command=self.generate_results).pack(side="right")

        _card, body = self._card(page)
        picker = tk.Frame(body, bg=WHITE)
        picker.pack(fill="x")
        for c in range(3):
            picker.columnconfigure(c, weight=1)
        self.res_exam_cb = self._field(picker, "Exam", 0, 0, values=[],
                                       kind="combo", width=38)
        self.res_class_cb = self._field(picker, "Class", 0, 1, width=16,
                                        kind="combo", state="normal")

        _card2, body2 = self._card(page, fill="both", expand=True)
        self.res_info = tk.Label(body2, text="", bg=WHITE, fg=MUTED,
                                 font=(f, 9), anchor="w")
        self.res_info.pack(fill="x", pady=(0, 10))
        cols = ("Rank", "Roll No", "Admission No", "Name", "Obtained", "Max",
                "Percentage", "Grade", "Failed", "Result")
        wrap, self.res_tree = self._table(
            body2, cols, [60, 80, 100, 170, 90, 65, 100, 65, 75, 75],
            anchors=["w", "w", "w", "w", "e", "e", "e", "w", "e", "w"])
        wrap.pack(fill="both", expand=True)

    def refresh_results_filters(self):
        rows = fetch_all("SELECT DISTINCT class_name FROM students "
                         "WHERE class_name IS NOT NULL AND class_name<>'' "
                         "ORDER BY class_name")
        self.res_class_cb["values"] = [r["class_name"] for r in rows]

    def _current_result_exam(self):
        label = self.res_exam_cb.get()
        if not label or label not in getattr(self, "exam_map", {}):
            return None
        return self.exam_map[label]

    def generate_results(self):
        clear_tree(self.res_tree)
        exam_id = self._current_result_exam()
        if not exam_id:
            messagebox.showinfo("Select an exam", "Please choose an exam first.")
            return
        exam = fetch_one("SELECT * FROM exams WHERE id=?", (exam_id,))
        class_name = self.res_class_cb.get().strip() or \
            (exam["class_name"] or "").strip()
        if not class_name:
            messagebox.showinfo("Class needed",
                                "Enter or pick a class to generate results.")
            return
        self.res_class_cb.set(class_name)

        results = compute_results(exam_id, class_name)
        if not results:
            self.res_info.configure(
                text="No marks found for this exam and class - enter marks first.")
            return

        for r in results:
            tags = ("fail",) if r["result"] == "Fail" else ()
            add_row(self.res_tree, (
                r["rank"], r["roll_no"], r["admission_no"], r["name"],
                fmt_num(r["obtained"]), fmt_num(r["total_max"]),
                f"{r['percentage']:.2f}", r["grade"], r["failed_subjects"],
                r["result"]), iid=str(r["student_id"]), tags=tags)

        passed = sum(1 for r in results if r["result"] == "Pass")
        topper = results[0]
        self.res_info.configure(
            text=f"{len(results)} student(s)   ·   Pass {passed}   ·   "
                 f"Fail {len(results) - passed}   ·   Topper: {topper['name']} "
                 f"({topper['percentage']:.2f}%)")
        self.status.set(f"Results generated for class {class_name}.")

    def export_results(self):
        rows = self.res_tree.get_children()
        if not rows:
            messagebox.showinfo("Nothing to export", "Generate the results first.")
            return
        path = filedialog.asksaveasfilename(
            title="Save result sheet", defaultextension=".csv",
            initialfile="results_export.csv",
            filetypes=[("CSV file", "*.csv"), ("All files", "*.*")])
        if not path:
            return
        headers = ["Rank", "Roll No", "Admission No", "Name", "Obtained",
                   "Max", "Percentage", "Grade", "Failed Subjects", "Result"]
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as fh:
                writer = csv.writer(fh)
                writer.writerow(headers)
                for iid in rows:
                    writer.writerow(self.res_tree.item(iid, "values"))
        except OSError as exc:
            messagebox.showerror("Export failed", f"Could not write the file:\n{exc}")
            return
        self.status.set(f"Results exported to {os.path.basename(path)}")
        messagebox.showinfo("Exported", f"Saved to:\n{path}")

    # ==================================================================
    #  SHARED REFRESH
    # ==================================================================
    def refresh_all(self):
        self.load_students()
        self.load_exams()
        self.load_subjects()
        self.load_schedule()
        self.refresh_exam_choices()
        self.refresh_subject_choices()
        self.refresh_marks_filters()
        self.refresh_results_filters()
        self.refresh_dashboard()

    def _on_tk_error(self, exc_type, exc_value, exc_tb):
        """Unexpected errors in a callback are logged and shown, not swallowed."""
        import traceback
        detail = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        try:
            with open(ERROR_LOG, "a", encoding="utf-8") as fh:
                fh.write(datetime.now().isoformat() + "\n" + detail + "\n")
        except OSError:
            pass
        try:
            messagebox.showerror(
                "Unexpected error",
                f"{exc_type.__name__}: {exc_value}\n\n"
                f"Details saved to:\n{os.path.basename(ERROR_LOG)}")
        except tk.TclError:
            print(detail)


# --------------------------------------------------------------------------
#  ENTRY POINT
# --------------------------------------------------------------------------
def selftest():
    """Headless check of the storage layer and the result maths.
    Run with:  python exam_module.py --selftest"""
    import tempfile
    global DB_FILE
    original = DB_FILE
    DB_FILE = os.path.join(tempfile.mkdtemp(), "selftest.db")
    try:
        init_db()
        checks = []

        checks.append(("date parsing", norm_date("25/10/2026") == "2026-10-25"
                       and norm_date("31/02/2026") is None))
        checks.append(("time parsing", norm_time("9:30 am") == "09:30"
                       and norm_time("25:00") is None))
        checks.append(("grades", grade_for(95) == "A1" and grade_for(20) == "E"))

        execute("INSERT INTO students (admission_no, roll_no, name, class_name,"
                " status) VALUES ('S1','1','Test Student','8','Active')")
        execute("INSERT INTO exams (exam_name, class_name) VALUES ('T','8')")
        execute("INSERT INTO subjects (subject_code, subject_name)"
                " VALUES ('MAT','Maths')")
        exam_id = fetch_one("SELECT id FROM exams")["id"]
        sub_id = fetch_one("SELECT id FROM subjects")["id"]
        stu_id = fetch_one("SELECT id FROM students")["id"]
        execute("INSERT INTO exam_schedule (exam_id, subject_id, max_marks,"
                " pass_marks) VALUES (?,?,100,33)", (exam_id, sub_id))
        execute("INSERT INTO marks (exam_id, student_id, subject_id,"
                " marks_obtained) VALUES (?,?,?,72)", (exam_id, stu_id, sub_id))
        res = compute_results(exam_id, "8")
        checks.append(("result maths", len(res) == 1
                       and res[0]["percentage"] == 72.0
                       and res[0]["grade"] == "B1"
                       and res[0]["result"] == "Pass"))
        try:
            execute("INSERT INTO students (admission_no, roll_no, name,"
                    " class_name) VALUES ('S1','2','Dup','8')")
            checks.append(("duplicate admission no blocked", False))
        except sqlite3.IntegrityError:
            checks.append(("duplicate admission no blocked", True))

        failed = [name for name, ok in checks if not ok]
        for name, ok in checks:
            print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
        print("\nSELF-TEST:", "ALL PASSED" if not failed else f"FAILED: {failed}")
        return 0 if not failed else 1
    finally:
        DB_FILE = original


def main():
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    resolve_db_file()
    try:
        init_db()
    except sqlite3.Error as exc:
        print(f"Could not open the database:\n{exc}")
        sys.exit(1)
    app = ExamApp()
    app.mainloop()


if __name__ == "__main__":
    main()
