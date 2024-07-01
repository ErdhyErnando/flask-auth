from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from models import User, ScriptLabels
from flask_socketio import emit
import os
import subprocess
import threading
import zmq
import time
import select

from werkzeug.utils import secure_filename

 # RASP_DIR = '/home/mhstrake28/flask-auth/orthosis_interface' # for hanif's linux
RASP_DIR = '/home/pi/flask-auth/orthosis-scripts'  # for raspberry pi

# Param parser for run_script_continuous()
def split_args(args):
    split_args = []
    for arg in args:
        if ' ' in arg:
            split_args.extend(arg.split())
        else:
            split_args.append(arg)
    return split_args

def register_routes(app, db, bcrypt, socketio):
    global running_thread, stop_thread
    running_thread = None
    stop_thread = False 

    def run_script_continuous(script_name, params):
        global stop_thread
        stop_thread = False

        try:
            port = "5001"
            # Creates a socket instance
            context = zmq.Context()
            socket = context.socket(zmq.SUB)
            # Connects to a bound socket
            socket.connect(f"tcp://localhost:{port}")
            # Subscribes to all topics
            socket.subscribe("")
            listPar = split_args(list(params.values()))
            process = subprocess.Popen(['python3', script_name] + listPar)
            while True:
                if stop_thread:
                    process.terminate()
                    break

                output = socket.recv_string()
                if output != "test-0:0:0:0":
                    output_with_breaks = output + '\n'
                    socketio.emit('script_output', {'output': output_with_breaks}, namespace='/')
                else:
                    break
                time.sleep(0.1)

        except Exception as e:
            socketio.emit('script_output', {'output': str(e)}, namespace='/')

    @socketio.on('start_script')
    def start_script(data):
        global running_thread
        filename = data['filename']
        params = data.get('params', {}) 
        if running_thread and running_thread.is_alive():
            emit('script_output', {'output': 'A script is already running.'}, namespace='/')
        else:
            running_thread = threading.Thread(target=run_script_continuous, args=(filename, params))
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

    @app.route('/uploadfile', methods=['GET', 'POST'])
    def uploadfile(): 
        if request.method == 'POST':
            file = request.files['file']
            title = request.form['title']
            output_label = request.form['outputLabel']

            if file and file.filename.endswith('.py'):
                folder_path = RASP_DIR
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)
                file_path = os.path.join(folder_path, file.filename)
                
                # Save the file
                file.save(file_path)

                # Save the label to db
                new_label = ScriptLabels(script_name=file.filename, Labels=output_label)
                db.session.add(new_label)
                db.session.commit()

                # Log for debugging
                print(f"File saved to: {file_path}")
                
                flash('File and label uploaded successfully', 'success')
            else:
                flash('Please select a valid python file', 'error')
        return render_template('uploadfile.html')

    # @app.route('/get-labels')
    # def get_labels():
    #     script_name = request.args.get('script')
    #     labels_entry = ScriptLabels.query.filter_by(script_name=script_name).first()
    #     if labels_entry:
    #         labels = labels_entry.Labels.split(',')
    #         return jsonify({'labels': labels})
    #     return jsonify({'labels': []})

    @app.route('/get-labels')
    def get_labels():
        script_name = request.args.get('script')
        label = ScriptLabels.query.filter_by(script_name=script_name).first()
        if label:
            return jsonify({'labels': label.Labels.split(',')})  # Assuming labels are comma-separated
        else:
            return jsonify({'labels': []}), 404
         
    @app.route('/gui', methods=['GET', 'POST'])
    def gui():
        if request.method == 'POST':
            selected_script = request.form.get('script')
            script_path = os.path.join(RASP_DIR, selected_script)

            if os.path.exists(script_path):
                socketio.emit('start_script', {'filename': script_path}, namespace='/')
            else:
                socketio.emit('script_output', {'output': 'Script not found'}, namespace='/')
        
        labels_query = ScriptLabels.query.all()
        labels_data = {}

        # labels for chartjs
        for label_entry in labels_query:
            labels_data[label_entry.script_name] = label_entry.Labels.split(',')
        
        scripts = get_scripts()

        return render_template('gui3.html', scripts=scripts, labels_data=labels_data)  


def get_scripts():
    scripts = []
    # for root, dirs, files in os.walk(SCRIPTS_DIR):
    for root, dirs, files in os.walk(RASP_DIR):
        for filename in files:
            if filename.endswith('.py'):
                script_path = os.path.join(root, filename)
                scripts.append(script_path)
    return scripts
