from ZMQ_subs import zmq_subscriber

msg = ""

while True:
    msg = zmq_subscriber("test")
    print(msg)