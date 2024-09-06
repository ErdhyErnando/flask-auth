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
# RASP_DIR = '/home/pi/OrthosisProject' # for testing pub dummy file 

# All Flask & SocketIO routes
def register_routes(app, db, bcrypt, socketio):
    """
    Register all routes and SocketIO events for the Flask application.

    This function sets up all the routes, SocketIO events, and related functionality
    for the orthosis web application.

    Parameters
    ----------
    app : Flask
        The Flask application instance.
    db : SQLAlchemy
        The SQLAlchemy database instance.
    bcrypt : Bcrypt
        The Bcrypt instance for password hashing.
    socketio : SocketIO
        The SocketIO instance for real-time communication.

    Notes
    -----
    This function defines several nested functions and decorators for various
    routes and SocketIO events. It handles script execution, data logging,
    user authentication, file management, and error handling.
    """
    global running_thread, stop_thread
    running_thread = None
    stop_thread = False 

    # Function to run the script; zmq, socketio, subprocess
    def run_script_continuous(script_name, params):
        """
        Run a script continuously and emit its output via SocketIO.

        Parameters
        ----------
        script_name : str
            The name of the script to run.
        params : dict
            A dictionary of parameters to pass to the script.

        Notes
        -----
        This function uses ZeroMQ to receive output from the script and
        emits it to connected clients via SocketIO. It can be stopped
        by setting the global stop_thread variable to True.
        """
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
        """
        SocketIO event handler for starting a script.

        Parameters
        ----------
        data : dict
            A dictionary containing 'filename' and optionally 'params'.

        Notes
        -----
        This function starts a new thread to run the specified script if no
        script is currently running.
        """
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
        """
        SocketIO event handler for stopping the currently running script.

        This function sets the stop_thread flag to True and attempts to
        terminate the running script process.
        """
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
        """
        SocketIO event handler for logging experimental data.

        Parameters
        ----------
        data : dict
            A dictionary containing 'filename', 'params', and 'data' to be logged.

        Notes
        -----
        This function creates a log file with experiment metadata and data points.
        It emits a 'logging_complete' event when finished.
        """
        print("Received log data: ", data)
        log_dir = os.path.join(RASP_DIR, 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        timestamp = datetime.now()
        script_name = os.path.splitext(os.path.basename(data['filename']))[0]
        log_filename = f"{script_name}_log_{timestamp.strftime('%Y%m%d_%H%M%S')}.txt"
        log_path = os.path.join(log_dir, log_filename)

        try:
            with open(log_path, 'w') as f:
                # Write metadata
                f.write(f"File Name: {script_name}\n")
                f.write(f"Experiment Date: {timestamp.strftime('%d.%m.%y')}\n")
                f.write(f"Experiment Time: {timestamp.strftime('%H:%M')}\n\n")
                f.write("User Input Parameters:\n")
                for param, value in data['params'].items():
                    f.write(f"{param}: {value}\n")
                f.write("\n")

                # Get all unique labels
                all_labels = list(data['data'].keys())
                
                # Write header
                header = "Time," + ",".join(all_labels)
                f.write(header + "\n")
                
                # Get all unique timestamps
                all_timestamps = set()
                for points in data['data'].values():
                    all_timestamps.update(point['x'] for point in points)
                
                # Sort timestamps
                sorted_timestamps = sorted(all_timestamps)
                
                for timestamp in sorted_timestamps:
                    # Convert timestamp to time format
                    time_str = str(timedelta(seconds=int(timestamp)))
                    
                    # Collect data for this timestamp
                    row_data = [time_str]
                    for label in all_labels:
                        point = next((p for p in data['data'][label] if p['x'] == timestamp), None)
                        if point is None or point['y'] is None:
                            row_data.append("-")
                        else:
                            row_data.append(f"{point['y']:.1f}")
                    
                    # Write the row
                    f.write(",".join(row_data) + "\n")

            print(f"Log file created: {log_path}")
            emit('logging_complete', {'message': f'Data logged to {log_filename}'})
        except Exception as e:
            print(f"Error during logging: {str(e)}")
            emit('logging_complete', {'message': f'Error during logging: {str(e)}'})


    # Page routes
    @app.route('/')
    def index():
        """
        Render the index page.

        Returns
        -------
        str
            The rendered HTML for the index page.
        """
        return render_template('index.html')

    # Signup and login routes
    @app.route('/signup', methods=['GET', 'POST'])
    @admin_required
    def signup():
        """
        Handle user signup (admin only).

        Returns
        -------
        str
            The rendered HTML for the signup page or a redirect response.

        Notes
        -----
        This route is protected by the admin_required decorator.
        """
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
        """
        Handle user login.

        Returns
        -------
        str
            The rendered HTML for the login page or a redirect response.
        """
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
        """
        Handle user logout.

        Returns
        -------
        werkzeug.wrappers.Response
            A redirect response to the index page.
        """
        logout_user()
        return redirect(url_for('index'))   


    # Error Pages
    @app.errorhandler(404)
    def page_not_found(e):
        """
        Handle 404 Not Found errors.

        Parameters
        ----------
        e : Exception
            The exception that triggered the 404 error.

        Returns
        -------
        tuple
            A tuple containing the rendered 404 page and the status code.
        """
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        """
        Handle 500 Internal Server Error.

        Parameters
        ----------
        e : Exception
            The exception that triggered the 500 error.

        Returns
        -------
        tuple
            A tuple containing the rendered 500 page and the status code.
        """
        return render_template('500.html'), 500

    @app.errorhandler(403)
    def forbidden(error):
        """
        Handle 403 Forbidden errors.

        Parameters
        ----------
        error : Exception
            The exception that triggered the 403 error.

        Returns
        -------
        tuple
            A tuple containing the rendered 403 page and the status code.
        """
        return render_template('403.html'), 403
    

    # Get File Structure
    @app.route('/get_file_structure')
    def get_file_structure():
        """
        Get the file structure of the RASP_DIR directory.

        Returns
        -------
        flask.Response
            A JSON response containing the file structure and base path.
        """
        file_structure = generate_file_structure(RASP_DIR)  
        return jsonify({
            'structure': file_structure,
            'base_path': RASP_DIR
        })

    def generate_file_structure(path):
        """
        Generate a nested dictionary representing the file structure.

        Parameters
        ----------
        path : str
            The root path to start generating the file structure from.

        Returns
        -------
        list
            A list of dictionaries representing the file structure.
        """
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
        """
        Get a list of folders in the RASP_DIR directory.

        Returns
        -------
        flask.Response
            A JSON response containing a list of folder names.
        """
        folders = [f for f in os.listdir(RASP_DIR) if os.path.isdir(os.path.join(RASP_DIR, f))]
        return jsonify({'folders': folders})

    @app.route('/uploadfile', methods=['GET', 'POST'])
    def uploadfile(): 
        """
        Handle file uploads.

        Returns
        -------
        str
            The rendered HTML for the upload file page or a redirect response.
        """
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
        """
        Handle the main GUI page.

        Returns
        -------
        str
            The rendered HTML for the GUI page.

        Notes
        -----
        This function handles both GET and POST requests. For POST requests,
        it starts the selected script. It also prepares the file structure
        and script labels for the GUI.
        """
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