from flask_login import UserMixin
from app import db

class User(db.Model, UserMixin):

    __tablename__ = 'users'
    uid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100))

    def __repr__(self):
        return f"User('{self.username}')"
    
    def get_id(self):
        return self.uid

class ScriptLabels(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    script_name = db.Column(db.String(100), unique=True, nullable=False)
    Labels = db.Column(db.String(100), nullable=False)