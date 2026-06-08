from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):

    __tablename__ = 'users'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    branch = db.Column(
        db.String(50)
    )

    semester = db.Column(
        db.String(20)
    )

    profile_picture = db.Column(
        db.String(255)
    )


class Resource(db.Model):

    __tablename__ = 'resources'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.String(255)
    )

    subject = db.Column(
        db.String(255)
    )

    resource_type = db.Column(
        db.String(100)
    )

    semester = db.Column(
        db.String(20)
    )

    description = db.Column(
        db.Text
    )

    file_name = db.Column(
        db.String(255)
    )

    uploaded_by = db.Column(
        db.Integer,
        db.ForeignKey('users.id')
    )

    user = db.relationship(
        'User',
        backref='resources'
    )

    upload_date = db.Column(
        db.DateTime,
        server_default=db.func.now()
    )