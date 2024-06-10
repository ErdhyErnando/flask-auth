from flask import render_template, request, redirect, url_for
from flask_login import login_user, logout_user, current_user, login_required
from flask import flash
from models import User

from flask import jsonify

import os
import subprocess

# TODO: Change this to the path on Raspberry Pi
SCRIPTS_DIR = 'C:\\Users\\Erdhy Ernando\\Desktop\\Dev\\flask-auth\\orthosis-scripts'

def register_routes(app, db, bcrypt):

    # Index Route
    @app.route('/')
    def index():
        return render_template('index.html')

    # ========= Authentication Route ============

    # Signup Route
    @app.route('/signup', methods=['GET', 'POST'])
    def signup():
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
        if request.method == 'GET':
            return render_template('login.html')
        elif request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            user = User.query.filter(User.username == username).first()

            if user is None:
                flash('No account exists with that username', 'error')
            elif bcrypt.check_password_hash(user.password, password):
                login_user(user)
                return render_template('index.html')
            else:
                flash('Invalid Credentials', 'error')
                
        return render_template('login.html')
                
    #Logout Route
    @app.route('/logout')
    def logout():
        logout_user()
        return redirect(url_for('index'))
    
    # ========= Custom Error Pages ============

    # Invalid URL
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404
    
    # Internal Server Error
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500
    
    # ========= Pages ============
    
    # GUI Page
    @app.route('/gui', methods=['GET', 'POST'])
    def gui():
        output = None  # Initialize output variable
        if request.method == 'POST':
            selected_script = request.form.get('script')  
            script_path = os.path.join(SCRIPTS_DIR, selected_script)
            if os.path.exists(script_path):
                result = subprocess.run(['python', script_path], capture_output=True)
                output = result.stdout.decode('utf-8')  
            else:
                output = 'Script not found'
        return render_template('gui.html', scripts=get_scripts(), output=output)  
    

    #Upload New File
    @app.route('/uploadfile', methods=['GET', 'POST'])
    def uploadfile(): 
        if request.method == 'POST':
            file = request.files['file']
            if file and file.filename.endswith('.py'):
                file_path = os.path.join(SCRIPTS_DIR, file.filename)
                file.save(file_path)
                flash('File uploaded successfully', 'success')
            else:
                flash('please select a valid python file', 'error')
        
        return render_template('uploadfile.html')
    
# ========= Helper Functions ============
def get_scripts():
    scripts = []
    for root, dirs, files in os.walk(SCRIPTS_DIR):
        for filename in files:
            if filename.endswith('.py'):
                # Prepend directory path to filename (optional)
                script_path = os.path.join(root, filename)
                scripts.append(script_path)  # Or scripts.append(filename)
    return scripts