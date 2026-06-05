from flask import Flask
from models import db, User, Resource

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://college_resource_db_user:cqahCPYi18s3JwnTEPYQ60bTeH07w7yU@dpg-d8hgg13eo5us73869uvg-a.oregon-postgres.render.com/college_resource_db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():

    db.create_all()

    print("Tables created!")

    print("User table:", User.__tablename__)
    print("Resource table:", Resource.__tablename__)