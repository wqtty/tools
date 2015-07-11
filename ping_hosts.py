import sys
import os
import platform
import subprocess
import Queue
import threading
import re

def worker_func(pingArgs, pending, done):
    try:
        while True:
            # Get the next address to ping.
            address = pending.get_nowait()

            ping = subprocess.Popen(pingArgs + [address],
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE
            )
            out, error = ping.communicate()

            # Output the result to the 'done' queue.
            done.put((out, error))
    except Queue.Empty:
        # No more addresses.
        pass
    finally:
        # Tell the main thread that a worker is about to terminate.
        done.put(None)

# The number of workers.
NUM_WORKERS = 4

plat = platform.system()
scriptDir = sys.path[0]
hosts = os.path.join(scriptDir, 'hosts.txt')

# The arguments for the 'ping', excluding the address.
if plat == "Windows":
    pingArgs = ["ping", "-n", "4", "-l", "1", "-w", "100"]
elif plat == "Linux":
    pingArgs = ["ping", "-c", "4", "-l", "1", "-s", "1", "-W", "1"]
elif plat == "Darwin":
    pingArgs = ["ping", "-c", "4", "-s", "1", "-W", "1"]
else:
    print plat
    raise ValueError("Unknown platform")

# The queue of addresses to ping.
pending = Queue.Queue()

# The queue of results.
done = Queue.Queue()

# Create all the workers.
workers = []
for _ in range(NUM_WORKERS):
    workers.append(threading.Thread(target=worker_func, args=(pingArgs, pending, done)))

# Put all the addresses into the 'pending' queue.
with open(hosts, "r") as hostsFile:
    for line in hostsFile:
        print re.match(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', line.strip()).group(0)
        pending.put(re.match(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', line.strip()).group(0))

# Start all the workers.
for w in workers:
    w.daemon = True
    w.start()

# Print out the results as they arrive.
numTerminated = 0
while numTerminated < NUM_WORKERS:
    result = done.get()
    if result is None:
        # A worker is about to terminate.
        numTerminated += 1
    else:
        print result[0] # out
        print result[1] # error

# Wait for all the workers to terminate.
for w in workers:
    w.join()