#!/usr/bin/env python

import os
import sys
import subprocess
from multiprocessing import Process, Queue

def run_command_live(args, cwd=None, shell=True, checkrc=False, workerid=None):

    """ Show realtime output for a subprocess """

    p = subprocess.Popen(args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=cwd,
            shell=shell)
    pid = p.pid
    so = ""
    se = ""
    while p.poll() is None:
        lo = p.stdout.readline() # This blocks until it receives a newline.
        sys.stdout.write('worker[' + str(workerid) + '] (' + str(pid) + ') ' + lo)
        so += lo
    print p.stdout.read()
    
    return (p.returncode, so, "", pid)


def mp_worker(input, output, options):

    """ A worker is forked per command """

    for command in iter(input.get, 'STOP'):
        thispid = os.getpid()
        print "worker[%s] --> command: %s" % (thispid, command)
        (rc, so, se, pid) = run_command_live(command, workerid=thispid)
        rdict = {
            'command': command,
            'rc': rc,
            'so': so,
            'se': se,
            'pid': pid
        }
        output.put(rdict)


def mp_processor(commands, options={}):

    """ Spawn processes for each command in a list and return the results """

    NUMBER_OF_PROCESSES = len(commands)    

    # Create queues
    task_queue = Queue()
    done_queue = Queue()

    # Add each command to the queue
    for command in commands:
        task_queue.put(command)

    # Fork the processes
    for i in range(NUMBER_OF_PROCESSES):
        Process(target=mp_worker, args=(task_queue, done_queue, options)).start()    

    # Collect results
    results = []
    for i in range(NUMBER_OF_PROCESSES):
        results.append(done_queue.get())

    # End the queue
    for i in range(NUMBER_OF_PROCESSES):
        task_queue.put('STOP')

    return results


if __name__ == "__main__":

    cmd1 = "whoami"
    cmd2 = "uname -a"
    cmd3 = "last | head"
    cmd4 = "for x in $(seq 1 10); do echo $x; sleep 1; done;"
    cmd5 = "for x in $(seq 1 10); do echo $x; sleep 2; done;"
    cmd6 = "for x in $(seq 1 10); do echo $x; sleep 3; done;"
    commands = [cmd1, cmd2, cmd3, cmd4, cmd5, cmd6]
    rdata = mp_processor(commands, options={})
