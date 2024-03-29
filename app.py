from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

db = SQLAlchemy()

def create_app():
    """
    Create and configure the Flask application.

    Returns:
        app (Flask): The Flask application instance.
    """
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./testdb.db'

    app.secret_key = 'supersecret'

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)

    from models import User

    @login_manager.user_loader
    def load_user(uid):
        """
        Load a user from the database.

        Args:
            uid (int): The user ID.

        Returns:
            user (User): The User object corresponding to the user ID.
        """
        return User.query.get(uid)
    
    bcrypt = Bcrypt(app)

    @login_manager.unauthorized_handler
    def unauthorized_callback():
        """
        Redirect unauthorized users to the index page.

        Returns:
            redirect: A redirect response to the index page.
        """
        return redirect(url_for('index'))

    from routes import register_routes
    register_routes(app, db, bcrypt)

    migrate = Migrate(app, db)

    return app

