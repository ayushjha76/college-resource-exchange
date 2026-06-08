import os
from flask import (
    Flask,
    request,
    session,
    redirect,
    send_from_directory
)


app = Flask(__name__)


from models import db, User, Resource
from werkzeug.utils import secure_filename
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)


app.secret_key = "college_resource_secret"
UPLOAD_FOLDER = "uploads"

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(
    app.config['UPLOAD_FOLDER'],
    exist_ok=True
)

app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://college_resource_db_user:cqahCPYi18s3JwnTEPYQ60bTeH07w7yU@dpg-d8hgg13eo5us73869uvg-a.oregon-postgres.render.com/college_resource_db"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

@app.route('/')
def home():
    return "PostgreSQL Version Running"


@app.route('/users')
def users():

    all_users = User.query.all()

    result = ""

    for user in all_users:
        result += f"{user.id} - {user.name} - {user.email}<br>"

    return result


@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        branch = request.form['branch']
        semester = request.form['semester']

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:
            return "Email already exists"

        

    return '''
    <form method="POST">
        <input name="name" placeholder="Name"><br>
        <input name="email" placeholder="Email"><br>
        <input name="password" placeholder="Password"><br>
        <input name="branch" placeholder="Branch"><br>
        <input name="semester" placeholder="Semester"><br>
        <button type="submit">Register</button>
    </form>
    '''


@app.route('/test-register')
def test_register():

    existing = User.query.filter_by(
        email="test2@example.com"
    ).first()

    if existing:
        return "User Already Exists"

    user = User(
        name="Test User",
        email="test2@example.com",
        password=generate_password_hash("123456"),
        branch="CSE",
        semester="6"
    )

    db.session.add(user)
    db.session.commit()

    return "User Added Successfully"

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(
            email=email
        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):

            session['user_id'] = user.id
            session['user_name'] = user.name

            return redirect('/dashboard')

        return "Invalid Email or Password"

    return '''
    <form method="POST">

        <input
            name="email"
            placeholder="Email">

        <br><br>

        <input
            type="password"
            name="password"
            placeholder="Password">

        <br><br>

        <button type="submit">
            Login
        </button>

    </form>
    '''
@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:
        return redirect('/login')

    total_resources = Resource.query.count()

    my_uploads = Resource.query.filter_by(
        uploaded_by=session['user_id']
    ).count()

    return f"""
    Welcome {session['user_name']}

    <br><br>

    Total Resources:
    {total_resources}

    <br><br>

    My Uploads:
    {my_uploads}
    """
@app.route('/logout')
def logout():

    session.clear()

    return redirect('/login')

@app.route('/profile')
def profile():

    if 'user_id' not in session:
        return redirect('/login')

    user = User.query.get(
        session['user_id']
    )

    total_uploads = Resource.query.filter_by(
        uploaded_by=session['user_id']
    ).count()

    image_html = ""

    if user.profile_picture:

        image_html = f"""
        <img
        src="/static/profile_pictures/{user.profile_picture}"
        width="150">
        <br><br>
        """

    return f"""
    <h1>My Profile</h1>

    {image_html}

    Name: {user.name}<br>
    Email: {user.email}<br>
    Branch: {user.branch}<br>
    Semester: {user.semester}<br>

    <br>

    Total Uploads:
    {total_uploads}

    <hr>

    <form
        method="POST"
        action="/upload-profile-picture"
        enctype="multipart/form-data">

        <input
            type="file"
            name="profile_picture">

        <button type="submit">
            Upload Picture
        </button>

    </form>
    """

@app.route('/user/<int:user_id>')
def public_profile(user_id):

    if 'user_id' not in session:
        return redirect('/login')

    user = User.query.get(user_id)

    if not user:
        return "User not found"

    total_uploads = Resource.query.filter_by(
        uploaded_by=user_id
    ).count()

    image_html = ""

    if user.profile_picture:

        image_html = f"""
        <img
        src="/static/profile_pictures/{user.profile_picture}"
        width="150">
        <br><br>
        """

    return f"""
    <h1>Public Profile</h1>

    {image_html}

    Name: {user.name}<br>
    Branch: {user.branch}<br>
    Semester: {user.semester}<br>

    Total Uploads:
    {total_uploads}
    """


