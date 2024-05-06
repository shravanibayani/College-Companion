from datetime import datetime, timedelta
from cs50 import SQL
from flask import Flask, jsonify, render_template, request, session, redirect, url_for
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from flask import send_file
import os, json, requests, pprint, sqlite3
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from oauthlib.oauth2 import WebApplicationClient
from dotenv import load_dotenv
from db import init_db_command
from user import User
import logging

logging.basicConfig(level=logging.DEBUG)

load_dotenv()
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('CLIENT_SECRET')
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

# Configuring the application
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
login_manager = LoginManager()
login_manager.init_app(app)

# Configuring the session
app.config["SESSION_PERMENENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# DB setup
try:
    init_db_command()
except sqlite3.OperationalError:
    pass

# OAuth 2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)

# Flask login helper to retrieve user from db
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# database
db = SQL("sqlite:///database.db")

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

# Allowed Subjects
subjects = {'ads':'Advanced Data Structures',
                'cn': 'Computer Networks',
                'sepm' : 'Software Engineering and Project Management',
                'os': 'Operating Systems',
                'm3' : 'Applied Mathematics - III',
                'cst' : 'Client Side Technology'}


@app.route("/")
def index():
    if current_user.is_authenticated:
        return render_template("home.html")
    else:
        return render_template("login.html")


def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()


@app.route("/login")
def login():
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)


