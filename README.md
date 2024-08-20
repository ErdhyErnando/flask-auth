# Orthosis Web App using Flask-SocketIO

This project is a specialized Flask Web Application designed to run on a Raspberry Pi, providing a user-friendly interface for controlling and monitoring an orthosis device. The application integrates secure user authentication, a command-line interface (CLI) via [Shellinabox](https://github.com/shellinabox/shellinabox), and real-time data visualization using [Flask-SocketIO](https://github.com/miguelgrinberg/Flask-SocketIO) and [Chart.js](https://github.com/chartjs/Chart.js).

## Project Structure

- `app.py`: Main application file for initializing and configuring the Flask app.
- `models.py`: Database models.
- `requirements.txt`: List of dependencies for the project.
- `routes.py`: Flask routes and SocketIO event handlers.
- `run.py`: Script to run the Flask application.
- `static/`: Static files (CSS, images, JavaScript).
- `templates/`: HTML templates.
- `utils.py`: Utility functions.
- `virt/`: Virtual environment directory.

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/ErdhyErnando/flask-auth.git
    cd flask-auth
    ```

2. Create a virtual environment and activate it:
    ```sh
    python3 -m venv <VIRTUAL_ENVIRONMENT_NAME>
    source <VIRTUAL_ENVIRONMENT_NAME>/bin/activate  # On Windows use `virt\Scripts\activate`
    ```

3. Install the dependencies:
    ```sh
    pip install -r requirements.txt
    ```

## Running the Application

1. Initialize the database:
    ```sh
    flask db init
    flask db migrate
    flask db upgrade
    ```

2. Run the Flask application:
    ```sh
    python run.py
    ```
