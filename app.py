
from flask import Flask, render_template_string

app = Flask(__name__)

@app.route("/")
def home():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Examination Management System</title>
        <style>
            body {
                margin: 0;
                font-family: Arial, sans-serif;
                background: #f1f5f9;
                color: #1e293b;
            }
            header {
                background: #172554;
                color: white;
                padding: 25px;
                text-align: center;
            }
            .container {
                max-width: 1000px;
                margin: 35px auto;
                padding: 20px;
            }
            .cards {
                display: grid;
                grid-template-columns:
                    repeat(auto-fit, minmax(220px, 1fr));
                gap: 20px;
            }
            .card {
                background: white;
                padding: 25px;
                border-radius: 12px;
                box-shadow: 0 4px 15px #0001;
            }
            .card h2 {
                color: #2563eb;
            }
            footer {
                text-align: center;
                padding: 20px;
                color: #64748b;
            }
        </style>
    </head>
    <body>
        <header>
            <h1>JINDAL PUBLIC SCHOOL</h1>
            <p>Examination Management System</p>
            <p>Manage students, exams and results in one place</p>
        </header>

        <div class="container">
            <h2>Dashboard</h2>
            <div class="cards">
                <div class="card">
                    <h2>Students</h2>
                    <p>Manage student records.</p>
                </div>
                <div class="card">
                    <h2>Exams</h2>
                    <p>View and schedule examinations.</p>
                </div>
                <div class="card">
                    <h2>Marks</h2>
                    <p>Enter examination marks.</p>
                </div>
                <div class="card">
                    <h2>Results</h2>
                    <p>Generate student results.</p>
                </div>
            </div>
        </div>

        <footer>Developed by Ayush Gupta | Examination Management System</footer>
    </body>
    </html>
    """)

if __name__ == "__main__":
    app.run(debug=True)
