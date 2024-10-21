# 🦾Orthosis Web App using Flask-SocketIO

This project is a specialized Flask Web Application designed to run on a Raspberry Pi, providing a user-friendly interface for controlling and monitoring an orthosis device. The application integrates user authentication, data visualization, and script management capabilities.

## Table of Contents

- [Features](#features)
- [Hardware Requirements](#hardware-requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Automatic Startup Using .bashrc](#automatic-startup-using-bashrc)
- [Usage](#usage)
- [Acknowledgements](#acknowledgements)

## Features

- User authentication with admin and regular user roles
- Real-time python script execution and monitoring using WebSockets (Flask-SocketIO)
- File management system for Python scripts
- Data logging capabilities
- Interactive GUI for script selection and execution
- Data visualization using Chart.js
- Command-line interface (CLI) via Shellinabox


## Hardware Requirements

The current application is run on the following hardware:

- **Raspberry Pi**: 2018 Raspberry Pi 4 Model b
- **Operating System**: Ubuntu 22.04

The Flask server is configured to start automatically on boot using bashrc, ensuring the application is always available when the Raspberry Pi is powered on.

## Project Structure

- `app.py`: Main application file for initializing and configuring the Flask app.
- `models.py`: Database models for User.
- `requirements.txt`: List of dependencies for the project.
- `routes.py`: Flask routes and SocketIO event handlers.
- `run.py`: Script to run the Flask application.
- `utils.py`: Utility functions for argument parsing and admin access control.
- `static/`: Static files (CSS, images, JavaScript).
- `templates/`: HTML templates for the web interface.

## Installation

1. Clone the repository:

   ```sh
   git clone https://github.com/ErdhyErnando/flask-auth.git
   cd flask-auth
   ```

2. Create a virtual environment and activate it:

   ```sh
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the dependencies:
   ```sh
   pip install -r requirements.txt
   ```

## Configuration

1. Update the `RASP_DIR` variable in `utils.py` and `routes.py` to point to your script directory.
2. Modify the database URI in `app.py` if needed.

## Running the Application

1. Initialize the database:

   ```sh
   flask db init
   flask db migrate
   flask db upgrade
   ```

2. The application will start automatically on boot. To run it manually:

   ```sh
   python3 run.py # or just `python` depending on python version
   ```

3. Access the application in your web browser at `http://<raspberry-pi-ip>:5000` or `http://localhost:5000`.

## Automatic Startup Using .bashrc

To make the application start automatically when the Raspberry Pi boots up, you can add the Python command to the `.bashrc` file:

1. Open the `.bashrc` file in a text editor:

   ```sh
   nano ~/.bashrc
   ```

2. Add the following line at the end of the file, replacing `/path/to/your/app` with the actual path to your application:

   ```sh
   python /path/to/your/app/run.py
   ```

3. Save the file and exit the text editor (in nano, press Ctrl+X, then Y, then Enter).

4. Reload the `.bashrc` file or restart the Raspberry Pi for the changes to take effect:

   ```sh
   source ~/.bashrc
   ```

Now, every time the Raspberry Pi boots up, it will automatically start the Flask application.

Note: This method will start the application in the current terminal session. For a more robust solution in a production environment, consider using a process manager like systemd or supervisor.

## Usage

1. Log in with your credentials or sign up for a new account (requires admin approval).
2. After logging in, navigate to the GUI page.
3. From the GUI page, navigate the file structure to select a script.
4. If using version 2 of the orthosis:
   a. Click the "Sudo IP Link" button.
   b. Wait for the light to go on and off before proceeding.
5. Input the parameters needed.
6. Click "Run" to open a confirmation modal, then confirm to execute scripts and view real-time output.
7. Monitor data visualization in real-time.
8. Log and download experiment data.

## Acknowledgements

- [Flask](https://flask.palletsprojects.com/)
- [Flask-SocketIO](https://flask-socketio.readthedocs.io/)
- [Chart.js](https://www.chartjs.org/)
- [Shellinabox](https://github.com/shellinabox/shellinabox)
