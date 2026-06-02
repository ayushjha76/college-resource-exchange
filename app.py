from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    send_from_directory
)
from flask_mail import Mail, Message
import random
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import os
import time
app = Flask(__name__)

# Secret Key
app.secret_key = "college_resource_secret"

# Upload Folder
UPLOAD_FOLDER = "uploads"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# MySQL Configuration


app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB')

mysql = MySQL(app)
# Mail Configuration

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True

app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')

mail = Mail(app)

# =========================
# Home Page
# =========================

@app.route('/')
def home():
    return render_template('index.html')


# =========================
# Register
# =========================

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        branch = request.form['branch']
        semester = request.form['semester']

        hashed_password = generate_password_hash(password)

        cur = mysql.connection.cursor()

        cur.execute(
            """
            INSERT INTO users
            (name, email, password, branch, semester)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                name,
                email,
                hashed_password,
                branch,
                semester
            )
        )

        mysql.connection.commit()
        cur.close()

        return redirect('/login')

    return render_template('register.html')
# =========================
# Login
# =========================

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()

        cur.execute(
            """
            SELECT * FROM users
            WHERE email=%s
            """,
            (email,)
        )

        user = cur.fetchone()

        cur.close()

        if user:

            stored_password = user[3]

            if check_password_hash(
                stored_password,
                password
            ):

                session['user_id'] = user[0]
                session['user_name'] = user[1]

                return redirect('/dashboard')

        return "Invalid Email or Password"

    return render_template('login.html')

# =========================
# Dashboard
# =========================

@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute("SELECT COUNT(*) FROM resources")
    total_resources = cur.fetchone()[0]

    cur.execute(
        """
        SELECT COUNT(*)
        FROM resources
        WHERE uploaded_by=%s
        """,
        (session['user_id'],)
    )

    my_uploads = cur.fetchone()[0]

    cur.close()

    return render_template(
        'dashboard.html',
        username=session['user_name'],
        total_resources=total_resources,
        my_uploads=my_uploads
    )


# =========================
# Logout
# =========================

@app.route('/logout')
def logout():

    session.clear()

    return redirect('/')


# =========================
# Upload Resource
# =========================

@app.route('/upload', methods=['GET', 'POST'])
def upload():

    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':

        title = request.form['title']
        subject = request.form['subject']
        resource_type = request.form['resource_type']
        semester = request.form['semester']
        description = request.form['description']

        file = request.files['file']

        filename = file.filename

        file.save(
            os.path.join(
                app.config['UPLOAD_FOLDER'],
                filename
            )
        )

        cur = mysql.connection.cursor()

        cur.execute(
            """
            INSERT INTO resources
            (
                title,
                subject,
                resource_type,
                semester,
                description,
                file_name,
                uploaded_by
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                title,
                subject,
                resource_type,
                semester,
                description,
                filename,
                session['user_id']
            )
        )

        mysql.connection.commit()
        cur.close()

        return redirect('/dashboard')

    return render_template('upload.html')


# =========================
# Resources + Search
# =========================

@app.route('/resources')
def resources():
    if 'user_id' not in session:
        return redirect('/login')

    search = request.args.get('search')

    cur = mysql.connection.cursor()

    if search:

        query = """
        SELECT
            resources.id,
            resources.title,
            resources.subject,
            resources.resource_type,
            resources.semester,
            resources.file_name,
            resources.uploaded_by,
            users.name
        FROM resources
        JOIN users
        ON resources.uploaded_by = users.id
        WHERE
            resources.title LIKE %s
            OR resources.subject LIKE %s
            OR resources.resource_type LIKE %s
        ORDER BY resources.upload_date DESC
        """

        value = f"%{search}%"

        cur.execute(
            query,
            (value, value, value)
        )

    else:

        cur.execute(
            """
            SELECT
                resources.id,
                resources.title,
                resources.subject,
                resources.resource_type,
                resources.semester,
                resources.file_name,
                resources.uploaded_by,
                users.name
            FROM resources
            JOIN users
            ON resources.uploaded_by = users.id
            ORDER BY resources.upload_date DESC
            """
        )

    all_resources = cur.fetchall()

    cur.close()

    return render_template(
        'resources.html',
        resources=all_resources
    )

# =========================
# My Resource
# =========================
@app.route('/my-resources')
def my_resources():

    if 'user_id' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute(
        """
        SELECT
            id,
            title,
            subject,
            resource_type,
            semester,
            file_name
        FROM resources
        WHERE uploaded_by = %s
        ORDER BY upload_date DESC
        """,
        (session['user_id'],)
    )

    my_resources = cur.fetchall()

    cur.close()

    return render_template(
        'my_resources.html',
        resources=my_resources,
        username=session['user_name']
    )

# =========================
# Download Resource
# =========================

@app.route('/download/<filename>')
def download(filename):

    if 'user_id' not in session:
        return redirect('/login')

    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        filename,
        as_attachment=True
    )

# =========================
# Delete Resource
# =========================

@app.route('/delete/<int:resource_id>')
def delete_resource(resource_id):

    if 'user_id' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute(
        """
        SELECT file_name, uploaded_by
        FROM resources
        WHERE id = %s
        """,
        (resource_id,)
    )

    resource = cur.fetchone()

    if resource:

        filename = resource[0]
        owner_id = resource[1]

        if owner_id == session['user_id']:

            file_path = os.path.join(
                app.config['UPLOAD_FOLDER'],
                filename
            )

            if os.path.exists(file_path):
                os.remove(file_path)

            cur.execute(
                """
                DELETE FROM resources
                WHERE id = %s
                """,
                (resource_id,)
            )

            mysql.connection.commit()

    cur.close()

    return redirect('/resources')

