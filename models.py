from flask_login import UserMixin
from app import db

class User(db.Model, UserMixin):
    """
    User model for storing user account information.

    This class represents a user in the application, storing their unique identifier,
    username, password, and role. It inherits from both SQLAlchemy's Model and 
    Flask-Login's UserMixin.

    Attributes
    ----------
    uid : int
        The unique identifier for the user (primary key).
    username : str
        The user's username (unique, not nullable).
    password : str
        The user's hashed password (not nullable).
    role : str
        The user's role in the application.

    Methods
    -------
    __repr__()
        Returns a string representation of the User instance.
    get_id()
        Returns the user's unique identifier as a string.
    """

    __tablename__ = 'users'
    uid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100))

    def __repr__(self):
        """
        Return a string representation of the User instance.

        Returns
        -------
        str
            A string containing the user's username.
        """
        return f"User('{self.username}')"
    
    def get_id(self):
        """
        Get the unique identifier for the user.

        This method is required by Flask-Login.

        Returns
        -------
        str
            The user's unique identifier as a string.
        """
        return self.uid

class ScriptLabels(db.Model):
    """
    ScriptLabels model for storing labels associated with scripts.

    This class represents the labels or parameters associated with a script
    in the application.

    Attributes
    ----------
    id : int
        The unique identifier for the script label entry (primary key).
    script_name : str
        The name of the script (unique, not nullable).
    Labels : str
        A string containing the labels or parameters associated with the script (not nullable).
    """
    id = db.Column(db.Integer, primary_key=True)
    script_name = db.Column(db.String(100), unique=True, nullable=False)
    Labels = db.Column(db.String(100), nullable=False)