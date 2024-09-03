from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO

db = SQLAlchemy()
socketio = SocketIO()

def create_app():
    """
    Create and configure the Flask application.

    This function initializes the Flask app with necessary extensions and configurations.
    It sets up the database, login manager, and registers routes.

    Returns
    -------
    app : Flask
        The configured Flask application instance.

    Notes
    -----
    This function performs the following tasks:
    1. Creates a Flask app instance
    2. Configures the database URI and secret key
    3. Initializes SQLAlchemy, SocketIO, and LoginManager
    4. Sets up the user loader for Flask-Login
    5. Initializes Bcrypt for password hashing
    6. Registers routes and error handlers
    7. Sets up database migrations with Flask-Migrate

    The function also defines an inner function `load_user` for Flask-Login
    and an `unauthorized_callback` for handling unauthorized access attempts.
    """
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./testdb.db'
    app.secret_key = 'supersecret'

    db.init_app(app)
    socketio.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)

    from models import User

    @login_manager.user_loader
    def load_user(uid):
        """
        Load a user from the database.

        This function is used by Flask-Login to reload the user object from
        the user ID stored in the session.

        Parameters
        ----------
        uid : str
            The user ID to load.

        Returns
        -------
        User or None
            The User object if found, None otherwise.
        """
        return User.query.get(uid)
    
    bcrypt = Bcrypt(app)

    @login_manager.unauthorized_handler
    def unauthorized_callback():
        """
        Handle unauthorized access attempts.

        This function is called when an unauthorized user tries to access
        a login_required route.

        Returns
        -------
        redirect
            A redirect response to the index page.
        """
        return redirect(url_for('index'))

    from routes import register_routes
    register_routes(app, db, bcrypt, socketio)

    migrate = Migrate(app, db)

    return app
