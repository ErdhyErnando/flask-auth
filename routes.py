from flask import render_template, request, redirect, url_for
from flask_login import login_user, logout_user, current_user, login_required
from flask import flash
from models import User

def register_routes(app, db, bcrypt):
    """
    Register routes for the Flask application.

    Args:
        app (Flask): The Flask application instance.
        db (SQLAlchemy): The SQLAlchemy database instance.
        bcrypt (Bcrypt): The Bcrypt instance for password hashing.

    Returns:
        None
    """

    # Index Route
    @app.route('/')
    def index():
        """
        Render the index.html template.

        Returns:
            str: The rendered HTML content.
        """
        return render_template('index.html')


    # Signup Route
    @app.route('/signup', methods=['GET', 'POST'])
    def signup():
        """
        Handle the signup form submission.

        If the request method is GET, render the signup.html template.
        If the request method is POST, retrieve the username and password from the form,
        hash the password using Bcrypt, create a new user in the database, and redirect to the index page.

        Returns:
            str: The rendered HTML content or a redirect response.
        """
        if request.method == 'GET':
            return render_template('signup.html')
        elif request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            hashed_password = bcrypt.generate_password_hash(password)

            user = User(username=username, password=hashed_password, role='user')

            db.session.add(user)
            db.session.commit()
            return redirect(url_for('index'))


    # Login Route
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """
        Handle the login form submission.

        If the request method is GET, render the login.html template.
        If the request method is POST, retrieve the username and password from the form,
        retrieve the user from the database based on the username,
        check if the password matches the hashed password in the database,
        and either log in the user or display an error message.

        Returns:
            str: The rendered HTML content or an error message.
        """
        if request.method == 'GET':
            return render_template('login.html')
        elif request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            user = User.query.filter(User.username == username).first()

            if bcrypt.check_password_hash(user.password, password):
                login_user(user)
                return render_template('index.html')
            else:
                flash('Invalid Credentials', 'error')
                
        return render_template('login.html')
                
    
    # Logout Route
    @app.route('/logout')
    def logout():
        """
        Handle the logout request.

        Log out the currently logged-in user.

        Returns:
            str: A message indicating successful logout.
        """
        logout_user()
        return redirect(url_for('index'))
    

    # version page
    @app.route('/version1')
    #@login_required
    def version1():
        """
        Render the version1.html template.

        Returns:
            str: The rendered HTML content.
        """
        return render_template('version1.html')
    
    @app.route('/version2')
    #@login_required
    def version2():
        """
        Render the version2.html template.

        Returns:
            str: The rendered HTML content.
        """
        return render_template('version2.html')
    

    # Custom Error Pages

    # Invalid URL
    @app.errorhandler(404)
    def page_not_found(e):
        """
        Render the 404.html template for invalid URLs.

        Args:
            e (Exception): The exception object.

        Returns:
            tuple: A tuple containing the rendered HTML content and the HTTP status code.
        """
        return render_template('404.html'), 404
    
    # Internal Server Error
    @app.errorhandler(500)
    def internal_server_error(e):
        """
        Render the 500.html template for internal server errors.

        Args:
            e (Exception): The exception object.

        Returns:
            tuple: A tuple containing the rendered HTML content and the HTTP status code.
        """
        return render_template('500.html'), 500


