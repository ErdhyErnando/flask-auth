import os

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

# Function to get the scripts in the scripts directory
def get_scripts():
    scripts = []
    # for root, dirs, files in os.walk(SCRIPTS_DIR):
    for root, dirs, files in os.walk(RASP_DIR):
        for filename in files:
            if filename.endswith('.py'):
                script_path = os.path.join(root, filename)
                scripts.append(script_path)
    return scripts