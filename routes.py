from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
from models import User
from flask_socketio import emit
import os
import subprocess
import threading

SCRIPTS_DIR = 'C:\\Users\\Erdhy Ernando\\Desktop\\Dev\\flask-auth\\orthosis-scripts'

def register_routes(app, db, bcrypt, socketio):
    global running_thread, stop_thread
    running_thread = None
    stop_thread = False

    def run_script_continuous(script_name):
        global stop_thread
        stop_thread = False
        try:
            process = subprocess.Popen(['python', script_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            while True:
                if stop_thread:
                    process.terminate()
                    break

                output = process.stdout.readline()
                if output:
                    socketio.emit('script_output', {'output': output}, namespace='/')
                else:
                    break

            for output in process.stdout.readlines():
                socketio.emit('script_output', {'output': output}, namespace='/')
            for output in process.stderr.readlines():
                socketio.emit('script_output', {'output': output}, namespace='/')

        except Exception as e:
            socketio.emit('script_output', {'output': str(e)}, namespace='/')

    @socketio.on('start_script')
    def start_script(data):
        global running_thread
        filename = data['filename']
        if running_thread and running_thread.is_alive():
            emit('script_output', {'output': 'A script is already running.'}, namespace='/')
        else:
            running_thread = threading.Thread(target=run_script_continuous, args=(filename,))
            running_thread.start()

    @socketio.on('stop_script')
    def stop_script():
        global stop_thread
        stop_thread = True
        if running_thread:
            running_thread.join()
            emit('script_output', {'output': 'Script stopped.'}, namespace='/')

    @app.route('/')
    def index():
        return render_template('index.html')

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

    @app.route('/logout')
    def logout():
        logout_user()
        return redirect(url_for('index'))

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500

    @app.route('/gui', methods=['GET', 'POST'])
    def gui():
        if request.method == 'POST':
            selected_script = request.form.get('script')
            script_path = os.path.join(SCRIPTS_DIR, selected_script)
            if os.path.exists(script_path):
                socketio.emit('start_script', {'filename': script_path}, namespace='/')
            else:
                socketio.emit('script_output', {'output': 'Script not found'}, namespace='/')
        return render_template('gui.html', scripts=get_scripts())  
    
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
    
def get_scripts():
    scripts = []
    for root, dirs, files in os.walk(SCRIPTS_DIR):
        for filename in files:
            if filename.endswith('.py'):
                script_path = os.path.join(root, filename)
                scripts.append(script_path)
    return scripts
