from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    send_from_directory
)

from flask_mysqldb import MySQL
import os

app = Flask(__name__)

# Secret Key
app.secret_key = "college_resource_secret"

# Upload Folder
UPLOAD_FOLDER = "uploads"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Ayush@1234'
app.config['MYSQL_DB'] = 'college_resource_db'

mysql = MySQL(app)


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

        cur = mysql.connection.cursor()

        cur.execute(
            """
            INSERT INTO users
            (name, email, password, branch, semester)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (name, email, password, branch, semester)
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
            WHERE email=%s AND password=%s
            """,
            (email, password)
        )

        user = cur.fetchone()

        cur.close()

        if user:

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
# Download Resource
# =========================

@app.route('/download/<filename>')
def download(filename):

    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        filename,
        as_attachment=True
    )


# =========================
# Run App
# =========================

if __name__ == '__main__':
    app.run(debug=True)