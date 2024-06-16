#!/usr/bin/env python3
import zmq

"""
Function to subscribe to a data.
input : topic (string) -> topic that want to be subscribe
output : None
"""

def zmq_subscriber(topic):
    port = "5001"
    # Creates a socket instance
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    # Connects to a bound socket
    socket.connect(f"tcp://localhost:{port}")
    # Subscribes to all topics
    socket.subscribe("")
    msg = socket.recv_string()
    return msg