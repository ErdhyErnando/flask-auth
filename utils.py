import os

from functools import wraps
from flask import abort
from flask_login import current_user

import socket

# RASP_DIR = '/home/pi/flask-auth/orthosis-scripts'  # for raspberry pi
RASP_DIR = '/home/pi/OrthosisProject/orthosis_interface' # take file from OrthosisProject
# RASP_DIR = '/home/pi/OrthosisProject' # for testing pub dummy file 

def split_args(args):
    """
    Split command-line arguments(input params) that may contain spaces.

    Parameters
    ----------
    args : list
        A list of command-line arguments.

    Returns
    -------
    list
        A new list where arguments containing spaces are split into separate elements.

    Examples
    --------
    >>> split_args(['param1', 'param2 with spaces', 'param3'])
    ['param1', 'param2', 'with', 'spaces', 'param3']
    """
    split_args = []
    for arg in args:
        if ' ' in arg:
            split_args.extend(arg.split())
        else:
            split_args.append(arg)
    return split_args

def remove_empty_array(arr):
    """
    Remove empty elements from an array.

    Parameters
    ----------
    arr : list
        The input array that may contain empty elements.

    Returns
    -------
    list
        A new list with all non-empty elements from the input array.

    Examples
    --------
    >>> remove_empty_array(['', 'a', '', 'b', 'c', ''])
    ['a', 'b', 'c']
    """
    return [item for item in arr if item]

def get_scripts():
    """
    Get a list of Python script paths in the RASP_DIR directory.

    Returns
    -------
    list
        A list of full paths to Python scripts (.py files) found in the RASP_DIR directory
        and its subdirectories.

    Notes
    -----
    This function uses os.walk to recursively search for .py files in RASP_DIR.
    """
    scripts = []
    for root, dirs, files in os.walk(RASP_DIR):
        for filename in files:
            if filename.endswith('.py'):
                script_path = os.path.join(root, filename)
                scripts.append(script_path)
    return scripts

def admin_required(f):
    """
    Decorator to restrict access to admin users only.

    This decorator checks if the current user is authenticated and has the 'admin' role.
    If not, it aborts the request with a 403 Forbidden error.

    Parameters
    ----------
    f : function
        The view function to be decorated.

    Returns
    -------
    function
        The decorated function that includes the admin check.

    Notes
    -----
    This decorator should be used on routes that should only be accessible by admin users.
    It relies on Flask-Login's current_user object.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def get_raspberry_pi_ip():
    """
    Get the IP address of the Raspberry Pi.

    This function attempts to determine the IP address of the Raspberry Pi
    by creating a socket connection to an external server (8.8.8.8).
    If successful, it returns the local IP address. If an exception occurs,
    it returns the loopback address (127.0.0.1).

    Returns
    -------
    str
        The IP address of the Raspberry Pi as a string.

    Notes
    -----
    This function uses a UDP socket to determine the IP address.
    It does not actually send any data to the external server.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
    except Exception:
        ip_address = "127.0.0.1"
    finally:
        s.close()
    return ip_address