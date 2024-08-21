from app import create_app, socketio

# Run the Flask app
def run_flask_app():
    flask_app = create_app()
    socketio.run(flask_app, host='0.0.0.0', debug=True, allow_unsafe_werkzeug=True)

if __name__ == '__main__':
    run_flask_app()

