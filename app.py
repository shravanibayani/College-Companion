from cs50 import SQL
import pprint
from flask import Flask, render_template, request, session, redirect
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from helpers import login_required, check_password

# Configuring the application
app = Flask(__name__)

# database
db = SQL("sqlite:///database.db")

# Configuring the session
app.config["SESSION_PERMENENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# Allowed branches
branches = ['csd']

# Allowed divisions
divisions = ['A', 'B']

# Allowed Years
years = [1, 2, 3, 4]


@app.route("/")
@login_required
def home():
    # Home screen
    return render_template("home.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        error = None
        if not username:
            error = "Please enter an username"

        elif not password:
            error = "Please enter a password"

        else:
            rows = db.execute(
                "SELECT * FROM students WHERE username = ?", username
            )

            if len(rows) != 1 or not check_password_hash(
                rows[0]["password_hash"], password
            ):
                error = "invalid username and/or password"

        if error is None:
            session["user_id"] = rows[0]["id"]
            return redirect("/")
        else:
            return render_template("login.html", error=error)
    else:
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")
        confirmation = request.form.get("confirmation")
        branch = request.form.get("branch")
        division = request.form.get("division")
        rollno = request.form.get("rollno")
        year = request.form.get("year")
        year_int = int(year)
        error = None
        success = None
        if not username:
            error = "Please enter a username"
        elif not password:
            error = "Please enter a password"
        elif not check_password(password):
            error = "Password doesn't meet requirements"
        elif not confirmation:
            error = "Password confirmation is required"
        elif not email:
            error = "Please enter your college email"
        elif not email.endswith("kkwagh.edu.in"):
            error = "Only students of K. K. Wagh Institute can register."
        elif password != confirmation:
            error = "Password confirmation did not match"
        elif not branch:
            error = "Please select your branch"
        elif branch not in branches:
            error = "Please select a valid branch"
        elif not division:
            error = "Please select your division"
        elif division not in divisions:
            error = "Please select a valid division"
        elif not rollno:
            error = "Please enter your roll number"
        elif int(rollno) < 1 or int(rollno) > 77:
            error = "Please enter a valid roll number"
        elif not year_int or year_int not in years:
            error = "Please choose a valid year"
        password_hash = generate_password_hash(password)
        if error is None:
            try:
                db.execute(
                    "INSERT INTO students (username, password_hash, email, roll_no, branch, division, year) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    username,
                    password_hash,
                    email,
                    int(rollno),
                    branch,
                    division,
                    year_int
                )
                return render_template("register.html", error=error, success="Registration Successful!")
            except:
                return render_template("register.html", error="Username and/or email has already been registered", success=success)
        else:
            return render_template("register.html", error=error, success=success)
    else:
        return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# to-do list feature
@app.route("/to-do")
@login_required
def to_do():
    tasks = db.execute(
        "SELECT * FROM todo WHERE student_id = ?", session['user_id'])
    task_number = 1
    return render_template("todo.html", tasks=tasks)


# add to-do route
@app.route("/add-to-do", methods=['POST'])
@login_required
def add_to_do():
    task = request.form.get("task")
    db.execute("INSERT INTO todo (task, status, student_id) VALUES (?, ?, ?)",
               task, -1, session['user_id'])
    return redirect("/to-do")


# update task status route
@app.route("/update/<int:task_id>")
@login_required
def update_to_do(task_id):
    curr_status = db.execute(
        "SELECT status FROM todo WHERE id = ? AND student_id = ?", task_id, session['user_id'])
    new_status = -1 * curr_status[0]['status']
    db.execute("UPDATE todo SET status = ? WHERE id = ? AND student_id = ?",
               new_status, task_id, session['user_id'])
    return redirect("/to-do")


# delete task route
@app.route("/delete/<int:task_id>")
@login_required
def delete_to_do(task_id):
    db.execute("DELETE FROM todo WHERE id = ? AND student_id = ?",
               task_id, session['user_id'])
    return redirect("/to-do")


# timetable
@app.route("/timetable")
@login_required
def timetable():
    student_id = session['user_id']
    student_branch = db.execute(
        "SELECT branch FROM students WHERE id = ?", student_id)[0]['branch']
    roll_no = db.execute("SELECT roll_no FROM students WHERE id = ?", student_id)[
                         0]['roll_no']
    batch = None
    if (roll_no < 27):
        batch = 'a1'
    elif (roll_no > 26 and roll_no < 53):
        batch = 'a2'
    elif (roll_no > 52 and roll_no < 78):
        batch = 'a3'
    time_table = db.execute(
        "SELECT day, time_slot, subject, faculty FROM timetable WHERE (branch = ?) AND ((batch = ?) OR (batch = ?))", student_branch, batch, 'all')
    faculty_data = db.execute(
        "SELECT id, name FROM faculty WHERE branch = ?", student_branch
    )
    faculty_names = {}

    for item in faculty_data:
        faculty_names[item['id']] = item['name']

    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(faculty_names)
    pp.pprint(time_table)
    return render_template("timetable.html", batch=batch, time_table = time_table, faculty_names = faculty_names)


# timetable batch switcher
@app.route("/timetable_batch", methods=['POST'])
@login_required
def timetable_batch():
    student_id = session['user_id']
    student_branch = db.execute(
        "SELECT branch FROM students WHERE id = ?", student_id)[0]['branch']
    batch = request.form.get('batch')
    time_table = db.execute(
        "SELECT day, time_slot, subject, faculty FROM timetable WHERE (branch = ?) AND ((batch = ?) OR (batch = ?))", student_branch, batch, 'all')
    faculty_data = db.execute(
        "SELECT id, name FROM faculty WHERE branch = ?", student_branch
    )
    faculty_names = {}

    for item in faculty_data:
        faculty_names[item['id']] = item['name']

    return render_template("timetable.html", batch=batch, time_table = time_table, faculty_names = faculty_names)


# study buddy
@app.route("/studybuddy/<int:id>")
@login_required
def studybuddy(id):
    if id == 1:
        return render_template("sem1.html")
    elif id == 2:
        return render_template("sem2.html")
    elif id == 2.1:
        file_path = ''
    elif id == 2.2:
        return render_template("sem2.html")
    elif id == 2.3:
        return render_template("sem2.html")
    elif id == 2.4:
        return render_template("sem2.html")
    














if __name__ == '__main__':
    app.run(debug=True)
