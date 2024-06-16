#!/usr/bin/env python3
import subprocess

# Command to run the script in a new gnome-terminal window
subprocess.Popen(['gnome-terminal', '--', 'python3', '-u', '/home/mhstrake28/bachelorarbeit/Code/Inverted Pendulum Simulation/JumpingSpring.py'])

# This will be executed immediately without waiting for the subprocess to finish
print("Hello World")
