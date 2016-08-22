#!/usr/bin/env python2

from ptrace.debugger import *
import sys


def write(pid, offset, data):
    print repr(offset), repr(data)
    d = PtraceDebugger()
    ps = d.addProcess(pid, False)
    ps.writeBytes(offset, data)
    ps.detach()
    d.quit()

if __name__ == '__main__':
    write(int(sys.argv[1]), int(sys.argv[2]), ''.join(map(lambda x: chr(int(x)), sys.argv[3:])))