@app.route(
    '/change-password',
    methods=['GET', 'POST']
)
def change_password():

    if 'user_id' not in session:
        return redirect('/login')

    user = User.query.get(
        session['user_id']
    )

    if request.method == 'POST':

        current_password = request.form[
            'current_password'
        ]

        new_password = request.form[
            'new_password'
        ]

        confirm_password = request.form[
            'confirm_password'
        ]

        if new_password != confirm_password:
            return "Passwords do not match"

        if not check_password_hash(
            user.password,
            current_password
        ):
            return "Current password incorrect"

        user.password = generate_password_hash(
            new_password
        )

        db.session.commit()

        return "Password Updated"

    return '''
    <form method="POST">

        <input
            type="password"
            name="current_password"
            placeholder="Current Password">

        <br><br>

        <input
            type="password"
            name="new_password"
            placeholder="New Password">

        <br><br>

        <input
            type="password"
            name="confirm_password"
            placeholder="Confirm Password">

        <br><br>

        <button type="submit">
            Change Password
        </button>

    </form>
    '''

@app.route(
    '/upload-profile-picture',
    methods=['POST']
)
def upload_profile_picture():

    if 'user_id' not in session:
        return redirect('/login')

    if 'profile_picture' not in request.files:
        return redirect('/profile')

    file = request.files['profile_picture']

    if file.filename == '':
        return redirect('/profile')

    filename = secure_filename(
        file.filename
    )

    filename = (
        str(session['user_id'])
        + "_"
        + filename
    )

    save_path = os.path.join(
        'static',
        'profile_pictures',
        filename
    )

    file.save(save_path)

    user = User.query.get(
        session['user_id']
    )

    user.profile_picture = filename

    db.session.commit()

    return redirect('/profile')


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

        resource = Resource(
            title=title,
            subject=subject,
            resource_type=resource_type,
            semester=semester,
            description=description,
            file_name=filename,
            uploaded_by=session['user_id']
        )

        db.session.add(resource)
        db.session.commit()

        return "Resource Uploaded"

    return '''
    <form method="POST" enctype="multipart/form-data">

        <input name="title" placeholder="Title"><br><br>

        <input name="subject" placeholder="Subject"><br><br>

        <input name="resource_type" placeholder="Type"><br><br>

        <input name="semester" placeholder="Semester"><br><br>

        <textarea name="description"></textarea><br><br>

        <input type="file" name="file"><br><br>

        <button type="submit">
            Upload
        </button>

    </form>
    '''

@app.route('/resources')
def resources():

    if 'user_id' not in session:
        return redirect('/login')

    search = request.args.get('search')

    if search:

        all_resources = Resource.query.filter(
            (Resource.title.ilike(f"%{search}%")) |
            (Resource.subject.ilike(f"%{search}%")) |
            (Resource.resource_type.ilike(f"%{search}%"))
        ).all()

    else:

        all_resources = Resource.query.order_by(
            Resource.upload_date.desc()
        ).all()

    result = """

    <form method="GET">

        <input
            name="search"
            placeholder="Search Resource">

        <button type="submit">
            Search
        </button>

    </form>

    <hr>
    """

    for resource in all_resources:

        result += f"""
        <b>{resource.title}</b><br>

        Subject:
        {resource.subject}<br>

        Uploaded By:
        {resource.user.name}<br>

        <a href="/download/{resource.file_name}">
        Download
        </a>

        <hr>
        """

    return result

@app.route('/my-resources')
def my_resources():

    if 'user_id' not in session:
        return redirect('/login')

    resources = Resource.query.filter_by(
        uploaded_by=session['user_id']
    ).all()

    result = ""

    for resource in resources:

        result += f"""
        {resource.title}

        <a href="/delete/{resource.id}">
        Delete
        </a>

        <br><br>
        """

    return result

@app.route('/download/<filename>')
def download(filename):

    if 'user_id' not in session:
        return redirect('/login')

    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        filename,
        as_attachment=True
    )

@app.route('/delete/<int:resource_id>')
def delete_resource(resource_id):

    if 'user_id' not in session:
        return redirect('/login')

    resource = Resource.query.get(
        resource_id
    )

    if not resource:
        return redirect('/resources')

    if resource.uploaded_by != session['user_id']:
        return "Unauthorized"

    file_path = os.path.join(
        app.config['UPLOAD_FOLDER'],
        resource.file_name
    )

    if os.path.exists(file_path):
        os.remove(file_path)

    db.session.delete(resource)

    db.session.commit()

    return redirect('/my-resources')


if __name__ == '__main__':
    app.run(debug=True)