from flask import Flask, render_template, request, redirect, session, flash
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
import mysql.connector
from mysql.connector import Error
from datetime import timedelta
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "empsecretkey"
app.permanent_session_lifetime = timedelta(minutes=30)

# File upload config
UPLOAD_FOLDER = 'static/images/profile'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB limit

# Email config
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'rahithya88@gmail.com'
app.config['MAIL_PASSWORD'] = 'lxuf tlxa fdcz evvk'

mail = Mail(app)
s = URLSafeTimedSerializer(app.secret_key)

# Database connection
def get_db():
    return mysql.connector.connect(
        host="localhost",
        user='root',
        password='Rahithya@123',
        database='company'
    )

# -----------------------
# Routes
# -----------------------

@app.route('/')
def home_page():
    return render_template("register.html")

@app.route('/home')
def home1():
    return render_template("home.html")

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == "POST":
        name = request.form['name']
        email = request.form['email']
        purpose = request.form['purpose']
        message = request.form['message']

        try:
            msg = Message(
                subject=f"New Contact Request: {purpose}",
                sender=email,
                recipients=["vishnusriamara@gmail.com"]
            )
            msg.body = f"Name: {name}\nEmail: {email}\nPurpose: {purpose}\n\nMessage:\n{message}"
            mail.send(msg)

            reply = Message(
                subject="Thank You for Contacting Us",
                sender="rahithya88@gmail.com",
                recipients=[email]
            )
            reply.body = f"Hello {name},\n\nThank you for contacting us regarding: {purpose}.\nWe have received your message.\n\nYour Message:\n{message}\n\nBest Regards,\nEMS Team"
            mail.send(reply)
            flash("Message sent successfully!", "success")
        except Exception as e:
            flash(f"Error sending email: {e}", "danger")

        return redirect('/contact')

    return render_template("contact.html")

# -----------------------
# User Registration & Login
# -----------------------
@app.route('/register', methods=['POST'])
def register():
    id = request.form['id']
    username = request.form['username']
    password = request.form['password']
    role = request.form['role']
    email = request.form['email']

    hashed_pw = generate_password_hash(password)

    conn = get_db()
    try:
        cursor = conn.cursor(buffered=True)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        if cursor.fetchone():
            flash("Email already registered. Please login.", "danger")
            return redirect("/login")

        cursor.execute(
            "INSERT INTO users(id, username, password, role, email) VALUES(%s,%s,%s,%s,%s)",
            (id, username, hashed_pw, role, email)
        )
        conn.commit()
        flash("Registration successful! Please login.", "success")
    finally:
        cursor.close()
        conn.close()

    return redirect("/login")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/logincheck", methods=['POST'])
def logincheck():
    username = request.form["username"]
    pwrd = request.form["pwrd"]
    session.permanent = True

    conn = get_db()
    try:
        cursor = conn.cursor(buffered=True)
        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

    if user and check_password_hash(user[2], pwrd):
        session['user'] = user[1]
        session['profile_pic'] = user[5] if user[5] else "default.png"
        return redirect("/dashboard")
    else:
        flash("Invalid username or password", "danger")
        return redirect("/login")

# -----------------------
# Password Reset
# -----------------------
@app.route('/forgot_password')
def forget_password():
    return render_template("forgot_password.html")

@app.route('/send_reset_link', methods=["POST"])
def send_reset_link():
    email = request.form['email']

    conn = get_db()
    try:
        cursor = conn.cursor(buffered=True)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

    if user:
        token = s.dumps(email, salt="Password-reset-salt")
        link = f"http://localhost:5000/reset_password/{token}"

        try:
            msg = Message(
                "Password reset request",
                sender="vishnusriamara@gmail.com",
                recipients=[email]
            )
            msg.body = f"Click the link to reset your password: {link}"
            mail.send(msg)
            flash("Reset link sent to your email.", "info")
        except Exception as e:
            flash(f"Error sending email: {e}", "danger")
        return redirect('/login')
    else:
        flash("Email not registered.", "danger")
        return redirect("/")

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='Password-reset-salt', max_age=3600)
    except SignatureExpired:
        return "Link expired! Try again."

    if request.method == "POST":
        new_password = request.form['password']
        hashed_pw = generate_password_hash(new_password)

        conn = get_db()
        try:
            cursor = conn.cursor(buffered=True)
            cursor.execute("UPDATE users SET password=%s WHERE email=%s", (hashed_pw, email))
            conn.commit()
            flash("Password reset successful. Please login.", "success")
        finally:
            cursor.close()
            conn.close()

        return redirect("/login")

    return render_template("reset_password.html")