@app.route("/login/callback")
def callback():
    code = request.args.get("code")
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )
    client.parse_request_body_response(json.dumps(token_response.json()))

    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
        if not users_email.endswith("kkwagh.edu.in"):
            return render_template("login_fail.html", message="Currently, only students of the K. K. Wagh Institute are allowed to sign up. Please ensure you have a valid K. K. Wagh Institute email address to proceed with the sign-up process.")
    else:
        return render_template("login_fail.html", message="User email not available or not verified by Google.")
    
    user = User(
        id_=unique_id, name=users_name, email=users_email, profile_pic=picture
    )

    if not User.get(unique_id):
        User.create(unique_id, users_name, users_email, picture)
        session["user_id"] = unique_id
        login_user(user)
        return redirect(url_for("register"))

    session["user_id"] = unique_id
    login_user(user)
    return redirect(url_for("index"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        branch = request.form.get("branch")
        division = request.form.get("division")
        rollno = request.form.get("rollno")
        year = request.form.get("year")
        year_int = int(year)
        error = None
        success = None

        if not branch:
            error = "Please select your branch"
        elif not username:
            error = "Please enter a username"
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
        if error is None:
            try:
                print("user id: ",session['user_id'])
                db.execute(
                    "INSERT INTO students (id, username, roll_no, branch, division, year) VALUES (?, ?, ?, ?, ?, ?)",
                    session['user_id'],
                    username,
                    int(rollno),
                    branch,
                    division,
                    year_int
                )
                return redirect((url_for("index")))
            except Exception as e:
                logging.error(f"Registration error: {e}")
                db.rollback()
                return jsonify({"error": str(e)}), 500
    else:
        return render_template("register.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for("index"))


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
    roll_number = int(db.execute(
        "SELECT roll_no FROM students WHERE id = ?", student_id)[0]['roll_no'])
    if roll_number <= 26:
        student_batch = 'a1'
    elif roll_number >= 27 and roll_number <= 52:
        student_batch = 'a2'
    elif roll_number >= 53 and roll_number <= 77:
        student_batch = 'a3'
    else:
        student_batch = 'all'

    batch = request.args.get('batch', student_batch)
    current_date = datetime.now()
    current_day = current_date.strftime('%A')
    current_time = datetime.now().time()

    if current_day == "Sunday":
        day = request.args.get('day', 'Monday')
    else:
        day = request.args.get('day', current_day)

    time_table = db.execute(
        "SELECT time_slot, subject, faculty FROM timetable WHERE (branch = ?) AND (batch = ? OR batch = ?) AND (day = ?)", student_branch, batch, 'all', day)

    faculty_data = db.execute(
        "SELECT id, name FROM faculty WHERE branch = ?", student_branch
    )
    faculty_names = {}

    for item in faculty_data:
        faculty_names[item['id']] = item['name']

    return render_template("timetable.html", batch=batch, day=day, time_table=time_table, faculty_names=faculty_names, current_time=current_time, datetime=datetime, current_day=current_day)


# timetable batch switcher
@app.route("/timetable_batch")
@login_required
def timetable_batch():
    student_id = session['user_id']
    student_branch = db.execute(
        "SELECT branch FROM students WHERE id = ?", student_id)[0]['branch']

    roll_number = int(db.execute(
        "SELECT roll_no FROM students WHERE id = ?", student_id)[0]['roll_no'])
    if roll_number <= 26:
        student_batch = 'a1'
    elif roll_number >= 27 and roll_number <= 52:
        student_batch = 'a2'
    elif roll_number >= 53 and roll_number <= 77:
        student_batch = 'a3'
    else:
        student_batch = 'all'

    batch = request.args.get('batch', student_batch)

    current_date = datetime.now()
    current_day = current_date.strftime('%A')

    if current_day == "Sunday":
        day = request.args.get('day', 'Monday')
    else:
        day = request.args.get('day', current_day)
    return redirect(url_for('timetable', batch=batch, day=day))


# study buddy
@app.route("/studybuddy")
@login_required
def studybuddy():
    sem = int(request.args.get('sem', 0))
    return render_template('studybuddy.html', sem=sem)


# syllabus
@app.route("/syllabus")
@login_required
def syllabus_download():
    sem = request.args.get('sem')
    student_id = session['user_id']
    student_branch = db.execute(
        "SELECT branch FROM students WHERE id = ?", student_id)[0]['branch']
    student_division = db.execute(
        "SELECT division FROM students WHERE id = ?", student_id)[0]['division']
    student_year = db.execute(
        "SELECT year FROM students WHERE id = ?", student_id)[0]['year']
    try:
        file_path = db.execute(
        "SELECT file_path FROM notes WHERE (branch = ?) AND (div = ?) AND (year = ?) AND (unit = ?) AND (subject = ?)", student_branch, student_division, student_year, sem, "syllabus")[0]['file_path']
        return send_file(file_path, as_attachment=True)
    except:
        return render_template('apology.html')


# notes
@app.route("/notes")
@login_required
def notes():
    student_id = session['user_id']
    stduent_username = db.execute(
        "SELECT username FROM students WHERE id = ?", student_id)[0]['username']
    student_branch = db.execute(
        "SELECT branch FROM students WHERE id = ?", student_id)[0]['branch']
    student_division = db.execute(
        "SELECT division FROM students WHERE id = ?", student_id)[0]['division']
    student_year = db.execute(
        "SELECT year FROM students WHERE id = ?", student_id)[0]['year']
    notes = db.execute(
        "SELECT id, subject, unit, uploaded_by, file_path FROM notes WHERE (branch = ?) AND (div = ?) AND (year = ?)", student_branch, student_division, student_year)
    
    # pretty print the notes 
    # pprint.pp(notes)

    unique_subjects = {}
    for note in notes:
        unique_subjects[note['subject']] = None
    unique_subject_list = list(unique_subjects.keys())

    if 'syllabus' in unique_subject_list:
        unique_subject_list.remove('syllabus')
    
    subject_requested = request.args.get('subject')
    requested_unit = request.args.get('unit')

    if subject_requested in unique_subject_list:
        requested_notes = [note for note in notes if note['subject'] == subject_requested]
        if requested_unit and requested_unit in ['0', '1', '2', '3', '4', '5']:
            notes_filtered = [note for note in requested_notes if note['unit'] == requested_unit]
            for note in notes_filtered:
                note['file_name'] = os.path.basename(note['file_path'])
            # print("Requested Notes: ")
            # pprint.pp(requested_notes)
            # print("Filtered Notes: ")
            # pprint.pp(notes_filtered)
            # print("Requested Unit: "+ str(requested_unit))
            if requested_unit == '0':
                requested_unit = 'Reference'
            return render_template('subject.html', notes_filtered=notes_filtered, subjects=subjects, subject_requested=subject_requested, requested_unit=requested_unit, student_username=stduent_username)
        else:
            return render_template('subject.html', subjects=subjects, subject_requested=subject_requested)
    else:
        return render_template('notes.html', unique_subjects=unique_subject_list, subjects=subjects)


# notes download
@app.route("/notes_download")
@login_required
def notes_download():
    file_path = request.args.get('file_path')
    response = send_file(file_path, as_attachment=True)
    return response


# notes upload
@app.route("/upload", methods=['POST'])
@login_required
def notes_upload():
    student_id = session['user_id']
    stduent_username = db.execute(
        "SELECT username FROM students WHERE id = ?", student_id)[0]['username']
    student_branch = db.execute(
        "SELECT branch FROM students WHERE id = ?", student_id)[0]['branch']
    student_division = db.execute(
        "SELECT division FROM students WHERE id = ?", student_id)[0]['division']
    student_year = db.execute(
        "SELECT year FROM students WHERE id = ?", student_id)[0]['year']
    file = request.files['file']
    file_name = file.filename
    file_path = os.path.join('upload',file_name)
    file.save(file_path)
    # print("File Name: " + file_name)
    subject = request.args.get('subject')
    unit = request.args.get('unit')
    if unit == 'Reference':
        unit = '0'
    # print("upload unit: " + unit)
    db.execute("INSERT INTO notes (subject, unit, uploaded_by, file_path, branch, div, year) VALUES (?, ?, ?, ?, ?, ?, ?)",
               subject, unit, stduent_username, file_path, student_branch, student_division, student_year)
    return redirect(request.referrer)


# notes delete
@app.route('/delete')
@login_required
def delete_notes():
    notes_id = int(request.args.get('notes_id'))
    file_path = db.execute("SELECT file_path FROM notes WHERE id = ?", notes_id)[0]['file_path']
    db.execute("DELETE FROM notes WHERE id = ?", notes_id)
    os.remove(file_path)
    return redirect(request.referrer)


# faculty
@app.route("/faculty")
@login_required
def faculty():
    student_id = session['user_id']
    student_branch = db.execute(
        "SELECT branch FROM students WHERE id = ?", student_id)[0]['branch']
    faculty = db.execute("SELECT * FROM faculty WHERE branch = ?", student_branch)
    return render_template("faculty.html", faculty=faculty, subjects=subjects)


if __name__ == '__main__':
    app.run(debug=True, ssl_context="adhoc")
