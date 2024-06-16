#!/usr/bin/env python3
import zmq
import SharedArray as sa
import time


"""
function to publish data from orthosis device.
Input : array of SharedArray address from whom the will be retrieved
output : None                                                   
"""

def zmq_publisher(sa_address, stop_flag_add):
    print("pub running")

    port = "5001"
    # Creates a socket instance
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    # Binds the socket to a predefined port on localhost
    socket.bind(f"tcp://*:{port}")

    stop_flag = 0

    while stop_flag == 0:

        data_arr = []
        for address in sa_address:
            data_arr.append(sa.attach(address))

        data_string = "test"
        for data in data_arr :
            data_string += f":{data[0]}"

        print(data_string)

        flags = sa.attach(stop_flag_add)
        stop_flag = flags[0]
        socket.send_string(data_string)

    time.sleep(0.5)
    socket.send_string("test-0:0:0:0")