from flask import Flask
from models import db
from models import db, User
from werkzeug.security import generate_password_hash
from flask import request

app = Flask(__name__)

app.secret_key = "college_resource_secret"

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

        new_user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            branch=branch,
            semester=semester
        )

        db.session.add(new_user)
        db.session.commit()

        return "Registration Successful"

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

if __name__ == '__main__':
    app.run(debug=True)

