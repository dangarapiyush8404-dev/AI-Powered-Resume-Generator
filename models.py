from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class StudentProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    name = db.Column(db.String(120))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(50))
    address = db.Column(db.String(200))
    summary = db.Column(db.Text)
    skills = db.Column(db.Text)
    projects = db.Column(db.Text)
    education = db.Column(db.Text)
    experience = db.Column(db.Text)
    language = db.Column(db.Text)
    photo_url = db.Column(db.String(500))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))