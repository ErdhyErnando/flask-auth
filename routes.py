from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from models import User, ScriptLabels
from flask_socketio import emit
import os
import json
import subprocess
import threading
import zmq
import time

import select
import signal

from werkzeug.utils import secure_filename

from utils import split_args, remove_empty_array, get_scripts, admin_required

import csv
from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError

# RASP_DIR = '/home/mhstrake28/OrthosisProject/orthosis_interface' # for hanif's linux
# RASP_DIR = '/home/mhstrake28/flask-auth/orthosis_interface'  # for hanif's linux with sharred array
RASP_DIR = '/home/pi/flask-auth/orthosis-scripts'  # for raspberry pi
# RASP_DIR = '/home/pi/OrthosisProject/orthosis_interface'  # for orthosis_interface outside raspberry pi


# All Flask & SocketIO routes
def register_routes(app, db, bcrypt, socketio):
    global running_thread, stop_thread
    running_thread = None
    stop_thread = False 

    # Function to run the script; zmq, socketio, subprocess
    def run_script_continuous(script_name, params):
        global stop_thread, process
        stop_thread = False

        try:
            port = "5001"
            context = zmq.Context()
            socket = context.socket(zmq.SUB)
            socket.connect(f"tcp://localhost:{port}")
            socket.subscribe("")
            socket.setsockopt(zmq.RCVTIMEO, 100)
            listPar = split_args(list(params.values()))
            cleanListPar = remove_empty_array(listPar)
            print(listPar)

            process = subprocess.Popen(['python3', script_name] + cleanListPar, preexec_fn=os.setsid)
            while not stop_thread:
                try:
                    output = socket.recv_string()
                    if output != "STOP":
                        output_with_breaks = output + '\n'
                        socketio.emit('script_output', {'output': output_with_breaks}, namespace='/')
                    else :
                        print('stop marker received')
                        socketio.emit('script_output', {'output': 'Script finished'}, namespace='/')
                        break
                    print(stop_thread)
                except zmq.Again:       
                    # Timeout occured, just continue the loop
                    continue
            if stop_thread:
                os.killpg(os.getpgid(process.pid), signal.SIGINT)
        except Exception as e:
            socketio.emit('script_output', {'output': str(e)}, namespace='/')         
                 

    # SocketIO start and stop script
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
        global stop_thread, running_thread, process
        stop_thread = True
        if running_thread and running_thread.is_alive():
            running_thread.join(timeout=5)
        if process:
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGINT)
                process.wait(timeout=5)
            except:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        emit('script_output', {'output': 'Script stopped.'}, namespace='/')

    
    # data logging
    @socketio.on('log_data')
    def log_data(data):
        print("Received log data: ", data)
        log_dir = os.path.join(RASP_DIR, 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        script_name = os.path.splitext(os.path.basename(data['filename']))[0]
        log_filename = f"{script_name}_log_{timestamp}.txt"
        log_path = os.path.join(log_dir, log_filename)

        try:
            with open(log_path, 'w') as f:
                # Get all unique timestamps
                all_timestamps = set()
                for label, points in data['data'].items():
                    all_timestamps.update(point['x'] for point in points)
                
                # Sort timestamps
                sorted_timestamps = sorted(all_timestamps)
                
                for timestamp in sorted_timestamps:
                    # Convert timestamp to time format
                    time_str = str(timedelta(seconds=int(timestamp)))
                    
                    # Collect data for this timestamp
                    data_points = []
                    for label, points in data['data'].items():
                        point = next((p for p in points if p['x'] == timestamp), None)
                        if point:
                            data_points.append(f"{label}:{point['y']:.1f}")
                    
                    # Write the line
                    line = f"time: {time_str} " + ":".join(data_points) + "\n"
                    f.write(line)

            print(f"Log file created: {log_path}")
            emit('logging_complete', {'message': f'Data logged to {log_filename}'})
        except Exception as e:
            print(f"Error during logging: {str(e)}")
            emit('logging_complete', {'message': f'Error during logging: {str(e)}'})


    # Page routes
    @app.route('/')
    def index():
        return render_template('index.html')

    # Signup and login routes
    @app.route('/signup', methods=['GET', 'POST'])
    @admin_required
    def signup():
        if request.method == 'GET':
            return render_template('signup.html')
        elif request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            # check if username already exists
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('Username already exists', 'error')
                return redirect(url_for('signup'))

            hashed_password = bcrypt.generate_password_hash(password)
            user = User(username=username, password=hashed_password, role='user')
            try:
                db.session.add(user)
                db.session.commit()
                flash('Account created successfully', 'success')
                return redirect(url_for('index'))
            except IntegrityError:
                db.session.rollback()
                flash('Error creating account', 'error')
                return redirect(url_for('signup'))

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


    # Error Pages
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500

    @app.errorhandler(403)
    def forbidden(error):
        return render_template('403.html'), 403
    

    # Get File Structure
    @app.route('/get_file_structure')
    def get_file_structure():
        file_structure = generate_file_structure(RASP_DIR)  
        return jsonify({
            'structure': file_structure,
            'base_path': RASP_DIR
        })

    def generate_file_structure(path):
        structure = []
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                structure.append({
                    'name': item,
                    'type': 'folder',
                    'children': generate_file_structure(item_path)
                })
            else:
                structure.append({
                    'name': item,
                    'type': 'file'
                })
        return structure


    # File upload and GUI routes
    @app.route('/get_folders')
    def get_folders():
        folders = [f for f in os.listdir(RASP_DIR) if os.path.isdir(os.path.join(RASP_DIR, f))]
        return jsonify({'folders': folders})

    @app.route('/uploadfile', methods=['GET', 'POST'])
    def uploadfile(): 
        if request.method == 'POST':
            print("Form Data: ", request.form)
            file = request.files['file']
            title = request.form['title']
            selected_folder = request.form['folder']

            if file and file.filename.endswith('.py'):
                folder_path = os.path.join(RASP_DIR, selected_folder)
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)
                file_path = os.path.join(folder_path, file.filename)
                
                # Save the file
                file.save(file_path)

                # Log for debugging
                print(f"File saved to: {file_path}")
                
                flash('File and label uploaded successfully', 'success')
            else:
                flash('Please select a valid python file', 'error')
        return render_template('uploadfile.html')


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
        
        # Instead of get_scripts(), we'll use the file structure
        file_structure = generate_file_structure(RASP_DIR)

        return render_template('gui3.html', file_structure=file_structure, labels_data=labels_data)