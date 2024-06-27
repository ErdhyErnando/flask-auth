import zmq
import SharedArray as sa
from ZMQ_pub import zmq_publisher
import multiprocessing as mp
import time


def increment():
    a[0] = 0
    b[0] = 0
    stop[0] = 0
    while a[0] < 100 and b[0] > -100:
        a[0] += 1
        b[0] -= 1
        time.sleep(0.1)

        
    
    stop[0] = 1


def run_publsiher():
    zmq_publisher(["shm://test1","shm://test2"], ["data1","data2"],"shm://stop")

    


if __name__ == "__main__" :

    if len(sa.list()) != 0:
        sa.delete("shm://test1")
        sa.delete("shm://test2")
        sa.delete("shm://stop")

    a = sa.create("shm://test1",1)
    b = sa.create("shm://test2",1)
    stop = sa.create("shm://stop",1)

    incr = mp.Process(target=increment)
    pub = mp.Process(target=run_publsiher)

    incr.start()
    pub.start()

