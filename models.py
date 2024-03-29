from flask_login import UserMixin
from app import db

class User(db.Model, UserMixin):
    """
    Represents a user in the application.

    Attributes:
        uid (int): The unique identifier for the user.
        username (str): The username of the user.
        password (str): The password of the user.
        role (str): The role of the user.

    Methods:
        __repr__(): Returns a string representation of the user object.
        get_id(): Returns the unique identifier of the user.

    """

    __tablename__ = 'users'
    uid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100))

    def __repr__(self):
        return f"User('{self.username}')"
    
    def get_id(self):
        return self.uid

