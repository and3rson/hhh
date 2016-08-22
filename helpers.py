import os
from multiprocessing import Process, Pipe
from select import select
from subprocess import Popen, PIPE
import math
import struct

WORKER_COUNT = 4


def findfast(haystack, pattern):
    def process(worker_id, conn, offset, step):
        print '[', worker_id, ']', 'Worker started', offset, step
        haystack_len = len(haystack)
        pattern_len = len(pattern)

        i = offset
        while i < haystack_len - pattern_len + 1:
            found = True
            k = 0
            while k < pattern_len:
                if (haystack[i + k] != pattern[k]) and \
                        (pattern[k] is not None):
                    found = False
                    break
                k += 1
            if found:
                conn.send('FOUND:' + str(i) + '.')
            i += step
        print '[', worker_id, ']', 'Worker finished'
        conn.send('QUIT:0.')

    processes = []
    pipes = []
    remaining = 0

    for i in xrange(0, WORKER_COUNT):
        parent_conn, child_conn = Pipe()
        p = Process(target=process, args=(i, child_conn, i, WORKER_COUNT))
        p.start()
        processes.append(p)
        pipes.append(parent_conn)
        remaining += 1

    results = []

    while remaining > 0:
        iready, oready, eready = select(pipes, [], [], 3600)
        for pipe in iready:
            data = filter(None, pipe.recv().split('.'))
            for packet in data:
                cmd, arg = packet.split(':')
                if cmd == 'FOUND':
                    results.append(arg)
                else:
                    print 'Worker finished.', remaining, 'remaining'
                    remaining -= 1

    for process in processes:
        process.join()

    return results


def dump(data, info=None, width=16):
    i = 0
    s = '\n\tInfo: %s\n\tLength: %d\n\t\t' % (info, len(data))
    data = map(ord, data)
    for i in xrange(0, int(math.ceil(float(len(data)) / width))):
        s += '%04X || ' % (i * width)
        for k in xrange(0, width):
            if i * width + k < len(data):
                s += '%02X ' % data[i * width + k]
            else:
                s += '   '

            if not ((k + 1) % 4):
                s += '| '
        s += ' '
        for k in xrange(0, width):
            if i * width + k < len(data):
                if data[i * width + k] == 9:
                    s += '\\t'
                elif data[i * width + k] == 10:
                    s += '\\n'
                elif data[i * width + k] == 13:
                    s += '\\r'
                elif data[i * width + k] >= 32 and data[i * width + k] <= 126:
                    s += '%c ' % chr(data[i * width + k])
                else:
                    s += '. '

                if not ((k + 1) % 4):
                    s += '| '
            else:
                s += '   '
        s += '\n\t\t'
    return s


def find(where, what):
    index = 0
    while True:
        index = where.find(what, index)
        if index >= 0:
            yield index
            index += 1
        else:
            return


def find_process(name):
    ignore_pids = (os.getpid(), os.getppid())

    out, err = Popen(
        ['ps', 'ax', '--no-headers'],
        stdout=PIPE,
        stderr=PIPE
    ).communicate()
    for line in filter(None, out.split('\n')):
        parts = filter(None, line.split(' '))

        if len(parts) > 0:
            pid = int(parts[0])
            command = ' '.join(parts[4:])

            if name in command and pid not in ignore_pids:
                return pid, command
    return None, None


def pidof(s):
    out, err = Popen(['pidof', s], stdout=PIPE).communicate()
    if out.strip():
        pid = int(out.strip())
        f = open('/proc/{}/cmdline'.format(pid), 'r')
        app, _, args = f.read().partition('\x00')
        args = ' '.join(args.split('\x00'))
        f.close()
        return pid, app, args
    else:
        return None, None, None


def recast(v, from_, to):
    return struct.unpack(to, struct.pack(from_, v))[0]
