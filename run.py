from app import create_app, socketio

def run_flask_app():
    """
    Runs the Flask application.

    This function creates a Flask application using the `create_app` function from the `app` module.
    It then runs the application on the specified host and enables debug mode.

    Args:
        None

    Returns:
        None
    """
    flask_app = create_app()
    socketio.run(flask_app, host='0.0.0.0', debug=True)


if __name__ == '__main__':
    run_flask_app()