# =========================
# change password
# =========================
@app.route('/change-password', methods=['GET', 'POST'])
def change_password():

    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':

        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            return "New passwords do not match"

        cur = mysql.connection.cursor()

        cur.execute(
            """
            SELECT password
            FROM users
            WHERE id=%s
            """,
            (session['user_id'],)
        )

        user = cur.fetchone()

        stored_password = user[0]

        if not check_password_hash(
            stored_password,
            current_password
        ):
            return "Current password is incorrect"

        hashed_password = generate_password_hash(
            new_password
        )

        cur.execute(
            """
            UPDATE users
            SET password=%s
            WHERE id=%s
            """,
            (
                hashed_password,
                session['user_id']
            )
        )

        mysql.connection.commit()

        cur.close()

        return redirect('/profile')

    return render_template(
        'change_password.html'
    )

# =========================
# PROFILE
# =========================
@app.route('/profile')
def profile():

    if 'user_id' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute(
        """
        SELECT
            name,
            email,
            branch,
            semester,
            profile_picture
        FROM users
        WHERE id = %s
        """,
        (session['user_id'],)
    )

    user = cur.fetchone()

    cur.execute(
        """
        SELECT COUNT(*)
        FROM resources
        WHERE uploaded_by = %s
        """,
        (session['user_id'],)
    )

    total_uploads = cur.fetchone()[0]

    cur.close()

    return render_template(
        'profile.html',
        user=user,
        total_uploads=total_uploads
    )

#public profile
@app.route('/user/<int:user_id>')
def public_profile(user_id):
    if 'user_id' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute(
        """
        SELECT
            name,
            branch,
            semester,
            profile_picture
        FROM users
        WHERE id = %s
        """,
        (user_id,)
    )

    user = cur.fetchone()

    if not user:
        cur.close()
        return "User not found"

    cur.execute(
        """
        SELECT COUNT(*)
        FROM resources
        WHERE uploaded_by = %s
        """,
        (user_id,)
    )

    total_uploads = cur.fetchone()[0]

    cur.close()

    return render_template(
        'public_profile.html',
        user=user,
        total_uploads=total_uploads
    )

# =========================
# profile pic upload
# =========================
from werkzeug.utils import secure_filename


@app.route('/upload-profile-picture', methods=['POST'])
def upload_profile_picture():

    if 'user_id' not in session:
        return redirect('/login')

    if 'profile_picture' not in request.files:
        return redirect('/profile')

    file = request.files['profile_picture']

    if file.filename == '':
        return redirect('/profile')

    # Create folder if it doesn't exist
    folder_path = os.path.join(
        app.root_path,
        'static',
        'profile_pictures'
    )

    os.makedirs(folder_path, exist_ok=True)

    # Safe filename
    original_filename = secure_filename(file.filename)

    filename = (
        str(session['user_id'])
        + "_"
        + original_filename
    )

    save_path = os.path.join(
        folder_path,
        filename
    )

    # Save image
    file.save(save_path)

    # Update database
    cur = mysql.connection.cursor()

    cur.execute(
        """
        UPDATE users
        SET profile_picture = %s
        WHERE id = %s
        """,
        (
            filename,
            session['user_id']
        )
    )

    mysql.connection.commit()
    cur.close()

    return redirect('/profile')

#SEND OTP
@app.route('/send-otp', methods=['POST'])
def send_otp():
    cur = mysql.connection.cursor()

    cur.execute(
        """
        SELECT id
        FROM users
        WHERE email=%s
        """,
        (request.form['email'],)
    )

    existing_user = cur.fetchone()

    cur.close()

    if existing_user:
        return "Email already registered"

    otp = str(random.randint(100000, 999999))

    session['otp'] = otp
    session['otp_time'] = time.time()

    session['temp_name'] = request.form['name']
    session['temp_email'] = request.form['email']
    session['temp_password'] = request.form['password']
    session['temp_branch'] = request.form['branch']
    session['temp_semester'] = request.form['semester']

    msg = Message(
        'College Resource Exchange OTP',
        sender=app.config['MAIL_USERNAME'],
        recipients=[request.form['email']]
    )

    msg.body = f"Your OTP is: {otp}"

    mail.send(msg)

    return redirect('/verify-otp')

#VERIFY OTP
@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    

    if time.time() - session['otp_time'] > 300:
        return "OTP Expired"

    if request.method == 'POST':

        entered_otp = request.form['otp']

        if time.time() - session.get('otp_time', 0) > 300:
            return "OTP Expired. Please register again."

        if entered_otp == session.get('otp'):

            hashed_password = generate_password_hash(
                session['temp_password']
            )

            cur = mysql.connection.cursor()

            cur.execute(
                """
                INSERT INTO users
                (name, email, password, branch, semester)
                VALUES (%s,%s,%s,%s,%s)
                """,
                (
                    session['temp_name'],
                    session['temp_email'],
                    hashed_password,
                    session['temp_branch'],
                    session['temp_semester']
                )
            )
            mysql.connection.commit()
            cur.close()

            # Clear OTP data
            session.pop('otp', None)
            session.pop('otp_time', None)

            # Clear temporary registration data
            session.pop('temp_name', None)
            session.pop('temp_email', None)
            session.pop('temp_password', None)
            session.pop('temp_branch', None)
            session.pop('temp_semester', None)

            return redirect('/login')

        return "Invalid OTP"

    return render_template('verify_otp.html')

# =========================
# Run App
# =========================

if __name__ == '__main__':
    app.run(debug=True)