# -----------------------
# Dashboard
# -----------------------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect("/login")

    conn = get_db()
    try:
        cursor = conn.cursor(buffered=True)
        cursor.execute("SELECT COUNT(*) FROM employee")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT edept) FROM employee")
        dept = cursor.fetchone()[0]
        cursor.execute("SELECT MAX(esalary) FROM employee")
        max_salary = cursor.fetchone()[0] or 0
    finally:
        cursor.close()
        conn.close()

    return render_template("dashboard.html", total=total, dept=dept, max_salary=max_salary)

# -----------------------
# Employee Management
# -----------------------
@app.route("/add_employee", methods=['GET', 'POST'])
def add_employee():
    if request.method == 'POST':
        eid = request.form['eid']
        ename = request.form['ename']
        edept = request.form['edept']
        esalary = request.form['esalary']
        ephone = request.form['ephone']

        conn = get_db()
        try:
            cursor = conn.cursor(buffered=True)
            cursor.execute(
                "INSERT INTO employee(eid, ename, edept, esalary, ephone) VALUES(%s,%s,%s,%s,%s)",
                (eid, ename, edept, esalary, ephone)
            )
            conn.commit()
            flash("Employee added successfully", "success")
        finally:
            cursor.close()
            conn.close()

        return redirect("/dashboard")

    return render_template('add_employee.html')

@app.route('/edit/<eid>')
def edit_employee_form(eid):
    conn = get_db()
    try:
        cursor = conn.cursor(buffered=True)
        cursor.execute("SELECT * FROM employee WHERE eid=%s", (eid,))
        data = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
    return render_template("edit_employee.html", employee=data)

@app.route('/edit_employee', methods=["POST"])
def edit_employee():
    eid = request.form['eid']
    ename = request.form['ename']
    edept = request.form['edept']
    esalary = request.form['esalary']
    ephone = request.form['ephone']

    conn = get_db()
    try:
        cursor = conn.cursor(buffered=True)
        cursor.execute(
            "UPDATE employee SET ename=%s, edept=%s, esalary=%s, ephone=%s WHERE eid=%s",
            (ename, edept, esalary, ephone, eid)
        )
        conn.commit()
        flash("Employee updated successfully", "success")
    finally:
        cursor.close()
        conn.close()

    return redirect("/view_employee")

@app.route("/view_employee", methods=['GET', 'POST'])
def view_employee():
    conn = get_db()
    try:
        cursor = conn.cursor(buffered=True)
        if request.method == "POST":
            search = request.form['search']
            cursor.execute("SELECT * FROM employee WHERE ename LIKE %s", ('%' + search + '%',))
        else:
            cursor.execute("SELECT * FROM employee")
        data = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
    return render_template("view_employee.html", employee=data)

@app.route("/delete/<eid>")
def delete_employee(eid):
    conn = get_db()
    try:
        cursor = conn.cursor(buffered=True)
        cursor.execute("DELETE FROM employee WHERE eid=%s", (eid,))
        conn.commit()
        flash("Employee deleted successfully", "info")
    finally:
        cursor.close()
        conn.close()
    return redirect("/view_employee")

# -----------------------
# Profile
# -----------------------
@app.route('/profile')
def profile():
    if 'user' not in session:
        return redirect('/login')

    conn = get_db()
    try:
        cursor = conn.cursor(buffered=True)
        cursor.execute("SELECT * FROM users WHERE username=%s", (session['user'],))
        user = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

    return render_template("profile.html", user=user)

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user' not in session:
        return redirect('/login')

    conn = get_db()
    try:
        cursor = conn.cursor(buffered=True)

        if request.method == "POST":
            username = request.form['username']
            email = request.form['email']
            role = request.form['role']
            file = request.files.get('profile_pic')
            filename = None

            if file and file.filename != "":
                filename = secure_filename(file.filename)
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                cursor.execute(
                    "UPDATE users SET username=%s, email=%s, role=%s, profile_pic=%s WHERE username=%s",
                    (username, email, role, filename, session['user'])
                )
                session['profile_pic'] = filename
            else:
                cursor.execute(
                    "UPDATE users SET username=%s, email=%s, role=%s WHERE username=%s",
                    (username, email, role, session['user'])
                )

            conn.commit()
            flash("Profile updated successfully", "success")
            return redirect('/profile')

        cursor.execute("SELECT * FROM users WHERE username=%s", (session['user'],))
        user = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

    return render_template("edit_profile.html", user=user)

# -----------------------
# Logout
# -----------------------
@app.route("/logout")
def logout():
    session.pop('user', None)
    session.pop('profile_pic', None)
    flash("Logged out successfully", "info")
    return redirect("/login")

# -----------------------
# Run App
# -----------------------
if __name__ == '__main__':
    app.run(debug=True)