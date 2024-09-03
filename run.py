from app import create_app, socketio

def run_flask_app():
    """
    Run the Flask application with SocketIO support.

    This function creates the Flask application using the factory function
    create_app() and then runs it using Flask-SocketIO. It's configured to
    run in debug mode and accept connections from any IP address.

    Returns
    -------
    None

    Notes
    -----
    The application is run with the following settings:
    - host: '0.0.0.0' (accepts connections from any IP)
    - debug: True (runs in debug mode)
    - allow_unsafe_werkzeug: True (allows running in debug mode with SocketIO)
    """
    flask_app = create_app()
    socketio.run(flask_app, host='0.0.0.0', debug=True, allow_unsafe_werkzeug=True)

if __name__ == '__main__':
    run_flask_app()

